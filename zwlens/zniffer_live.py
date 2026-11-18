"""Live capture from a Zniffer USB stick over its serial port.

The protocol follows the open-source Z-Wave JS implementation: 115200 baud 8N1,
command frames [0x23, function, length, payload...] and data frames starting 0x21.

On Linux and macOS the port is driven with the standard library. On Windows the
optional `pyserial` package is required (pip install pyserial).
"""
from __future__ import annotations

import glob
import os
import signal
import stat
import subprocess
import sys
import threading
import time

from .parsers.zlf import parse_zniffer_frame

BAUD = 115200
FN_VERSION, FN_SET_FREQ, FN_FREQS, FN_START, FN_STOP, FN_BAUD, FN_FREQ_INFO = 0x01, 0x02, 0x03, 0x04, 0x05, 0x0E, 0x13
MAX_FRAMES = 200000


class SerialError(Exception):
    pass


class _PosixPort:
    def __init__(self, path: str):
        import termios
        try:
            mode = os.stat(path).st_mode
        except OSError as exc:
            raise SerialError(f"cannot open {path}: {exc.strerror}") from None
        if not stat.S_ISCHR(mode):
            raise SerialError(f"{path} is not a serial device")
        try:
            self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        except PermissionError:
            raise SerialError(f"permission denied for {path}. On Linux add your user to the 'dialout' "
                              "group (sudo usermod -aG dialout $USER) and log in again.") from None
        except OSError as exc:
            raise SerialError(f"cannot open {path}: {exc.strerror}") from None
        try:
            # Never talk to a port another program is using: stray bytes would disturb its session.
            import fcntl
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.fd)
            who = ", ".join(f"{h['name']} (process {h['pid']})" for h in port_holders(path))
            raise SerialError(f"{path} is in use by {who or 'another program (for example Z-Wave JS UI)'}. "
                              "Close it there first; nothing was sent to the device.") from None
        try:
            attrs = termios.tcgetattr(self.fd)
            cflag = attrs[2] & ~(termios.CSIZE | termios.PARENB | termios.CSTOPB | termios.HUPCL
                                 | getattr(termios, "CRTSCTS", 0))
            cflag |= termios.CS8 | termios.CREAD | termios.CLOCAL
            cc = attrs[6]
            cc[termios.VMIN], cc[termios.VTIME] = 0, 0
            termios.tcsetattr(self.fd, termios.TCSANOW,
                              [0, 0, cflag, 0, termios.B115200, termios.B115200, cc])
            termios.tcflush(self.fd, termios.TCIOFLUSH)
        except (termios.error, OSError) as exc:
            os.close(self.fd)
            raise SerialError(f"{path} could not be configured as a serial port: {exc}") from None

    def read(self, timeout: float = 0.2) -> bytes:
        import select
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return b""
        try:
            data = os.read(self.fd, 4096)
        except BlockingIOError:
            return b""
        if not data:
            raise SerialError("the device was disconnected")
        return data

    def write(self, data: bytes) -> None:
        import select
        while data:
            try:
                n = os.write(self.fd, data)
                data = data[n:]
            except BlockingIOError:
                select.select([], [self.fd], [], 1.0)

    def close(self) -> None:
        try:
            os.close(self.fd)
        except OSError:
            pass


class _PySerialPort:
    def __init__(self, path: str):
        try:
            import serial  # type: ignore
        except ImportError:
            raise SerialError("Reading a serial port on this system needs the 'pyserial' package: "
                              "run 'pip install pyserial' and try again.") from None
        try:
            self.ser = serial.Serial(path, BAUD, timeout=0.2)
        except Exception as exc:
            raise SerialError(f"cannot open {path}: {exc}") from None

    def read(self, timeout: float = 0.2) -> bytes:
        try:
            self.ser.timeout = timeout
            return self.ser.read(self.ser.in_waiting or 1)
        except Exception as exc:
            raise SerialError(f"the device was disconnected ({exc})") from None

    def write(self, data: bytes) -> None:
        self.ser.write(data)

    def close(self) -> None:
        try:
            self.ser.close()
        except Exception:
            pass


def _friendly(name: str, cmd: str) -> str:
    text = f"{name} {cmd}".lower()
    if "zwave-js-ui" in text or "zwavejs2mqtt" in text:
        return "Z-Wave JS UI"
    if "zwave" in text:
        return "Z-Wave JS"
    if "hass" in text or "homeassistant" in text or "home-assistant" in text:
        return "Home Assistant"
    return name or "unknown program"


