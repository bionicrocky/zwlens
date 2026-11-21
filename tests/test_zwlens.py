"""Run with: python -m unittest discover -s tests"""
import faulthandler
import json
import os
import socket
import struct
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

if os.environ.get("CI"):  # on CI, a hung test prints every thread's stack and exits instead of stalling
    faulthandler.dump_traceback_later(300, exit=True)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "samples"))

import make_samples  # noqa: E402
from zwlens.aliases import AliasStore  # noqa: E402
from zwlens.analysis import analyze, report_markdown  # noqa: E402
from zwlens.live import LiveClient, log_event_to_text  # noqa: E402
from zwlens.mpdu import build_mpdu, crc16, decode_mpdu, find_mpdu  # noqa: E402
from zwlens.parsers import parse_bytes  # noqa: E402
from zwlens.parsers.zlf import write_zlf  # noqa: E402
from zwlens.server import Session, serve  # noqa: E402


def issue(a, iid):
    return next(i for i in a["issues"] if i["id"] == iid)


def node(a, nid):
    return next(n for n in a["nodes"] if n["id"] == nid and not n["foreign"])


class Mpdu(unittest.TestCase):
    def test_crc_known_vector(self):
        # CRC-16/AUG-CCITT ("123456789") = 0xE5CC
        self.assertEqual(crc16(b"123456789"), 0xE5CC)

    def test_singlecast_roundtrip(self):
        for rate in ("40k", "100k"):
            f = decode_mpdu(build_mpdu("c0ffee01", 1, 5, bytes([0x25, 1, 0xFF]), seq=7, rate=rate), rate)
            self.assertEqual((f.home, f.src, f.dst, f.seq, f.ack_req), ("c0ffee01", 1, 5, 7, True))
            self.assertEqual((f.cc_name, f.cmd_name, f.summary, f.errors), ("Binary Switch", "Set", "value: on", []))

    def test_routed_transmitter(self):
        out = decode_mpdu(build_mpdu("c0ffee01", 1, 7, b"\x20\x02", repeaters=[3, 4], hop=1))
        self.assertEqual((out.routed, out.repeaters, out.hop, out.txn), (True, [3, 4], 1, 3))
        back = decode_mpdu(build_mpdu("c0ffee01", 7, 1, repeaters=[4, 3], hop=2, inbound=True, routed_ack=True))
        self.assertEqual((back.kind, back.txn), ("routed_ack", 7))

    def test_corruption_detected(self):
        raw = bytearray(build_mpdu("c0ffee01", 1, 5, b"\x20\x02"))
        raw[9] ^= 0x10
        self.assertIn("bad checksum", decode_mpdu(bytes(raw), "40k").errors)

    def test_garbage_never_raises(self):
        for blob in (b"", b"\x00" * 5, bytes(range(40)), b"\xff" * 300):
            decode_mpdu(blob)
            find_mpdu(blob)
            for name in ("x.zlf", "x.log", "x.pcap", "x.txt"):
                self.assertIsInstance(parse_bytes(blob, name).frames, list)

    def test_find_with_prefix(self):
        mpdu = build_mpdu("c0ffee01", 2, 1, bytes([0x80, 3, 50]), rate="100k")
        self.assertEqual(find_mpdu(b"\xaa\x55\x01" + mpdu + b"\x00\x00").src, 2)


