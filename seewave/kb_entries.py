"""Catalogue of known Z-Wave failure modes.

Compiled from the Z-Wave JS troubleshooting docs and driver source (log strings are quoted from
there), Silicon Labs documentation, and Home Assistant / Hubitat / openHAB / vendor forums.
`log` holds regular expressions matched against Z-Wave JS log entries. Entries whose id has a
traffic detector in knowledge.py are also checked against decoded frames.
"""

SRC = {
    "zjs-common": "https://github.com/zwave-js/zwave-js/blob/master/docs/troubleshooting/common-issues.md",
    "zjs-first": "https://github.com/zwave-js/zwave-js/blob/master/docs/troubleshooting/first-steps.md",
    "zjs-noupd": "https://github.com/zwave-js/zwave-js/blob/master/docs/troubleshooting/no-updates.md",
    "zjs-nonsense": "https://github.com/zwave-js/zwave-js/blob/master/docs/troubleshooting/nonsensical-values.md",
    "zjs-zniffer": "https://github.com/zwave-js/zwave-js/blob/master/docs/troubleshooting/zniffer.md",
    "zjs-lr": "https://github.com/zwave-js/zwave-js/blob/master/docs/getting-started/long-range.md",
    "zjs-s2": "https://github.com/zwave-js/zwave-js/blob/master/docs/getting-started/security-s2.md",
    "zjs-opts": "https://github.com/zwave-js/zwave-js/blob/master/docs/api/driver.md",
    "zjs-src": "https://github.com/zwave-js/zwave-js",
    "gh-3906": "https://github.com/zwave-js/zwave-js/issues/3906",
    "gh-6260": "https://github.com/zwave-js/zwave-js/issues/6260",
    "gh-6295": "https://github.com/zwave-js/node-zwave-js/discussions/6295",
    "gh-6512": "https://github.com/zwave-js/node-zwave-js/discussions/6512",
    "gh-6161": "https://github.com/zwave-js/node-zwave-js/discussions/6161",
    "gh-4352": "https://github.com/zwave-js/zwave-js/issues/4352",
    "gh-9086": "https://github.com/zwave-js/zwave-js/pull/9086",
    "gh-5471": "https://github.com/zwave-js/node-zwave-js/issues/5471",
    "kpine": "https://github.com/kpine/zwave-js-server-docker/wiki/700-series-Controller-Firmware-Updates-(Linux)",
    "ha-zwjs": "https://www.home-assistant.io/integrations/zwave_js/",
    "ha-jammed": "https://community.home-assistant.io/t/how-to-troubleshoot-controller-errors-jammed/641338",
    "ha-solved": "https://community.home-assistant.io/t/how-i-solved-my-z-wave-problems-no-dead-nodes-anymore/604462",
    "ha-ghost": "https://community.home-assistant.io/t/how-to-remove-dead-fake-nodes/740198",
    "ha-nvm": "https://community.home-assistant.io/t/zwave-js-nvm-backup-restore-zwave-500-700/354991",
    "sl-sleep": "https://docs.silabs.com/z-wave/1.0.0/z-wave-training-docs/gateway-session4-sleeping-nodes",
    "sl-batt": "https://docs.silabs.com/z-wave/8.0.0/z-wave-battery-support-basics/",
    "sl-net": "https://docs.silabs.com/z-wave/8.0.0/z-wave-networking-basics/",
    "sl-assoc": "https://docs.silabs.com/z-wave/8.0.0/z-wave-association-basics/",
    "sl-perf": "https://docs.silabs.com/z-wave/7.24.3/z-wave-performance-report/network-latency",
    "oh-routing": "https://community.openhab.org/t/z-wave-routing-basics/92408",
    "oh-retry": "https://community.openhab.org/t/z-wave-routing-basics-retry-strategies/92431",
    "oh-heal": "https://community.openhab.org/t/z-wave-routing-basics-application-binding-retries-heal-and-explorer/92551",
    "hub-ghost": "https://community.hubitat.com/t/how-to-remove-ghost-devices-using-hub-tools-or-a-uzb-stick/73914",
    "vest-108": "https://www.vesternet.com/knowledgebase/technical/kb-108",
    "s0nomore": "https://arxiv.org/abs/2205.00781",
}

ENTRIES: list = []


def E(eid, title, category, what, causes, fixes, src=(), log=(), severity="warn"):
    ENTRIES.append({"id": eid, "title": title, "category": category, "what": what, "causes": list(causes),
                    "fixes": list(fixes), "sources": [SRC.get(s, s) for s in src], "log": list(log),
                    "severity": severity})


# ---------------------------------------------------------------- radio
E("usb3-port-interference", "USB 3 noise at the controller", "rf",
  "The stick sits in or next to a USB 3 port, drive or hub, which deafens its receiver. Commands fail at random "
  "across unrelated nodes, nearby nodes go missing from the neighbour list, and inclusion fails or ends up insecure.",
  ["Controller plugged straight into a computer, especially a USB 3 port", "Stick at the back of a rack or on metal"],
  ["Put the controller on a USB extension cable, away from other USB ports and drives, in a central spot off metal.",
   "Rebuild routes afterwards so nodes use the better link.",
   "Expect a quiet noise floor of about -90 dBm (500 series), -100 dBm (700) or -110 dBm (800)."],
  ["zjs-first", "ha-zwjs"])
E("elevated-noise-floor", "External RF noise source", "rf",
  "An appliance, drive or power adapter raises the noise floor, making links flaky across the network or in one area.",
  ["Switch-mode power supplies, LED drivers, USB drives, other sub-GHz radios"],
  ["Find and move or remove the noise source; move the controller; add repeaters.",
   "Aim for a signal at least 17 dB above the noise floor (the margin Z-Wave JS's health check wants)."],
  ["zjs-first"])
