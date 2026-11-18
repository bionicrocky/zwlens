"""Z-Wave MAC frame (MPDU) decoding for classic 2-channel regions and Long Range.

Layouts follow ITU-T G.9959 as implemented by the open-source Z-Wave JS zniffer.
The 3-channel configuration used in Japan/Korea has a different header and is
not decoded.
"""
from __future__ import annotations

from .cc import decode_payload
from .model import BROADCAST, BROADCAST_LR, Frame

HEADER_SINGLECAST, HEADER_MULTICAST, HEADER_ACK, HEADER_EXPLORER, HEADER_ROUTED = 1, 2, 3, 5, 8


def xor_checksum(data: bytes) -> int:
    c = 0xFF
    for b in data:
        c ^= b
    return c


def crc16(data: bytes, crc: int = 0x1D0F) -> int:
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
        crc &= 0xFFFF
    return crc


def _apply_payload(f: Frame, payload: bytes) -> None:
    f.payload = payload.hex()
    d = decode_payload(payload)
    f.cc, f.cmd, f.cc_name, f.cmd_name = d["cc"], d["cmd"], d["cc_name"], d["cmd_name"]
    f.encap, f.encrypted, f.summary = d["encap"], d["encrypted"], d["summary"]
    if d["event"]:
        f.event = d["event"]


def checksum_state(data: bytes):
    """Return (ok16, ok8) for a candidate MPDU."""
    ok16 = len(data) >= 11 and crc16(data[:-2]) == int.from_bytes(data[-2:], "big")
    ok8 = len(data) >= 9 and xor_checksum(data[:-1]) == data[-1]
    return ok16, ok8


def decode_mpdu(data: bytes, rate: str | None = None) -> Frame | None:
    """Decode one MPDU. `rate` is '9.6k', '40k', '100k', 'LR' or None (auto-detect)."""
    if rate == "LR":
        return _decode_lr(data)
    if len(data) < 9:
        return None
    f = Frame(speed=rate)
    declared = data[7]
    if declared != len(data):
        if 9 <= declared < len(data):
            data = data[:declared]
        else:
            f.errors.append(f"length byte {declared} does not match {len(data)} captured bytes")
    ok16, ok8 = checksum_state(data)
    if rate == "100k":
        cs, ok = 2, ok16
    elif rate in ("9.6k", "40k"):
        cs, ok = 1, ok8
    elif ok16:
        cs, ok, f.speed = 2, True, "100k"
    else:
        cs, ok = 1, ok8
    if not ok:
        f.errors.append("bad checksum")

    f.raw = data.hex()
    f.length = len(data)
    f.home = data[0:4].hex()
    f.src = f.txn = data[4]
    fc0, fc1 = data[5], data[6]
    routed_bit = bool(fc0 & 0x80)
    f.ack_req = bool(fc0 & 0x40)
    header = fc0 & 0x0F
    f.seq = fc1 & 0x0F
    body = data[8:len(data) - cs]
    if not body:
        f.errors.append("truncated frame")
        return f

    if header == HEADER_ACK:
        f.kind, f.dst = "ack", body[0]
    elif header == HEADER_MULTICAST:
        f.kind, f.dst = "multicast", BROADCAST
        n = body[0] & 0x1F
        _apply_payload(f, body[1 + n:])
    elif header == HEADER_EXPLORER:
        f.kind, f.dst = "explorer", body[0]
        if len(body) >= 9:
            command = body[1] & 0x1F
            f.inbound = bool(body[2] & 0x02)
            f.repeaters = [r for r in body[5:9] if r]
            f.summary = {0: "", 1: "inclusion request", 2: "search result"}.get(command, "")
            if command == 0:
                extra = f.summary
                _apply_payload(f, body[9:])
                f.summary = f.summary or extra
            elif command == 1:
                f.cc_name, f.cmd_name = "Explorer", "Inclusion Request"
            else:
                f.cc_name, f.cmd_name = "Explorer", "Search Result"
        else:
            f.errors.append("truncated explorer header")
    elif header == HEADER_ROUTED or (header == HEADER_SINGLECAST and routed_bit):
        f.routed, f.dst = True, body[0]
        if len(body) < 3:
            f.errors.append("truncated routing header")
            return f
        flags, hops = body[1], body[2]
        f.inbound = bool(flags & 0x01)
        n = hops >> 4
        hop = hops & 0x0F
        if f.inbound:
            hop = (hop + 1) % 16
        f.hop = hop
        f.repeaters = list(body[3:3 + n])
        off = 3 + n
        if flags & 0x08 and off < len(body):  # extended header
            ext_len, ext_type = body[off] >> 4, body[off] & 0x0F
            ext = body[off + 1:off + 1 + ext_len]
            if ext_type == 0 and ext:
                f.wake = "1000 ms" if ext[0] & 0x40 else "250 ms" if ext[0] & 0x20 else None
            elif ext_type == 1:
                f.rep_rssi = [b - 256 for b in ext if b > 0x7F]  # 0x7D-0x7F mean "not available"
            off += 1 + ext_len
        # Which radio actually sent this copy of the frame.
        if f.inbound:
            f.txn = f.src if hop >= n else (f.repeaters[hop] if hop < len(f.repeaters) else f.src)
        else:
            f.txn = f.src if hop == 0 else (f.repeaters[hop - 1] if hop - 1 < len(f.repeaters) else f.src)
        if flags & 0x04:
            f.kind, f.route_failed = "routed_err", str(flags >> 4)
        elif flags & 0x02:
            f.kind = "routed_ack"
        else:
            _apply_payload(f, body[off:])
    elif header == HEADER_SINGLECAST:
        f.dst = body[0]
        _apply_payload(f, body[1:])
    else:
        f.errors.append(f"unknown header type {header}")
    return f


