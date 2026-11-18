"""Analysis engine: conversations, node categorisation, the five troubleshooters, suggestions."""
from __future__ import annotations

from collections import Counter, defaultdict
from statistics import median

from .cc import DEVICE_TYPES, PLUMBING
from .knowledge import evaluate as evaluate_catalog
from .model import BROADCAST, Frame

CONV_GAP = 3.0      # seconds of silence that ends a conversation
RETX_WINDOW = 2.0   # identical frame seen again within this window = retransmission
ACK_WINDOW = 1.0
SNIFFED = ("zniffer", "sdr")
BITRATE = {"9.6k": 9600, "40k": 40000, "100k": 100000, "LR": 100000}
SEV = {"ok": 0, "info": 1, "warn": 2, "crit": 3}

RSSI_WEAK, RSSI_CRIT = -85.0, -92.0
NOISE_HIGH = -85.0
MARGIN_MIN = 10.0


class Msg:
    """One logical message: the original frame plus its forwards, retransmissions and ACKs."""
    __slots__ = ("id", "first", "frames", "src", "dst", "home", "ack_req", "acked", "retx", "hops",
                 "last", "last_hop", "failed", "routed", "repeaters", "route_failed", "wake", "superseded")

    def __init__(self, mid: int, f: Frame):
        self.id, self.first, self.frames = mid, f, [f]
        self.src, self.dst, self.home = f.src, f.dst, f.home
        self.ack_req, self.acked, self.retx = f.ack_req, False, 0
        self.hops, self.last, self.last_hop = {f.hop}, f.ts, f.hop
        self.failed, self.routed, self.repeaters = False, f.routed, list(f.repeaters)
        self.route_failed = f.route_failed
        self.wake = bool(f.wake)       # delivered (or retried) with a FLiRS wake-up beam
        self.superseded = False        # an immediate retry of the same command replaced this one

    @property
    def outcome(self) -> str:
        f = self.first
        if f.source in SNIFFED:
            if self.superseded or self.dst in (BROADCAST, None):
                return "na"
            if self.acked:
                return "ok"
            if self.failed:
                return "failed"
            if not self.ack_req:
                return "na"
            return "unacked"
        if f.tx_status is None:
            return "na"
        return "ok" if f.tx_status == "OK" else "failed"

    @property
    def security(self) -> str:
        e = self.first.encap
        return "S2" if "S2" in e else "S0" if "S0" in e else "plain"


def _med(values):
    return median(values) if values else None


def _prepare(frames: list) -> bool:
    """Sort by time, fill in missing timestamps, assign indexes. Returns True if real timing exists."""
    has_time = any(f.ts is not None for f in frames)
    last = 0.0
    for f in frames:
        if f.ts is None:
            f.ts = last + 0.1
            f.errors = f.errors + ["no timestamp"] if "no timestamp" not in f.errors else f.errors
        last = f.ts
    frames.sort(key=lambda f: f.ts)
    for i, f in enumerate(frames):
        f.idx, f.msg, f.role, f.conv = i, None, "", None
    return has_time


def _group_messages(frames: list) -> list:
    msgs: list[Msg] = []
    open_by_key: dict = {}
    by_seq: dict = {}
    by_pair: dict = {}
    by_src: dict = {}
    by_payload: dict = {}
    last_beam: dict = {}
    for f in frames:
        if f.kind == "beam":
            last_beam[f.dst] = f.ts
        if f.kind in ("data", "explorer", "multicast"):
            if f.source in SNIFFED:
                key = (f.home, f.src, f.dst, f.seq, f.payload)
                m = open_by_key.get(key)
                if m and f.ts - m.last <= RETX_WINDOW:
                    if f.routed and f.hop not in m.hops:
                        f.role = "fwd"
                        m.hops.add(f.hop)
                    else:
                        f.role = "retx"
                        m.retx += 1
                    m.frames.append(f)
                    m.last, m.last_hop = f.ts, f.hop
                    m.wake = m.wake or bool(f.wake)
                    f.msg = m.id
                    continue
            m = Msg(len(msgs), f)
            msgs.append(m)
            f.msg, f.role = m.id, "orig"
            if f.source in SNIFFED:
                pkey = (f.home, f.src, f.dst, f.payload)
                prev = by_payload.get(pkey)
                if prev is not None and not prev.acked and f.ts - prev.last <= 3.0:
                    # The sender gave up on the first attempt and immediately tried again.
                    prev.superseded = True
                    beamed = last_beam.get(f.dst, -1) >= prev.first.ts
                    if beamed or m.wake or prev.wake:
                        # FLiRS device: failing once, beaming, then succeeding is how it normally works.
                        m.wake = prev.wake = True
                    else:
                        m.retx += prev.retx + 1
                by_payload[pkey] = m
                open_by_key[(f.home, f.src, f.dst, f.seq, f.payload)] = m
                by_seq[(f.home, f.src, f.dst, f.seq)] = m
                by_src[(f.home, f.src, f.seq)] = m
                by_pair[(f.home, f.src, f.dst)] = m
            elif f.attempts and f.attempts > 1:
                m.retx = f.attempts - 1
        elif f.kind == "ack":
            m = by_seq.get((f.home, f.dst, f.src, f.seq))
            if m is None:
                # A repeater acknowledging one hop of a routed message.
                m = by_src.get((f.home, f.dst, f.seq))
                if m is not None and f.src not in m.repeaters:
                    m = None
            if m and f.ts - m.last <= ACK_WINDOW:
                f.msg, f.role = m.id, "ack"
                m.frames.append(f)
                # For a routed message only the ACK of the final hop proves delivery.
                if not m.routed or m.last_hop is None or m.last_hop >= len(m.repeaters):
                    m.acked = True
        elif f.kind in ("routed_ack", "routed_err"):
            m = by_pair.get((f.home, f.dst, f.src))
            if m and f.ts - m.last <= RETX_WINDOW * 2:
                f.msg = m.id
                m.frames.append(f)
                if f.kind == "routed_ack":
                    m.acked = True
                else:
                    m.failed, m.route_failed = True, f.route_failed
    for m in msgs:
        if m.wake:  # retries spent waking a FLiRS device are not a fault
            m.retx = 0
            if m.acked or m.superseded:
                m.route_failed = None
    return msgs


