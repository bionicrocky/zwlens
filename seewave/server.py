"""Local web server: a small JSON API plus the single-page UI. Standard library only."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__
from .aliases import AckStore, AliasStore
from .analysis import analyze, report_markdown
from .controllers import catalogue as controller_catalogue
from .controllers import guide as controller_guide
from .device_guides import catalogue as device_catalogue
from .device_guides import device as device_guide
from .help_content import help_data
from .live import LiveClient
from .parsers import parse_bytes
from .parsers.zlf import write_zlf
from .zniffer_live import SerialError, ZnifferClient, list_ports, port_holders, release_port

WEB = Path(__file__).parent / "web"
STATIC = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8"),
          "/logo.svg": ("logo.svg", "image/svg+xml"),
          "/favicon.ico": ("favicon.ico", "image/x-icon")}
MAX_UPLOAD = 300 * 1024 * 1024
MAX_CONVS = 3000


class Session:
    """Everything loaded into one running instance of the tool."""

    def __init__(self, aliases: AliasStore | None = None, chip: str = "700"):
        self.aliases = aliases or AliasStore()
        self.acks = AckStore(self.aliases.path.with_name("acks.json"))
        self.chip = chip
        self.lock = threading.RLock()
        self.captures: list[dict] = []
        self.live: LiveClient | None = None
        self.version = 1
        self._next_id = 1
        self._cache = None  # (version, analysis, frames)

    def bump(self) -> None:
        with self.lock:
            self.version += 1

    def add(self, name: str, data: bytes) -> dict:
        res = parse_bytes(data, name, self.chip)
        with self.lock:
            cap = {"id": self._next_id, "name": name, "kind": res.kind, "frames": res.frames,
                   "warnings": res.warnings}
            self._next_id += 1
            if res.frames:
                self.captures.append(cap)
                self.version += 1
        return {"id": cap["id"], "name": name, "kind": res.kind, "frames": len(res.frames),
                "warnings": res.warnings, "loaded": bool(res.frames)}

    def remove(self, cid: int) -> None:
        with self.lock:
            self.captures = [c for c in self.captures if c["id"] != cid]
            self.version += 1

    def clear(self) -> None:
        self.stop_live()
        with self.lock:
            self.captures = []
            self.version += 1

    def start_live(self, url: str, frequency: int | None = None) -> None:
        """`url` is a Z-Wave JS server (ws://...) or the serial port of a Zniffer stick."""
        if not url:
            raise ValueError("give a ws:// URL or a serial port")
        self.stop_live()
        with self.lock:
            if url.lower().startswith(("ws://", "wss://")):
                self.live = LiveClient(url, self.bump, self.lock)
            else:
                self.live = ZnifferClient(url, self.bump, self.lock, frequency)
            self.version += 1

    def stop_live(self) -> None:
        live = self.live
        if live is None:
            return
        live.stop()  # outside the lock: the capture thread needs it to finish
        with self.lock:
            if self.live is live:
                # Keep what was captured as an ordinary capture.
                if live.frames:
                    self.captures.append({"id": self._next_id, "name": f"live: {live.url}",
                                          "kind": live.kind, "frames": list(live.frames), "warnings": []})
                    self._next_id += 1
                self.live = None
                self.version += 1

    def analysis(self):
        with self.lock:
            if self._cache and self._cache[0] == self.version:
                return self._cache[1], self._cache[2]
            version = self.version
            frames = [f for c in self.captures for f in c["frames"]]
            meta = {}
            if self.live:
                frames += list(self.live.frames)
                meta = dict(self.live.meta)
            a = analyze(frames, self.aliases.name, meta)
            self._cache = (version, a, frames)
            return a, frames

    def summary(self) -> dict:
        a, _ = self.analysis()
        with self.lock:
            out = dict(a)
            out["conv_total"] = len(a["conversations"])
            out["conversations"] = a["conversations"][-MAX_CONVS:]
            out["version"] = self.version
            out["captures"] = [{"id": c["id"], "name": c["name"], "kind": c["kind"],
                                "frames": len(c["frames"]), "warnings": c["warnings"]} for c in self.captures]
            out["live"] = self.live.status() if self.live else None
            out["aliases"] = self.aliases.data
            out["alias_file"] = str(self.aliases.path)
            out["guides"] = controller_catalogue()
            home, ctrl = a["network"].get("home") or "", a["network"].get("controller")
            out["acks"] = self.acks.get(home)
            out["devices"] = device_catalogue()
            model = self.aliases.model(home, ctrl)
            g = controller_guide(model)
            out["controller_model"] = model if (g or model == "other") else None
            out["controller_key"] = {"home": home or "*", "node": ctrl if ctrl is not None else 0}
            if g:
                out["nodes"] = [dict(n, type=g["name"]) if n["controller"] and not n["foreign"] else n
                                for n in a["nodes"]]
            out["settings"] = {"chip": self.chip}
            out["app_version"] = __version__
        return out

    def frames(self, q: dict) -> dict:
        _, frames = self.analysis()

        def one(name, cast=str):
            v = q.get(name, [None])[0]
            try:
                return cast(v) if v not in (None, "") else None
            except ValueError:
                return None

        conv, node, text, kind = one("conv", int), one("node", int), one("q"), one("kind")
        offset, limit = one("offset", int) or 0, min(one("limit", int) or 200, 2000)
        sel = frames
        if conv is not None:
            sel = [f for f in sel if f.conv == conv]
        if node is not None:
            sel = [f for f in sel if node in (f.src, f.dst, f.txn) or node in f.repeaters]
        if kind == "problems":
            sel = [f for f in sel if f.errors or f.role == "retx" or f.kind in ("routed_err", "event")
                   or f.tx_status in ("NoAck", "Fail")]
        if text:
            t = text.lower()
            sel = [f for f in sel if t in f.label().lower() or t in f.summary.lower() or t in f.raw
                   or t in " ".join(f.encap).lower() or t in (f.text or "").lower()]
        return {"total": len(sel), "offset": offset,
                "frames": [f.to_dict() for f in sel[offset:offset + limit]]}


def valid_key(home: str, node: str) -> bool:
    """Alias keys are '<8 hex digit home id or *>:<node id>'."""
    return node.isdigit() and int(node) <= 4095 and (
        home == "*" or (len(home) == 8 and all(ch in "0123456789abcdef" for ch in home)))


def make_handler(session: Session, allowed_hosts: set | None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "SeeWave/" + __version__

        def log_message(self, *args):  # keep the console quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200) -> None:
            self._send(code, json.dumps(obj, separators=(",", ":")).encode(), "application/json")

        def _host_ok(self) -> bool:
            # Reject DNS-rebinding: the Host header must be one we are actually served on.
            if allowed_hosts is None:
                return True
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0].lower()
            return host in allowed_hosts

        def do_GET(self):
            if not self._host_ok():
                return self._json({"error": "forbidden host"}, 403)
            u = urlparse(self.path)
            try:
                if u.path in STATIC:
                    name, ctype = STATIC[u.path]
                    return self._send(200, (WEB / name).read_bytes(), ctype)
                if u.path == "/api/version":
                    return self._json({"version": session.version})
                if u.path == "/api/analysis":
                    return self._json(session.summary())
                if u.path == "/api/help":
                    return self._json(help_data())
                if u.path == "/api/frames":
                    return self._json(session.frames(parse_qs(u.query)))
                if u.path == "/api/port":
                    path = parse_qs(u.query).get("path", [""])[0]
                    return self._json({"path": path, "holders": port_holders(path) if path else []})
                if u.path == "/api/ports":
                    return self._json({"ports": list_ports()})
                if u.path == "/api/capture.zlf":
                    _, frames = session.analysis()
                    entries = [(f.ts, bytes.fromhex(f.raw), None if f.kind == "beam" else (f.speed or "40k"),
                                f.rssi if f.rssi is not None else -70)
                               for f in frames if f.source in ("zniffer", "sdr") and f.raw
                               and (f.kind != "beam" or f.raw.startswith("21"))]
                    self.send_response(200)
                    body = write_zlf(entries)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Disposition", 'attachment; filename="seewave-capture.zlf"')
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    return self.wfile.write(body)
                if u.path == "/api/report.md":
                    a, _ = session.analysis()
                    return self._send(200, report_markdown(a).encode(), "text/markdown; charset=utf-8")
                self._json({"error": "not found"}, 404)
            except Exception as exc:
                self._json({"error": str(exc)}, 500)

        def do_POST(self):
            # A custom header forces a CORS preflight, which we never grant, so other sites cannot post here.
            if not self._host_ok() or self.headers.get("X-SeeWave") != "1":
                return self._json({"error": "forbidden"}, 403)
            u = urlparse(self.path)
            try:
                length = int(self.headers.get("Content-Length") or 0)
                if length > MAX_UPLOAD:
                    return self._json({"error": "file too large (limit 300 MB)"}, 413)
                body = self.rfile.read(length)
                if u.path == "/api/upload":
                    name = parse_qs(u.query).get("name", ["capture"])[0][:200]
                    return self._json(session.add(name, body))
                data = json.loads(body or b"{}")
                if u.path == "/api/clear":
                    session.clear()
                elif u.path == "/api/remove":
                    session.remove(int(data["id"]))
                elif u.path == "/api/alias":
                    key = str(data["key"])
                    home, _, node = key.rpartition(":")
                    if not valid_key(home, node):
                        return self._json({"error": "bad alias key"}, 400)
                    session.aliases.set(key, str(data.get("name", "")), str(data.get("location", "")),
                                        str(data.get("notes", "")))
                    session.bump()
                elif u.path == "/api/controller":
                    home, node = str(data.get("home") or "*"), str(data.get("node", 0))
                    model = str(data.get("model") or "")
                    if not valid_key(home, node):
                        return self._json({"error": "bad network or node"}, 400)
                    if model and model != "other" and controller_guide(model) is None:
                        return self._json({"error": "unknown controller model"}, 400)
                    session.aliases.update(f"{home}:{node}", model=model)
                    session.bump()
                elif u.path == "/api/device":
                    key = str(data.get("key", ""))
                    home, _, node = key.rpartition(":")
                    dev = str(data.get("device") or "")
                    if not valid_key(home, node):
                        return self._json({"error": "bad node key"}, 400)
                    if dev and device_guide(dev) is None:
                        return self._json({"error": "unknown device guide"}, 400)
                    session.aliases.update(key, device=dev)
                    session.bump()
                elif u.path == "/api/ack":
                    home = str(data.get("home") or "")
                    if home and not valid_key(home, "0"):
                        return self._json({"error": "bad network"}, 400)
                    items = data.get("items") or {}
                    if not isinstance(items, dict):
                        return self._json({"error": "items must be an object"}, 400)
                    if data.get("clear"):
                        session.acks.unack(home)
                    elif data.get("remove"):
                        session.acks.unack(home, [str(k) for k in data["remove"]])
                    else:
                        session.acks.ack(home, {str(k): str(v) for k, v in items.items()})
                    session.bump()
                elif u.path == "/api/live/start":
                    freq = data.get("frequency")
                    session.start_live(str(data["url"]).strip(), int(freq) if freq not in (None, "") else None)
                elif u.path == "/api/port/release":
                    try:
                        freed = release_port(str(data["path"]), int(data["pid"]))
                    except SerialError as exc:
                        return self._json({"error": str(exc)}, 409)
                    return self._json({"ok": True, "freed": freed})
                elif u.path == "/api/live/region":
                    live = session.live
                    if live is None or not hasattr(live, "set_region"):
                        return self._json({"error": "no Zniffer capture is running"}, 409)
                    try:
                        live.set_region(int(data["id"]))
                    except SerialError as exc:
                        return self._json({"error": str(exc)}, 409)
                elif u.path == "/api/sample":
                    from .sample_data import sample_bytes
                    return self._json(session.add(*sample_bytes(str(data.get("kind", "zniffer")))))
                elif u.path == "/api/settings":
                    if data.get("chip") in ("500", "700"):
                        session.chip = data["chip"]
                        session.bump()
                elif u.path == "/api/live/stop":
                    session.stop_live()
                else:
                    return self._json({"error": "not found"}, 404)
                self._json({"ok": True})
            except (KeyError, ValueError) as exc:
                self._json({"error": f"bad request: {exc}"}, 400)
            except Exception as exc:
                self._json({"error": str(exc)}, 500)

    return Handler


def serve(session: Session, host: str = "127.0.0.1", port: int = 8377) -> ThreadingHTTPServer:
    loopback = host in ("127.0.0.1", "localhost", "::1")
    allowed = {"127.0.0.1", "localhost", "[::1]"} if loopback else None
    httpd = ThreadingHTTPServer((host, port), make_handler(session, allowed))
    httpd.daemon_threads = True
    return httpd