E("marginal-link-low-power-margin", "Link only works at full power", "rf",
  "A node sits at the edge of range, so its link quality drifts: sporadic failures and route changes.",
  ["Distance, walls, metal enclosures", "No repeater in between"],
  ["Run the Z-Wave JS health check: a good link has 0 failed pings, under 100 ms latency, more than 2 neighbours, "
   "works at -6 dBm or lower power, and has 17 dB of margin.",
   "Move the device, remove noise, add a repeater, or assign a priority route."],
  ["zjs-first", "zjs-src"])
E("asymmetric-link-lost-acks", "One direction works, acknowledgements get lost", "rf",
  "Noise near one end swallows ACKs. The device carries out commands but the controller reports failure, or "
  "reports arrive twice a moment apart.",
  ["Noise close to the controller (lost ACKs from nodes) or close to the node (lost ACKs from the controller)"],
  ["Compare the health check's failed pings in each direction to find the noisy end, then treat it as interference."],
  ["zjs-first"])
E("low-speed-xor-checksum-corruption", "Corrupted frames accepted at low speed", "rf",
  "Frames at 9.6 and 40 kbit/s carry only an 8-bit checksum, so bit errors can pass as valid. You see nonsense "
  "values, reports credited to the wrong node, phantom capabilities, or a spurious 'device reset' notification.",
  ["Noise or weak links on nodes talking below 100 kbit/s", "Chatty unencrypted reporting"],
  ["Fix the noise or connectivity first and reduce reporting.",
   "Include the device with S2 (or S0 as a last resort), or enable CRC-16 encapsulation on it, so corrupt frames are rejected."],
  ["zjs-nonsense", "gh-6295"])
E("crc-errors-collisions", "Checksum errors and collisions on air", "rf",
  "Frames collide or arrive damaged: typically nodes that cannot hear each other transmitting together, or bursts of reports.",
  ["Hidden nodes, report bursts, interference", "A sniffer set to the wrong region shows the same symptom"],
  ["Cut traffic from chatty nodes and check the controller firmware.",
   "If nearly every frame is bad, check the sniffer's region and frequency setting first."],
  ["gh-6161", "zjs-first"])
E("receiver-saturation-too-close", "Receiver saturated by a node that is too close", "rf",
  "A node centimetres from the controller or sniffer overdrives the receiver.",
  ["Devices paired or tested right next to the stick"],
  ["Separate the devices by at least a metre."],
  ["zjs-src"], log=[r"receiver saturated"], severity="info")
E("foreign-network-co-channel", "Neighbouring Z-Wave network on the same channel", "rf",
  "Another home's network shares your airtime. Its traffic raises collisions and delays on yours.",
  ["Apartments and close neighbours", "A second test network of your own"],
  ["Reduce your own traffic, move the controller, and add repeaters to raise signal margin."],
  ["zjs-zniffer"])
E("channel-busy-tx-fail", "Controller cannot get the channel", "rf",
  "The radio never transmits because the channel is busy. Commands hang and Z-Wave JS reports the controller as jammed.",
  ["A burst of traffic or strong interference at that moment", "Persistent jamming until reset points at the firmware bug instead"],
  ["Check the noise floor and traffic level at the time of the failure.",
   "The driver retries 5 times at 1 s intervals; if it never recovers, see the 700/800 lock-up entry."],
  ["zjs-src", "gh-6295", "gh-6512"], log=[r"transmit status:\s*Fail"])
E("eu-duty-cycle-limit", "EU duty-cycle limit", "rf",
  "EU 868 MHz bands carry a 1% duty-cycle rule (36 s of transmission per hour). A very chatty node could run into it.",
  ["Extremely frequent reporting or polling"],
  ["Reduce reporting. How firmware enforces the limit is not documented, so treat this as a rule of thumb."],
  [], severity="info")

# ---------------------------------------------------------------- routing
E("ghost-failed-node", "Ghost node left in the controller", "routing",
  "A failed inclusion, or a device reset or removed without exclusion, leaves a node ID behind. It shows as a nameless "
  "node stuck early in its interview, can slow the mesh, and other nodes may still try to route through it.",
  ["Failed or interrupted inclusion", "Device factory-reset or discarded without excluding it"],
  ["Power off the original device if it still exists, ping the node so it is marked failed, then use Remove Failed Node.",
   "Expect several attempts. If the controller refuses, use Silicon Labs PC Controller, then rebuild routes."],
  ["hub-ghost", "ha-ghost", "zjs-src"],
  log=[r"is not in the list of failed nodes", r"Interview attempt \(\d+/\d+\) failed, node is dead"])
E("route-through-dead-repeater", "Route goes through a dead repeater", "routing",
  "A stored route contains a repeater that is unplugged or broken. Commands stall for seconds, then succeed another "
  "way; or the device can be controlled but its reports are lost.",
  ["A repeater was unplugged, moved or failed", "Stale priority or return routes"],
  ["Restore or replace the repeater, rebuild routes for the affected nodes, and delete stale priority routes.",
   "After 3 failed transmissions a sender treats a link as down and tries its next route."],
  ["sl-net", "oh-retry", "zjs-src"], log=[r"route failed here"])
E("bad-priority-route", "Stuck priority route", "routing",
  "A manually assigned priority route is always tried first, even after it fails. If it is bad, every command pays the delay.",
  ["A priority route through a repeater that moved or died", "Manual routes on battery nodes"],
  ["Remove or correct the priority route."],
  ["zjs-first", "oh-retry", "ha-solved"], log=[r"Skipping route rebuild because the node has priority return routes"],
  severity="info")