class Parsers(unittest.TestCase):
    def test_zlf(self):
        entries = make_samples.sniffer_entries()
        res = parse_bytes(write_zlf(entries), "a.zlf")
        self.assertEqual((res.kind, len(res.frames)), ("zniffer", len(entries)))
        self.assertAlmostEqual(res.frames[0].ts, entries[0][0], places=2)
        self.assertFalse(any(f.errors for f in res.frames))

    def test_zlf_damaged_resync(self):
        data = bytearray(write_zlf(make_samples.sniffer_entries()))
        data[2048 + 9:2048 + 13] = b"\xff\xff\xff\xff"  # wreck the first entry's length
        res = parse_bytes(bytes(data), "a.zlf")
        self.assertGreater(len(res.frames), 500)
        self.assertTrue(res.warnings)

    def test_sdr_text_and_pcap(self):
        res = parse_bytes(make_samples.sdr_text().encode(), "sdr.txt")
        self.assertEqual((res.kind, len(res.frames)), ("sdr", 120))
        self.assertEqual(res.frames[0].rssi, -55)
        mpdu = build_mpdu("c0ffee01", 1, 2, b"\x25\x02", rate="100k")
        pcap = struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 147)
        pcap += struct.pack("<IIII", 1700000000, 500000, len(mpdu) + 4, len(mpdu) + 4) + b"\x00\x01\x02\x03" + mpdu
        res = parse_bytes(pcap, "c.pcap")
        self.assertEqual((len(res.frames), res.frames[0].dst, res.frames[0].ts), (1, 2, 1700000000.5))

    def test_sdr_keyvalue_line(self):
        res = parse_bytes(b"HomeId: d6b2a2a0, SourceNodeId: 01, DestNodeId: 05, CommandClass: 25, Payload: 01 ff\n", "w.txt")
        f = res.frames[0]
        self.assertEqual((f.home, f.src, f.dst, f.cc_name, f.cmd_name), ("d6b2a2a0", 1, 5, "Binary Switch", "Set"))

    def test_log(self):
        res = parse_bytes(make_samples.zwavejs_log().encode(), "z.log")
        self.assertEqual(res.kind, "log")
        sends = [f for f in res.frames if f.kind == "data" and f.src == 1]
        self.assertTrue(all(f.tx_status in ("OK", "NoAck") for f in sends))
        routed = next(f for f in sends if f.dst == 7)
        self.assertEqual((routed.repeaters, routed.speed, routed.cc_name), ([3], "40k", "Multilevel Switch"))
        meter = next(f for f in res.frames if f.src == 9)
        self.assertEqual((meter.cc_name, meter.encap, meter.rssi), ("Meter", ["S0"], -71))
        self.assertTrue(any(f.event == "dead" and f.src == 5 for f in res.frames))
        self.assertEqual(res.frames[0].home, "c0ffee01")

    def test_log_without_dates_and_crlf(self):
        text = ("23:59:59.900 DRIVER « [Node 004] [REQ] [ApplicationCommand]\r\n"
                "                  └─[BasicCCReport]\r\n"
                "00:00:00.100 CNTRLR   [Node 004] The node is alive.\r\n")
        fr = parse_bytes(text.encode(), "c.log").frames
        self.assertEqual(len(fr), 2)
        self.assertAlmostEqual(fr[1].ts - fr[0].ts, 0.2, places=3)


class Analysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sniff = analyze(parse_bytes(write_zlf(make_samples.sniffer_entries()), "a.zlf").frames)
        cls.log = analyze(parse_bytes(make_samples.zwavejs_log().encode(), "z.log").frames)

    def test_empty(self):
        a = analyze([])
        self.assertEqual(a["network"]["frames"], 0)
        report_markdown(a)

    def test_sniffer_findings(self):
        a = self.sniff
        self.assertEqual(a["network"]["controller"], 1)
        self.assertEqual(a["network"]["foreign_nodes"], 2)
        self.assertEqual(node(a, 5)["health"], "Failing")
        self.assertEqual(node(a, 5)["retx"], 24)
        self.assertEqual(node(a, 7)["route"], [3])
        self.assertEqual(node(a, 7)["fails"], 0)  # delivered through the repeater
        self.assertEqual(node(a, 3)["role"], "Repeater (routes for others)")
        self.assertEqual(node(a, 12)["power"], "Battery, sleeping")
        self.assertEqual(node(a, 9)["traffic"], "Chatty")
        self.assertEqual(node(a, 14)["type"], "Door lock")
        self.assertEqual(issue(a, "unreachable")["severity"], "crit")
        self.assertEqual(issue(a, "signal")["severity"], "crit")
        self.assertEqual(issue(a, "security")["severity"], "crit")
        self.assertEqual(issue(a, "congestion")["severity"], "warn")

    def test_log_findings(self):
        a = self.log
        self.assertEqual(issue(a, "routing")["severity"], "warn")
        self.assertIn("marked dead", issue(a, "unreachable")["findings"][0]["text"])
        self.assertEqual(a["network"]["noise_floor"], -100.5)
        self.assertEqual(node(a, 9)["type"], "Energy meter / smart plug")

    def test_conversations(self):
        convs = self.sniff["conversations"]
        first = convs[0]
        self.assertEqual((first["a"], first["b"], first["status"]), (1, 2, "ok"))
        self.assertIn("Binary Switch Set", first["title"])
        self.assertTrue(any(c["status"] == "fail" and c["b"] == 5 for c in convs))

    def test_aliases_in_output(self):
        frames = parse_bytes(make_samples.zwavejs_log().encode(), "z.log").frames
        a = analyze(frames, lambda home, nid: "Garage plug" if nid == 9 else None)
        self.assertEqual(node(a, 9)["name"], "Garage plug (#9)")
        self.assertIn("Garage plug (#9)", report_markdown(a))