def _conversations(frames: list, msgs: list, nm) -> list:
    convs: list[dict] = []
    open_convs: dict = {}
    for f in frames:
        if f.kind == "noise" or (f.src is None and f.dst is None):
            continue
        if f.kind in ("event", "beam"):
            who = f.src if f.kind == "event" else f.dst
            cands = [c for k, c in open_convs.items() if who in k[1:] and f.ts - c["end"] <= CONV_GAP]
            if cands:
                c = max(cands, key=lambda c: c["end"])
                f.conv = c["id"]
                c["frames"] += 1
                c["end"] = f.ts
                if f.kind == "event":
                    c["events"].append(f.event)
            continue
        owner = msgs[f.msg].first if f.msg is not None and f.role != "orig" else None
        if owner is not None and owner.conv is not None:
            # ACKs, forwards and retransmissions belong to the conversation of their message.
            c = convs[owner.conv]
            f.conv = c["id"]
            c["frames"] += 1
            c["end"] = max(c["end"], f.ts)
            continue
        if f.dst in (BROADCAST, None):
            key = (f.home, f.src, BROADCAST)
        else:
            key = (f.home, min(f.src or 0, f.dst), max(f.src or 0, f.dst))
        c = open_convs.get(key)
        if c is None or f.ts - c["end"] > CONV_GAP:
            c = {"id": len(convs), "home": f.home, "a": f.src, "b": f.dst, "start": f.ts, "end": f.ts,
                 "frames": 0, "msgs": [], "events": [], "sources": set()}
            convs.append(c)
            open_convs[key] = c
        f.conv = c["id"]
        c["frames"] += 1
        c["end"] = f.ts
        c["sources"].add(f.source)
        if f.msg is not None and f.role == "orig":
            c["msgs"].append(f.msg)

    for c in convs:
        ms = [msgs[i] for i in c["msgs"]]
        app = [m for m in ms if (m.first.cc, m.first.cmd) not in PLUMBING] or ms
        cmds = list(dict.fromkeys(m.first.label() for m in app))
        outcomes = Counter(m.outcome for m in ms)
        retx = sum(m.retx for m in ms)
        flags = []
        if retx:
            flags.append(f"{retx} retransmission{'s' if retx != 1 else ''}")
        if outcomes["unacked"]:
            flags.append(f"{outcomes['unacked']} unacknowledged")
        if outcomes["failed"]:
            flags.append(f"{outcomes['failed']} failed")
        if any(m.wake for m in ms):
            flags.append("FLiRS wake-up")
        if any(m.routed for m in ms):
            hops = max(len(m.repeaters) for m in ms)
            flags.append(f"routed, {hops} repeater{'s' if hops != 1 else ''}")
        sec = {m.security for m in ms} - {"plain"}
        flags += sorted(sec)
        bad_events = [e for e in c["events"] if e in ("dead", "no_response", "nonce_error", "decode_error",
                                                       "interview_failed")]
        if bad_events:
            flags.append(", ".join(sorted(set(bad_events))).replace("_", " "))
        status = "fail" if (outcomes["failed"] or outcomes["unacked"] or "dead" in bad_events) else \
            "warn" if (retx or bad_events or any(m.route_failed for m in ms)) else "ok"
        b_name = "everyone (broadcast)" if c["b"] in (BROADCAST, None) else nm(c["home"], c["b"])
        c.update(title=" → ".join(cmds[:3]) + (" …" if len(cmds) > 3 else "") or "(link-layer only)",
                 a_name=nm(c["home"], c["a"]), b_name=b_name, n_msgs=len(ms), flags=flags,
                 status=status, duration=c["end"] - c["start"], sources=sorted(c["sources"]))
        del c["msgs"], c["events"]
    return convs


def _new_node(home, nid):
    return {"id": nid, "home": home, "tx": 0, "rx": 0, "rssi": [], "speeds": Counter(), "ccs": set(),
            "repeats": 0, "routes": Counter(), "attempts": 0, "fails": 0, "retx": 0, "events": Counter(),
            "battery": None, "wakeups": 0, "beams": 0, "sec": Counter(), "plain_ccs": set(),
            "first": None, "last": None, "reports": Counter(), "tx_ms": [], "route_fail": 0,
            "explorer": 0, "sos": 0, "route_changes": 0, "fail_frames": [], "lr": False}


