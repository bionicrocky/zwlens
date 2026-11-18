"""Parsers for SDR-derived captures.

SDR decoders (rtl_zwave, waving-z, GNU Radio / Scapy-radio flows, custom scripts)
have no common output format, so this module is deliberately tolerant:

* text: one frame per line, containing the frame as hex somewhere on the line,
  optionally with a timestamp and an RSSI value; or key/value lines
  (HomeId: ..., SourceNodeId: ..., DestNodeId: ..., Payload: ...).
* pcap: classic libpcap files; each packet is searched for a checksum-valid frame.
"""
from __future__ import annotations

import re
import struct
from datetime import datetime, timezone

from ..model import Frame, ParseResult
from ..mpdu import _apply_payload, find_mpdu

EPOCH = re.compile(r"(?<![\w.])(1\d{9})(\.\d+)?(?![\w])")
ISO = re.compile(r"(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d):(\d\d)(\.\d+)?")
TOD = re.compile(r"(?<![\d:])(\d\d):(\d\d):(\d\d)(\.\d+)?(?![\d:])")
RSSI = re.compile(r"rssi[\s=:\"']{0,4}(-?\d+(?:\.\d+)?)", re.I)
HEXRUN = re.compile(r"(?:(?:0x)?[0-9a-fA-F]{2}[\s:,\-]{0,2}){9,}")
KV = {
    "home": re.compile(r"home\s*_?id\W{1,3}(?:0x)?([0-9a-f]{8})", re.I),
    "src": re.compile(r"(?:source|src)\w*\W{1,3}(?:0x)?([0-9a-f]{1,2})\b", re.I),
    "dst": re.compile(r"(?:dest|dst)\w*\W{1,3}(?:0x)?([0-9a-f]{1,2})\b", re.I),
    "payload": re.compile(r"payload\W{1,3}((?:(?:0x)?[0-9a-f]{2}[\s,:]*)+)", re.I),
    "cc": re.compile(r"command\s*_?class\W{1,3}(?:0x)?([0-9a-f]{2})\b", re.I),
}
PCAP_MAGIC = {b"\xd4\xc3\xb2\xa1": ("<", 1e-6), b"\xa1\xb2\xc3\xd4": (">", 1e-6),
              b"\x4d\x3c\xb2\xa1": ("<", 1e-9), b"\xa1\xb2\x3c\x4d": (">", 1e-9)}


def is_pcap(data: bytes) -> bool:
    return data[:4] in PCAP_MAGIC


def _take_time(line: str):
    """Return (timestamp or None, line with the timestamp removed)."""
    m = ISO.search(line)
    if m:
        dt = datetime(*(int(m.group(i)) for i in range(1, 7)), tzinfo=timezone.utc)
        return dt.timestamp() + float(m.group(7) or 0), line[:m.start()] + " " + line[m.end():]
    m = EPOCH.search(line)
    if m:
        return float(m.group(1) + (m.group(2) or "")), line[:m.start()] + " " + line[m.end():]
    m = TOD.search(line)
    if m:
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + float(m.group(4) or 0)
        return t, line[:m.start()] + " " + line[m.end():]
    return None, line


def _hex_bytes(s: str) -> bytes:
    s = re.sub(r"0x", "", s, flags=re.I)
    s = re.sub(r"[^0-9a-fA-F]", "", s)
    return bytes.fromhex(s[:len(s) // 2 * 2])


def _kv_frame(line: str) -> Frame | None:
    home, src, dst = (KV[k].search(line) for k in ("home", "src", "dst"))
    if not (home and src and dst):
        return None
    f = Frame(home=home.group(1).lower(), src=int(src.group(1), 16), dst=int(dst.group(1), 16))
    f.txn = f.src
    payload = b""
    cc = KV["cc"].search(line)
    if cc:
        payload += bytes([int(cc.group(1), 16)])
    p = KV["payload"].search(line)
    if p:
        payload += _hex_bytes(p.group(1))
    _apply_payload(f, payload)
    f.length = 9 + len(payload)
    m = re.search(r"\back\w*\W{1,3}(1|true)\b", line, re.I)
    f.ack_req = bool(m)
    return f


def parse_sdr_text(text: str, capture: str = "") -> ParseResult:
    frames, warnings, rejected = [], [], 0
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        ts, rest = _take_time(line)
        rssi = RSSI.search(rest)
        if rssi:
            rest_nohex = rest[:rssi.start()] + " " + rest[rssi.end():]
        else:
            rest_nohex = rest
        f = None
        for m in sorted(HEXRUN.finditer(rest_nohex), key=lambda m: -len(m.group(0))):
            f = find_mpdu(_hex_bytes(m.group(0)))
            if f:
                break
        if f is None:
            f = _kv_frame(rest)
        if f is None:
            if HEXRUN.search(rest_nohex):
                rejected += 1
            continue
        f.ts, f.source, f.capture = ts, "sdr", capture
        if rssi:
            f.rssi = float(rssi.group(1))
        frames.append(f)
    if rejected:
        warnings.append(f"{rejected} line(s) contained hex data without a checksum-valid Z-Wave frame "
                        "(noise, partial frames, or an unsupported format).")
    if not frames:
        warnings.append("No Z-Wave frames were recognised in this text.")
    elif all(f.ts is None for f in frames):
        warnings.append("The capture has no timestamps; rate and timing analysis is disabled for it.")
    return ParseResult("sdr", frames, warnings)


def parse_pcap(data: bytes, capture: str = "") -> ParseResult:
    endian, frac = PCAP_MAGIC[data[:4]]
    frames, warnings, pos, total = [], [], 24, 0
    while pos + 16 <= len(data):
        sec, sub, incl, _orig = struct.unpack_from(endian + "IIII", data, pos)
        pos += 16
        if incl > 65535 or pos + incl > len(data):
            warnings.append("The pcap file is truncated or damaged; reading stopped early.")
            break
        pkt = data[pos:pos + incl]
        pos += incl
        total += 1
        f = find_mpdu(pkt)
        if f is None:
            continue
        f.ts, f.source, f.capture = sec + sub * frac, "sdr", capture
        frames.append(f)
    if total and not frames:
        warnings.append("The pcap was read but none of its packets contain a checksum-valid Z-Wave frame.")
    elif total > len(frames):
        warnings.append(f"{total - len(frames)} of {total} packets held no valid Z-Wave frame and were skipped.")
    return ParseResult("sdr", frames, warnings)