class Flirs(unittest.TestCase):
    """Patterns taken from a real capture of beam-woken (FLiRS) locks."""
    H = "c0ffee01"

    def frames(self, entries):
        return parse_bytes(write_zlf([(1000 + t, m, "40k", -60) for t, m in entries]), "f.zlf").frames

    def test_direct_beam_wakeup_is_not_a_failure(self):
        get = bytes([0x98, 0x40])
        fr = self.frames([(0.00, build_mpdu(self.H, 1, 6, get, seq=11)), (0.07, build_mpdu(self.H, 1, 6, get, seq=11)),
                          (0.14, build_mpdu(self.H, 1, 6, get, seq=11)),
                          (1.27, build_mpdu(self.H, 1, 6, get, seq=12)), (1.28, build_mpdu(self.H, 6, 1, ack=True, seq=12))])
        from zwlens.model import Frame
        fr.insert(3, Frame(kind="beam", dst=6, ts=1000.16, source="zniffer", speed="40k"))
        a = analyze(fr)
        n = node(a, 6)
        self.assertEqual((n["fails"], n["retx"], n["power"]), (0, 0, "Battery, FLiRS (beam wake-up)"))
        self.assertEqual(issue(a, "unreachable")["findings"], [])
        self.assertIn("FLiRS wake-up", a["conversations"][0]["flags"])
        self.assertEqual(a["conversations"][0]["frames"], 6)  # the beam is shown in the conversation

    def test_routed_wakeup_extension_header(self):
        def routed(seq, hop, ext=b"", flags=0):
            body = bytes([9, flags | (8 if ext else 0), 0x10 | hop, 14]) + ext + bytes([0x98, 0x40])
            head = bytes.fromhex(self.H) + bytes([1, 0x81, seq, 8 + len(body) + 1])
            from zwlens.mpdu import xor_checksum
            return head + body + bytes([xor_checksum(head + body)])
        first = decode_mpdu(routed(8, 0, bytes([0x10, 0x40])))
        self.assertEqual((first.wake, first.cc_name, first.cmd_name, first.errors), ("1000 ms", "Security", "Nonce Get", []))
        err = build_mpdu(self.H, 9, 1, repeaters=[14], hop=0, inbound=True, routed_err=1, ack_req=False, seq=10)
        okack = build_mpdu(self.H, 9, 1, repeaters=[14], hop=1, inbound=True, routed_ack=True, ack_req=False, seq=9)
        fr = self.frames([(0.0, routed(10, 0)), (0.01, routed(10, 1)), (0.15, routed(10, 1)), (0.30, err),
                          (0.36, routed(9, 0, bytes([0x10, 0x40]))), (1.48, routed(9, 1, bytes([0x10, 0x40]))), (1.49, okack)])
        a = analyze(fr)
        n = node(a, 9)
        self.assertEqual((n["fails"], n["retx"], n["route"]), (0, 0, [14]))
        self.assertEqual(issue(a, "routing")["findings"], [])
        self.assertIn("FLiRS", n["power"])

    def test_sniffer_that_hears_everything_weakly(self):
        fr = parse_bytes(write_zlf([(1000 + i, build_mpdu(self.H, 1 + i % 3, 1 if i % 3 else 2, b"\x25\x02", seq=i % 16), "40k", -92)
                                    for i in range(30)]), "w.zlf").frames
        sig = issue(analyze(fr), "signal")
        self.assertEqual([f["severity"] for f in sig["findings"]], ["info"])


