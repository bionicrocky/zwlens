"""Unified frame model shared by every parser and the analysis engine."""
from __future__ import annotations

from dataclasses import dataclass, field

BROADCAST = 255
BROADCAST_LR = 4095


@dataclass
class Frame:
    # provenance
    source: str = ""          # log | zniffer | sdr | live
    capture: str = ""         # file name / live URL
    kind: str = "data"        # data | ack | routed_ack | routed_err | explorer | multicast | beam | event | noise
    ts: float | None = None   # seconds (epoch when the source has dates)

    # addressing
    home: str | None = None
    src: int | None = None
    dst: int | None = None
    txn: int | None = None    # node that physically transmitted this frame (differs from src when routed)
    seq: int | None = None
    ack_req: bool = False

    # routing
    routed: bool = False
    repeaters: list = field(default_factory=list)
    hop: int | None = None
    inbound: bool = False
    route_failed: str | None = None
    scheme: str | None = None
    wake: str | None = None       # sender asked the last hop to wake the target with a beam
    rep_rssi: list = field(default_factory=list)  # dBm measured by repeaters (routed ACK)

    # radio
    speed: str | None = None  # 9.6k | 40k | 100k | LR
    channel: int | None = None
    rssi: float | None = None      # dBm as heard by the observer
    ack_rssi: float | None = None  # dBm of the ACK (TX reports in logs)
    noise: float | None = None     # dBm noise floor sample

    # application
    cc: int | None = None
    cmd: int | None = None
    cc_name: str = ""
    cmd_name: str = ""
    encap: list = field(default_factory=list)
    encrypted: bool = False
    summary: str = ""
    length: int = 0
    raw: str = ""
    payload: str = ""

    # controller TX report (logs / live)
    tx_status: str | None = None   # OK | NoAck | Fail
    tx_ms: float | None = None
    attempts: int | None = None

    # status events and annotations
    event: str | None = None
    text: str = ""
    errors: list = field(default_factory=list)

    # filled in by analysis
    idx: int = -1
    msg: int | None = None
    role: str = ""            # orig | retx | fwd | ack
    conv: int | None = None

    def label(self) -> str:
        if self.kind == "event":
            return self.text or (self.event or "event")
        if self.kind == "ack":
            return "ACK"
        if self.kind == "routed_ack":
            return "Routed ACK"
        if self.kind == "routed_err":
            return "Routed error" + (f" (failed at hop {self.route_failed})" if self.route_failed else "")
        if self.kind == "beam":
            return "Wake-up beam"
        if self.kind == "noise":
            return f"Background noise {self.noise:.0f} dBm" if self.noise is not None else "Background noise"
        name = " ".join(x for x in (self.cc_name, self.cmd_name) if x) or "(no payload)"
        return name

    def to_dict(self) -> dict:
        d = {
            "idx": self.idx, "ts": self.ts, "source": self.source, "capture": self.capture,
            "kind": self.kind, "home": self.home, "src": self.src, "dst": self.dst,
            "txn": self.txn, "seq": self.seq, "ack_req": self.ack_req, "routed": self.routed,
            "repeaters": self.repeaters, "hop": self.hop, "inbound": self.inbound,
            "route_failed": self.route_failed, "scheme": self.scheme, "wake": self.wake,
            "rep_rssi": self.rep_rssi, "speed": self.speed,
            "channel": self.channel, "rssi": self.rssi, "ack_rssi": self.ack_rssi,
            "noise": self.noise, "cc": self.cc, "label": self.label(), "encap": self.encap,
            "encrypted": self.encrypted, "summary": self.summary, "length": self.length,
            "raw": self.raw, "tx_status": self.tx_status, "tx_ms": self.tx_ms,
            "attempts": self.attempts, "event": self.event, "errors": self.errors,
            "msg": self.msg, "role": self.role, "conv": self.conv,
        }
        return d


@dataclass
class ParseResult:
    kind: str                 # log | zniffer | sdr
    frames: list
    warnings: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)
