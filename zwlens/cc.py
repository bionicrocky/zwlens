"""Command class tables and application payload decoding."""
from __future__ import annotations

import re

# id -> (name, {command id -> command name})
CC = {
    0x00: ("No Operation", {}),
    0x01: ("Z-Wave Protocol", {
        0x01: "Node Info", 0x02: "Request Node Info", 0x03: "Assign IDs",
        0x04: "Find Nodes In Range", 0x05: "Get Nodes In Range", 0x06: "Range Info",
        0x07: "Command Complete", 0x08: "Transfer Presentation", 0x09: "Transfer Node Info",
        0x0A: "Transfer Range Info", 0x0B: "Transfer End", 0x0C: "Assign Return Route",
        0x0D: "New Node Registered", 0x0E: "New Range Registered",
        0x0F: "Transfer New Primary Complete", 0x10: "Automatic Controller Update Start",
        0x11: "SUC Node ID", 0x12: "Set SUC", 0x13: "Set SUC Ack",
        0x14: "Assign SUC Return Route", 0x15: "Static Route Request", 0x16: "Lost",
        0x17: "Accept Lost", 0x18: "NOP Power", 0x19: "Reserve Node IDs",
        0x1A: "Reserved IDs", 0x1F: "Nodes Exist", 0x20: "Nodes Exist Reply",
        0x22: "Set NWI Mode", 0x23: "Exclude Request", 0x24: "Assign Return Route Priority",
        0x25: "Assign SUC Return Route Priority", 0x27: "Smart Start Included Node Info",
        0x28: "Smart Start Prime", 0x29: "Smart Start Inclusion Request",
    }),
    0x20: ("Basic", {1: "Set", 2: "Get", 3: "Report"}),
    0x22: ("Application Status", {1: "Busy", 2: "Rejected Request"}),
    0x25: ("Binary Switch", {1: "Set", 2: "Get", 3: "Report"}),
    0x26: ("Multilevel Switch", {1: "Set", 2: "Get", 3: "Report", 4: "Start Level Change",
                                 5: "Stop Level Change", 6: "Supported Get", 7: "Supported Report"}),
    0x27: ("All Switch", {}),
    0x2B: ("Scene Activation", {1: "Set"}),
    0x2C: ("Scene Actuator Configuration", {1: "Set", 2: "Get", 3: "Report"}),
    0x2D: ("Scene Controller Configuration", {1: "Set", 2: "Get", 3: "Report"}),
    0x30: ("Binary Sensor", {1: "Supported Get", 2: "Get", 3: "Report", 4: "Supported Report"}),
    0x31: ("Multilevel Sensor", {1: "Supported Sensor Get", 2: "Supported Sensor Report",
                                 3: "Supported Scale Get", 4: "Get", 5: "Report",
                                 6: "Supported Scale Report"}),
    0x32: ("Meter", {1: "Get", 2: "Report", 3: "Supported Get", 4: "Supported Report", 5: "Reset"}),
    0x33: ("Color Switch", {1: "Supported Get", 2: "Supported Report", 3: "Get", 4: "Report",
                            5: "Set", 6: "Start Level Change", 7: "Stop Level Change"}),
    0x40: ("Thermostat Mode", {1: "Set", 2: "Get", 3: "Report", 4: "Supported Get", 5: "Supported Report"}),
    0x42: ("Thermostat Operating State", {2: "Get", 3: "Report"}),
    0x43: ("Thermostat Setpoint", {1: "Set", 2: "Get", 3: "Report", 4: "Supported Get", 5: "Supported Report"}),
    0x44: ("Thermostat Fan Mode", {1: "Set", 2: "Get", 3: "Report"}),
    0x45: ("Thermostat Fan State", {2: "Get", 3: "Report"}),
    0x46: ("Climate Control Schedule", {}),
    0x4C: ("Door Lock Logging", {}),
    0x4E: ("Schedule Entry Lock", {}),
    0x55: ("Transport Service", {}),
    0x56: ("CRC16", {1: "Encapsulation"}),
    0x59: ("Association Group Info", {1: "Name Get", 2: "Name Report", 3: "Info Get",
                                      4: "Info Report", 5: "Command List Get", 6: "Command List Report"}),
    0x5A: ("Device Reset Locally", {1: "Notification"}),
    0x5B: ("Central Scene", {1: "Supported Get", 2: "Supported Report", 3: "Notification",
                             4: "Configuration Set", 5: "Configuration Get", 6: "Configuration Report"}),
    0x5E: ("Z-Wave Plus Info", {1: "Get", 2: "Report"}),
    0x60: ("Multi Channel", {7: "End Point Get", 8: "End Point Report", 9: "Capability Get",
                             0x0A: "Capability Report", 0x0B: "End Point Find",
                             0x0C: "End Point Find Report", 0x0D: "Command Encapsulation"}),
    0x62: ("Door Lock", {1: "Operation Set", 2: "Operation Get", 3: "Operation Report",
                         4: "Configuration Set", 5: "Configuration Get", 6: "Configuration Report"}),
    0x63: ("User Code", {1: "Set", 2: "Get", 3: "Report", 4: "Users Number Get", 5: "Users Number Report"}),
    0x66: ("Barrier Operator", {1: "Set", 2: "Get", 3: "Report"}),
    0x6A: ("Window Covering", {}),
    0x6C: ("Supervision", {1: "Get", 2: "Report"}),
    0x70: ("Configuration", {4: "Set", 5: "Get", 6: "Report", 7: "Bulk Set", 8: "Bulk Get", 9: "Bulk Report"}),
    0x71: ("Notification", {4: "Get", 5: "Report", 6: "Set", 7: "Supported Get", 8: "Supported Report"}),
    0x72: ("Manufacturer Specific", {4: "Get", 5: "Report", 6: "Device Specific Get", 7: "Device Specific Report"}),
    0x73: ("Powerlevel", {1: "Set", 2: "Get", 3: "Report", 4: "Test Node Set",
                          5: "Test Node Get", 6: "Test Node Report"}),
    0x75: ("Protection", {1: "Set", 2: "Get", 3: "Report"}),
    0x79: ("Sound Switch", {}),
    0x7A: ("Firmware Update Meta Data", {1: "Meta Data Get", 2: "Meta Data Report", 3: "Request Get",
                                         4: "Request Report", 5: "Get", 6: "Report", 7: "Status Report"}),
    0x80: ("Battery", {2: "Get", 3: "Report"}),
    0x81: ("Clock", {4: "Set", 5: "Get", 6: "Report"}),
    0x84: ("Wake Up", {4: "Interval Set", 5: "Interval Get", 6: "Interval Report", 7: "Notification",
                       8: "No More Information", 9: "Interval Capabilities Get",
                       0x0A: "Interval Capabilities Report"}),
    0x85: ("Association", {1: "Set", 2: "Get", 3: "Report", 4: "Remove",
                           5: "Supported Groupings Get", 6: "Supported Groupings Report"}),
    0x86: ("Version", {0x11: "Get", 0x12: "Report", 0x13: "Command Class Get",
                       0x14: "Command Class Report"}),
    0x87: ("Indicator", {1: "Set", 2: "Get", 3: "Report"}),
    0x8A: ("Time", {1: "Time Get", 2: "Time Report", 3: "Date Get", 4: "Date Report"}),
    0x8E: ("Multi Channel Association", {1: "Set", 2: "Get", 3: "Report", 4: "Remove"}),
    0x8F: ("Multi Command", {1: "Encapsulation"}),
    0x91: ("Manufacturer Proprietary", {}),
    0x98: ("Security", {2: "Commands Supported Get", 3: "Commands Supported Report", 4: "Scheme Get",
                        5: "Scheme Report", 6: "Network Key Set", 7: "Network Key Verify",
                        8: "Scheme Inherit", 0x40: "Nonce Get", 0x80: "Nonce Report",
                        0x81: "Command Encapsulation", 0xC1: "Command Encapsulation + Nonce Get"}),
    0x9C: ("Alarm Sensor", {1: "Get", 2: "Report"}),
    0x9F: ("Security 2", {1: "Nonce Get", 2: "Nonce Report", 3: "Message Encapsulation", 4: "KEX Get",
                          5: "KEX Report", 6: "KEX Set", 7: "KEX Fail", 8: "Public Key Report",
                          9: "Network Key Get", 0x0A: "Network Key Report", 0x0B: "Network Key Verify",
                          0x0C: "Transfer End", 0x0D: "Commands Supported Get",
                          0x0E: "Commands Supported Report"}),
}