class Catalogue(unittest.TestCase):
    def test_entries_are_complete_and_rules_compile(self):
        from zwlens.knowledge import BY_ID, CATEGORIES, DETECTORS, ENTRIES, match_log
        self.assertGreaterEqual(len(ENTRIES), 80)
        self.assertEqual(len(BY_ID), len(ENTRIES))
        for e in ENTRIES:
            self.assertTrue(e["title"] and e["what"] and e["fixes"], e["id"])
            self.assertIn(e["category"], CATEGORIES, e["id"])
            self.assertTrue(all(u.startswith("https://") for u in e["sources"]), e["id"])
        self.assertEqual([d for d in DETECTORS if d not in BY_ID], [])
        self.assertEqual(match_log("Failed to send the command, the controller is jammed"), ["zw700-800-jammed-lockup"])
        self.assertEqual(match_log("[Node 002] [REQ] [ApplicationCommand]"), [])

    def test_log_rules_reach_the_report(self):
        text = make_samples.zwavejs_log() + (
            "2026-11-01T09:10:00.000Z CNTRLR   The controller is unresponsive\n"
            "2026-11-01T09:10:01.000Z CNTRLR   [Node 007] Security S2 bootstrapping failed: a secure inclusion timer has elapsed\n")
        a = analyze(parse_bytes(text.encode(), "z.log").frames)
        hits = {e["id"]: e["hits"] for e in a["catalog"] if e["hits"]}
        self.assertIn("zw700-800-unresponsive-missed-callback", hits)
        self.assertEqual(hits["s2-bootstrap-failure"][0]["node"], "c0ffee01:7")
        self.assertIn("report-flooding-misconfigured-meter", hits)
        self.assertTrue(any(s["issue"] == "kb-s2-bootstrap-failure" for s in a["suggestions"]))
        self.assertIn("Other known issues detected", report_markdown(a))

    def test_traffic_detectors(self):
        H = "c0ffee01"
        entries, t = [], 1000.0
        for i in range(6):   # node 4 keeps saying it is busy; node 5 announces a factory reset once
            t += 1
            entries.append((t, build_mpdu(H, 4, 1, bytes([0x22, 0x01, 0x00]), seq=i), "40k", -60))
            entries.append((t + .01, build_mpdu(H, 1, 4, ack=True, seq=i), "40k", -60))
        entries.append((t + 2, build_mpdu(H, 5, 1, bytes([0x5A, 0x01]), seq=1), "40k", -60))
        entries.append((t + 2.01, build_mpdu(H, 1, 5, ack=True, seq=1), "40k", -60))
        a = analyze(parse_bytes(write_zlf(entries), "d.zlf").frames)
        hits = {e["id"]: e["hits"] for e in a["catalog"] if e["hits"]}
        self.assertEqual(set(hits), {"application-busy-or-rejected", "device-reset-locally"})
        self.assertEqual(hits["device-reset-locally"][0]["severity"], "crit")
        quiet = [(1.0, build_mpdu(H, 1, 4, b"\x25\x02", seq=1), "40k", -60), (1.01, build_mpdu(H, 4, 1, ack=True, seq=1), "40k", -60)]
        clean = analyze(parse_bytes(write_zlf(quiet), "c.zlf").frames)
        self.assertFalse([e for e in clean["catalog"] if e["hits"]])


class ControllerGuides(unittest.TestCase):
    def test_guides_are_complete(self):
        from zwlens.controllers import ACTIONS, ISSUE_ACTIONS, catalogue
        guides = catalogue()["controllers"]
        self.assertGreaterEqual(len(guides), 17)
        self.assertEqual(len({g["id"] for g in guides}), len(guides))
        for g in guides:
            self.assertIn(g.get("kind"), ("hub", "panel"), g["id"])
            self.assertEqual(set(g["actions"]), set(ACTIONS), g["id"])
            self.assertTrue(g["summary"] and g["docs"], g["id"])
            for act in g["actions"].values():
                self.assertTrue(act["how"])
                self.assertTrue(act["src"] == "" or act["src"].startswith("https://"))
        self.assertTrue(all(a in ACTIONS for acts in ISSUE_ACTIONS.values() for a in acts))
        self.assertIn("qolsys", {g["id"] for g in guides})


class Help(unittest.TestCase):
    def setUp(self):
        from zwlens.help_content import help_data
        self.data = help_data()

    def test_sections_are_complete(self):
        groups = {g["id"] for g in self.data["groups"]}
        for s in self.data["sections"]:
            self.assertTrue(s["title"].strip(), s["id"])
            self.assertTrue(s["body"] or s["id"] == "glossary", s["id"])
            self.assertIn(s["group"], groups, s["id"])
            for block in s["body"]:
                for text in (block if isinstance(block, list) else [block]):
                    self.assertIsInstance(text, str)
                    self.assertTrue(text.strip(), s["id"])

    def test_ids_unique_and_cross_links_resolve(self):
        import re
        ids = [s["id"] for s in self.data["sections"]] + [g["id"] for g in self.data["glossary"]]
        self.assertEqual(len(ids), len(set(ids)))
        for i in ids:
            self.assertRegex(i, r"^[a-z0-9-]+$")
        refs = re.findall(r"\[\[([\w-]+)", json.dumps(self.data))
        self.assertTrue(refs)
        self.assertEqual([r for r in refs if r not in ids], [])
        self.assertEqual([g["see"] for g in self.data["glossary"] if g["see"] not in ids], [])

    def test_links_are_https(self):
        links = [link for s in self.data["sections"] for link in s["links"]]
        self.assertTrue(links)
        for link in links:
            self.assertTrue(link["url"].startswith("https://"), link["url"])
            self.assertTrue(link["label"].strip())

    def test_required_topics_present(self):
        ids = {s["id"] for s in self.data["sections"]}
        for need in ("live-zniffer", "files", "controller-guides", "aliases", "saving", "health-score", "mesh",
                     "routing", "acks", "data-rates", "frequencies", "signal", "sleeping", "flirs", "inclusion",
                     "security", "command-classes", "associations", "supervision", "multicast", "long-range",
                     "zniffer", "glossary", "faq-score"):
            self.assertIn(need, ids)
        for issue in ("unreachable", "signal", "routing", "congestion", "security"):
            self.assertIn("faq-" + issue, ids)  # the UI links each troubleshooter to faq-<issue id>
        terms = {g["term"].split(" (")[0] for g in self.data["glossary"]}
        for need in ("FLiRS", "DSK", "SUC / SIS", "NVM", "RSSI", "S0", "S2", "Explorer frame"):
            self.assertIn(need, terms)
        self.assertTrue(any(g["term"].startswith("NIF") for g in self.data["glossary"]))
        self.assertTrue(any(g["term"].startswith("LWR") for g in self.data["glossary"]))

    def test_help_is_served(self):
        session = Session(AliasStore(Path(tempfile.mkdtemp()) / "a.json"))
        httpd = serve(session, "127.0.0.1", 0)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            with urllib.request.urlopen(base + "/api/help") as r:
                self.assertEqual(r.status, 200)
                self.assertEqual(json.loads(r.read()), json.loads(json.dumps(self.data)))
            with urllib.request.urlopen(base + "/") as r:
                self.assertIn(b'data-tab="help"', r.read())
        finally:
            httpd.shutdown()
            httpd.server_close()


