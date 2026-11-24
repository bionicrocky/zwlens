"""Parser for Z-Wave JS driver logs (files, Home Assistant add-on logs, live log events)."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from ..cc import ENCAP_TAGS, lookup_log_cc, split_camel
from ..model import Frame, ParseResult

HEAD = re.compile(
    r"^\s*(?:(\d{4})-(\d\d)-(\d\d)[T ])?(\d\d):(\d\d):(\d\d)[.,](\d{3})Z?\s+"
    r"(SERIAL|DRIVER|CNTRLR|CONFIG|ZNIFFR)\s?(.*)$")
NODE = re.compile(r"\[Node (\d+)\]")
TAG = re.compile(r"\[([^\]\[]+)\]")
CCTAG = re.compile(r"\[(\w+?)CC(\w*)\]")
DBM = re.compile(r"(-?\d+(?:\.\d+)?)\s*dBm")
BOX = " \t│├└─┌┐┘┬┴┼"

EVENT_RULES = [
    ("dead", ("presumed dead", "node is dead", "is now dead")),
    ("no_response", ("did not respond", "timed out while waiting for a response",
                     "failed to send the command", "failed to send the message")),
    ("asleep", ("is asleep", "is now asleep")),
    ("awake", ("is awake", "is now awake", "wakeup notification", "wake up notification",
               "wake-up notification")),
    ("alive", ("is alive", "is now alive")),
]


def looks_like_log(text: str) -> bool:
    hits = 0
    for line in text.splitlines()[:400]:
        if HEAD.match(line):
            hits += 1
            if hits >= 2:
                return True
    return hits >= 1 and len(text.splitlines()) < 5


def _speed(v: str) -> str | None:
    v = v.lower()
    if "long range" in v:
        return "LR"
    for key, name in (("9.6", "9.6k"), ("40", "40k"), ("100", "100k")):
        if key in v:
            return name
    return None


def _dbm(v: str | None) -> float | None:
    if not v:
        return None
    m = DBM.search(v)
    return float(m.group(1)) if m else None


def classify_event(low: str) -> str | None:
    for name, needles in EVENT_RULES:
        if any(n in low for n in needles):
            return name
    if "interview" in low and "fail" in low:
        return "interview_failed"
    if "nonce" in low and any(w in low for w in ("fail", "expired", "no nonce", "out of sync", "desync", "timed out")):
        return "nonce_error"
    if ("decode" in low or "decrypt" in low) and any(w in low for w in ("fail", "cannot", "could not", "unable")):
        return "decode_error"
    if "dropping" in low and ("message" in low or "command" in low):
        return "decode_error"
    return None


class LogParser:
    """Incremental parser: feed() text in any chunking, then finish()."""

    def __init__(self, capture: str = "", source: str = "log", controller: int = 1):
        self.capture, self.source, self.controller = capture, source, controller
        self.home: str | None = None
        self.frames: list[Frame] = []
        self.warnings: list[str] = []
        self._cur = None
        self._pending: dict[str, Frame] = {}
        self._last_out: Frame | None = None
        self._day = 0
        self._last_tod: float | None = None
        self.entries = 0

    # -- input -----------------------------------------------------------
    def feed(self, text: str) -> None:
        for line in text.splitlines():
            m = HEAD.match(line)
            if m:
                self._flush()
                self._cur = (self._ts(m), m.group(8), m.group(9), [])
            elif self._cur is not None and line.strip():
                self._cur[3].append(line)

    def finish(self) -> ParseResult:
        self._flush()
        if self.home:
            for f in self.frames:
                if f.home is None:
                    f.home = self.home
        if not self.entries:
            self.warnings.append("No Z-Wave JS log entries were recognised.")
        elif not any(f.kind == "data" for f in self.frames):
            self.warnings.append(
                "The log contains no command traffic. Set the driver log level to 'debug' "
                "to capture commands and transmit reports.")
        return ParseResult("log", self.frames, self.warnings,
                           {"controller": self.controller, "home": self.home})

    def _ts(self, m) -> float:
        tod = int(m.group(4)) * 3600 + int(m.group(5)) * 60 + int(m.group(6)) + int(m.group(7)) / 1000
        if m.group(1):
            day = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
            return day.timestamp() + tod
        if self._last_tod is not None and tod < self._last_tod - 43200:
            self._day += 1  # crossed midnight in a date-less log
        self._last_tod = tod
        return self._day * 86400 + tod

    def _flush(self) -> None:
        if self._cur is None:
            return
        cur, self._cur = self._cur, None
        self.entries += 1
        try:
            self._emit(*cur)
        except Exception as exc:  # one malformed entry must never abort a whole log
            if len(self.warnings) < 20:
                self.warnings.append(f"Skipped an unparseable log entry: {exc}")

    # -- interpretation --------------------------------------------------
    def _new(self, ts, **kw) -> Frame:
        f = Frame(source=self.source, capture=self.capture, ts=ts, home=self.home, **kw)
        self.frames.append(f)
        return f

    def _emit(self, ts: float, label: str, rest: str, body: list) -> None:
        if label == "SERIAL":
            return
        rest = rest.strip()
        direction = "out" if rest.startswith("»") else "in" if rest.startswith("«") else ""
        head = rest.lstrip("»« ").strip()
        text = "\n".join([head] + body)
        low = text.lower()

        m = re.search(r"own node id[:\s]+(\d+)", low)
        if m:
            self.controller = int(m.group(1))
        m = re.search(r"home id[:\s]+(?:0x)?([0-9a-f]{8})\b", low)
        if m:
            self.home = m.group(1)

        m = NODE.search(head)
        node = int(m.group(1)) if m else None
        tags = TAG.findall(head)
        fields = {}
        after_cc: list[str] = []
        for ln in body:
            s = ln.strip(BOX)
            if s.startswith("["):
                after_cc = []
                continue
            k, sep, v = s.partition(":")
            if sep:
                fields[k.strip().lower()] = v.strip()
                after_cc.append(f"{k.strip()}: {v.strip()}")

        from ..knowledge import match_log
        for eid in match_log(text):
            self._new(ts, kind="event", src=node, event="kb:" + eid, text=head[:240])

        func = next((t for t in tags if t.startswith("SendData") or t in (
            "ApplicationCommand", "BridgeApplicationCommand", "ApplicationUpdateRequest",
            "GetBackgroundRSSI")), None)

        if label == "DRIVER" and func:
            if func.startswith("SendData"):
                if direction == "out" and node is not None:
                    f = self._new(ts, kind="data", src=self.controller, dst=node, txn=self.controller,
                                  ack_req=True)
                    self._apply_cc(f, text, after_cc)
                    cb = fields.get("callback id")
                    if cb:
                        self._pending[cb] = f
                    self._last_out = f
                    return
                if direction == "in" and "transmit status" in fields:
                    self._tx_report(fields)
                    return
                return
            if func in ("ApplicationCommand", "BridgeApplicationCommand") and node is not None:
                f = self._new(ts, kind="data", src=node, dst=self.controller, txn=node,
                              rssi=_dbm(fields.get("rssi")))
                self._apply_cc(f, text, after_cc)
                return
            if func == "ApplicationUpdateRequest" and node is not None:
                self._new(ts, kind="data", src=node, dst=self.controller, txn=node, cc=0x01, cmd=0x01,
                          cc_name="Z-Wave Protocol", cmd_name="Node Info")
                return
            if func == "GetBackgroundRSSI" and direction == "in":
                vals = [float(v) for v in re.findall(r"channel \d+:\s*(-?\d+(?:\.\d+)?)\s*dbm", low)]
                if vals:
                    self._new(ts, kind="noise", noise=sum(vals) / len(vals))
                return

        event = classify_event(low)
        if event:
            self._new(ts, kind="event", src=node, event=event, text=head[:240])

    def _apply_cc(self, f: Frame, text: str, detail: list) -> None:
        ccs = CCTAG.findall(text)
        if not ccs:
            f.cc_name, f.cmd_name = "(no command)", ""
            return
        for name, _cmd in ccs[:-1]:
            cid, disp = lookup_log_cc(name)
            f.encap.append(ENCAP_TAGS.get(cid, disp))
        name, cmd = ccs[-1]
        f.cc, f.cc_name = lookup_log_cc(name)
        f.cmd_name = split_camel(cmd)
        if f.cc in (0x98, 0x9F):
            f.encap.append(ENCAP_TAGS[f.cc])
            if f.cc == 0x9F and "nonce report" in f.cmd_name.lower() and re.search(r"sos:\s*true", text.lower()):
                f.event = "s2_sos"
        f.encap = list(dict.fromkeys(f.encap))
        f.summary = ", ".join(detail[:3])[:160]

    def _tx_report(self, fields: dict) -> None:
        f = self._pending.pop(fields.get("callback id", ""), None) or self._last_out
        if f is None or f.tx_status is not None:
            return
        status = fields["transmit status"]
        f.tx_status = status.split(",")[0].strip()
        m = re.search(r"took\s+(\d+(?:\.\d+)?)\s*ms", status)
        if m:
            f.tx_ms = float(m.group(1))
        if fields.get("routing attempts", "").isdigit():
            f.attempts = int(fields["routing attempts"])
        f.speed = _speed(fields.get("protocol & route speed", "")) or f.speed
        f.scheme = fields.get("routing scheme")
        f.ack_rssi = _dbm(fields.get("ack rssi"))
        f.noise = _dbm(fields.get("measured noise floor"))
        reps = [int(x) for x in re.findall(r"\d+", fields.get("repeater node ids", ""))]
        if reps:
            f.routed, f.repeaters = True, reps
        if fields.get("route failed here"):
            f.route_failed = fields["route failed here"]
        ch = fields.get("tx channel no.")
        if ch and ch.isdigit():
            f.channel = int(ch)


def parse_log(text: str, capture: str = "") -> ParseResult:
    p = LogParser(capture)
    p.feed(text)
    return p.finish()
