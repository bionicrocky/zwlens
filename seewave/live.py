"""Read-only live connection to a Z-Wave JS server (the WebSocket server used by
Z-Wave JS UI and Home Assistant, default ws://host:3000).

Only three commands are ever sent: set_api_schema, start_listening and
start_listening_logs. Nothing on the network or controller is changed.
A minimal WebSocket client is implemented here so the tool has no dependencies.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import ssl
import struct
import threading
import time
from urllib.parse import urlparse

from .model import Frame
from .parsers.zwavejs_log import HEAD, LogParser

MAX_MESSAGE = 64 * 1024 * 1024
NODE_EVENTS = {"dead": "dead", "alive": "alive", "sleep": "asleep", "wake up": "awake"}


class WebSocket:
    def __init__(self, url: str, timeout: float = 10.0):
        u = urlparse(url)
        if u.scheme not in ("ws", "wss") or not u.hostname:
            raise ValueError("URL must look like ws://host:3000")
        port = u.port or (443 if u.scheme == "wss" else 80)
        sock = socket.create_connection((u.hostname, port), timeout=timeout)
        if u.scheme == "wss":
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=u.hostname)
        self.sock = sock
        key = base64.b64encode(os.urandom(16)).decode()
        path = (u.path or "/") + (f"?{u.query}" if u.query else "")
        host = u.hostname if port in (80, 443) else f"{u.hostname}:{port}"
        sock.sendall((f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
                      f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                      "Sec-WebSocket-Version: 13\r\n\r\n").encode())
        self._buf = b""
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError("connection closed during handshake")
            head += chunk
            if len(head) > 65536:
                raise ConnectionError("oversized handshake response")
        head, self._buf = head.split(b"\r\n\r\n", 1)
        status = head.split(b"\r\n", 1)[0].decode("latin-1")
        if " 101" not in status:
            raise ConnectionError(f"server refused the WebSocket upgrade: {status}")
        sock.settimeout(None)

    def _read(self, n: int) -> bytes:
        while len(self._buf) < n:
            chunk = self.sock.recv(max(65536, n - len(self._buf)))
            if not chunk:
                raise ConnectionError("connection closed")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def _send(self, opcode: int, payload: bytes) -> None:
        mask = os.urandom(4)
        n = len(payload)
        head = bytes([0x80 | opcode])
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(head + mask + masked)

    def send_json(self, obj) -> None:
        self._send(0x1, json.dumps(obj).encode())

    def recv(self) -> str | None:
        """Return the next text message, or None when the server closes the connection."""
        parts, total = [], 0
        while True:
            b0, b1 = self._read(2)
            opcode, n = b0 & 0x0F, b1 & 0x7F
            if n == 126:
                n, = struct.unpack(">H", self._read(2))
            elif n == 127:
                n, = struct.unpack(">Q", self._read(8))
            total += n
            if total > MAX_MESSAGE:
                raise ConnectionError("message too large")
            mask = self._read(4) if b1 & 0x80 else None
            data = self._read(n)
            if mask:
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            if opcode == 0x8:
                return None
            if opcode == 0x9:
                self._send(0xA, data)
                continue
            if opcode == 0xA:
                continue
            parts.append(data)
            if b0 & 0x80:
                return b"".join(parts).decode("utf-8", errors="replace")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


def log_event_to_text(ev: dict) -> str:
    """Rebuild a driver log entry from a zwave-js-server 'logging' event."""
    formatted = ev.get("formattedMessage")
    if isinstance(formatted, str) and HEAD.match(formatted.split("\n", 1)[0]):
        return formatted
    msg = ev.get("message", "")
    if isinstance(msg, list):
        msg = "\n".join(str(m) for m in msg)
    lines = str(msg).split("\n")
    ts = str(ev.get("timestamp") or time.strftime("%H:%M:%S.000"))
    direction = str(ev.get("direction") or "  ").strip() or " "
    tags = str(ev.get("primaryTags") or "")
    head = f"{ts} {ev.get('label') or 'DRIVER'} {direction} {tags} {lines[0]}".rstrip()
    return "\n".join([head] + ["    " + ln for ln in lines[1:]])


class LiveClient:
    """Background thread that turns server events into frames."""

    kind = "live"

    def __init__(self, url: str, on_change, lock: threading.RLock):
        self.url, self._on_change, self._lock = url, on_change, lock
        self.state, self.error = "connecting", None
        self.parser = LogParser(capture=url, source="live")
        self.meta: dict[int, dict] = {}
        self._ws: WebSocket | None = None
        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True, name="seewave-live")
        self._thread.start()

    @property
    def frames(self) -> list:
        return self.parser.frames

    def stop(self) -> None:
        self._stop = True
        if self._ws:
            self._ws.close()
        self.state = "stopped"

    def status(self) -> dict:
        return {"url": self.url, "state": self.state, "error": self.error, "frames": len(self.parser.frames),
                "info": "", "kind": self.kind}

    def _run(self) -> None:
        try:
            self._ws = ws = WebSocket(self.url)
            while not self._stop:
                raw = ws.recv()
                if raw is None:
                    break
                try:
                    self.handle(json.loads(raw), ws.send_json)
                except (ValueError, KeyError, TypeError, AttributeError):
                    continue  # ignore messages we do not understand
            if not self._stop:
                self.state, self.error = "closed", "The server closed the connection."
        except Exception as exc:
            if not self._stop:
                self.state, self.error = "error", str(exc)
        finally:
            self._on_change()

    def handle(self, msg: dict, send) -> None:
        """Process one decoded server message. Separate from the socket loop so it can be tested."""
        kind = msg.get("type")
        if kind == "version":
            home = msg.get("homeId")
            if isinstance(home, int):
                self.parser.home = f"{home & 0xFFFFFFFF:08x}"
            schema = min(int(msg.get("maxSchemaVersion", 0)), 40)
            send({"messageId": "schema", "command": "set_api_schema", "schemaVersion": schema})
            send({"messageId": "listen", "command": "start_listening"})
            send({"messageId": "logs", "command": "start_listening_logs"})
            self.state = "connected"
            self._on_change()
        elif kind == "result":
            if msg.get("messageId") == "listen" and msg.get("success"):
                self._load_state(msg["result"]["state"])
                self._on_change()
            elif msg.get("success") is False and msg.get("messageId") == "logs":
                self.error = "The server refused log streaming; only node status events will be shown."
        elif kind == "event":
            ev = msg.get("event") or {}
            with self._lock:
                before = len(self.parser.frames)
                if ev.get("source") == "driver" and ev.get("event") == "logging":
                    self.parser.feed(log_event_to_text(ev))
                    self.parser._flush()
                elif ev.get("source") == "node" and ev.get("event") in NODE_EVENTS:
                    name = NODE_EVENTS[ev["event"]]
                    self.parser.frames.append(Frame(
                        source="live", capture=self.url, kind="event", ts=time.time(),
                        home=self.parser.home, src=ev.get("nodeId"), event=name,
                        text=f"Node {ev.get('nodeId')} is {name}"))
                changed = len(self.parser.frames) != before
                if len(self.parser.frames) > 200000:
                    del self.parser.frames[:50000]
            if changed:
                self._on_change()

    def _load_state(self, state: dict) -> None:
        own = (state.get("controller") or {}).get("ownNodeId")
        if isinstance(own, int):
            self.parser.controller = own
        for n in state.get("nodes") or []:
            nid = n.get("nodeId")
            if not isinstance(nid, int):
                continue
            cfg = n.get("deviceConfig") or {}
            product = " ".join(str(x) for x in (cfg.get("manufacturer"), cfg.get("label")) if x)
            self.meta[nid] = {
                "name": n.get("name") or None, "location": n.get("location") or None,
                "isListening": n.get("isListening"), "isFrequentListening": bool(n.get("isFrequentListening")),
                "product": product or None,
            }