class ControllerModel(unittest.TestCase):
    def test_action_for_mapping(self):
        from zwlens.controllers import action_for
        self.assertEqual(action_for("Rebuild routes for this node."), "rebuild")
        self.assertEqual(action_for("Use Remove Failed Node, then rebuild routes."), "remove_failed")
        self.assertEqual(action_for("Exclude this device and re-include it with S2."), "exclude")
        self.assertEqual(action_for("Raise the reporting thresholds in its configuration parameters."), "config")
        self.assertEqual(action_for("Update the controller firmware."), "firmware")
        self.assertEqual(action_for("Put the controller on a USB extension cable."), "routes")
        self.assertIsNone(action_for("Nothing actionable here."))

    def test_findings_and_suggestions_carry_actions(self):
        from zwlens.controllers import ACTIONS
        a = analyze(parse_bytes(write_zlf(make_samples.sniffer_entries()), "a.zlf").frames)
        for iss in a["issues"]:
            for f in iss["findings"]:
                self.assertIn(f["action"], list(ACTIONS) + [None])
        self.assertTrue(all("action" in s for s in a["suggestions"]))
        self.assertTrue(all(e["action"] in ACTIONS for e in a["catalog"]))
        unreachable = next(i for i in a["issues"] if i["id"] == "unreachable")["findings"][0]
        self.assertEqual(unreachable["action"], "rebuild")

    def test_alias_update_keeps_model_on_rename(self):
        with tempfile.TemporaryDirectory() as d:
            s = AliasStore(Path(d) / "a.json")
            s.update("c0ffee01:1", model="hubitat")
            s.set("c0ffee01:1", "Hub", "Office")
            again = AliasStore(Path(d) / "a.json")
            self.assertEqual(again.data["c0ffee01:1"], {"model": "hubitat", "name": "Hub", "location": "Office"})
            self.assertEqual(again.model("c0ffee01", 1), "hubitat")
            again.set("c0ffee01:1")  # clearing the alias keeps the model
            self.assertEqual(again.data["c0ffee01:1"], {"model": "hubitat"})
            again.update("c0ffee01:1", model="")
            self.assertNotIn("c0ffee01:1", again.data)
            again.update("*:0", model="ring")  # chosen before a controller was identified
            self.assertEqual(again.model("deadbeef", 5), "ring")


