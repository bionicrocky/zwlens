"""Format detection and a single entry point for parsing any supported capture."""
from __future__ import annotations

from ..model import ParseResult
from .sdr import is_pcap, parse_pcap, parse_sdr_text
from .zlf import parse_zlf
from .zwavejs_log import looks_like_log, parse_log


def _decode_text(data: bytes) -> str:
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8-sig", errors="replace")


def parse_bytes(data: bytes, name: str = "", chip: str = "700") -> ParseResult:
    """Parse a capture of unknown type. Never raises for malformed input."""
    lower = name.lower()
    try:
        if lower.endswith(".zlf") or (len(data) >= 2048 and data[0] == 0x68 and data[0x7FE:0x800] == b"\x23\x12"):
            return parse_zlf(data, name, chip)
        if is_pcap(data):
            return parse_pcap(data, name)
        if data[:4] == b"\x0a\x0d\x0d\x0a":
            return ParseResult("sdr", [], ["pcapng files are not supported; convert with "
                                           "'editcap -F pcap in.pcapng out.pcap'."])
        if b"\x00" in data[:4096] and data[:2] not in (b"\xff\xfe", b"\xfe\xff"):
            return ParseResult("unknown", [], ["Unrecognised binary file."])
        text = _decode_text(data)
        if looks_like_log(text):
            return parse_log(text, name)
        return parse_sdr_text(text, name)
    except Exception as exc:  # defensive: a bad file must not take the tool down
        return ParseResult("unknown", [], [f"Could not parse this file: {exc}"])