def port_holders(path: str) -> list[dict]:
    """Other processes that have this serial port open (best effort; own-user processes only
    unless running as root). Returns [] where the platform cannot tell."""
    try:
        real = os.path.realpath(path)
    except OSError:
        return []
    pids = []
    if sys.platform.startswith("linux"):
        for pid in os.listdir("/proc"):
            if not pid.isdigit() or int(pid) == os.getpid():
                continue
            try:
                fds = os.listdir(f"/proc/{pid}/fd")
                if any(os.readlink(f"/proc/{pid}/fd/{fd}") == real for fd in fds):
                    pids.append(int(pid))
            except OSError:
                continue
    elif os.name == "posix":
        try:
            res = subprocess.run(["lsof", "-t", "--", real], capture_output=True, text=True, timeout=5)
            pids = [int(p) for p in res.stdout.split() if p.isdigit() and int(p) != os.getpid()]
        except (OSError, subprocess.SubprocessError):
            pids = []
    out = []
    for pid in pids:
        name = cmd = ""
        try:
            if sys.platform.startswith("linux"):
                name = Path_read(f"/proc/{pid}/comm").strip()
                cmd = Path_read(f"/proc/{pid}/cmdline").replace("\0", " ").strip()
            else:
                cmd = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True,
                                     text=True, timeout=5).stdout.strip()
                name = os.path.basename(cmd.split(" ")[0]) if cmd else ""
        except (OSError, subprocess.SubprocessError):
            pass
        out.append({"pid": pid, "name": _friendly(name, cmd), "command": cmd[:200]})
    return out


def Path_read(path: str) -> str:
    with open(path, "r", errors="replace") as fh:
        return fh.read()


def release_port(path: str, pid: int, wait: float = 5.0) -> bool:
    """Ask a process that holds `path` to quit (SIGTERM). Refuses any pid that is not holding it."""
    if not any(h["pid"] == pid for h in port_holders(path)):
        raise SerialError(f"process {pid} is not using {path}")
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        raise SerialError(f"could not stop process {pid}: {exc.strerror}") from None
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if not any(h["pid"] == pid for h in port_holders(path)):
            return True
        time.sleep(0.2)
    return False


def open_port(path: str):
    return _PosixPort(path) if os.name == "posix" else _PySerialPort(path)


def list_ports() -> list[dict]:
    """Serial ports that might be a Zniffer stick."""
    out = []
    try:
        from serial.tools import list_ports as lp  # type: ignore
        for p in lp.comports():
            if (p.hwid or "n/a") == "n/a" and (p.description or "n/a") == "n/a":
                continue  # legacy motherboard ports with nothing attached
            out.append({"path": p.device, "label": p.description or p.device})
        if out:
            return out
    except ImportError:
        pass
    if os.name == "posix":
        seen = set()
        for path in sorted(glob.glob("/dev/serial/by-id/*")):
            real = os.path.realpath(path)
            seen.add(real)
            out.append({"path": path, "label": f"{os.path.basename(path)} ({real})"})
        for pattern in ("/dev/ttyUSB*", "/dev/ttyACM*", "/dev/cu.usb*", "/dev/cu.SLAB*"):
            for path in sorted(glob.glob(pattern)):
                if path not in seen:
                    out.append({"path": path, "label": path})
    return out


class ZnifferStream:
    """Splits the serial byte stream into Zniffer frames."""

    def __init__(self):
        self.buf = bytearray()
        self.discarded = 0

    def feed(self, data: bytes) -> list[bytes]:
        self.buf += data
        frames = []
        buf = self.buf
        while buf:
            b0 = buf[0]
            if b0 == 0x23:
                if len(buf) < 3:
                    break
                need = buf[2] + 3
            elif b0 == 0x21:
                if len(buf) < 2:
                    break
                kind = buf[1]
                if kind == 0x04:
                    need = 11
                elif kind == 0x05:
                    need = 7
                elif kind in (0x01, 0x02):
                    if len(buf) < 10:
                        break
                    # A real data frame carries a 0x21 0x03 marker; anything else is a false start.
                    if buf[7] != 0x21 or buf[8] != 0x03:
                        del buf[0]
                        self.discarded += 1
                        continue
                    need = buf[9] + 10
                else:
                    del buf[0]
                    self.discarded += 1
                    continue
            else:
                del buf[0]
                self.discarded += 1
                continue
            if len(buf) < need:
                break
            frames.append(bytes(buf[:need]))
            del buf[:need]
        return frames


