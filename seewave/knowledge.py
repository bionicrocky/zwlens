"""Knowledge base of known Z-Wave issues and failure modes, and the checks that look for them.

Each catalogue entry (see kb_entries.py) describes one failure mode. An entry is detected by
* a log rule: a regular expression matched against Z-Wave JS log entries, and/or
* a traffic detector: a function below that inspects decoded messages.
Entries with neither are reference material: real problems that traffic alone cannot reveal.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from statistics import median

from .controllers import action_for
from .kb_entries import ENTRIES
from .model import BROADCAST

SNIFFED = ("zniffer", "sdr")
BY_ID = {e["id"]: e for e in ENTRIES}
LOG_RULES = [(re.compile(rx, re.I), e["id"]) for e in ENTRIES for rx in e.get("log", [])]
# Fallback when an entry's advice does not name a recognisable controller action.
CATEGORY_ACTION = {
    "rf": "routes", "routing": "rebuild", "controller": "firmware", "power-sleep": "config",
    "security": "exclude", "inclusion-interview": "include", "application-config": "config",
    "firmware": "firmware", "long-range": "include", "capacity-traffic": "config",
    "hardware-environment": "routes",
}
CATEGORIES = {
    "rf": "Radio and interference", "routing": "Routing and mesh", "controller": "Controller",
    "power-sleep": "Battery and sleep", "security": "Security", "inclusion-interview": "Inclusion and interview",
    "application-config": "Device behaviour and configuration", "firmware": "Firmware",
    "long-range": "Long Range", "capacity-traffic": "Traffic and capacity",
    "hardware-environment": "Hardware and environment",
}


def match_log(text: str) -> list[str]:
    """IDs of catalogue entries whose log rule matches this log entry."""
    return list(dict.fromkeys(eid for rx, eid in LOG_RULES if rx.search(text)))


class Ctx:
    def __init__(self, frames, msgs, cats, net, nm):
        self.frames, self.msgs, self.cats, self.net, self.nm = frames, msgs, cats, net, nm
        self.home = net.get("home") or ""
        self.ctrl = net.get("controller")
        self.mine = [m for m in msgs if (m.home or "") == self.home]
        self.minutes = (net["duration"] / 60.0) if net.get("duration") else None
        self.by_src = defaultdict(list)
        self.by_dst = defaultdict(list)
        for m in self.mine:
            self.by_src[m.src].append(m)
            if m.dst not in (None, BROADCAST):
                self.by_dst[m.dst].append(m)
        self.cat = {c["id"]: c for c in cats if not c["foreign"]}

    def name(self, nid):
        return self.nm(self.home, nid)

    def key(self, nid):
        return f"{self.home or '*'}:{nid}"

    def is_cmd(self, m, cc, *words):
        f = m.first
        return f.cc == cc and all(w in f.cmd_name.lower() for w in words)


def hit(sev, text, ctx=None, node=None):
    return {"severity": sev, "text": text, "node": ctx.key(node) if ctx and node is not None else None}


DETECTORS = {}


def detector(eid):
    def wrap(fn):
        DETECTORS[eid] = fn
        return fn
    return wrap


@detector("application-busy-or-rejected")
def _busy(c):
    out = []
    for nid, ms in c.by_src.items():
        n = sum(1 for m in ms if c.is_cmd(m, 0x22, "busy"))
        if n:
            out.append(hit("warn" if n >= 3 else "info", f"{c.name(nid)} answered 'Application Busy' {n} time(s).", c, nid))
    return out + _rejected(c)


def _rejected(c):
    out = []
    for nid, ms in c.by_src.items():
        n = sum(1 for m in ms if c.is_cmd(m, 0x22, "rejected"))
        if n:
            out.append(hit("warn", f"{c.name(nid)} rejected {n} request(s).", c, nid))
    return out


@detector("supervision-fail-nosupport-working")
def _supervision(c):
    out = []
    for nid, ms in c.by_src.items():
        bad = Counter(m.first.summary for m in ms if c.is_cmd(m, 0x6C, "report") and m.first.summary in ("fail", "no support"))
        for status, n in bad.items():
            out.append(hit("warn", f"{c.name(nid)} reported Supervision status '{status}' {n} time(s): "
                           "it received the command but did not carry it out.", c, nid))
    return out


@detector("s2-bootstrap-failure")
def _kex(c):
    return [hit("crit", f"{c.name(m.src)} sent S2 KEX Fail: secure inclusion was aborted.", c, m.src)
            for m in c.mine if m.first.cc == 0x9F and (m.first.cmd == 0x07 or "kex fail" in m.first.cmd_name.lower())][:5]


@detector("device-reset-locally")
def _reset(c):
    seen = {m.src for m in c.mine if m.first.cc == 0x5A}
    return [hit("crit", f"{c.name(n)} announced it was factory reset. It has left the network and its node ID is now a ghost.", c, n)
            for n in sorted(seen)]


@detector("battery-low")
def _battery(c):
    out = []
    for nid, cat in c.cat.items():
        b = cat.get("battery") or ""
        if "LOW" in b:
            out.append(hit("warn", f"{c.name(nid)} sent a low-battery warning.", c, nid))
        else:
            m = re.match(r"(\d+)", b)
            if m and int(m.group(1)) <= 20:
                out.append(hit("warn" if int(m.group(1)) <= 10 else "info", f"{c.name(nid)} battery is at {m.group(1)}%.", c, nid))
    return out


@detector("wakeup-interval-misconfig")
def _wake_freq(c):
    out = []
    for nid, ms in c.by_src.items():
        times = [m.first.ts for m in ms if c.is_cmd(m, 0x84, "notification")]
        gaps = [b - a for a, b in zip(times, times[1:]) if b - a > 5]
        if len(gaps) >= 2 and median(gaps) < 300 and c.net.get("has_time"):
            out.append(hit("warn", f"{c.name(nid)} wakes up every {median(gaps):.0f} s on average, which drains its battery fast.", c, nid))
        for m in ms:
            if c.is_cmd(m, 0x84, "interval", "report") and "interval:" in m.first.summary:
                secs = int(re.search(r"(\d+)", m.first.summary).group(1))
                if 0 < secs < 600:
                    out.append(hit("info", f"{c.name(nid)} is configured to wake every {secs} s.", c, nid))
                    break
    return out


@detector("missing-wake-up-no-more-information")
def _no_more_info(c):
    out = []
    for nid, ms in c.by_src.items():
        wakes = [m.first.ts for m in ms if c.is_cmd(m, 0x84, "notification")]
        if len(wakes) < 2:
            continue
        sleeps = [m.first.ts for m in c.by_dst.get(nid, []) if c.is_cmd(m, 0x84, "no more")]
        missed = sum(1 for t in wakes if not any(0 <= s - t <= 15 for s in sleeps))
        if missed >= 2 and missed >= len(wakes) * 0.5:
            out.append(hit("info", f"{c.name(nid)} woke up {len(wakes)} times but was told to go back to sleep "
                           f"only {len(wakes) - missed} time(s); it stays awake until its own timeout.", c, nid))
    return out


@detector("polling-storm")
def _polling(c):
    out = []
    if c.ctrl is None:
        return out
    for nid, ms in c.by_dst.items():
        gets = [m for m in ms if m.src == c.ctrl and m.first.cmd_name.lower().endswith("get")
                and "nonce" not in m.first.cmd_name.lower()]
        if len(gets) < 15:
            continue
        rate = len(gets) / c.minutes if c.minutes else None
        if rate is None or rate >= 4:
            top = Counter(m.first.label() for m in gets).most_common(1)[0]
            out.append(hit("warn", f"The controller polled {c.name(nid)} {len(gets)} times"
                           + (f" ({rate:.0f}/min)" if rate else "") + f", mostly {top[0]}.", c, nid))
    return out


@detector("duplicate-reports-multichannel-lifeline")
def _dupes(c):
    out = []
    for nid, ms in c.by_src.items():
        if nid == c.ctrl:
            continue
        last, dup = {}, 0
        for m in ms:
            f = m.first
            sig = (m.dst, f.payload or f.label() + f.summary)
            if "report" in f.cmd_name.lower() and not f.encrypted and sig in last and 0 < f.ts - last[sig] <= 1.0:
                dup += 1
            last[sig] = f.ts
        if dup >= 3:
            out.append(hit("info", f"{c.name(nid)} sent the same report twice in a row {dup} times.", c, nid))
    return out


@detector("crc-errors-collisions")
def _corrupt(c):
    sn = [f for f in c.frames if f.source in SNIFFED and f.kind != "beam"]
    bad = sum(1 for f in sn if "bad checksum" in f.errors)
    if len(sn) >= 20 and bad / len(sn) > 0.05:
        return [hit("crit" if bad / len(sn) > 0.3 else "warn",
                    f"{bad} of {len(sn)} captured frames ({bad / len(sn):.0%}) failed their checksum.")]
    return []


@detector("nop-ping-loop")
def _nop(c):
    out = []
    for nid, ms in c.by_dst.items():
        n = sum(1 for m in ms if m.first.cc == 0x00)
        failed = sum(1 for m in ms if m.first.cc == 0x00 and m.outcome in ("failed", "unacked"))
        if n >= 5:
            out.append(hit("warn" if failed >= n * 0.5 else "info",
                           f"The controller pinged {c.name(nid)} {n} times ({failed} unanswered).", c, nid))
    return out


@detector("s0-nonce-timeout")
def _nonce(c):
    out = []
    for nid in c.cat:
        gets = [m for m in c.by_dst.get(nid, []) if m.first.cc == 0x98 and m.first.cmd == 0x40 and not m.superseded
                and m.first.source in SNIFFED]
        reports = [m.first.ts for m in c.by_src.get(nid, []) if m.first.cc == 0x98 and m.first.cmd == 0x80]
        missed = sum(1 for g in gets if g.outcome == "ok" and not any(0 <= t - g.first.ts <= 3 for t in reports))
        if missed >= 2:
            out.append(hit("warn", f"{c.name(nid)} acknowledged {missed} S0 nonce requests but never sent the nonce.", c, nid))
    return out


@detector("flirs-beam-failure")
def _beam(c):
    out = []
    beams = defaultdict(list)
    for f in c.frames:
        if f.kind == "beam" and f.dst not in (None, BROADCAST):
            beams[f.dst].append(f.ts)
    for nid, times in beams.items():
        heard = [m.first.ts for m in c.by_src.get(nid, [])] + \
                [fr.ts for m in c.by_dst.get(nid, []) for fr in m.frames if fr.kind in ("ack", "routed_ack")]
        silent = sum(1 for t in times if not any(0 <= h - t <= 4 for h in heard))
        if silent >= 2 and silent >= len(times) * 0.5:
            out.append(hit("warn", f"{c.name(nid)} was sent {len(times)} wake-up beams and stayed silent after {silent} of them.", c, nid))
    return out


@detector("ota-firmware-update-failure")
def _ota(c):
    nodes = Counter()
    for m in c.mine:
        if m.first.cc == 0x7A:
            nodes[m.dst if m.src == c.ctrl else m.src] += 1
    return [hit("info", f"A firmware update is exchanging data with {c.name(n)} ({k} messages); expect heavy traffic until it ends.", c, n)
            for n, k in nodes.items() if k >= 5]


@detector("transport-service-segmentation-failure")
def _transport(c):
    nodes = Counter(m.src for m in c.mine if m.first.cc == 0x55)
    return [hit("info", f"{c.name(n)} is splitting large messages into {k} Transport Service segments.", c, n)
            for n, k in nodes.items() if k >= 4]


@detector("direct-association-traffic")
def _assoc(c):
    pairs = Counter()
    for m in c.mine:
        if c.ctrl is not None and c.ctrl not in (m.src, m.dst) and m.dst not in (None, BROADCAST) \
                and m.first.cc in (0x20, 0x25, 0x26, 0x2B) and "set" in m.first.cmd_name.lower():
            pairs[(m.src, m.dst)] += 1
    return [hit("info", f"{c.name(a)} controls {c.name(b)} directly ({k} commands), bypassing the controller.", c, a)
            for (a, b), k in pairs.items()]


@detector("association-loop")
def _loop(c):
    pairs = Counter()
    for m in c.mine:
        if c.ctrl is not None and c.ctrl not in (m.src, m.dst) and m.dst not in (None, BROADCAST) \
                and m.first.cc in (0x20, 0x25, 0x26) and "set" in m.first.cmd_name.lower():
            pairs[(m.src, m.dst)] += 1
    return [hit("warn", f"{c.name(a)} and {c.name(b)} send Set commands to each other ({k} and {pairs[(b, a)]}); "
                "they may be triggering one another.", c, a)
            for (a, b), k in pairs.items() if a < b and pairs.get((b, a), 0) >= 3 and k >= 3]


@detector("route-maintenance-traffic")
def _routes(c):
    n = sum(1 for m in c.mine if m.first.cc == 0x01 and m.first.cmd in (0x04, 0x05, 0x06, 0x0C, 0x14, 0x24, 0x25))
    return [hit("info", f"{n} route-maintenance messages were seen (neighbour discovery, route assignment): "
                "a route rebuild or inclusion is under way.")] if n >= 10 else []


@detector("inclusion-activity")
def _inclusion(c):
    out = []
    n = sum(1 for f in c.frames if f.kind == "explorer" and f.cmd_name == "Inclusion Request")
    if n:
        out.append(hit("info", f"{n} network-wide inclusion requests were seen: a device is trying to join a network."))
    nif = Counter(m.src for m in c.mine if m.first.cc == 0x01 and m.first.cmd == 0x01 and m.dst in (BROADCAST, None))
    for nid, k in nif.items():
        if k >= 5:
            out.append(hit("info", f"{c.name(nid)} broadcast its node information {k} times "
                           "(button presses, or a device stuck in learn mode).", c, nid))
    return out


@detector("multicast-broadcast-partial-delivery")
def _multicast(c):
    n = sum(1 for m in c.mine if m.first.kind == "multicast" or (m.dst == BROADCAST and m.first.cc not in (None, 0, 1)))
    if n >= 10 and (c.minutes is None or n / max(c.minutes, 0.1) >= 5):
        return [hit("warn", f"{n} multicast or broadcast application messages were seen; every node has to process each one.")]
    return []


@detector("foreign-network-co-channel")
def _foreign(c):
    homes = [h for h in c.net.get("homes", []) if h != c.home]
    if not homes:
        return []
    foreign = [f for f in c.frames if f.home and f.home != c.home]
    share = len(foreign) / max(len(c.frames), 1)
    return [hit("warn" if share > 0.3 else "info",
                f"{len(homes)} other Z-Wave network(s) are in range and account for {share:.0%} of captured frames.")]


@detector("report-flooding-misconfigured-meter")
def _flood(c):
    out = []
    if not c.minutes:
        return out
    for nid, ms in c.by_src.items():
        if nid == c.ctrl:
            continue
        reports = Counter(m.first.cc_name for m in ms if "report" in m.first.cmd_name.lower() and not m.first.encrypted)
        for cc, n in reports.items():
            if n >= 12 and n / c.minutes >= 6:
                out.append(hit("warn", f"{c.name(nid)} sends {cc} reports {n / c.minutes:.0f} times a minute.", c, nid))
    return out


@detector("s0-nonce-get-dos")
def _nonce_dos(c):
    out = []
    if c.ctrl is None:
        return out
    for nid, ms in c.by_src.items():
        gets = [m for m in ms if m.dst == c.ctrl and m.first.cc == 0x98 and m.first.cmd == 0x40 and not m.superseded]
        used = sum(1 for m in ms if m.first.cc == 0x98 and m.first.cmd in (0x81, 0xC1))
        if len(gets) >= 8 and used <= len(gets) * 0.2 and gets[0].first.source in SNIFFED:
            out.append(hit("warn", f"{c.name(nid)} requested {len(gets)} S0 nonces and used only {used}.", c, nid))
    return out


@detector("hop-limit-exhausted")
def _hops(c):
    nodes = Counter(m.dst for m in c.mine if len(m.repeaters) >= 4 and m.dst not in (None, BROADCAST))
    return [hit("warn", f"{c.name(n)} is reached through 4 repeaters, the protocol maximum ({k} messages).", c, n)
            for n, k in nodes.items()]


@detector("wakeup-destination-wrong")
def _wake_dest(c):
    out = []
    if c.ctrl is None:
        return out
    for nid, ms in c.by_src.items():
        wrong = Counter(m.dst for m in ms if c.is_cmd(m, 0x84, "notification") and m.dst not in (c.ctrl, None))
        for dst, k in wrong.items():
            where = "as a broadcast" if dst == BROADCAST else f"to {c.name(dst)}"
            out.append(hit("warn", f"{c.name(nid)} sends its wake-up notifications {where}, not to the controller ({k} seen).", c, nid))
    return out


@detector("supervised-reports-doubling-traffic")
def _supervised(c):
    out = []
    for nid, ms in c.by_src.items():
        if nid == c.ctrl:
            continue
        n = sum(1 for m in ms if "Supervision" in m.first.encap and "report" in m.first.cmd_name.lower())
        if n >= 10:
            out.append(hit("info", f"{c.name(nid)} sent {n} reports wrapped in Supervision; each one costs a confirmation back.", c, nid))
    return out


@detector("retransmit-storm-missed-acks")
def _storm(c):
    out = []
    for nid, ms in c.by_src.items():
        if nid == c.ctrl:
            continue
        worst = max((m.retx for m in ms if not m.wake), default=0)
        if worst >= 5:
            out.append(hit("warn", f"{c.name(nid)} repeated a single message {worst} times.", c, nid))
    return out


@detector("get-acked-but-no-report")
def _no_report(c):
    out = []
    if c.ctrl is None:
        return out
    for nid, ms in c.by_dst.items():
        replies = [m.first.ts for m in c.by_src.get(nid, [])]
        gets = [m for m in ms if m.src == c.ctrl and m.first.cmd_name.lower().endswith("get") and not m.first.encap
                and m.first.cc not in (0x98, 0x9F) and m.outcome == "ok"]
        silent = sum(1 for g in gets if not any(0 <= t - g.first.ts <= 3 for t in replies))
        if silent >= 3 and silent >= len(gets) * 0.5:
            out.append(hit("warn", f"{c.name(nid)} acknowledged {silent} of {len(gets)} queries but never answered them.", c, nid))
    return out


@detector("lr-out-of-range-no-mesh")
def _lr(c):
    return [hit("warn", f"{cat['name']} is a Long Range device with {cat['fails']} of {cat['attempts']} messages undelivered; "
                "Long Range cannot use repeaters.", c, nid)
            for nid, cat in c.cat.items() if cat["link"] == "Long Range" and cat["attempts"] >= 3 and cat["fail_rate"] >= 0.15]


@detector("region-frequency-mismatch")
def _region(c):
    sn = [f for f in c.frames if f.source in SNIFFED and f.kind != "beam"]
    bad = sum(1 for f in sn if "bad checksum" in f.errors)
    if len(sn) >= 20 and bad / len(sn) > 0.5:
        return [hit("warn", f"{bad / len(sn):.0%} of captured frames are corrupt, which usually means the sniffer is set to the wrong region.")]
    return []


def evaluate(frames, msgs, cats, net, nm) -> list[dict]:
    """Run every check and return the whole catalogue, detected entries first."""
    ctx = Ctx(frames, msgs, cats, net, nm)
    log_hits = defaultdict(Counter)
    for f in frames:
        if f.kind == "event" and f.event and f.event.startswith("kb:"):
            log_hits[f.event[3:]][f.src] += 1
    out = []
    for e in ENTRIES:
        hits = []
        fn = DETECTORS.get(e["id"])
        if fn:
            try:
                hits += fn(ctx)
            except Exception:  # one faulty check must not break the analysis
                pass
        for nid, n in log_hits.get(e["id"], {}).items():
            who = f"{ctx.name(nid)}: " if nid is not None else ""
            hits.append(hit(e.get("severity", "warn"), f"{who}the controller log shows this {n} time(s).", ctx, nid))
        detectable = bool(fn or e.get("log"))
        out.append({
            "id": e["id"], "title": e["title"], "category": e["category"],
            "category_name": CATEGORIES.get(e["category"], e["category"]),
            "what": e["what"], "causes": e.get("causes", []), "fixes": e.get("fixes", []),
            "sources": e.get("sources", []), "hits": hits,
            "action": e.get("action") or action_for(" ".join(e.get("fixes", [])[:1]))
            or CATEGORY_ACTION.get(e["category"]),
            "status": "detected" if hits else ("clear" if detectable else "manual"),
            "how": ("traffic and logs" if fn and e.get("log") else "traffic" if fn else "controller logs" if e.get("log") else "not visible in traffic"),
        })
    rank = {"detected": 0, "clear": 1, "manual": 2}
    out.sort(key=lambda x: (rank[x["status"]], x["category"], x["title"]))
    return out