class AliasesAndServer(unittest.TestCase):
    def test_alias_store(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sub" / "a.json"
            s = AliasStore(path)
            s.set("c0ffee01:9", "Plug", "Garage")
            s.set("*:3", "Repeater")
            s2 = AliasStore(path)
            self.assertEqual((s2.name("c0ffee01", 9), s2.name("anything", 3), s2.name("c0ffee01", 4)), ("Plug", "Repeater", None))
            s2.set("*:3")
            self.assertIsNone(AliasStore(path).name("x", 3))
            path.write_text("{broken")
            self.assertEqual(AliasStore(path).data, {})

    def test_http_api(self):
        with tempfile.TemporaryDirectory() as d:
            session = Session(AliasStore(Path(d) / "a.json"))
            httpd = serve(session, "127.0.0.1", 0)
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"

            def call(path, data=None, headers=None):
                req = urllib.request.Request(base + path, data=data, headers=headers or {})
                try:
                    with urllib.request.urlopen(req) as r:
                        return r.status, r.read()
                except urllib.error.HTTPError as e:
                    return e.code, e.read()

            try:
                h = {"X-ZWLens": "1"}
                self.assertEqual(call("/")[0], 200)
                self.assertEqual(call("/api/upload?name=a.zlf", b"x")[0], 403)  # no custom header
                self.assertEqual(call("/api/analysis", headers={"Host": "evil.example"})[0], 403)
                code, body = call("/api/upload?name=a.zlf", write_zlf(make_samples.sniffer_entries()), h)
                self.assertTrue(json.loads(body)["loaded"])
                self.assertFalse(json.loads(call("/api/upload?name=junk.bin", b"\x00\x01\x02", h)[1])["loaded"])
                self.assertEqual(call("/api/alias", json.dumps({"key": "c0ffee01:9", "name": "<b>Plug</b>"}).encode(), h)[0], 200)
                self.assertEqual(call("/api/alias", json.dumps({"key": "../x:9", "name": "x"}).encode(), h)[0], 400)
                a = json.loads(call("/api/analysis")[1])
                self.assertEqual(node(a, 9)["name"], "<b>Plug</b> (#9)")
                conv = a["conversations"][0]["id"]
                fr = json.loads(call(f"/api/frames?conv={conv}")[1])
                self.assertEqual(fr["total"], 4)
                self.assertEqual(json.loads(call("/api/frames?node=5&kind=problems")[1])["total"], 24)
                self.assertIn(b"# Z-Wave analysis", call("/api/report.md")[1])
                saved = parse_bytes(call("/api/capture.zlf")[1], "saved.zlf")
                self.assertEqual(len(saved.frames), len(make_samples.sniffer_entries()))
                self.assertFalse(any(f.errors for f in saved.frames))
                ico = call("/favicon.ico")
                self.assertEqual((ico[0], ico[1][:4]), (200, b"\x00\x00\x01\x00"))
                loaded = json.loads(call("/api/sample", b'{"kind":"log"}', h)[1])
                self.assertTrue(loaded["loaded"] and loaded["kind"] == "log")
                self.assertEqual(call("/api/settings", b'{"chip":"500"}', h)[0], 200)
                self.assertEqual(json.loads(call("/api/analysis")[1])["settings"]["chip"], "500")
                self.assertEqual(call("/api/live/region", b'{"id":1}', h)[0], 409)
                summary = json.loads(call("/api/analysis")[1])
                self.assertIsNone(summary["controller_model"])
                self.assertEqual(summary["controller_key"], {"home": "c0ffee01", "node": 1})
                self.assertEqual(call("/api/controller", b'{"home":"c0ffee01","node":1,"model":"nope"}', h)[0], 400)
                self.assertEqual(call("/api/controller", b'{"home":"../x","node":1,"model":"ring"}', h)[0], 400)
                self.assertEqual(call("/api/controller", b'{"home":"c0ffee01","node":1,"model":"qolsys"}', h)[0], 200)
                summary = json.loads(call("/api/analysis")[1])
                self.assertEqual(summary["controller_model"], "qolsys")
                ctrl = next(n for n in summary["nodes"] if n["controller"] and not n["foreign"])
                self.assertTrue(ctrl["type"].startswith("Qolsys"))
                call("/api/alias", json.dumps({"key": "c0ffee01:1", "name": "Panel"}).encode(), h)
                self.assertEqual(json.loads(call("/api/analysis")[1])["controller_model"], "qolsys")
                call("/api/controller", b'{"home":"c0ffee01","node":1,"model":"other"}', h)
                self.assertEqual(json.loads(call("/api/analysis")[1])["controller_model"], "other")
                self.assertEqual(call("/api/nope")[0], 404)
                self.assertEqual(call("/../zwlens/server.py")[0], 404)
            finally:
                httpd.shutdown()
                httpd.server_close()


class Live(unittest.TestCase):
    def test_event_handling(self):
        sent = []
        lc = LiveClient.__new__(LiveClient)  # no socket: drive the message handler directly
        from zwlens.parsers.zwavejs_log import LogParser
        lc.url, lc._on_change, lc._lock = "ws://test", lambda: None, threading.RLock()
        lc.state, lc.error, lc.meta = "connecting", None, {}
        lc.parser = LogParser("ws://test", "live")
        lc.handle({"type": "version", "homeId": 0xC0FFEE01, "maxSchemaVersion": 99}, sent.append)
        self.assertEqual([m["command"] for m in sent], ["set_api_schema", "start_listening", "start_listening_logs"])
        lc.handle({"type": "result", "messageId": "listen", "success": True, "result": {"state": {
            "controller": {"ownNodeId": 1},
            "nodes": [{"nodeId": 9, "name": "Plug", "isListening": True, "deviceConfig": {"manufacturer": "Acme", "label": "P1"}}]}}}, sent.append)
        lc.handle({"type": "event", "event": {"source": "driver", "event": "logging", "label": "DRIVER", "direction": "« ",
                   "timestamp": "09:00:00.000", "primaryTags": "[Node 009] [REQ] [ApplicationCommand]",
                   "message": ["└─[MeterCCReport]", "    value: 5"]}}, sent.append)
        lc.handle({"type": "event", "event": {"source": "node", "event": "dead", "nodeId": 5}}, sent.append)
        lc.handle({"type": "nonsense"}, sent.append)
        f = lc.frames[0]
        self.assertEqual((f.src, f.dst, f.cc_name, f.home, f.source), (9, 1, "Meter", "c0ffee01", "live"))
        self.assertEqual(lc.frames[1].event, "dead")
        a = analyze(list(lc.frames), None, lc.meta)
        self.assertEqual(node(a, 9)["name"], "Plug (#9)")

    def test_websocket_client_against_local_server(self):
        import base64, hashlib
        srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
        port = srv.getsockname()[1]

        def frame(text):
            b = text.encode()
            head = bytes([0x81, len(b)]) if len(b) < 126 else bytes([0x81, 126]) + struct.pack(">H", len(b))
            return head + b

        got = []

        def server():
            c, _ = srv.accept()
            req = b""
            while b"\r\n\r\n" not in req:
                req += c.recv(4096)
            key = [ln.split(b": ")[1] for ln in req.split(b"\r\n") if ln.lower().startswith(b"sec-websocket-key")][0]
            acc = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
            c.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + acc + b"\r\n\r\n")
            c.sendall(frame(json.dumps({"type": "version", "homeId": 1, "maxSchemaVersion": 30})))
            for _ in range(3):  # read the three masked client commands
                b0, b1 = c.recv(2)
                n = b1 & 0x7F
                mask = c.recv(4)
                data = bytes(x ^ mask[i % 4] for i, x in enumerate(c.recv(n)))
                got.append(json.loads(data)["command"])
            c.sendall(frame(json.dumps({"type": "event", "event": {"source": "node", "event": "alive", "nodeId": 3}})))
            c.sendall(bytes([0x88, 0]))
            c.close()

        threading.Thread(target=server, daemon=True).start()
        changed = threading.Event()
        lc = LiveClient(f"ws://127.0.0.1:{port}", changed.set, threading.RLock())
        lc._thread.join(5)
        srv.close()
        self.assertEqual(got, ["set_api_schema", "start_listening", "start_listening_logs"])
        self.assertEqual([f.event for f in lc.frames], ["alive"])
        self.assertEqual(lc.state, "closed")

    def test_formatted_message_preferred(self):
        text = log_event_to_text({"formattedMessage": "2026-11-01T09:00:00.000Z CNTRLR   [Node 004] The node is dead.", "message": "x"})
        self.assertTrue(text.startswith("2026-11-01T09:00:00.000Z CNTRLR"))