E("missing-or-stale-return-routes", "Controllable but no status updates", "routing",
  "The device has no working route back to the controller. Commands work, but its own reports are missing or very late.",
  ["Controller or repeaters were moved", "Stick migration", "Route assignment failed during inclusion"],
  ["Rebuild routes for that node (wake battery devices first), or assign priority return routes.",
   "Check that the lifeline association points at the controller."],
  ["oh-retry", "oh-routing", "zjs-noupd"],
  log=[r"Assigning return routes failed", r"failed to assign return route to node", r"Deleting return routes failed"])
E("suc-return-route-missing", "SUC return route missing", "routing",
  "The route to the network's update controller was not assigned or is stale, so the node cannot reach it for "
  "unsolicited traffic.",
  ["Failed route assignment", "Migration"],
  ["Rebuild routes for the node."],
  ["zjs-src"], log=[r"Assigning (custom )?SUC return route.*failed", r"Deleting SUC return route failed"])
E("rebuild-routes-failure", "Route rebuild fails or makes things worse", "routing",
  "Neighbour discovery fails on a busy or weak network, so a heal leaves nodes with worse routes than before.",
  ["Healing the whole network at once", "RF problems not fixed first", "700-series firmware older than 7.17.2"],
  ["Rebuild one node at a time, at a quiet time, after fixing radio problems.",
   "Prefer priority routes over repeated heals for stubborn nodes."],
  ["zjs-src", "gh-3906", "zjs-first", "oh-heal"],
  log=[r"refreshing neighbor list failed", r"rebuilding routes failed", r"Cannot rebuild routes because the node is not responding"])
E("wrong-or-empty-neighbor-list", "Wrong or empty neighbour list", "routing",
  "The controller lists few or no neighbours, or leaves out nearby nodes, and so routes through repeaters it does not need.",
  ["USB interference at the controller", "Devices moved without a rebuild", "Old 700-series firmware"],
  ["Fix controller placement, update firmware, then rebuild routes or set a direct priority route."],
  ["zjs-first", "gh-3906"], log=[r"requesting the node neighbors failed"])
E("too-few-neighbors-no-redundancy", "Too few neighbours, no redundancy", "routing",
  "A node has two or fewer routing neighbours, so one repeater failing isolates it.",
  ["Sparse mesh", "Mostly battery devices, which never repeat"],
  ["Add mains-powered repeaters so each node has at least two, preferably four, good neighbours."],
  ["zjs-src", "oh-heal", "oh-routing"], severity="info")
E("hop-limit-exhausted", "Hop limit reached", "routing",
  "The destination needs more than four repeaters, the protocol maximum, and cannot be reached however good the links are.",
  ["Controller at one end of a long building", "Too few repeaters with long reach"],
  ["Move the controller to the middle, use Z-Wave Long Range, or split into two networks."],
  ["zjs-src", "ha-solved"], log=[r"transmit status:\s*NoRoute"])
E("route-resolution-escalation", "Every command falls back to route search", "routing",
  "There is no stable route, so each command walks the whole retry ladder and ends in an explorer search. Latency of 1 to 5 seconds.",
  ["One weak hop on the usual path", "Frequent route changes"],
  ["Improve the weak hop, add a repeater, or pin a priority route. The target is zero route changes."],
  ["oh-retry", "sl-net", "zjs-first"], log=[r"routing scheme:\s*(Explore|ResortDirect)"])

# ---------------------------------------------------------------- controller
E("zw700-800-jammed-lockup", "700/800 controller firmware lock-up (jammed)", "controller",
  "A known Silicon Labs bug: the controller can lock up, stop acknowledging and stop transmitting. Latency grows, "
  "healthy nodes are marked dead, and nodes flood retransmitted reports. Often triggered by a burst of meter reports.",
  ["Controller SDK older than 7.17.2, or 7.20 to 7.21.3", "Bursts of incoming reports"],
  ["Update the controller firmware: 700 series prefer SDK 7.17.2 to 7.18.x (or 7.21.8+), 800 series prefer 7.22.x. "
   "Avoid versions below 7.17.2 and 7.20 to 7.21.3.",
   "Reduce power-meter and sensor reporting.",
   "Keep Z-Wave JS current: version 12.10.1 and later reset the controller automatically when this happens."],
  ["zjs-common", "gh-6512", "gh-6295", "kpine"],
  log=[r"the controller is jammed", r"Attempting to recover jammed controller", r"Cannot recover jammed controller"],
  severity="crit")
E("zw700-800-unresponsive-missed-callback", "Controller hangs mid-transmission", "controller",
  "The controller never reports the result of a send, and after that all sends fail until it is restarted.",
  ["Controller firmware 7.19.x to 7.21.x", "Chatty nodes", "Unstable serial path"],
  ["Update or change controller firmware as for the jammed lock-up.",
   "Leave automatic controller recovery enabled and use the /dev/serial/by-id/ path."],
  ["gh-6260", "gh-6295", "ha-jammed", "zjs-opts"],
  log=[r"Timeout while waiting for a callback from the controller", r"Controller missed Send Data callback",
       r"The controller is unresponsive", r"Attempting to recover unresponsive controller",
       r"Automatic controller recovery failed", r"causing the controller to become unresponsive"],
  severity="crit")
E("zw700-pre-7.17.2-flood-bug", "700-series firmware before 7.17.2", "controller",
  "Old 700-series firmware blocks under bursts of reports and may not acknowledge them, so nodes repeat themselves: "
  "delays of up to a minute, failed sends and failed heals.",
  ["Controller SDK below 7.17.2", "Large or busy networks"],
  ["Update the controller to 7.17.2 or later, avoiding 7.20 to 7.21.3."],
  ["gh-3906", "kpine"])
E("zw500-lockup-on-dead-node", "500-series stick stalls on dead nodes", "controller",
  "Aeotec Z-Stick Gen5/Gen5+ firmware 1.0 and 1.1 can delay or lock up when sending to a dead node.",
  ["Dead nodes still in the network", "Old stick firmware"],
  ["Remove dead nodes; update the stick to firmware 1.2 where possible."],
  ["zjs-common", "zjs-opts"])
