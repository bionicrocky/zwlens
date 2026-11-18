"""Generate synthetic sample captures that exercise every troubleshooter.

    python samples/make_samples.py

The data is invented; it exists so the tool can be tried and tested without hardware.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zwlens.mpdu import build_mpdu  # noqa: E402
from zwlens.parsers.zlf import write_zlf  # noqa: E402

HOME = "c0ffee01"
T0 = datetime(2026, 11, 1, 9, 0, 0, tzinfo=timezone.utc).timestamp()


def sniffer_entries():
    """(ts, mpdu, rate, rssi) tuples. Node 1 = controller, 3 = repeater, 5 = dead, 7 = routed dimmer,
    9 = chatty S0 meter, 12 = weak battery sensor, 14 = unencrypted lock."""
    out, t, seq = [], T0, 0

    def tx(src, dst, payload, rate="100k", rssi=-60, dt=0.02, **kw):
        nonlocal t, seq
        t += dt
        if "seq" not in kw:
            seq = (seq + 1) % 16
            kw["seq"] = seq
        out.append((t, build_mpdu(HOME, src, dst, payload, rate=rate, **kw), rate, rssi))
        return kw["seq"]

    def ack(src, dst, s, rate="100k", rssi=-60):
        nonlocal t
        t += 0.006
        out.append((t, build_mpdu(HOME, src, dst, ack=True, seq=s, rate=rate), rate, rssi))

    def exchange(a, b, payload, rate="100k", ra=-55, rb=-62, dt=0.5):
        s = tx(a, b, payload, rate, ra, dt)
        ack(b, a, s, rate, rb)

    for i in range(12):
        # Node 2: healthy switch, direct at 100k.
        exchange(1, 2, bytes([0x25, 0x01, 0xFF if i % 2 else 0x00]), dt=4.0)
        exchange(2, 1, bytes([0x25, 0x03, 0xFF if i % 2 else 0x00]), ra=-62, rb=-55, dt=0.08)

        # Node 9: chatty power meter on S0 (nonce get, nonce report, encrypted report), 5 per round.
        for _ in range(5):
            exchange(9, 1, bytes([0x98, 0x40]), "40k", -70, -55, dt=0.25)
            exchange(1, 9, bytes([0x98, 0x80]) + bytes(8), "40k", -55, -70, dt=0.03)
            exchange(9, 1, bytes([0x98, 0x81]) + bytes(range(20)), "40k", -70, -55, dt=0.03)

        # Node 7: dimmer reached through repeater 3.
        s = tx(1, 7, bytes([0x26, 0x01, 10 * i % 100]), "40k", -55, 1.0, repeaters=[3], hop=0)
        ack(3, 1, s, "40k", -64)
        tx(1, 7, bytes([0x26, 0x01, 10 * i % 100]), "40k", -64, 0.012, repeaters=[3], hop=1, seq=s)
        ack(7, 1, s, "40k", -88)
        tx(7, 1, b"", "40k", -88, 0.015, repeaters=[3], hop=1, inbound=True, routed_ack=True, ack_req=False)
        tx(7, 1, b"", "40k", -64, 0.012, repeaters=[3], hop=0, inbound=True, routed_ack=True, ack_req=False, seq=seq)

        # Node 5: never answers; three attempts each round.
        s = tx(1, 5, bytes([0x20, 0x02]), "40k", -55, 1.5)
        for _ in range(2):
            tx(1, 5, bytes([0x20, 0x02]), "40k", -55, 0.12, seq=s)

        if i % 4 == 0:
            # Node 12: battery sensor waking up with a weak signal, falling back to 9.6k.
            exchange(12, 1, bytes([0x84, 0x07]), "9.6k", -94, -55, dt=2.0)
            exchange(12, 1, bytes([0x80, 0x03, 0x18]), "9.6k", -95, -55, dt=0.2)
            exchange(12, 1, bytes([0x31, 0x05, 0x01, 0x22, 0x00, 0xD7]), "9.6k", -94, -55, dt=0.2)
            exchange(1, 12, bytes([0x84, 0x08]), "9.6k", -55, -94, dt=0.2)

        if i % 3 == 0:
            # Node 14: a lock operated without encryption, and losing S2 sync.
            exchange(1, 14, bytes([0x62, 0x01, 0xFF]), dt=1.0)
            exchange(14, 1, bytes([0x62, 0x03, 0xFF, 0x00, 0x00, 0xFE, 0xFE]), ra=-66, rb=-55, dt=0.3)
            exchange(14, 1, bytes([0x9F, 0x02, i, 0x01]) + bytes(16), ra=-66, rb=-55, dt=0.4)

        # A neighbour's network in radio range.
        t += 0.7
        out.append((t, build_mpdu("deadbeef", 1, 4, bytes([0x25, 0x02]), seq=i % 16, rate="40k"), "40k", -90))
    return out


def sdr_text():
    """A few of the same frames as an SDR decoder might print them."""
    lines = ["# timestamp rssi frame"]
    for ts, mpdu, _rate, rssi in sniffer_entries()[:120]:
        lines.append(f"{ts:.3f} rssi={rssi} {mpdu.hex(' ')}")
    return "\n".join(lines) + "\n"


def zwavejs_log():
    """A Z-Wave JS driver log (debug level) with the same cast of nodes."""
    t = datetime(2026, 11, 1, 9, 0, 0, tzinfo=timezone.utc)
    L, cb = [], 0
    pad = " " * 34

    def stamp():
        return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"

    def step(ms):
        nonlocal t
        t += timedelta(milliseconds=ms)

    def send(node, cc_lines, status="OK", took=25, extra=()):
        nonlocal cb
        cb += 1
        L.append(f"{stamp()} DRIVER » [Node {node:03d}] [REQ] [SendData]")
        L.append(f"{pad}│ transmit options: 0x25")
        L.append(f"{pad}│ callback id:      {cb}")
        L.extend(pad + ln for ln in cc_lines)
        step(8)
        L.append(f"{stamp()} DRIVER « [RES] [SendData]")
        L.append(f"{pad}  was sent: true")
        step(took)
        L.append(f"{stamp()} DRIVER « [REQ] [SendData]")
        L.append(f"{pad}  callback id:            {cb}")
        L.append(f"{pad}  transmit status:        {status}, took {took} ms")
        for ln in extra:
            L.append(f"{pad}  {ln}")

    def recv(node, cc_lines, rssi=None):
        L.append(f"{stamp()} DRIVER « [Node {node:03d}] [REQ] [ApplicationCommand]")
        if rssi is not None:
            L.append(f"{pad}│ RSSI: {rssi} dBm")
        L.extend(pad + ln for ln in cc_lines)

    def note(text):
        L.append(f"{stamp()} CNTRLR   {text}")

    ok = ("routing attempts:       1", "protocol & route speed: Z-Wave, 100 kbit/s",
          "routing scheme:         LWR", "ACK RSSI:               -58 dBm",
          "measured noise floor:   -101 dBm")
    L.append(f"{stamp()} CNTRLR   home ID: 0xc0ffee01")
    L.append(f"{stamp()} CNTRLR   own node ID: 1")
    for i in range(10):
        step(5000)
        L.append(f"{stamp()} DRIVER « [RES] [GetBackgroundRSSI]")
        L.append(f"{pad}  channel 0: -101 dBm")
        L.append(f"{pad}  channel 1: -99 dBm")

        step(500)
        send(2, ["└─[BinarySwitchCCSet]", "    target value: " + ("true" if i % 2 else "false")], extra=ok)
        step(60)
        recv(2, ["└─[BinarySwitchCCReport]", "    current value: " + ("true" if i % 2 else "false")], -58)

        # Node 7 through repeater 3; the route breaks now and then.
        step(900)
        if i % 3 == 2:
            send(7, ["└─[MultilevelSwitchCCSet]", f"    target value: {i * 10}"], took=1320, extra=(
                "repeater node IDs:      3", "routing attempts:       3",
                "protocol & route speed: Z-Wave, 40 kbit/s", "routing scheme:         NLWR",
                "ACK RSSI:               -89 dBm", "route failed here:      3 -> 7"))
        else:
            send(7, ["└─[MultilevelSwitchCCSet]", f"    target value: {i * 10}"], took=140, extra=(
                "repeater node IDs:      3", "routing attempts:       1",
                "protocol & route speed: Z-Wave, 40 kbit/s", "routing scheme:         LWR",
                "ACK RSSI:               -88 dBm"))

        # Node 5 does not answer and is eventually declared dead.
        step(700)
        send(5, ["└─[BasicCCGet]"], status="NoAck", took=1530, extra=(
            "routing attempts:       3", "protocol & route speed: Z-Wave, 40 kbit/s",
            "routing scheme:         Explore"))
        if i == 6:
            step(20)
            note("[Node 005] The node did not respond after 3 attempts, it is presumed dead")

        # Node 9 floods S0-encapsulated meter reports.
        for k in range(8):
            step(350)
            recv(9, ["└─[SecurityCCCommandEncapsulation]", "  │ nonce id: 12",
                     "  └─[MeterCCReport]", "      type: Electric", f"      value: {40 + k + i}"], -71)

        if i % 4 == 1:
            step(400)
            recv(12, ["└─[WakeUpCCWakeUpNotification]"], -93)
            step(5)
            note("[Node 012] The node is now awake.")
            step(200)
            recv(12, ["└─[BatteryCCReport]", "    level: 24"], -94)
            step(900)
            note("[Node 012] The node is now asleep.")
    return "\n".join(L) + "\n"


def main():
    here = Path(__file__).resolve().parent
    (here / "zniffer-sample.zlf").write_bytes(write_zlf(sniffer_entries()))
    (here / "sdr-sample.txt").write_text(sdr_text(), encoding="utf-8")
    (here / "zwavejs-sample.log").write_text(zwavejs_log(), encoding="utf-8")
    print("wrote", ", ".join(p.name for p in sorted(here.glob("*-sample.*"))))


if __name__ == "__main__":
    main()
