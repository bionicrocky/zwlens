"""Persistent node aliases (friendly names, locations, notes), stored as a small JSON file."""
from __future__ import annotations

import json
import os
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
    return base / "zwlens" / "aliases.json"


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
        entry = {k: v.strip()[:200] for k, v in (("name", name), ("location", location), ("notes", notes))
                 if v and v.strip()}
        with self._lock:
            if entry:
                self.data[key] = entry
            else:
                self.data.pop(key, None)
            self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)