E("serial-ack-timeout", "Controller not answering on the serial port", "controller",
  "The software cannot talk to the stick at all.",
  ["Wrong serial path", "Locked-up or bricked controller", "Faulty USB passthrough in a virtual machine"],
  ["Check the serial path (prefer /dev/serial/by-id/), power-cycle the stick, fix passthrough."],
  ["zjs-common", "zjs-src"],
  log=[r"Timeout while waiting for an ACK from the controller", r"no response from the controller",
       r"Serial API did not respond"], severity="crit")
E("serial-can-nak", "Serial collisions and rejected frames", "controller",
  "The host and controller talk over each other (CAN) or the controller rejects a frame (NAK). A fraction of a "
  "percent is normal; a high rate means the controller is being flooded with incoming traffic.",
  ["Floods of incoming reports", "Heavy polling"],
  ["Reduce traffic from chatty nodes and automations."],
  ["oh-retry", "zjs-src"], log=[r"Failed to execute controller command"], severity="info")
E("serial-port-dropout-or-unexpected-restart", "Serial port drops or controller restarts", "controller",
  "The stick disconnects, re-enumerates or resets by itself.",
  ["USB power glitches or a failing stick", "tty path changing after a soft reset (Docker)", "Brown-out or watchdog reset"],
  ["Use the by-id serial path and a powered hub; disable soft reset only for 500-series sticks that need it."],
  ["zjs-opts", "zjs-src"],
  log=[r"Serial port closed unexpectedly", r"Serial API restarted unexpectedly",
       r"Serial API did not respond after soft-reset"])
E("tx-queue-full-or-response-nok", "Controller refuses commands (queue full)", "controller",
  "The controller rejects a send because its queue is full or it is busy.",
  ["Automations or polling sending faster than the radio can transmit", "A controller lock-up"],
  ["Throttle automations and polling; check for the controller lock-up entries."],
  ["zjs-src"],
  log=[r"Transmission queue full", r"The controller response indicated failure", r"The controller callback indicated failure"])
E("controller-stuck-beaming", "Controller stuck sending wake-up beams", "controller",
  "A firmware fault leaves the controller beaming constantly, blocking the channel for everything else.",
  ["Controller firmware bug (incorrect stored configuration)"],
  ["Update the controller firmware and soft-reset it."],
  ["gh-6512", "gh-6161"])
E("nvm-migration-problems", "Problems after controller migration or restore", "controller",
  "After moving the network to a new stick, nodes are dead, routes are stale, or security data is wrong.",
  ["Routes copied from the old stick's position", "Source stick firmware too old to convert", "Keys not carried over"],
  ["Back up first and keep the same network keys.",
   "Rebuild routes and re-interview after the move; empty routes for a few days are normal."],
  ["ha-zwjs", "gh-3906", "gh-4352", "ha-nvm"],
  log=[r"Failed to convert NVM", r"Failed to restore NVM backup", r"Cannot restore the NVM"])
E("suc-sis-role-misconfig", "Controller has the wrong role", "controller",
  "The controller is not the network's primary/SIS, so it cannot include or remove devices, or nodes report to a "
  "different controller.",
  ["Restore onto a stick that was classed as secondary", "An old secondary controller still in the network"],
  ["Let Z-Wave JS promote the controller to SUC/SIS, and remove stale secondary controllers."],
  ["zjs-src"], log=[r"This controller is not the primary controller", r"SUC node ID \d+ is not part of the network",
                    r"Promotion to SUC/SIS failed"])
E("controller-in-bootloader-or-bricked", "Controller stuck in bootloader", "controller",
  "A firmware update left the stick in its bootloader; the radio is silent.",
  ["Interrupted or invalid firmware update", "Skipping required intermediate versions (go via 7.18.8 before 7.21)"],
  ["Flash a valid firmware image. Downgrades are generally blocked."],
  ["zjs-src", "kpine", "zjs-common"],
  log=[r"Controller is in bootloader", r"Failed to recover from bootloader", r"OTW update failed", r"OTW update was aborted"],
  severity="crit")
E("node-id-capacity-and-invalid-ids", "Node table full or invalid node IDs", "controller",
  "Classic Z-Wave allows 232 nodes, and ghost nodes use up IDs. A host/controller mismatch can also produce IDs above 232.",
  ["Many ghost nodes", "Old driver versions with a node-ID width mismatch"],
  ["Remove ghost nodes; update Z-Wave JS. Long Range nodes legitimately start at ID 256."],
  ["zjs-src", "gh-6295", "zjs-lr"], severity="info")

# ---------------------------------------------------------------- battery and sleep
E("sleeping-node-treated-as-unreachable", "Commands waiting for a sleeping device", "power-sleep",
  "A command sent to a battery device waits until its next wake-up. Settings 'do not apply' and the device looks dead.",
  ["Automations or polling aimed at battery devices", "Long wake-up interval"],
  ["Wake the device manually to deliver queued commands; do not poll or ping battery devices.",
   "A device that sends reports is not necessarily awake to receive."],
  ["zjs-common", "zjs-src", "gh-9086"],
  log=[r"It is probably asleep, moving its messages to the wakeup queue"], severity="info")
E("wakeup-interval-misconfig", "Wake-up interval too short or too long", "power-sleep",
  "Too short drains the battery; too long delays queued commands. An interval of 0 means the device only wakes on events.",
  ["Hub defaults overriding the device's own", "Leftover test settings"],
  ["Choose the longest interval you can live with (hours, not minutes) unless you often change settings."],
  ["sl-sleep", "sl-batt", "vest-108"])