def _collect(frames: list, msgs: list):
    nodes: dict = {}
    noise: list = []

    def node(home, nid):
        key = (home or "", nid)
        if key not in nodes:
            nodes[key] = _new_node(home or "", nid)
        return nodes[key]

    def seen(n, ts):
        n["first"] = ts if n["first"] is None else min(n["first"], ts)
        n["last"] = ts if n["last"] is None else max(n["last"], ts)

    for f in frames:
        if f.noise is not None:
            noise.append(f.noise)
        if f.kind == "beam" and f.dst not in (None, BROADCAST):
            node(f.home, f.dst)["beams"] += 1
        if f.kind == "event" and f.src is not None:
            n = node(f.home, f.src)
            n["events"][f.event] += 1
            if f.event == "awake":
                n["wakeups"] += 1
            seen(n, f.ts)
        if f.rssi is not None and f.txn is not None and f.kind != "beam":
            node(f.home, f.txn)["rssi"].append(f.rssi)
        if f.speed and f.src is not None and f.source in SNIFFED and f.kind != "beam":
            n = node(f.home, f.src)
            n["speeds"][f.speed] += 1
            n["lr"] = n["lr"] or f.speed == "LR"

    for m in msgs:
        f = m.first
        if m.src is None:
            continue
        s = node(m.home, m.src)
        s["tx"] += 1
        seen(s, f.ts)
        d = None
        if m.dst not in (None, BROADCAST):
            d = node(m.home, m.dst)
            d["rx"] += 1
        for r in m.repeaters:
            node(m.home, r)["repeats"] += 1
        if f.kind == "explorer":
            s["explorer"] += 1
        if f.cc is not None:
            s["ccs"].add(f.cc)
            if d:
                d["ccs"].add(f.cc)
            if f.cc not in (0, 1):
                sec = m.security
                for n in (s, d):
                    if n:
                        n["sec"][sec] += 1
                        if sec == "plain":
                            n["plain_ccs"].add(f.cc)
        if f.cc == 0x84 and "notification" in f.cmd_name.lower():
            s["wakeups"] += 1
        if f.cc == 0x80 and "battery:" in f.summary:
            s["battery"] = f.summary.split("battery:")[1].strip()
        if f.event == "s2_sos":
            s["sos"] += 1
        low = f.cmd_name.lower()
        if "report" in low or "notification" in low:
            s["reports"][f.cc_name] += 1
        out = m.outcome
        if d and out != "na":
            d["attempts"] += 1
            d["retx"] += m.retx
            if out != "ok":
                d["fails"] += 1
                d["fail_frames"].append(f.idx)
        if d and m.wake and not m.superseded:
            d["beams"] += 1
        if d and m.route_failed and not m.superseded:
            d["route_fail"] += 1
        if d and f.tx_ms is not None and f.tx_status == "OK":
            d["tx_ms"].append(f.tx_ms)
        if d and f.ack_rssi is not None:
            (node(m.home, m.repeaters[0]) if m.repeaters else d)["rssi"].append(f.ack_rssi)
        if d and f.source not in SNIFFED and f.speed:
            d["speeds"][f.speed] += 1
            d["lr"] = d["lr"] or f.speed == "LR"
    return nodes, noise


def _device_type(ccs: set, power: str = "", security: str = "") -> str:
    for name, ids in DEVICE_TYPES:
        if ccs & ids:
            return name
    if "FLiRS" in power and security[:2] in ("S0", "S2"):
        return "Lock or secure keypad (likely)"  # beam-woken and encrypted: almost always a lock
    return "Unknown"


def _categorise(nodes: dict, msgs: list, duration: float, has_time: bool, nm, meta: dict, sniffed=False):
    """Fill in role, power, security, health and traffic categories for every node."""
    by_home = Counter()
    for (home, _), n in nodes.items():
        by_home[home] += n["tx"] + n["rx"]
    primary = by_home.most_common(1)[0][0] if by_home else ""

    peers = defaultdict(set)
    for m in msgs:
        if m.src is not None and m.dst not in (None, BROADCAST):
            peers[(m.home or "", m.src)].add(m.dst)
            peers[(m.home or "", m.dst)].add(m.src)
    controllers = {}
    for home in by_home:
        cands = [(len(peers[k]), -k[1], k[1]) for k in nodes if k[0] == home]
        if cands:
            controllers[home] = max(cands)[2]

    # Routes, normalised to controller -> node order.
    last_route = {}
    for m in msgs:
        ctrl = controllers.get(m.home or "")
        known = m.first.source in SNIFFED or m.first.tx_status is not None
        if not known or ctrl is None:
            continue
        if m.src == ctrl and m.dst not in (None, BROADCAST):
            key, route = (m.home or "", m.dst), tuple(m.repeaters)
        elif m.dst == ctrl:
            key, route = (m.home or "", m.src), tuple(reversed(m.repeaters))
        else:
            continue
        n = nodes[key]
        n["routes"][route] += 1
        if key in last_route and last_route[key] != route:
            n["route_changes"] += 1
        last_route[key] = route

    # A sniffer that hears even the controller weakly is badly placed or miscalibrated:
    # its absolute signal levels then say nothing about individual links.
    ctrl_rssi = _med(nodes[(primary, controllers[primary])]["rssi"]) if primary in controllers else None
    rssi_trusted = not (sniffed and ctrl_rssi is not None and ctrl_rssi < RSSI_WEAK)

    total_tx = sum(n["tx"] for k, n in nodes.items() if n["id"] != controllers.get(k[0])) or 1
    minutes = max(duration / 60.0, 1 / 60) if has_time else None
    out = []
    for key, n in sorted(nodes.items()):
        home, nid = key
        info = meta.get(nid, {}) if home == primary else {}
        is_ctrl = controllers.get(home) == nid
        rssi = _med(n["rssi"])
        fail_rate = n["fails"] / n["attempts"] if n["attempts"] else 0.0
        route = n["routes"].most_common(1)[0][0] if n["routes"] else None

        if is_ctrl:
            role = "Controller"
        elif n["repeats"]:
            role = "Repeater (routes for others)"
        else:
            role = "End device"

        if is_ctrl:
            power = "Mains"
        elif info.get("isListening") is False and info.get("isFrequentListening"):
            power = "Battery, FLiRS (beam wake-up)"
        elif info.get("isListening") is False:
            power = "Battery, sleeping"
        elif n["beams"]:
            power = "Battery, FLiRS (beam wake-up)"
        elif n["wakeups"] or 0x84 in n["ccs"] or n["events"]["asleep"]:
            power = "Battery, sleeping"
        elif n["repeats"] or info.get("isListening"):
            power = "Mains"
        else:
            power = "Unknown (likely mains)" if n["tx"] else "Unknown"

        sec = n["sec"]
        if is_ctrl:
            security = "n/a (controller)"
        elif sec["S2"]:
            security = "S2" + (" + unencrypted traffic" if sec["plain"] else "")
        elif sec["S0"]:
            security = "S0 (legacy)" + (" + unencrypted traffic" if sec["plain"] else "")
        elif sec["plain"]:
            security = "None"
        else:
            security = "Unknown"

        dead = n["events"]["dead"] > n["events"]["alive"]
        if dead or (n["attempts"] >= 3 and fail_rate >= 0.5):
            health = "Failing"
        elif (n["attempts"] >= 3 and fail_rate >= 0.15) or (rssi_trusted and rssi is not None and rssi < RSSI_WEAK) \
                or n["route_fail"] or n["events"]["no_response"] or n["route_changes"] > 2:
            health = "Marginal"
        elif n["tx"] + n["rx"] == 0:
            health = "Unknown"
        else:
            health = "Healthy"

        share = n["tx"] / total_tx if not is_ctrl else 0.0
        per_min = n["tx"] / minutes if minutes else None
        if is_ctrl:
            traffic = "Hub"
        elif (share > 0.3 and n["tx"] >= 20) or (per_min is not None and per_min > 20 and n["tx"] >= 20):
            traffic = "Chatty"
        elif n["tx"] <= 2:
            traffic = "Quiet"
        else:
            traffic = "Normal"

        out.append({
            "key": f"{home or '*'}:{nid}", "id": nid, "home": home, "name": nm(home, nid),
            "foreign": home != primary, "controller": is_ctrl,
            "role": role, "power": power, "security": security, "health": health, "traffic": traffic,
            "type": info.get("type") or ("Controller" if is_ctrl else _device_type(n["ccs"], power, security)),
            "link": "Long Range" if (n["lr"] or nid >= 256) else "Mesh",
            "tx": n["tx"], "rx": n["rx"], "share": round(share, 3),
            "per_min": round(per_min, 1) if per_min is not None else None,
            "rssi": round(rssi, 1) if rssi is not None else None, "rssi_n": len(n["rssi"]),
            "attempts": n["attempts"], "fails": n["fails"], "fail_rate": round(fail_rate, 3),
            "retx": n["retx"], "route": list(route) if route is not None else None,
            "routes": len(n["routes"]), "route_changes": n["route_changes"],
            "speeds": dict(n["speeds"]), "battery": n["battery"], "wakeups": n["wakeups"],
            "events": dict(n["events"]), "first": n["first"], "last": n["last"],
            "product": info.get("product"), "location": info.get("location"),
            "_n": n,
        })
    return out, primary, controllers, rssi_trusted