# Security plumbing: frames that carry no application meaning on their own.
PLUMBING = {(0x98, 0x40), (0x98, 0x80), (0x9F, 0x01), (0x9F, 0x02)}

# Device-type inference: first match wins.
DEVICE_TYPES = [
    ("Door lock", {0x62, 0x63, 0x4C, 0x4E}),
    ("Garage / barrier", {0x66}),
    ("Thermostat", {0x40, 0x42, 0x43, 0x44, 0x45}),
    ("Window covering", {0x6A}),
    ("Siren", {0x79}),
    ("Energy meter / smart plug", {0x32}),
    ("Dimmer", {0x26}),
    ("Light (color)", {0x33}),
    ("Switch", {0x25}),
    ("Sensor", {0x30, 0x31, 0x71, 0x9C}),
    ("Remote / scene controller", {0x5B, 0x2B}),
]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


NAME_TO_CC = {_norm(name): cid for cid, (name, _) in CC.items()}
NAME_TO_CC.update({"zwaveplus": 0x5E, "zwaveprotocol": 0x01, "security2": 0x9F, "crc16": 0x56,
                   "firmwareupdatemetadata": 0x7A, "switchbinary": 0x25, "switchmultilevel": 0x26,
                   "sensorbinary": 0x30, "sensormultilevel": 0x31, "alarm": 0x71})