E("missing-wake-up-no-more-information", "Device kept awake after waking", "power-sleep",
  "The controller never tells a woken device it can go back to sleep, so it stays awake until its own timeout "
  "(about 10 s after the last frame) and drains its battery.",
  ["Controller busy or jammed", "Long queued interviews", "Bad route to the node so the message is lost"],
  ["Fix the route to the device; make sure the controller software is not overloaded."],
  ["sl-sleep", "zjs-opts"], severity="info")
E("sleeping-node-stopped-waking", "Battery device has stopped waking up", "power-sleep",
  "The battery died, but the device still shows as 'asleep' indefinitely.",
  ["Flat battery", "Device moved out of range"],
  ["Treat a device as failed when more than twice its wake-up interval (plus 10%) passes without a wake-up notification.",
   "Replace the battery and wake it manually."],
  ["sl-sleep", "gh-9086"])
E("wakeup-destination-wrong", "Wake-up notifications go to the wrong controller", "power-sleep",
  "The device was told to send wake-up notifications to another node (an old hub or secondary controller), so this "
  "controller never learns it is awake and its queue never drains.",
  ["Device previously set up on another hub", "Secondary controller in the network"],
  ["Re-interview the device while it is awake so the wake-up destination is set to this controller."],
  ["sl-sleep"])
E("flirs-beam-failure", "Wake-up beam fails to wake a lock or siren", "power-sleep",
  "Locks, sirens and some thermostats sleep and must be woken by a beam. If the beam does not get through, commands "
  "take seconds or fail.",
  ["Weak link to the device", "A repeater on the route that cannot beam", "Too many beams congesting the channel"],
  ["Give the device a direct or strong route and put a beam-capable mains repeater near it.",
   "Do not poll beam-woken devices: every beam interrupts other traffic for up to a second."],
  ["sl-sleep", "sl-batt", "sl-perf"])
E("battery-drain-from-reporting-or-retries", "Battery drains in days or weeks", "power-sleep",
  "Too-frequent reports, tiny thresholds or a weak link (every report retried) empty a battery that should last one to three years.",
  ["Reporting thresholds set too low", "Weak link causing retries and route searches", "Very short wake-up interval"],
  ["Raise thresholds and intervals, lengthen the wake-up interval, add a repeater nearby."],
  ["vest-108", "zjs-first"])
E("battery-node-first-interview-slow", "Battery device interview takes hours", "power-sleep",
  "The interview only progresses while the device is awake, so a battery device can take hours to finish setting up.",
  ["Normal behaviour for sleeping devices"],
  ["Wake the device manually, several times if needed, or keep it awake during setup."],
  ["zjs-common", "ha-zwjs"], log=[r"the node is probably asleep\. Retrying after wakeup"], severity="info")

# ---------------------------------------------------------------- security
E("s2-bootstrap-failure", "S2 secure inclusion failed", "security",
  "The key exchange failed or timed out, so the device ended up unencrypted or at a lower security class.",
  ["Weak link during inclusion (the usual cause of timeouts)", "PIN entered late or wrongly", "Device needs a factory reset"],
  ["Exclude, factory-reset and re-include the device close to the controller, entering the PIN promptly "
   "(protocol steps time out after 10 s, user prompts after 240 s)."],
  ["zjs-src", "zjs-s2", "zjs-common"],
  log=[r"Security S2 bootstrapping failed", r"canceled the Security S2 bootstrapping", r"has failed S2 bootstrapping"],
  severity="crit")
E("s0-downgrade-or-unintended-security-class", "Device on S0 or no security when it should use S2", "security",
  "An S2-capable device ended up on S0 or unencrypted.",
  ["Inclusion timed out and fell back", "Device firmware claims S2 but does not complete it"],
  ["Exclude and re-include with the right strategy; force S0 only for S0-only locks."],
  ["zjs-src", "zjs-s2"],
  log=[r"Possible S0 downgrade attack detected", r"Security S0 bootstrapping failed", r"continuing without encryption"])
E("missing-or-wrong-network-keys", "Network keys missing or wrong", "security",
  "The software has no key, or the wrong one, for secure devices. They cannot be controlled and their values are missing.",
  ["Reinstall or migration without restoring the keys"],
  ["Configure the original keys (one for S0, three for S2, two more for Long Range). Otherwise exclude and re-include."],
  ["zjs-common", "zjs-src"],
  log=[r"No network key for S[02] configured", r"network keys are not set",
       r"security classes were granted but have no key configured"], severity="crit")
E("s0-nonce-timeout", "S0 nonce exchange times out", "security",
  "The S0 handshake fails because a nonce report is lost or arrives after the nonce expired (5 s by default).",
  ["Weak or congested link", "S0 on a chatty sensor: three frames per report"],
  ["Improve the link; move sensors and meters off S0."],
  ["zjs-src", "zjs-opts", "zjs-first", "gh-5471"],
  log=[r"No nonce received from the node", r"failed to send nonce"])
E("s0-nonce-get-dos", "S0 nonce requests flooding the controller", "security",
  "A faulty node, or an attacker, keeps requesting S0 nonces and never uses them, exhausting the controller's nonce table.",
  ["Buggy device firmware", "Deliberate denial of service (published as 'S0-No-More')"],
  ["Identify the node sending the requests and exclude or replace it."],
  ["s0nomore", "zjs-src"], log=[r"Cannot generate a new nonce"])
E("s2-mpan-multicast-desync", "S2 group command reaches some devices late", "security",
  "A member of an S2 multicast group lacks the current group key state and needs a follow-up message, so a group "
  "command hits devices one after another (the 'popcorn' effect).",
  ["A group member missed earlier multicasts"],
  ["Usually self-healing after the next single message; improve the link to the slow member."],
  ["zjs-src"], log=[r"MPAN is not known yet", r"did not respond to the multicast request"], severity="info")