# --------------------------------------------------------------------------
# The five troubleshooters
# --------------------------------------------------------------------------

def _issue(iid, title, what, findings, steps, ok_text):
    sev = max((f["severity"] for f in findings), key=lambda s: SEV[s], default="ok")
    findings.sort(key=lambda f: -SEV[f["severity"]])
    return {"id": iid, "title": title, "what": what, "severity": sev, "findings": findings,
            "steps": steps, "summary": f"{len(findings)} finding{'s' if len(findings) != 1 else ''}"
            if findings else ok_text}


def _finding(sev, text, fix, node=None, frames=None):
    return {"severity": sev, "text": text, "fix": fix, "node": node, "frames": (frames or [])[:20]}


def _unreachable(cats, sniffed):
    out = []
    for c in cats:
        n = c["_n"]
        if c["controller"] or c["foreign"]:
            continue
        ev = n["events"]
        sleeping = c["power"].startswith("Battery, sleeping")
        if ev["dead"] > ev["alive"]:
            out.append(_finding("crit", f"{c['name']} was marked dead by the controller"
                                + (f" after {c['fails']} failed deliveries." if c["fails"] else "."),
                                "Check that the device has power, then ping it. If it stays dead, heal its "
                                "routes or re-include it; replace it if it never answers at close range.",
                                c["key"], n["fail_frames"]))
        elif c["attempts"] >= 3 and c["fail_rate"] >= 0.15:
            sev = "crit" if c["fail_rate"] >= 0.5 else "warn"
            note = (" This device sleeps, so commands sent while it is asleep are expected to fail; "
                    "only failures right after a wake-up matter.") if sleeping else ""
            out.append(_finding(sev, f"{c['name']}: {c['fails']} of {c['attempts']} messages "
                                f"({c['fail_rate']:.0%}) were not delivered." + note,
                                "Rebuild routes for this node, and add or move a mains-powered repeater "
                                "between it and the controller." if not sleeping else
                                "Wake the device manually and watch whether delivery succeeds; if it does, "
                                "shorten the wake-up interval rather than changing the mesh.",
                                c["key"], n["fail_frames"]))
        elif ev["no_response"]:
            out.append(_finding("warn", f"{c['name']} accepted commands but did not answer "
                                f"{ev['no_response']} time(s).",
                                "The radio link works but the device is slow or busy. Check for firmware "
                                "updates and for polling that overloads it.", c["key"]))
        if ev["interview_failed"]:
            out.append(_finding("warn", f"{c['name']}: the interview failed {ev['interview_failed']} time(s).",
                                "Re-interview the device while it is awake and close to the controller.",
                                c["key"]))
    steps = [
        "Confirm the device has power (mains devices: breaker and wiring; battery devices: fresh batteries).",
        "Ping the node from the controller software and watch the conversation here: no ACK at all means a "
        "radio/route problem, an ACK without a report means the device firmware is not answering.",
        "For battery devices, wake the device manually first. Sleeping devices only listen briefly after a wake-up.",
        "Rebuild (heal) routes for just that node, not the whole network.",
        "Move the device or add a mains-powered repeater roughly halfway to the controller.",
        "If it still fails at close range, exclude and re-include it; if that fails too, replace the device.",
    ]
    if sniffed:
        steps.append("Sniffer note: an ACK the sniffer did not hear is counted as missing. If the sniffer sits "
                     "far from the device, confirm with the controller's own log before acting.")
    return _issue("unreachable", "Unreachable or dead nodes",
                  "Messages that were never acknowledged, and nodes the controller has given up on.",
                  out, steps, "Every acknowledged message reached its destination.")


