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


def catalogue() -> dict:
    return {"actions": ACTIONS, "issue_actions": ISSUE_ACTIONS, "controllers": GUIDES}
