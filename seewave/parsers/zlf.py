"""Parser for Zniffer capture files (.zlf) from the Silicon Labs Zniffer or Z-Wave JS."""
from __future__ import annotations

import struct

from ..model import Frame, ParseResult
from ..mpdu import decode_mpdu

HEADER_SIZE = 2048
NET_EPOCH_TICKS = 621355968000000000
TRAILER_ZNIFFER = 0xFE
KNOWN_TRAILERS = {0xFE, 0xF8, 0xF5, 0xF4}
RATES = {0: "9.6k", 1: "40k", 2: "100k", 3: "LR"}


def rssi_to_dbm(raw: int, chip: str = "700") -> float:
    """Convert a Zniffer RSSI byte to dBm. The formulas are the reverse-engineered ones
    used by Z-Wave JS, so treat the result as approximate."""
    if chip == "500":
        return raw * 1.5 - 153.5
    return raw * 4.0 - 256.0


def parse_zniffer_frame(raw: bytes, chip: str = "700") -> Frame | None:
    """Decode one Zniffer serial frame (0x21 data/beam frames; 0x23 command frames are ignored)."""
    if len(raw) < 7 or raw[0] != 0x21:
        return None
    ftype = raw[1]
    rate = RATES.get(raw[4] & 0x1F)
    channel = raw[4] >> 5
    rssi = rssi_to_dbm(raw[6], chip)
    if ftype == 0x01:
        if len(raw) < 11 or raw[7] != 0x21 or raw[8] != 0x03:
            return None
        mpdu = raw[10:10 + raw[9]]
        f = decode_mpdu(mpdu, rate)
        if f is None:
            return None
    elif ftype == 0x04 and len(raw) >= 9:
        f = Frame(kind="beam", raw=raw.hex(), length=len(raw), speed=rate)
        f.dst = (int.from_bytes(raw[8:10], "big") & 0x0FFF) if rate == "LR" and len(raw) >= 10 else raw[8]
    else:
        return None
    f.channel, f.rssi = channel, rssi
    return f


def parse_zlf(data: bytes, capture: str = "", chip: str = "700") -> ParseResult:
    frames: list[Frame] = []
    warnings: list[str] = []
    if len(data) < HEADER_SIZE:
        return ParseResult("zniffer", [], ["File is shorter than the 2048-byte ZLF header."])
    pos, skipped, bad = HEADER_SIZE, 0, 0
    while pos + 14 <= len(data):
        ticks, = struct.unpack_from("<Q", data, pos)
        length, = struct.unpack_from("<I", data, pos + 9)
        end = pos + 13 + length
        if length > 4096 or end >= len(data) or data[end] not in KNOWN_TRAILERS:
            # Resynchronise on the next end-of-entry marker instead of giving up.
            bad += 1
            nxt = data.find(bytes([TRAILER_ZNIFFER]), pos + 1)
            if nxt < 0 or bad > 200:
                break
            pos = nxt + 1
            continue
        raw = data[pos + 13:end]
        trailer = data[end]
        pos = end + 1
        if trailer != TRAILER_ZNIFFER:
            skipped += 1
            continue
        f = parse_zniffer_frame(raw, chip)
        if f is None:
            skipped += 1
            continue
        ms = ((ticks & ((1 << 62) - 1)) - NET_EPOCH_TICKS) / 10000
        f.ts = ms / 1000.0
        f.source, f.capture = "zniffer", capture
        frames.append(f)
    if bad:
        warnings.append(f"{bad} damaged region(s) were skipped while reading the capture.")
    if not frames:
        warnings.append("No decodable Zniffer frames were found.")
    badsum = sum(1 for f in frames if "bad checksum" in f.errors)
    if frames and badsum > len(frames) * 0.5:
        warnings.append("Most frames fail their checksum; the capture may use the 3-channel "
                        "(Japan/Korea) frame format, which is not supported.")
    return ParseResult("zniffer", frames, warnings, {"skipped": skipped})


def write_zlf(entries) -> bytes:
    """Write a .zlf from (timestamp_seconds, mpdu_bytes, rate, rssi_dbm) tuples. Used for samples/tests."""
    out = bytearray(HEADER_SIZE)
    out[0] = 0x68
    struct.pack_into(">H", out, 0x07FE, 0x2312)
    rate_ids = {v: k for k, v in RATES.items()}
    for ts, mpdu, rate, rssi in entries:
        if rate is None:  # already a complete Zniffer frame (e.g. a wake-up beam)
            ticks = (int(ts * 1000) * 10000 + NET_EPOCH_TICKS) | (2 << 62)
            out += struct.pack("<QBI", ticks, 0x01, len(mpdu)) + mpdu + bytes([TRAILER_ZNIFFER])
            continue
        raw_rssi = max(0, min(255, round((rssi + 256) / 4)))
        channel = 0 if rate == "100k" else 1 if rate == "40k" else 2
        raw = bytes([0x21, 0x01, 0, 0, (channel << 5) | rate_ids[rate], 0, raw_rssi, 0x21, 0x03,
                     len(mpdu)]) + mpdu
        ticks = (int(ts * 1000) * 10000 + NET_EPOCH_TICKS) | (2 << 62)
        out += struct.pack("<QBI", ticks, 0x01, len(raw)) + raw + bytes([TRAILER_ZNIFFER])
    return bytes(out)