def _signal(cats, noise, sniffed, rssi_trusted=True):
    out = []
    floor = _med(noise)
    if not rssi_trusted:
        levels = [c["rssi"] for c in cats if not c["foreign"] and c["rssi"] is not None]
        out.append(_finding("info", f"The sniffer hears every node weakly, the controller included "
                            f"({min(levels):.0f} to {max(levels):.0f} dBm), so these levels describe the "
                            "sniffer, not the links.",
                            "Move the sniffer next to the controller, or treat the numbers as relative only "
                            "(Zniffer RSSI conversion is approximate). Per-node weak-signal checks were skipped."))
    if floor is not None and floor > NOISE_HIGH:
        out.append(_finding("crit" if floor > -75 else "warn",
                            f"The background noise floor is {floor:.0f} dBm (a quiet site is below -95 dBm).",
                            "Something is transmitting on the Z-Wave band near the controller. Put the "
                            "controller on a USB extension cable away from USB 3 ports, SSDs and other "
                            "radios, then re-measure."))
    for c in cats:
        if c["foreign"] or c["rssi"] is None or c["rssi_n"] < 2:
            continue
        r = c["rssi"]
        margin = r - floor if floor is not None else None
        where = "at the sniffer" if sniffed else "at the controller"
        if not rssi_trusted:
            sev = None
        elif r < RSSI_CRIT or (margin is not None and margin < MARGIN_MIN / 2):
            sev = "crit"
        elif r < RSSI_WEAK or (margin is not None and margin < MARGIN_MIN):
            sev = "warn"
        else:
            sev = None
        if sev:
            extra = f", only {margin:.0f} dB above the noise floor" if margin is not None else ""
            out.append(_finding(sev, f"{c['name']} is heard at {r:.0f} dBm {where}{extra}.",
                                "Shorten the radio path: move the device, re-orient it away from metal, or "
                                "add a mains-powered repeater between it and its next hop.", c["key"]))
        sp = c["speeds"]
        slow = sp.get("9.6k", 0) + sp.get("40k", 0)
        if not c["controller"] and sp.get("100k") and slow >= 3 and slow > sp["100k"] * 0.3:
            out.append(_finding("info", f"{c['name']} can use 100 kbit/s but fell back to a slower rate "
                                f"for {slow} frames.",
                                "Speed fallback is a sign of a marginal link; treat it like weak signal.",
                                c["key"]))
    steps = [
        "Compare each node's signal with the noise floor: you want at least 10 dB of margin, ideally 17 dB or more.",
        "Move the controller first. A USB extension cable that gets the stick 1 m away from the computer "
        "fixes more Z-Wave problems than any other single change.",
        "Look for interference: USB 3 devices, 900 MHz baby monitors and cordless phones, LED drivers, "
        "and (868 MHz regions) LoRa or alarm sensors.",
        "For a single weak node, check what is physically in the way: metal boxes, mirrors, appliances, foil-backed insulation.",
        "Add mains-powered Z-Wave Plus devices as repeaters. Battery devices never repeat.",
        "After any physical change, rebuild routes for the affected nodes so they pick the better path.",
    ]
    if sniffed:
        steps.append("Sniffer note: signal levels are measured where the sniffer is, not at the controller. "
                     "Place the sniffer next to the controller for comparable numbers, and note that "
                     "Zniffer RSSI conversion is approximate.")
    return _issue("signal", "Weak signal and interference",
                  "Nodes heard close to the noise floor, high background noise, and speed fallbacks.",
                  out, steps, "No weak links or elevated noise were observed.")


def _routing(cats):
    out = []
    explorer_total = 0
    for c in cats:
        n = c["_n"]
        if c["foreign"] or c["controller"]:
            explorer_total += n["explorer"] if not c["foreign"] else 0
            continue
        explorer_total += n["explorer"]
        if n["route_fail"]:
            out.append(_finding("warn", f"{c['name']}: a route broke {n['route_fail']} time(s) on the way to it.",
                                "One repeater on its path is unreliable. Rebuild this node's routes and check "
                                "the health of the repeaters it uses.", c["key"], n["fail_frames"]))
        if c["route_changes"] > 2:
            out.append(_finding("warn", f"{c['name']} switched routes {c['route_changes']} times "
                                f"across {c['routes']} different paths.",
                                "The mesh cannot settle on a path. Usually one weak hop is to blame; fix that "
                                "hop's signal, or set a priority route once the path is stable.", c["key"]))
        longest = max((len(r) for r in n["routes"]), default=0)
        if longest >= 3:
            out.append(_finding("warn" if longest >= 4 else "info",
                                f"{c['name']} is reached through {longest} repeaters.",
                                "Each hop adds delay and a point of failure (4 is the protocol maximum). "
                                "Add a repeater that shortens the path or move the controller more centrally.",
                                c["key"]))
        if c["attempts"] >= 5 and c["retx"] / c["attempts"] > 0.3 and c["fail_rate"] < 0.15:
            out.append(_finding("info", f"{c['name']} needed {c['retx']} retries over {c['attempts']} messages; "
                                "they arrive, but slowly.",
                                "A route that only works on the second attempt wastes airtime. Rebuild routes "
                                "for this node.", c["key"]))
    if explorer_total >= 3:
        out.append(_finding("warn" if explorer_total >= 10 else "info",
                            f"{explorer_total} explorer frames were seen: nodes had to flood the network to find a route.",
                            "Explorer frames mean stored routes have failed. Find the nodes sending them and "
                            "rebuild their routes; frequent floods slow the whole network."))
    steps = [
        "Open the Network map and look at the affected node's path. Identify every repeater on it.",
        "Check each repeater on that path under 'Weak signal' and 'Unreachable'. One bad hop breaks the route.",
        "Rebuild routes for the affected node only, during a quiet period, with battery devices awake.",
        "If a device was moved or removed recently, rebuild routes for its former neighbours too. Remove dead "
        "nodes from the controller so nothing tries to route through them.",
        "For a critical device, assign a priority route through a repeater you trust.",
        "Avoid network-wide heals as a routine fix: they generate heavy traffic and can replace good routes with worse ones.",
    ]
    return _issue("routing", "Routing problems",
                  "Broken or unstable routes, long hop chains, retries and explorer floods.",
                  out, steps, "Routes were stable and short.")