E("s2-collision-and-lower-security-discard", "S2 collisions or reports dropped for low security", "security",
  "Either both sides start a secure exchange at once (costing extra round trips), or a device sends a command at a "
  "lower security level than it was granted and the controller discards it, so reports go missing.",
  ["Simultaneous traffic in both directions", "Device firmware reporting unencrypted or with S0 after S2 inclusion"],
  ["Re-interview the device; check the security of its associations and its firmware."],
  ["zjs-src"],
  log=[r"S2 collision detected", r"received at a lower security level than expected",
       r"failed to decode the message after re-transmission"])

# ---------------------------------------------------------------- inclusion and interview
E("inclusion-no-device-found", "Inclusion finds no device", "inclusion-interview",
  "The controller never hears the device that is trying to join.",
  ["Device still included in another network", "Region mismatch", "Out of range: some devices lower their power for inclusion",
   "Device not actually in inclusion mode"],
  ["Exclude the device first (any controller can do it), move it close, check the region, then retry."],
  ["zjs-common"], severity="info")
E("inclusion-fails-at-controller", "Inclusion or exclusion fails", "inclusion-interview",
  "The controller starts adding or removing the device but the process fails.",
  ["Weak link", "Device or controller in an odd state"],
  ["Power-cycle the device, exclude and retry; soft-reset then power-cycle the controller."],
  ["zjs-common", "zjs-src"], log=[r"ZW0207", r"ZW0208", r"inclusion failed", r"exclusion failed"])
E("interview-stuck-early-stage", "Interview stuck at ProtocolInfo or NodeInfo", "inclusion-interview",
  "The device never answers the request for its node information, so setup stops at the first stages.",
  ["Ghost node", "Sleeping device", "Out of range", "Device needs a factory reset"],
  ["Wake the device and re-interview it nearby. If nothing ever answers from that node ID, remove it as a ghost."],
  ["zjs-src", "zjs-common"],
  log=[r"Querying the node info failed", r"Interview attempt \d+/\d+ failed"])
E("interview-incomplete-commandclasses", "Interview incomplete: missing values or 'unknown device'", "inclusion-interview",
  "Queries time out part-way through setup, leaving missing entities, an unknown manufacturer or an undetermined security class.",
  ["Weak link: the device answers but the reply or its ACK is lost"],
  ["Improve the link and re-interview; if it still fails, exclude, factory-reset and re-include."],
  ["zjs-common", "zjs-opts"], log=[r"Timed out while waiting for a response from the node"])
E("smartstart-inclusion-failure", "SmartStart inclusion fails", "inclusion-interview",
  "A device keeps announcing itself for SmartStart but the controller never includes it.",
  ["QR code/DSK not in the provisioning list or mistyped", "Provisioning entry inactive", "Missing key for the granted class", "Out of range"],
  ["Check the provisioning entry and its DSK, make sure it is active, and bring the device closer."],
  ["zjs-src"],
  log=[r"NWI Home ID not found in provisioning list", r"provisioning entry for this node is inactive",
       r"SmartStart inclusion failed", r"Smart Start inclusion could not be started"])
E("node-included-twice-or-by-other-controller", "Device included twice", "inclusion-interview",
  "The device was re-included without being excluded, leaving its old node ID behind as a ghost next to the new one.",
  ["Re-pairing without excluding first", "A secondary controller adding nodes"],
  ["Remove the old, failed node ID (see ghost node)."],
  ["zjs-src", "hub-ghost"],
  log=[r"included by another controller, but it is already part of the network", r"Ignoring proxy inclusion request"])
E("secure-device-communicating-insecurely", "Secure device talking without encryption", "security",
  "A lock or other secure device was included without encryption, or its security level could not be determined.",
  ["Wrong or missing keys", "Included without security", "Device did not answer when its security level was probed"],
  ["Re-interview the device; if it is still insecure, exclude and re-include it securely."],
  ["zjs-common"], log=[r"ZW0214", r"ZW1403"], severity="crit")

# ---------------------------------------------------------------- device behaviour
E("lifeline-association-missing", "Lifeline association missing", "application-config",
  "The device has no association to the controller in its lifeline group, so it obeys commands but never reports "
  "physical changes.",
  ["Interview did not finish", "Association overwritten or pointing at an old hub", "Legacy device with no lifeline: it must be polled"],
  ["Re-interview the device (the lifeline is assigned automatically) or set group 1 to the controller by hand."],
  ["zjs-noupd", "sl-assoc"], log=[r"ZW1300", r"ZW1301"])
E("root-vs-endpoint-report-ambiguity", "Multi-endpoint device reports from the wrong place", "application-config",
  "A multi-channel device reports from its root instead of the endpoint, so the software cannot tell which endpoint "
  "changed and that endpoint's state never updates.",
  ["Device firmware reporting without Multi Channel encapsulation", "Lifeline set as a plain instead of a multi-channel association"],
  ["Switch the lifeline between a node association and a multi-channel association to endpoint 0; check for a device "
   "configuration update."],
  ["zjs-noupd"], severity="info")
E("duplicate-reports-multichannel-lifeline", "Every change reported twice", "application-config",
  "Both the root and an endpoint lifeline exist, or the device mirrors endpoint 1 to the root, so each change arrives "
  "twice and doubles traffic.",
  ["Redundant associations", "Device mirroring an endpoint to its root"],
  ["Remove the redundant associations: only the root lifeline should point at the controller. Then re-interview."],
  ["sl-assoc"], severity="info")
E("report-flooding-misconfigured-meter", "Meter or sensor flooding the network with reports", "capacity-traffic",
  "Power, energy or sensor reports at short intervals or tiny thresholds saturate the mesh and can trigger controller "
  "lock-ups. Z-Wave carries only about 10 to 20 messages a second at best.",
  ["Default or over-eager reporting parameters", "Multi-socket plugs reporting several values per socket"],
  ["Disable reports you do not use; prefer change thresholds over timed reports (for example 50 W for an appliance); "
   "lengthen intervals to minutes or an hour."],
  ["zjs-first", "oh-heal", "gh-6512"])