def _decode_lr(data: bytes) -> Frame | None:
    if len(data) < 14:
        return None
    f = Frame(speed="LR", raw=data.hex(), length=len(data))
    if crc16(data[:-2]) != int.from_bytes(data[-2:], "big"):
        f.errors.append("bad checksum")
    f.home = data[0:4].hex()
    ids = int.from_bytes(data[4:7], "big")
    f.src = f.txn = ids >> 12
    f.dst = ids & 0xFFF
    fc = data[8]
    f.ack_req = bool(fc & 0x80)
    header = fc & 0x07
    f.seq = data[9]
    f.noise = float(int.from_bytes(data[10:11], "big", signed=True))
    off = 12
    if fc & 0x40 and len(data) > 12:
        off = 13 + (data[12] & 0x07)
    payload = data[off:-2]
    if header == HEADER_ACK:
        f.kind = "ack"
        if payload:
            f.ack_rssi = float(int.from_bytes(payload[0:1], "big", signed=True))
    else:
        if f.dst == BROADCAST_LR:
            f.dst = BROADCAST
        _apply_payload(f, payload)
    return f


def find_mpdu(buf: bytes) -> Frame | None:
    """Locate a checksum-valid classic MPDU anywhere in `buf` (SDR tools add varying prefixes)."""
    n = len(buf)
    best = None
    for off in range(0, max(0, n - 8)):
        length = buf[off + 7]
        if length < 9 or off + length > n:
            continue
        cand = buf[off:off + length]
        ok16, ok8 = checksum_state(cand)
        if not (ok16 or ok8):
            continue
        header = cand[5] & 0x0F
        if header not in (1, 2, 3, 5, 8) or cand[4] == 0:
            continue
        if ok16 or off == 0:
            return decode_mpdu(cand)
        if best is None:
            best = cand
    return decode_mpdu(best) if best is not None else None


def build_mpdu(home: str, src: int, dst: int, payload: bytes = b"", *, seq: int = 1,
               ack: bool = False, ack_req: bool = True, rate: str = "40k",
               repeaters=(), hop: int = 0, inbound: bool = False,
               routed_ack: bool = False, routed_err: int | None = None) -> bytes:
    """Build a classic MPDU. Used to generate sample captures and by the tests."""
    fc0 = HEADER_ACK if ack else HEADER_SINGLECAST
    body = bytes([dst])
    if repeaters:
        fc0 |= 0x80
        flags = (1 if inbound else 0) | (2 if routed_ack else 0)
        if routed_err is not None:
            flags |= 0x04 | (routed_err << 4)
        raw_hop = (hop - 1) % 16 if inbound else hop
        body += bytes([flags, (len(repeaters) << 4) | raw_hop]) + bytes(repeaters)
    if ack_req and not ack:
        fc0 |= 0x40
    body += payload
    cs = 2 if rate == "100k" else 1
    head = bytes.fromhex(home) + bytes([src, fc0, seq & 0x0F, 8 + len(body) + cs])
    frame = head + body
    if cs == 2:
        return frame + crc16(frame).to_bytes(2, "big")
    return frame + bytes([xor_checksum(frame)])