def _congestion(cats, net, msgs):
    out = []
    if net["airtime_pct"] is not None and net["airtime_pct"] > 5:
        out.append(_finding("crit" if net["airtime_pct"] > 15 else "warn",
                            f"The channel was busy {net['airtime_pct']:.1f}% of the time.",
                            "Z-Wave is a low-duty-cycle network; above a few percent, collisions and delays "
                            "rise quickly. Cut down the chatty nodes listed here."))
    for c in cats:
        n = c["_n"]
        if c["foreign"] or c["controller"]:
            continue
        if c["traffic"] == "Chatty":
            top = n["reports"].most_common(1)
            what = f", mostly {top[0][0]} reports ({top[0][1]})" if top else ""
            rate = f" ({c['per_min']:.0f}/min)" if c["per_min"] else ""
            out.append(_finding("warn", f"{c['name']} sent {c['tx']} messages{rate}, "
                                f"{c['share']:.0%} of all device traffic{what}.",
                                "Raise this device's reporting thresholds and intervals in its configuration "
                                "parameters (for meters: report on a larger change in W, and less often).",
                                c["key"]))
        slow = [t for t in n["tx_ms"] if t > 1000]
        if len(n["tx_ms"]) >= 3 and (_med(n["tx_ms"]) > 300 or len(slow) >= 2):
            out.append(_finding("warn", f"Commands to {c['name']} take a median of {_med(n['tx_ms']):.0f} ms "
                                f"to be acknowledged ({len(slow)} took over a second).",
                                "Slow acknowledgements come from retries or a busy channel. Check this node's "
                                "route and whether a chatty neighbour is talking over it.", c["key"]))
    jammed = [m.first.idx for m in msgs if m.first.tx_status == "Fail"]
    if jammed:
        out.append(_finding("warn", f"{len(jammed)} transmission(s) failed with status 'Fail': the controller "
                            "could not get airtime at all.",
                            "The channel was jammed or the controller radio was busy. Look for interference "
                            "and for bursts of traffic at those moments.", frames=jammed))
    if net["retx_pct"] is not None and net["retx_pct"] > 10 and net["messages"] >= 20:
        out.append(_finding("warn", f"{net['retx_pct']:.0f}% of messages needed at least one retransmission.",
                            "A high retry rate across many nodes points at congestion or interference rather "
                            "than one bad device."))
    steps = [
        "Sort the Nodes tab by messages sent. A healthy sensor reports a few times a minute at most.",
        "For each chatty device, open its configuration parameters and raise the reporting thresholds "
        "(power in W, temperature change, etc.) and the periodic report interval.",
        "Turn off polling in your controller software wherever the device already reports changes itself.",
        "Check security: a device included with S0 sends three frames for every one. Re-include chatty S0 "
        "devices with S2 or without security.",
        "Remove unneeded associations so devices do not report to several targets.",
        "Re-capture for the same length of time and compare the busy percentage and retry rate.",
    ]
    return _issue("congestion", "Congestion and chatty devices",
                  "Devices flooding the network with reports, a busy channel, and slow or jammed transmissions.",
                  out, steps, "Traffic levels were normal.")


def _security(cats):
    out = []
    s0_total = sum(c["_n"]["sec"]["S0"] for c in cats if not c["foreign"] and not c["controller"])
    all_total = sum(sum(c["_n"]["sec"].values()) for c in cats if not c["foreign"] and not c["controller"])
    for c in cats:
        n = c["_n"]
        if c["foreign"] or c["controller"]:
            continue
        sec = n["sec"]
        if n["plain_ccs"] & {0x62, 0x63, 0x66}:
            out.append(_finding("crit", f"{c['name']} exchanges lock or barrier commands without encryption.",
                                "Exclude this device and re-include it with S2 (Access Control). Unencrypted "
                                "lock commands can be replayed by anyone in radio range.", c["key"]))
        if n["sos"] >= 2:
            out.append(_finding("warn", f"{c['name']} reported losing S2 synchronisation {n['sos']} times.",
                                "Occasional resyncs are normal after lost frames; repeated ones mean frames to "
                                "this node are being dropped. Fix its link quality first.", c["key"]))
        bad = n["events"]["nonce_error"] + n["events"]["decode_error"]
        if bad:
            out.append(_finding("warn", f"{c['name']}: {bad} message(s) could not be decrypted or had no valid nonce.",
                                "If this persists after fixing signal problems, the device and controller no "
                                "longer share keys: re-include the device.", c["key"]))
        if sec["S0"] >= 10 and c["traffic"] in ("Chatty", "Normal") and sec["S0"] >= sec["S2"]:
            out.append(_finding("warn" if c["traffic"] == "Chatty" else "info",
                                f"{c['name']} uses legacy S0 security for {sec['S0']} messages.",
                                "S0 needs a nonce exchange for every command, tripling airtime. Re-include with "
                                "S2 if the device supports it, or without security if it is not a lock.",
                                c["key"]))
    if all_total >= 20 and s0_total / all_total > 0.4:
        out.append(_finding("warn", f"{s0_total / all_total:.0%} of application traffic uses S0.",
                            "A network dominated by S0 is slow by design. Plan to migrate the busiest devices."))
    steps = [
        "Use the Nodes tab's Security column to see which devices use S2, S0 or nothing.",
        "Locks, garage doors and alarm devices must use S2 (or at least S0). Everything else can use S2 or no security.",
        "For decryption or nonce errors, first fix signal and routing problems for that node: lost frames are the usual cause.",
        "If errors persist on a good link, exclude and re-include the device so it receives fresh keys. "
        "Keep the device within a couple of metres of the controller during secure inclusion.",
        "Move chatty S0 devices (power meters, multisensors) to S2 or unsecured to cut their airtime by two thirds.",
        "Back up the controller's network keys before migrating anything.",
    ]
    return _issue("security", "Security overhead and failures",
                  "S0 overhead, S2 resynchronisation, decryption failures and unencrypted locks.",
                  out, steps, "No security problems were observed.")