class ZnifferClient:
    """Background thread capturing from a Zniffer stick. Same interface as live.LiveClient."""

    kind = "zniffer"

    def __init__(self, path: str, on_change, lock: threading.RLock, frequency: int | None = None,
                 port_factory=open_port):
        self.url, self._on_change, self._lock = path, on_change, lock
        self.frequency = frequency
        self.state, self.error, self.info = "connecting", None, ""
        self.frames: list = []
        self.meta: dict = {}
        self.chip = "700"
        self.corrupt = 0
        self._factory = port_factory
        self._port = None
        self._stream = ZnifferStream()
        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True, name="zwlens-zniffer")
        self._thread.start()

    def status(self) -> dict:
        return {"url": self.url, "state": self.state, "error": self.error, "frames": len(self.frames),
                "info": self.info, "kind": self.kind}

    def stop(self) -> None:
        self._stop = True
        self._thread.join(2.0)
        self.state = "stopped"

    # -- protocol --------------------------------------------------------
    def _pump(self, timeout: float):
        """Read once; store data frames, return any command frames."""
        commands = []
        for raw in self._stream.feed(self._port.read(timeout)):
            if raw[0] == 0x23:
                commands.append(raw)
            else:
                self._data(raw)
        return commands

    def _command(self, fn: int, payload: bytes = b"", timeout: float = 1.0) -> bytes | None:
        """Send a command and return its response payload, or None if the stick stays silent."""
        self._port.write(bytes([0x23, fn, len(payload)]) + payload)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not self._stop:
            for raw in self._pump(0.1):
                if raw[1] == fn:
                    return raw[3:]
        return None

    def _data(self, raw: bytes) -> None:
        f = parse_zniffer_frame(raw, self.chip)
        if f is None:
            return
        if "bad checksum" in f.errors:
            self.corrupt += 1
        f.ts, f.source, f.capture = time.time(), "zniffer", f"zniffer: {self.url}"
        with self._lock:
            self.frames.append(f)
            if len(self.frames) > MAX_FRAMES:
                del self.frames[:MAX_FRAMES // 4]

    def _handshake(self) -> None:
        self._command(FN_STOP, timeout=0.4)  # in case an earlier session left it capturing
        version = self._command(FN_VERSION)
        if version is None or len(version) < 4:
            raise SerialError("no answer from the device. Check that this port is a Zniffer stick "
                              "(a controller stick will not respond) and that nothing else has it open.")
        self.chip = "700" if version[0] >= 0x07 else "500"
        parts = [f"{self.chip if self.chip == '500' else '700/800'} series, firmware {version[2]}.{version[3]}"]
        self._command(FN_BAUD, b"\x00")
        freqs = self._command(FN_FREQS)
        if freqs:
            current, supported = freqs[0], list(freqs[1:])
            if self.frequency is not None and self.frequency != current:
                if self.frequency in supported:
                    self._command(FN_SET_FREQ, bytes([self.frequency]))
                    current = self.frequency
                else:
                    self.error = (f"frequency {self.frequency} is not supported by this stick "
                                  f"(supported: {', '.join(map(str, supported))}); using {current}.")
            name = self._command(FN_FREQ_INFO, bytes([current]), timeout=0.5)
            label = name[2:].decode("ascii", "replace").strip("\x00 ") if name and len(name) > 2 else ""
            parts.append(f"frequency {label or current}")
        if self._command(FN_START) is None:
            raise SerialError("the device did not acknowledge the start command.")
        self.info = ", ".join(parts)

    def _run(self) -> None:
        try:
            self._port = self._factory(self.url)
            self._handshake()
            self.state = "connected"
            self._on_change()
            last = 0
            while not self._stop:
                self._pump(0.2)
                if len(self.frames) != last:
                    last = len(self.frames)
                    self._on_change()
        except Exception as exc:
            if not self._stop:
                self.state, self.error = "error", str(exc)
        finally:
            if self._port is not None:
                try:
                    self._port.write(bytes([0x23, FN_STOP, 0]))
                except Exception:
                    pass
                self._port.close()
            self._on_change()