class ZnifferLive(unittest.TestCase):
    def test_stream_splitter(self):
        from zwlens.zniffer_live import ZnifferStream
        mpdu = build_mpdu("c0ffee01", 1, 2, b"\x25\x02")
        data = bytes([0x21, 1, 0, 0, 0x21, 0, 50, 0x21, 3, len(mpdu)]) + mpdu
        beam_start = bytes([0x21, 4, 0, 0, 1, 0, 50, 0x55, 9, 0, 0])
        beam_stop = bytes([0x21, 5, 0, 0, 1, 0, 50])
        cmd = bytes([0x23, 1, 4, 7, 0, 1, 2])
        blob = b"\x00\xff" + cmd + b"\x21\x99" + data + beam_start + b"\x21\x01junk-no-marker" + beam_stop + data
        s = ZnifferStream()
        out = []
        for i in range(0, len(blob), 3):  # arbitrary chunking
            out += s.feed(blob[i:i + 3])
        self.assertEqual(out, [cmd, data, beam_start, beam_stop, data])
        self.assertGreater(s.discarded, 0)

    @unittest.skipUnless(hasattr(__import__("os"), "openpty"), "needs a pseudo-terminal")
    def test_capture_from_simulated_stick(self):
        import os, time
        from zwlens.zniffer_live import ZnifferClient, ZnifferStream
        master, slave = os.openpty()
        entries = make_samples.sniffer_entries()[:40]
        seen = []
        done = threading.Event()

        def stick():
            import select
            stream = ZnifferStream()
            while not done.is_set():  # poll: on macOS, close() waits for a thread blocked in read()
                if not select.select([master], [], [], 0.05)[0]:
                    continue
                try:
                    chunk = os.read(master, 256)
                except OSError:
                    return
                for cmd in stream.feed(chunk):
                    fn = cmd[1]
                    seen.append(fn)
                    reply = {1: bytes([8, 0, 10, 23]), 3: bytes([0, 0, 1]), 0x13: bytes([cmd[3] if len(cmd) > 3 else 0, 2]) + b"EU"}.get(fn, b"")
                    os.write(master, bytes([0x23, fn, len(reply)]) + reply)
                    if fn == 4:
                        for _ts, mpdu, rate, _rssi in entries:
                            rid = {"9.6k": 0, "40k": 1, "100k": 2}[rate]
                            os.write(master, bytes([0x21, 1, 0, 0, rid, 0, 49, 0x21, 3, len(mpdu)]) + mpdu)

        stick_thread = threading.Thread(target=stick, daemon=True)
        stick_thread.start()
        with tempfile.TemporaryDirectory() as d:
            session = Session(AliasStore(Path(d) / "a.json"))
            session.start_live(os.ttyname(slave))
            for _ in range(60):
                if session.live.state != "connecting" and len(session.live.frames) >= len(entries):
                    break
                time.sleep(0.05)
            st = session.live.status()
            self.assertEqual((st["state"], st["frames"], st["error"]), ("connected", len(entries), None))
            self.assertIn("700/800 series, firmware 10.23", st["info"])
            self.assertIn("EU", st["info"])
            f = session.live.frames[0]
            self.assertEqual((f.source, f.src, f.dst, f.rssi, f.errors), ("zniffer", 1, 2, -60.0, []))
            self.assertEqual(session.summary()["network"]["frames"], len(entries))
            self.assertEqual((st["region"], [r["name"] for r in st["regions"]]), (0, ["EU", "EU"]))
            session.live.set_region(1)
            for _ in range(60):
                if session.live.region == 1:
                    break
                time.sleep(0.05)
            self.assertEqual(session.live.region, 1)
            self.assertIn(2, seen)              # the set-frequency command reached the stick
            with self.assertRaises(Exception):
                session.live.set_region(99)
            session.stop_live()
            self.assertIsNone(session.live)
            self.assertEqual(session.captures[0]["kind"], "zniffer")
            time.sleep(0.1)
            self.assertEqual(seen[0], 5)        # stop first, in case it was already capturing
            self.assertEqual(seen[-1], 5)       # and stop on the way out
            self.assertIn(4, seen)
        done.set()
        stick_thread.join(2)
        os.close(master); os.close(slave)

    @unittest.skipUnless(hasattr(__import__("os"), "openpty"), "needs a pseudo-terminal")
    def test_port_in_use_is_refused_without_writing(self):
        import fcntl, os, select
        from zwlens.zniffer_live import SerialError, open_port
        master, slave = os.openpty()
        holder = os.open(os.ttyname(slave), os.O_RDWR | os.O_NOCTTY)
        fcntl.flock(holder, fcntl.LOCK_EX)
        with self.assertRaises(SerialError) as ctx:
            open_port(os.ttyname(slave))
        self.assertIn("in use", str(ctx.exception))
        self.assertEqual(select.select([master], [], [], 0.2)[0], [])  # nothing reached the device
        for fd in (holder, master, slave):
            os.close(fd)

    @unittest.skipUnless(sys.platform.startswith("linux"), "process lookup is Linux-specific here")
    def test_find_and_stop_port_holder(self):
        import os, subprocess
        from zwlens.zniffer_live import SerialError, port_holders, release_port
        master, slave = os.openpty()
        path = os.ttyname(slave)
        holder = subprocess.Popen([sys.executable, "-c",
                                   "import sys,time,os; os.open(sys.argv[1], os.O_RDWR|os.O_NOCTTY); time.sleep(60)", path])
        try:
            for _ in range(50):
                found = [h for h in port_holders(path) if h["pid"] == holder.pid]
                if found:
                    break
                __import__("time").sleep(0.05)
            self.assertTrue(found)
            with self.assertRaises(SerialError):
                release_port(path, 1)          # never signal a process that is not holding the port
            self.assertTrue(release_port(path, holder.pid))
            self.assertIsNotNone(holder.wait(3))
        finally:
            holder.kill()
            os.close(master); os.close(slave)

    def test_bad_ports_report_errors(self):
        import time
        with tempfile.TemporaryDirectory() as d:
            session = Session(AliasStore(Path(d) / "a.json"))
            for path in (str(Path(d) / "missing"), __file__):
                session.start_live(path)
                for _ in range(40):
                    if session.live.state == "error":
                        break
                    time.sleep(0.05)
                self.assertEqual(session.live.state, "error")
                self.assertTrue(session.live.error)
            session.stop_live()


if __name__ == "__main__":
    unittest.main()