# --------------------------------------------------------------------------

def _network(frames, msgs, cats, noise, has_time, duration, primary):
    mine = [c for c in cats if not c["foreign"]]
    sniffed = [f for f in frames if f.source in SNIFFED and f.kind != "beam"]
    airtime = None
    if sniffed and has_time and duration > 1:
        secs = sum((f.length * 8 + 80) / BITRATE.get(f.speed, 40000) for f in sniffed)
        airtime = round(100 * secs / duration, 2)
    counted = [m for m in msgs if m.outcome != "na"]
    retx_pct = round(100 * sum(1 for m in counted if m.retx) / len(counted), 1) if counted else None
    fail_pct = round(100 * sum(1 for m in counted if m.outcome != "ok") / len(counted), 1) if counted else None
    routed_nodes = [c for c in mine if c["route"]]
    max_hops = max((len(c["route"]) for c in routed_nodes), default=0)
    devices = [c for c in mine if not c["controller"]]
    if not devices:
        topology = "No devices seen"
    elif not routed_nodes:
        topology = "Star (every node talks directly to the controller)"
    elif max_hops >= 3:
        topology = "Deep mesh (paths of 3 or more repeaters)"
    elif len(routed_nodes) > len(devices) * 0.4:
        topology = "Mesh (many nodes rely on repeaters)"
    else:
        topology = "Mostly direct, light mesh"
    size = "Small" if len(mine) < 12 else "Medium" if len(mine) < 40 else "Large"

    def tally(field, strip=False):
        c = Counter((x[field].split(",")[0].split(" (")[0].split(" +")[0] if strip else x[field]) for x in devices)
        return dict(c.most_common())

    speeds = Counter()
    for c in mine:
        speeds.update(c["speeds"])
    return {
        "home": primary or None,
        "homes": sorted({c["home"] for c in cats if c["home"]}),
        "foreign_nodes": sum(1 for c in cats if c["foreign"]),
        "nodes": len(mine), "frames": len(frames), "messages": len(msgs),
        "duration": duration if has_time else None, "has_time": has_time,
        "start": frames[0].ts if frames and has_time else None,
        "msgs_per_min": round(len(msgs) / (duration / 60), 1) if has_time and duration > 1 else None,
        "airtime_pct": airtime, "retx_pct": retx_pct, "fail_pct": fail_pct,
        "noise_floor": round(_med(noise), 1) if noise else None,
        "topology": topology, "size": f"{size} ({len(mine)} nodes)", "max_hops": max_hops,
        "long_range": sum(1 for c in mine if c["link"] == "Long Range"),
        "by_power": tally("power", True), "by_security": tally("security", True),
        "by_type": tally("type"), "by_health": tally("health"), "by_role": tally("role", True),
        "speeds": dict(speeds),
        "sources": dict(Counter(f.source for f in frames)),
    }