E("supervised-reports-doubling-traffic", "Supervised reports doubling traffic", "capacity-traffic",
  "The device wraps routine reports in Supervision, so every report costs a confirmation back from the controller.",
  ["Device default for S2-included devices"],
  ["Turn off supervision for non-critical reports in the device's configuration, where it offers that."],
  ["zjs-first"], severity="info")
E("retransmit-storm-missed-acks", "Device resends the same report many times", "capacity-traffic",
  "The device does not see the controller's acknowledgement and resends one report over and over, briefly swamping the network.",
  ["Controller not acknowledging in time (700-series firmware bug)", "Device firmware", "Group commands fanned out as many single messages"],
  ["Update controller and device firmware; use multicast or scenes for groups instead of many single commands."],
  ["gh-3906"])
E("polling-storm", "Polling storm", "capacity-traffic",
  "Automations or integrations poll values or ping nodes at short intervals, flooding the network.",
  ["Polling enabled on devices that already report by themselves", "Automations that refresh values on a timer"],
  ["Use polling only as a last resort; remove it wherever the device reports changes itself."],
  ["ha-zwjs", "oh-heal"], log=[r"Scheduled poll canceled"])
E("application-busy-or-rejected", "Device answers 'busy' or rejects requests", "application-config",
  "The device replies that it is busy (try later) or rejects the request outright.",
  ["Device mid-operation (motor running, firmware update, booting)", "Command sent at the wrong security level or to an unsupported endpoint"],
  ["Retry after the device finishes; if it always rejects, re-interview it and check the endpoint and security used."],
  ["zjs-src"], log=[r"Node is busy, re-queueing commands"])
E("supervision-fail-nosupport-working", "Device reports a command failed (Supervision)", "application-config",
  "A supervised command came back as 'fail' or 'no support': the device received it and did not carry it out.",
  ["Unsupported command or value", "Lock bolt blocked", "Wrong security class"],
  ["Check the value sent and the device's physical state; re-interview if it claims no support for something it should do."],
  ["zjs-src"], log=[r"ZW1100"])
E("unsupported-or-unknown-command-discarded", "Commands discarded as unknown or invalid", "application-config",
  "The software drops what a device sends because it is malformed, of an unexpected version, or not something the "
  "device advertised.",
  ["Incomplete interview", "Corrupted frames at low speed", "Device firmware quirks"],
  ["Re-interview the device, check for a device configuration update, and rule out frame corruption."],
  ["zjs-src", "zjs-nonsense"],
  log=[r"Dropping message because it contains invalid data", r"could not be deserialized",
       r"is unknown - discarding received command", r"No handlers for received request"])
E("get-acked-but-no-report", "Device acknowledges a query but never answers", "application-config",
  "The radio acknowledges the request, but the device never sends the value back (the software waits 1 s by default).",
  ["Unsupported query", "Device firmware bug or device busy", "The answer is sent but lost on a bad return route"],
  ["If answers never arrive from one device, rebuild its routes; if only one kind of query fails, it is unsupported."],
  ["zjs-opts", "zjs-src"], log=[r"ZW0201"])
E("transport-service-segmentation-failure", "Large messages lose segments", "application-config",
  "Big messages (secure inclusion keys, long reports) are split into segments, and a weak link loses some of them.",
  ["Weak or busy link during secure inclusion or a large report"],
  ["Improve the link, or do secure inclusion close to the controller."],
  ["zjs-src"],
  log=[r"Transport Service RX session #\d+ failed", r"Segment with offset \d+ missing", r"Segment Complete missing",
       r"Dropping incomplete partial CC session"])
E("multicast-broadcast-partial-delivery", "Group command misses some devices", "capacity-traffic",
  "Multicast and broadcast frames are not acknowledged, so some devices miss a group command; and groups sent as many "
  "single commands create bursts.",
  ["Weak link to some group members", "Heavy use of broadcasts"],
  ["Improve the link to the members that miss commands; keep broadcast traffic rare."],
  ["zjs-common", "zjs-src"], log=[r"did not respond to the multicast request"])
E("ota-firmware-update-failure", "Device firmware update stalls or fails", "firmware",
  "An over-the-air update stalls or aborts, usually on a weak link, a sleeping device or a slow S0 link.",
  ["Weak link or busy network", "Battery device falling asleep", "Wrong firmware file for the device or region"],
  ["Update with the device near the controller on a quiet network, keep battery devices awake, and try a smaller fragment size."],
  ["zjs-src"],
  log=[r"Failed to start the update", r"Failed to send firmware fragment", r"Firmware update timed out",
       r"firmware update is for a different (device|region)"])

# ---------------------------------------------------------------- long range
E("lr-out-of-range-no-mesh", "Long Range device out of range", "long-range",
  "Long Range is a star network: devices talk straight to the controller and cannot be repeated. A device out of "
  "range has no fallback.",
  ["Distance or obstacles", "Controller antenna placement"],
  ["Move the controller or its antenna, raise transmit power, or re-include the device as classic mesh so repeaters can help."],
  ["zjs-lr", "zjs-src"], log=[r"for nodes using Z-Wave Long Range", r"for Long Range node \d+"])
E("lr-key-or-inclusion-misconfig", "Long Range keys or inclusion misconfigured", "long-range",
  "Long Range needs its own two S2 keys and is included only through SmartStart. Without the keys nothing can be decrypted.",
  ["Long Range keys not configured", "Wrong controller role after a restore"],
  ["Configure both Long Range keys, and check that the controller is the network's primary."],
  ["zjs-lr", "zjs-src"], log=[r"No network key for Z-Wave Long Range configured"], severity="crit")
