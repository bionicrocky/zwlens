"""Persistent node aliases (friendly names, locations, notes), stored as a small JSON file."""
from __future__ import annotations

import json
import os
import shutil
import sys
import threading
from pathlib import Path


def default_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    new, old = base / "seewave", base / "zwlens"  # the app was called zwlens before
    if not new.exists() and old.is_dir():
        try:
            shutil.copytree(old, new)
        except OSError:
            return old / "aliases.json"
    return new / "aliases.json"


class AliasStore:
    """Keys are '<home id>:<node id>', or '*:<node id>' when the home ID is unknown."""

    def __init__(self, path: str | os.PathLike | None = None):
        self.path = Path(path) if path else default_path()
        self._lock = threading.Lock()
        self.data: dict[str, dict] = {}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data = {str(k): v for k, v in loaded.items() if isinstance(v, dict)}
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            print(f"warning: could not read aliases from {self.path}: {exc}", file=sys.stderr)

    def get(self, home: str, node: int) -> dict | None:
        return self.data.get(f"{home or '*'}:{node}") or self.data.get(f"*:{node}")

    def name(self, home: str, node: int) -> str | None:
        entry = self.get(home, node)
        return (entry or {}).get("name") or None

    def set(self, key: str, name: str = "", location: str = "", notes: str = "") -> None:
        """Set a node's alias, location and notes. Other fields on the entry (such as model) are kept."""
        self.update(key, name=name, location=location, notes=notes)

    def update(self, key: str, **fields) -> None:
        """Merge fields into an entry. An empty value removes that field; an empty entry is deleted."""
        with self._lock:
            entry = dict(self.data.get(key, {}))
            for k, v in fields.items():
                v = (v or "").strip()[:200]
                if v:
                    entry[k] = v
                else:
                    entry.pop(k, None)
            if entry:
                self.data[key] = entry
            else:
                self.data.pop(key, None)
            self._save()

    def model(self, home: str, controller: int | None) -> str | None:
        """The controller model saved for a network: on its controller's entry, or on node 0 when the
        controller was not identified when it was chosen."""
        for node in ([controller] if controller is not None else []) + [0]:
            m = (self.data.get(f"{home or '*'}:{node}") or {}).get("model")
            if m:
                return m
        return (self.data.get("*:0") or {}).get("model") or None

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)


SEVERITIES = ("info", "warn", "crit")


class AckStore:
    """Acknowledged findings, per network: {home: {finding key: severity when acknowledged}}.

    A finding comes back if it gets worse than the severity it had when it was acknowledged.
    """

    MAX_PER_HOME = 5000

    def __init__(self, path: str | os.PathLike):
        self.path = Path(path)
        self._lock = threading.Lock()
        self.data: dict[str, dict[str, str]] = {}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data = {str(h): {str(k): v for k, v in m.items() if v in SEVERITIES}
                             for h, m in loaded.items() if isinstance(m, dict)}
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            print(f"warning: could not read acknowledgements from {self.path}: {exc}", file=sys.stderr)

    def get(self, home: str) -> dict[str, str]:
        return dict(self.data.get(home or "*", {}))

    def ack(self, home: str, items: dict[str, str]) -> None:
        with self._lock:
            m = self.data.setdefault(home or "*", {})
            for k, sev in items.items():
                if sev in SEVERITIES and 0 < len(k) <= 400 and (k in m or len(m) < self.MAX_PER_HOME):
                    m[k] = sev
            self._save()

    def unack(self, home: str, keys=None) -> None:
        """Forget some acknowledgements, or all of them for this network when keys is None."""
        with self._lock:
            if keys is None:
                self.data.pop(home or "*", None)
            else:
                m = self.data.get(home or "*", {})
                for k in keys:
                    m.pop(k, None)
                if not m:
                    self.data.pop(home or "*", None)
            self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)