def _suggestions(issues, net, cats):
    out = []
    for iss in issues:
        for f in iss["findings"]:
            if f["severity"] in ("crit", "warn"):
                out.append({"severity": f["severity"], "issue": iss["id"], "area": iss["title"],
                            "why": f["text"], "do": f["fix"], "node": f["node"]})
    out.sort(key=lambda s: -SEV[s["severity"]])
    general = []
    repeaters = sum(1 for c in cats if not c["foreign"] and c["power"] == "Mains" and not c["controller"])
    battery = sum(1 for c in cats if not c["foreign"] and c["power"].startswith("Battery"))
    if battery >= 4 and repeaters < max(1, battery // 4):
        general.append(("info", "Network design", f"{battery} battery devices rely on only {repeaters} known "
                        "mains-powered repeater(s).",
                        "Battery devices never repeat. Add a few mains-powered Z-Wave Plus devices spread "
                        "through the building to give the mesh alternative paths."))
    if net["foreign_nodes"]:
        general.append(("info", "Neighbouring network", f"Traffic from {len(net['homes']) - 1} other Z-Wave "
                        f"network(s) is in range ({net['foreign_nodes']} foreign nodes).",
                        "Foreign networks share your airtime. Nothing to fix, but expect more collisions if "
                        "they are busy; they are excluded from the health findings."))
    if set(net["sources"]) & {"log", "live"} and set(net["sources"]) & set(SNIFFED):
        general.append(("info", "Mixed sources", "Controller logs and sniffer captures are loaded together.",
                        "If they cover the same period, the same messages are counted twice. Analyse them "
                        "separately for accurate rates."))
    if not net["has_time"]:
        general.append(("info", "No timestamps", "The capture has no timestamps.",
                        "Rate, airtime and latency analysis is disabled. Configure your SDR tool to print a "
                        "timestamp per frame."))
    for sev, area, why, do in general:
        out.append({"severity": sev, "issue": None, "area": area, "why": why, "do": do, "node": None})
    if not out:
        out.append({"severity": "ok", "issue": None, "area": "All clear",
                    "why": "None of the five troubleshooters found a problem in this capture.",
                    "do": "Capture for longer, or during the time problems occur, to dig deeper.", "node": None})
    return out


def analyze(frames: list, namer=None, meta: dict | None = None) -> dict:
    """Run the full analysis. `namer(home, node_id)` returns a display name or None."""
    meta = meta or {}

    def nm(home, nid):
        if nid is None:
            return "?"
        name = (namer(home or "", nid) if namer else None) or (meta.get(nid) or {}).get("name")
        return f"{name} (#{nid})" if name else f"Node {nid}"

    homes = Counter(f.home for f in frames if f.home)
    if homes:  # beams carry no home ID; they belong to the network being watched
        main_home = homes.most_common(1)[0][0]
        for f in frames:
            if f.kind == "beam" and f.home is None:
                f.home = main_home
    has_time = _prepare(frames)
    duration = (frames[-1].ts - frames[0].ts) if frames else 0.0
    msgs = _group_messages(frames)
    convs = _conversations(frames, msgs, nm)
    nodes, noise = _collect(frames, msgs)
    sniffed = any(f.source in SNIFFED for f in frames)
    cats, primary, controllers, rssi_trusted = _categorise(nodes, msgs, duration, has_time, nm, meta, sniffed)
    for c in convs:
        c["foreign"] = (c["home"] or "") != primary
    net = _network(frames, msgs, cats, noise, has_time, duration, primary)
    net["controller"] = controllers.get(primary)
    sniffed = bool(set(net["sources"]) & set(SNIFFED))
    issues = [_unreachable(cats, sniffed), _signal(cats, noise, sniffed, rssi_trusted), _routing(cats),
              _congestion(cats, net, msgs), _security(cats)]
    catalog = evaluate_catalog(frames, msgs, cats, net, nm)
    suggestions = _suggestions(issues, net, cats)
    extra = [{"severity": h["severity"], "issue": "kb-" + e["id"], "area": e["title"], "why": h["text"],
              "do": e["fixes"][0] if e["fixes"] else "", "node": h["node"]}
             for e in catalog for h in e["hits"] if h["severity"] in ("crit", "warn")]
    if extra:
        suggestions = [s for s in suggestions if s["severity"] != "ok"] + extra
        suggestions.sort(key=lambda s: -SEV[s["severity"]])
    score = 100 - sum({"crit": 15, "warn": 6, "info": 1}.get(h["severity"], 0) for e in catalog for h in e["hits"])
    for iss in issues:
        for f in iss["findings"]:
            score -= {"crit": 15, "warn": 6, "info": 1}.get(f["severity"], 0)
    net["score"] = max(0, score)
    net["grade"] = "Healthy" if score >= 85 else "Needs attention" if score >= 60 else "Unhealthy"
    for c in cats:
        del c["_n"]
    return {"network": net, "nodes": cats, "issues": issues, "suggestions": suggestions,
            "conversations": convs, "catalog": catalog}


def report_markdown(a: dict) -> str:
    """Plain-text/Markdown report for the command line and export."""
    n = a["network"]
    if not n["frames"]:
        return "# Z-Wave analysis\n\nNo frames loaded.\n"
    L = ["# Z-Wave analysis", ""]
    dur = f"{n['duration']:.0f} s" if n["duration"] is not None else "unknown duration"
    L += [f"**Health: {n['score']}/100 ({n['grade']})**", "",
          f"- Network: home ID {n['home'] or 'unknown'}, {n['size']}, {n['topology']}",
          f"- Capture: {n['frames']} frames, {n['messages']} messages, {len(a['conversations'])} conversations, {dur}",
          f"- Delivery: {n['fail_pct'] if n['fail_pct'] is not None else '?'}% failed, "
          f"{n['retx_pct'] if n['retx_pct'] is not None else '?'}% retried"
          + (f", channel busy {n['airtime_pct']}%" if n["airtime_pct"] is not None else "")
          + (f", noise floor {n['noise_floor']} dBm" if n["noise_floor"] is not None else ""), ""]
    L += ["## Network categories", "", "| Node | Type | Role | Power | Security | Health | Traffic | Signal |",
          "|---|---|---|---|---|---|---|---|"]
    for c in a["nodes"]:
        if c["foreign"]:
            continue
        sig = f"{c['rssi']:.0f} dBm" if c["rssi"] is not None else "-"
        L.append(f"| {c['name']} | {c['type']} | {c['role']} | {c['power']} | {c['security']} | "
                 f"{c['health']} | {c['traffic']} | {sig} |")
    L += ["", "## Troubleshooters", ""]
    for iss in a["issues"]:
        L.append(f"### [{iss['severity'].upper()}] {iss['title']}: {iss['summary']}")
        for f in iss["findings"]:
            L += [f"- **{f['severity']}**: {f['text']}", f"  - Fix: {f['fix']}"]
        L.append("")
    found = [e for e in a.get("catalog", []) if e["hits"]]
    if found:
        L += ["## Other known issues detected", ""]
        for e in found:
            L.append(f"### {e['title']} ({e['category_name']})")
            L += [f"- **{h['severity']}**: {h['text']}" for h in e["hits"]]
            L += [f"  - Fix: {fx}" for fx in e["fixes"][:3]]
            L.append("")
    L.append(f"_{len(a.get('catalog', []))} known failure modes were checked._\n")
    L += ["## Suggestions", ""]
    for i, s in enumerate(a["suggestions"], 1):
        L.append(f"{i}. [{s['severity']}] {s['why']} {s['do']}")
    return "\n".join(L) + "\n"