E("lr-power-channel-config", "Long Range power or channel setting wrong", "long-range",
  "Transmit power limits or the Long Range channel are misconfigured; a sniffer on the wrong channel hears nothing.",
  ["Region or power defaults not applied", "Sniffer set to a different Long Range channel"],
  ["Let Z-Wave JS apply the legal power level; set the sniffer to the matching Long Range region."],
  ["zjs-lr", "zjs-src"],
  log=[r"Querying the max\. Long Range powerlevel failed", r"Querying the Long Range channel information failed"],
  severity="info")

# ---------------------------------------------------------------- hardware and environment
E("metal-enclosure-attenuation", "Device shielded by a metal box", "hardware-environment",
  "An in-wall switch or relay inside a metal box or behind a metal plate is blocked in both directions and has never "
  "had a good link.",
  ["Metal back boxes, faceplates or weatherproof enclosures"],
  ["Use a plastic box, add a repeater within a few metres, or use a controller with an external antenna."],
  ["zjs-first"])
E("controller-placement-rack-or-metal", "Controller badly placed", "hardware-environment",
  "The controller sits on metal, at the back of a rack, or at one end of the building, weakening every link.",
  ["Convenience placement next to the server"],
  ["Move the controller to a central, open spot on an extension cable."],
  ["zjs-first", "ha-solved"])
E("aeotec-gen5-zw090-on-pi4", "Aeotec Z-Stick Gen5 not detected on Raspberry Pi 4", "hardware-environment",
  "The original Aeotec Z-Stick Gen5 is not recognised on Raspberry Pi 4 USB ports, so there is no Z-Wave at all.",
  ["Hardware incompatibility of the original Gen5 revision"],
  ["Put a USB 2.0 hub (preferably powered) between stick and Pi, or use the Gen5+ revision."],
  ["https://community.home-assistant.io/t/raspberry-pi4-not-detecting-aeotec-z-stick-gen5/214670"], severity="info")
E("region-frequency-mismatch", "Region or frequency mismatch", "hardware-environment",
  "Controller, device or sniffer is set to a different radio region. Inclusion finds nothing, and a sniffer hears "
  "nothing or only garbage.",
  ["Imported devices", "Sniffer left on another region"],
  ["Select the right region on the sniffer and controller (700/800 controllers can change region). A device's own "
   "frequency cannot be changed."],
  ["zjs-common", "zjs-zniffer", "ha-zwjs"], log=[r"is not a valid RF region", r"Querying the RF region failed"])
E("repeater-powered-off", "Repeater switched off", "hardware-environment",
  "A mains repeater is switched off at the wall or breaker (smart plugs, bulbs on ordinary switches), so several "
  "devices in one area become unreachable together.",
  ["Bulbs used as repeaters on wall switches", "Seasonal devices unplugged"],
  ["Keep repeaters permanently powered, then rebuild routes for the devices that depended on them."],
  ["https://homey.app/en-co/wiki/z-wave-troubleshooting-fixing-slow-or-missing-responses"])
E("failing-or-underpowered-stick", "Failing or under-powered controller stick", "hardware-environment",
  "Flaky USB power or an ageing stick causes resets and serial dropouts. Rule out the firmware lock-up first: "
  "swapping hardware rarely fixes that.",
  ["Weak USB power, long unpowered cables", "Ageing hardware"],
  ["Use a powered hub and a short quality cable; replace the stick only after ruling out firmware."],
  ["gh-6512", "zjs-opts"], severity="info")

# ---------------------------------------------------------------- traffic-only checks (not from the research list)
E("device-reset-locally", "Device was factory reset", "inclusion-interview",
  "The device announced that it was reset to factory defaults. It has left the network, and its node ID remains as a ghost.",
  ["Reset button held, or a reset from the device's own menu"],
  ["Remove the old node ID as a failed node, then include the device again."], [], severity="crit")
E("battery-low", "Low battery", "power-sleep",
  "A device reported a low battery. Weak batteries cause missed reports and failed wake-ups before the device dies.",
  ["Battery at end of life", "Excess reporting draining it"],
  ["Replace the battery; if it drains quickly, see the battery-drain entry."], [], severity="warn")
E("nop-ping-loop", "Controller keeps pinging a node", "routing",
  "The controller is sending repeated empty 'ping' frames to a node, which it does when it suspects the node is dead.",
  ["Node unreachable or unplugged", "Health checks or automations pinging on a timer"],
  ["Check that the node is powered and in range; stop automated pinging once it is fixed."], [], severity="info")
E("direct-association-traffic", "Devices controlling each other directly", "application-config",
  "One device sends commands straight to another through an association, without going through the controller. "
  "This is normal, but it explains changes the controller did not cause.",
  ["Associations set up on purpose, or left over from an earlier installation"],
  ["Review the source device's association groups if this is unexpected."], [], severity="info")
E("association-loop", "Two devices triggering each other", "application-config",
  "Two devices send Set commands to each other and may be switching one another in a loop. This is a heuristic: "
  "no vendor source documents it.",
  ["Mutual associations between two switches or dimmers"],
  ["Remove the association in one direction."], [])
E("route-maintenance-traffic", "Route rebuild or inclusion in progress", "routing",
  "Neighbour discovery and route assignment frames are in the air. Expect slow responses until it finishes.",
  ["A route rebuild, an inclusion, or a device being re-interviewed"],
  ["Wait for it to finish before judging network performance."], [], severity="info")
E("inclusion-activity", "A device is trying to join", "inclusion-interview",
  "Inclusion requests or repeated node information broadcasts were seen: a device is in learn mode or announcing itself.",
  ["A new or reset device powered on nearby", "A neighbour's device", "A device stuck in learn mode"],
  ["If it is yours, start inclusion on the controller; otherwise it can be ignored."], [], severity="info")
