"""Per-controller directions: how to carry out each troubleshooting action on a specific hub.

Menu paths are quoted from the manufacturers' documentation (sources are linked per item).
Firmware updates move menus around, so treat them as a guide and check the linked page.
"""
from __future__ import annotations

from .controller_guides import GUIDES

# Action id -> label shown in the UI, in display order.
ACTIONS = {
    "include": "Add (include) a device",
    "exclude": "Remove (exclude) a device",
    "remove_failed": "Remove or replace a dead node",
    "rebuild": "Rebuild routes / repair the network",
    "routes": "See routes, neighbours and signal",
    "logs": "Get logs and diagnostics",
    "config": "Change wake-up, polling and reporting settings",
    "firmware": "Update firmware, back up the network",
}

# Which actions matter for each of the five troubleshooters.
ISSUE_ACTIONS = {
    "unreachable": ["remove_failed", "rebuild", "exclude", "include"],
    "signal": ["routes", "rebuild", "logs"],
    "routing": ["routes", "rebuild", "remove_failed"],
    "congestion": ["config", "logs"],
    "security": ["exclude", "include", "firmware"],
}


# Which controller action a piece of advice needs, judged from its wording. First match wins.
_ACTION_RULES = [
    ("remove_failed", ("remove failed", "remove the old", "marked dead", "ping it", "ghost", "remove dead nodes")),
    ("exclude", ("exclude", "re-include", "include it again", "include the device again")),
    ("rebuild", ("rebuild", "heal", "rediscover", "route assignment", "routes for")),
    ("config", ("parameter", "threshold", "polling", "poll ", "wake-up interval", "wake the device", "association",
                "reporting", "report on", "supervision", "lifeline")),
    ("firmware", ("firmware", "network keys", "back up")),
    ("include", ("smartstart", "provisioning", "start inclusion", "bring the device closer")),
    ("routes", ("move the controller", "extension cable", "interference", "noise", "repeater", "signal", "sniffer",
                "move the device", "metal", "path")),
    ("logs", ("log", "debug")),
]


def action_for(text: str) -> str | None:
    low = (text or "").lower()
    for action, needles in _ACTION_RULES:
        if any(n in low for n in needles):
            return action
    return None


def guide(gid: str | None) -> dict | None:
    return next((g for g in GUIDES if g["id"] == gid), None)


def catalogue() -> dict:
    return {"actions": ACTIONS, "issue_actions": ISSUE_ACTIONS, "controllers": GUIDES}