ENCAP_TAGS = {0x98: "S0", 0x9F: "S2", 0x56: "CRC16", 0x60: "MultiChannel", 0x6C: "Supervision",
              0x8F: "MultiCommand", 0x55: "TransportService"}


def cc_name(cid) -> str:
    if cid is None:
        return ""
    return CC[cid][0] if cid in CC else f"CC 0x{cid:02X}"


def cmd_name(cid, cmd) -> str:
    if cid is None or cmd is None:
        return ""
    name = CC.get(cid, ("", {}))[1].get(cmd)
    return name if name else f"cmd 0x{cmd:02X}"


def split_camel(s: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)


def lookup_log_cc(name: str):
    """Map a Z-Wave JS class-name fragment such as 'BinarySwitch' to (id, display name)."""
    cid = NAME_TO_CC.get(_norm(name))
    return cid, (CC[cid][0] if cid is not None else split_camel(name))


def _level(v: int) -> str:
    if v == 0:
        return "off"
    if v == 0xFF:
        return "on"
    if v == 0xFE:
        return "unknown"
    return str(v)


def _describe(cid: int, cmd: int, p: bytes) -> str:
    """Short human summary of the values in a few very common commands."""
    try:
        if cid in (0x20, 0x25) and cmd in (1, 3) and len(p) > 2:
            return f"value: {_level(p[2])}"
        if cid == 0x26 and cmd in (1, 3) and len(p) > 2:
            return f"level: {_level(p[2])}"
        if cid == 0x30 and cmd == 3 and len(p) > 2:
            return "state: " + ("triggered" if p[2] else "idle")
        if cid == 0x80 and cmd == 3 and len(p) > 2:
            return "battery: " + ("LOW warning" if p[2] == 0xFF else f"{p[2]}%")
        if cid == 0x84 and cmd in (4, 6) and len(p) > 4:
            return f"interval: {int.from_bytes(p[2:5], 'big')} s"
        if cid == 0x71 and cmd == 5 and len(p) > 7:
            return f"type {p[6]}, event {p[7]}"
        if cid == 0x31 and cmd == 5 and len(p) > 2:
            return f"sensor type {p[2]}"
        if cid == 0x70 and cmd in (4, 5, 6) and len(p) > 2:
            return f"parameter {p[2]}"
        if cid == 0x5B and cmd == 3 and len(p) > 4:
            return f"scene {p[4]}"
        if cid == 0x9F and cmd == 2 and len(p) > 3:
            flags = [n for bit, n in ((1, "SOS: receiver lost sync"), (2, "MOS")) if p[3] & bit]
            return ", ".join(flags)
        if cid == 0x6C and cmd == 2 and len(p) > 3:
            return {0: "no support", 1: "working", 2: "fail", 0xFF: "success"}.get(p[3], f"status {p[3]}")
    except IndexError:
        pass
    return ""


def decode_payload(p: bytes) -> dict:
    """Decode an application payload, unwrapping transparent encapsulations."""
    out = {"cc": None, "cmd": None, "cc_name": "", "cmd_name": "", "encap": [],
           "encrypted": False, "summary": "", "event": None}
    encap = []
    for _ in range(4):  # bounded unwrap depth
        if not p:
            break
        cid = p[0]
        cmd = p[1] if len(p) > 1 else None
        if cid == 0x56 and cmd == 1 and len(p) > 5:
            encap.append("CRC16")
            p = p[2:-2]
            continue
        if cid == 0x60 and cmd == 0x0D and len(p) > 5:
            encap.append(f"MultiChannel ep{p[2] & 0x7F}>{p[3] & 0x7F}")
            p = p[4:]
            continue
        if cid == 0x6C and cmd == 1 and len(p) > 5:
            encap.append("Supervision")
            p = p[4:4 + p[3]]
            continue
        break
    if not p:
        out["encap"] = encap
        return out
    cid = p[0]
    if cid == 0x00:
        out.update(cc=0, cc_name="No Operation", cmd_name="(ping)", encap=encap)
        return out
    cmd = p[1] if len(p) > 1 else None
    out.update(cc=cid, cmd=cmd, cc_name=cc_name(cid), cmd_name=cmd_name(cid, cmd))
    if cid == 0x98:
        encap.append("S0")
        out["encrypted"] = cmd in (0x81, 0xC1)
    elif cid == 0x9F:
        encap.append("S2")
        out["encrypted"] = cmd == 0x03
        if cmd == 0x02 and len(p) > 3 and p[3] & 1:
            out["event"] = "s2_sos"
    elif cid == 0x8F:
        encap.append("MultiCommand")
    elif cid == 0x55:
        encap.append("TransportService")
        out["cmd_name"] = "segment"
    out["encap"] = encap
    out["summary"] = _describe(cid, cmd, p) if cmd is not None else ""
    return out
