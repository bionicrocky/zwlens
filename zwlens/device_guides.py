"""Troubleshooting guides for common Z-Wave end devices (locks, switches, sensors).

Each guide lists the problems people most often hit with that device family, with causes and
fixes, and the device-side steps (the button sequences on the device itself) for adding,
removing, resetting and updating it. Text is taken from the makers' manuals and support pages,
then from the Z-Wave Alliance product database, Z-Wave JS and user forums; each item links its
sources, and labels say when a source is not the maker's own.
"""
from __future__ import annotations

NONE = "Not documented by the maker."

# Device-side step id -> label, in display order.
STEPS = {
    "include": "Add it to your network",
    "exclude": "Remove it from a network",
    "reset": "Factory reset",
    "firmware": "Firmware updates",
}

KINDS = {"lock": "Door locks", "switch": "Switches and dimmers", "sensor": "Sensors",
         "thermostat": "Thermostats", "plug": "Plugs"}


def A(how, src="", note=""):
    return {"how": how, "src": src, "note": note}


DEVICES = [
{
    "id": "kwikset",
    "name": "Kwikset SmartCode 910, 912, 914, 916 and 888, and Home Connect 620, 918 Z-Wave locks",
    "kind": "lock",
    "manufacturer_ids": [0x0090],
    "summary": (
        "Kwikset's battery-powered keypad and touchscreen deadbolts and levers with a built-in Z-Wave radio, "
        "often installed with alarm panels such as Qolsys IQ on Alarm.com. The most common complaint is a lock "
        "that keeps going \"offline\" or eats batteries, usually because it was enrolled too far from the panel "
        "or has no beaming-capable repeater near it."
    ),
    "quirks": [
        "Generations: the SmartCode 910, 912, 914, 916 and 888 are 500-series Z-Wave Plus (early 910s are "
        "older) and join with S0 only. The Home Connect 620 and 918 are 700-series and add S2 and SmartStart. "
        "Alarm.com says Z-Wave Long Range is only on 800-series versions of the 620.",
        "Most models also came in a Zigbee version, and the Z-Wave and Zigbee button sequences differ. A Zigbee "
        "914 will never pair with a Qolsys panel. Check the box or manual for \"Z-Wave\".",
        "The lock is a sleeping (FLiRS) device and does not repeat for other devices. Kwikset's 916 guide says "
        "35 feet+ is a typical distance and that you may need \"additional Z-Wave beaming capable devices that "
        "can serve as repeaters\".",
        "Alarm.com says: \"Do not add or delete user codes locally to or from the lock.\" Manage codes only from "
        "the Alarm.com app or website, or codes will fall out of sync.",
        "After several failed attempts to reach the system, Kwikset says the lock \"will go into sleep mode\". "
        "Locking and unlocking it with a key makes it send its status again.",
        "A factory reset also removes the lock from the network on 500-series models, so the panel keeps a "
        "dead entry. The 910 technical guide also offers a remote reset: write 1 to configuration parameter 40.",
        "Z-Wave JS turns off Supervision for the Home Connect 620, because the lock can get stuck sending "
        "Supervision reports without end.",
    ],
    "steps": {
        "include": A(
            "Start add mode on the controller, then press button \"A\" on the lock interior one time. On the 910 "
            "family, \"The red LED will illuminate when the lock enters Add Mode.\" On a Qolsys IQ Panel: "
            "Settings > Advanced Settings > Installer Code > Installation > Devices > Z-Wave Devices > Add "
            "Device, then press \"A\" (Brinks says to wait 2 minutes). Home Connect 620/918 can also join with "
            "S2 or SmartStart.",
            "https://products.z-wavealliance.org/wp-content/uploads/products/50445/Install%20Guide_910_small.pdf",
            "500-series locks join with S0; 700/800-series locks can use S2 or SmartStart. Alarm.com says to "
            "begin with the lock within 6 feet of the panel and wait 2 minutes before operating it. Kwikset "
            "says some systems need the lock within 12\" of the controller, held still for 60 seconds.",
        ),
        "exclude": A(
            "Start remove (exclude) mode on the controller, then press button \"A\" on the lock one time. On a "
            "Qolsys IQ Panel the remove option is Settings > Advanced Settings > Installer Code > Installation > "
            "Devices > Z-Wave Devices > \"Clear Device\".",
            "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/Kwikset/"
            "Kwikset-Weiser_Home_Connect_620/Enroll_delete_or_reset_a_Kwikset-Weiser_Home_Connect_620_Deadbolt",
            "Same button on every generation. The Zigbee versions use a different sequence (button \"B\" nine "
            "times on the 916), so do not follow a Zigbee manual.",
        ),
        "reset": A(
            "\"Remove battery pack.\" \"Press and HOLD the Program button while reinserting the battery pack.\" "
            "\"Keep holding the button for 30 seconds until the lock beeps and the status LED flashes red.\" "
            "\"Press the Program button once more.\" The LED flashes red and green, then the lock runs its door "
            "handing (the bolt extends and retracts). On the 910 and 914, perform handing yourself; the 916 "
            "does it on its own.",
            "https://www.kwikset.com/support/answers/"
            "how-to-restore-default-settings-on-my-signature-series-or-smartcode-deadbolt-perform-a-factory-reset",
            "Erases all user codes and settings and removes the lock from the smart home system. The 910 guide "
            "says it \"will not remove any anti-theft settings\" and asks you to use a local reset only when the "
            "primary controller is missing. Exclude it at the panel too, then include it again.",
        ),
        "firmware": A(
            "Kwikset publishes no Z-Wave firmware files for users. Kwikset's 912 troubleshooting guide covers OTA "
            "updates pushed by a service provider's touchscreen controller (on Zigbee systems), and says to "
            "contact Kwikset for a replacement if OTA keeps failing. Kwikset told one Z-Wave JS user the HC620 "
            "had no updates. The Z-Wave JS firmware update service lists no Kwikset files.",
            "https://cdn.shopify.com/s/files/1/0052/5395/5651/files/912_Troubleshooting_Guide.pdf",
            "The Kwikset app's Bluetooth firmware updates are for Halo and Aura locks, not these Z-Wave models.",
        ),
    },
    "problems": [
        {
            "title": "Lock keeps showing \"Offline\" or \"Malfunction\" on the Qolsys panel or Alarm.com app",
            "signs": (
                "Alarm.com sends offline alerts, often at the same time every day, and app commands hang, but "
                "the lock still works at the door and comes back when used; a sniffer would show unanswered "
                "beams or frames to the lock with no ACK."
            ),
            "causes": [
                "The lock was enrolled far from the panel, so secure enrollment or routing is weak.",
                "No beaming-capable, AC-powered repeater between the panel and the lock. Locks do not repeat.",
                "Weak or generic batteries reduce the lock's radio range before a low-battery alert appears.",
                "After many failed attempts the lock goes into Kwikset's \"sleep mode\" and stops reporting.",
            ],
            "fixes": [
                "Clear the lock at the panel, wait for Alarm.com to drop it from the device list, then re-add it "
                "within 6 feet of the panel and wait before moving it.",
                "Add one or two AC-powered Z-Wave Plus repeaters (plug-in modules or switches) between the panel "
                "and the lock, then run System Tests > Z-Wave Tests > Network Rediscovery.",
                "Replace all batteries with fresh name-brand alkaline cells.",
                "Lock and unlock once with the key so the lock sends its status and wakes from sleep mode.",
            ],
            "kb": [
                "flirs-beam-failure",
                "too-few-neighbors-no-redundancy",
                "marginal-link-low-power-margin",
                "route-through-dead-repeater",
            ],
            "src": [
                "https://support.suretyhome.com/t/kwikset-914-z-wave-lock-goes-offline-everyday/5372",
                "https://support.suretyhome.com/t/kwikset-914-zwave-plus-lock-repeated-offline-malfunction/6084",
                "https://cdn.shopify.com/s/files/1/0052/5395/5651/files/912_Troubleshooting_Guide.pdf",
            ],
        },
        {
            "title": "Batteries drain in a few weeks instead of a year",
            "signs": (
                "Low-battery alerts arrive weeks after fresh batteries, where Kwikset expects over a year at 10 "
                "operations per day; a sniffer would show many retries or frequent polling to the lock."
            ),
            "causes": [
                "The controller polls (pings) the lock too often.",
                "The lock is at the edge of range, so every message is resent.",
                "The panel falsely reports low battery when the battery is fine.",
                "A bolt that rubs on a misaligned strike makes the motor work harder.",
                "A faulty lock: Kwikset says a drain within one day means the lock must be replaced.",
            ],
            "fixes": [
                "Check at the lock: turn on switch #1 so the status LED flashes every six seconds. \"If the red "
                "flash is not seen, the battery is not low.\"",
                "Lower the controller's ping or poll rate to the lowest setting.",
                "Add a beaming repeater near the lock and re-enroll the lock close to the panel.",
                "Test stand-alone: remove the lock from the system and run it on new batteries for a week. If it "
                "still drains, the lock is at fault; call Kwikset.",
                "Check that the bolt extends freely into the strike.",
            ],
            "kb": ["battery-drain-from-reporting-or-retries", "polling-storm", "battery-low"],
            "src": [
                "https://www.kwikset.com/support/answers/on-my-smartcode-the-batteries-drain-within-a-few-weeks",
                "https://cdn.shopify.com/s/files/1/0052/5395/5651/files/912_Troubleshooting_Guide.pdf",
                "https://support.suretyhome.com/t/kwikset-912-lock-qolsys-iq2-panel-and-z-wave-extender/15947",
            ],
        },
        {
            "title": "Secure enrollment failed, or the lock joins as a generic device with no lock controls",
            "signs": (
                "Alarm.com shows \"Secure Enrollment Failed\", or the controller shows \"Highest security: None\" "
                "and no lock entity; a sniffer would show the S0 key exchange (Nonce Get / Network Key Set) "
                "timing out."
            ),
            "causes": [
                "The lock was too far from the panel during S0 key exchange. Surety says failed secure inclusion "
                "\"almost always means it was learned in while too far from the panel.\"",
                "The lock was moved or operated before enrollment finished.",
                "On 700/800-series locks with S2, a wrong DSK was entered.",
            ],
            "fixes": [
                "Power cycle the lock, clear it at the panel, and enroll again within 3 to 6 feet of the panel.",
                "Leave it still for a few minutes after it pairs before you operate it.",
                "If it still fails, factory reset the lock and try again. Alarm.com's last step is to remove all "
                "Z-Wave devices from the panel.",
                "On S2 locks, check the DSK, delete any device key, and re-enroll.",
            ],
            "kb": [
                "s0-nonce-timeout",
                "s0-downgrade-or-unintended-security-class",
                "s2-bootstrap-failure",
                "interview-incomplete-commandclasses",
            ],
            "src": [
                "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Partner_Portal_and_MobileTech/"
                "Customer_Trouble_Conditions/Secure_Enrollment_Failed",
                "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/General_Lock_Information/"
                "Enrolling_Z-Wave_Locks_-_Best_Practices",
                "https://community.home-assistant.io/t/"
                "kwikset-z-wave-lock-inclusion-problems-cant-seem-to-get-s0-security-to-work/910304",
            ],
        },
        {
            "title": "The lock will not pair at all",
            "signs": (
                "The panel times out (Qolsys shows an error such as 514) even with the lock next to it; a sniffer "
                "would show no Node Information Frame from the lock."
            ),
            "causes": [
                "It is the Zigbee model, not the Z-Wave model.",
                "The lock is still joined to an old network or panel.",
                "The interior and exterior assemblies are not connected (the anti-tamper alarm sounds).",
            ],
            "fixes": [
                "Confirm the model says Z-Wave. On Z-Wave models press button \"A\" once, not four times.",
                "Exclude it first: start remove mode at any controller and press \"A\" once, then include again.",
                "Reconnect the exterior cable to the interior, reinsert the battery pack, and pair within 12\" of "
                "the controller.",
                "Factory reset the lock if exclusion does not work.",
            ],
            "kb": ["inclusion-no-device-found", "node-included-twice-or-by-other-controller", "device-reset-locally"],
            "src": [
                "https://support.suretyhome.com/t/kwikset-914-not-pairing/19072",
                "https://cdn.shopify.com/s/files/1/0052/5395/5651/files/912_Troubleshooting_Guide.pdf",
            ],
        },
        {
            "title": "\"Jammed\" alerts, or the lock drops off the network after a jam",
            "signs": (
                "The panel reports a jam (a 916 flashes its symbols five times with five beeps); some 888 owners "
                "on Z-Wave JS see the node marked dead right after a lock command, with no jam alarm sent."
            ),
            "causes": [
                "The bolt cannot fully extend because the door is not shut or the strike is misaligned.",
                "The lock was moved to another door, or handing was never done, so it turns the wrong way.",
                "Low batteries leave the motor too weak to throw the bolt.",
            ],
            "fixes": [
                "Kwikset: \"Manually re-lock door. If needed, reposition strike.\"",
                "Redo door handing (factory reset on most models, or the manual handing steps in the guide).",
                "Replace the batteries.",
                "If the node stays dead after a jam, remove and reinsert the battery pack. That was the only "
                "workaround reported.",
            ],
            "kb": ["ghost-failed-node", "battery-low"],
            "src": [
                "https://www.gokeyless.com/documents/916-installation-user.pdf",
                "https://community.home-assistant.io/t/kwikset-888-locks-become-unavailable-if-lock-jams/734451",
                "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/General_Lock_Information/"
                "Lock_status_is_not_updating_or_the_status_is_incorrect",
            ],
        },
        {
            "title": "User codes from Alarm.com stay \"pending\" or don't open the door",
            "signs": (
                "New codes show pending for a long time or never work, though lock and unlock from the app work; "
                "small lock commands get through while longer code messages fail."
            ),
            "causes": [
                "Codes were added or deleted on the lock keypad, so the lock and Alarm.com disagree.",
                "A weak or partly failed enrollment, often from enrolling far from the panel.",
                "The lock has not had time to take the code (users report about 5 minutes).",
            ],
            "fixes": [
                "Manage codes only from Alarm.com. Toggle the user's lock access off and on to resend the code.",
                "Re-enroll the lock near the panel, move it back, and run a Network Rediscovery.",
                "Add a beaming repeater if the lock is far from the panel.",
            ],
            "kb": ["marginal-link-low-power-margin", "flirs-beam-failure"],
            "src": [
                "https://support.suretyhome.com/t/cant-set-kwikset-user-codes-from-alarm-com/1127",
                "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/General_Lock_Information/"
                "Enrolling_Z-Wave_Locks_-_Best_Practices",
            ],
        },
        {
            "title": "Lock status in the app is wrong or does not update",
            "signs": (
                "The app shows unlocked when the door is locked, or the state changes only when the door is open; "
                "a sniffer may show the command ACKed but no Door Lock or Notification report back."
            ),
            "causes": [
                "Generic batteries that do not read back the proper status.",
                "The bolt does not fully extend into the frame.",
                "Weak Z-Wave link or a lock in Kwikset's sleep mode after failed attempts.",
            ],
            "fixes": [
                "Use name-brand batteries.",
                "Test with the door open; if it works then, adjust the strike so the bolt fully extends.",
                "Re-hand the lock (needs a factory reset, which deletes codes), or delete and re-add it.",
                "Lock and unlock with the key to make it report again.",
            ],
            "kb": ["get-acked-but-no-report", "lifeline-association-missing"],
            "src": [
                "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/General_Lock_Information/"
                "Lock_status_is_not_updating_or_the_status_is_incorrect",
                "https://cdn.shopify.com/s/files/1/0052/5395/5651/files/912_Troubleshooting_Guide.pdf",
            ],
        },
        {
            "title": "Home Connect 620 is slow from the app or floods the network with messages",
            "signs": (
                "Alarm.com app commands take a long time; on other controllers a sniffer shows endless Supervision "
                "Report \"Working\" frames from the lock with the same session ID."
            ),
            "causes": [
                "Old Qolsys panel software (IQ2/IQ2+ before 2.6.0, IQ4 4.0.1 or older) on lock models 98920, "
                "98930 and 98690.",
                "HC620 firmware bug: it keeps reporting Supervision \"Working\" and never finishes.",
            ],
            "fixes": [
                "Update the Qolsys panel (Kwikset lists IQ2/IQ2+ 2.6.2 and IQ4 4.0.1).",
                "On Z-Wave JS, update to a release that disables Supervision for the HC620, then re-interview "
                "the lock.",
                "Pull and reinsert the battery pack to stop a stuck lock.",
            ],
            "kb": ["supervision-fail-nosupport-working", "report-flooding-misconfigured-meter"],
            "src": [
                "https://www.kwikset.com/support/answers/why-does-my-home-connect-620-take-a-long-time-to-respond-"
                "to-a-command-from-the-alarm.com-app-or-web-portal",
                "https://github.com/zwave-js/node-zwave-js/discussions/5566",
            ],
        },
    ],
    "docs": [
        {
            "label": "Kwikset: factory reset for Signature Series and SmartCode deadbolts",
            "url": "https://www.kwikset.com/support/answers/"
            "how-to-restore-default-settings-on-my-signature-series-or-smartcode-deadbolt-perform-a-factory-reset",
        },
        {
            "label": "Kwikset: SmartCode batteries drain within a few weeks",
            "url": "https://www.kwikset.com/support/answers/on-my-smartcode-the-batteries-drain-within-a-few-weeks",
        },
        {
            "label": "Kwikset: Home Connect 620 slow to respond from Alarm.com (Qolsys software)",
            "url": "https://www.kwikset.com/support/answers/why-does-my-home-connect-620-take-a-long-time-to-respond-"
            "to-a-command-from-the-alarm.com-app-or-web-portal",
        },
        {
            "label": "Kwikset SmartCode 910 Installation and User Guide, with Z-Wave technical appendix "
            "(Z-Wave Alliance copy)",
            "url": "https://products.z-wavealliance.org/wp-content/uploads/products/50445/"
            "Install%20Guide_910_small.pdf",
        },
        {
            "label": "Kwikset SmartCode 916 Installation and User Guide (dealer copy)",
            "url": "https://www.gokeyless.com/documents/916-installation-user.pdf",
        },
        {
            "label": "Kwikset Programming and Troubleshooting Guide 62813 (retailer copy)",
            "url": "https://cdn.shopify.com/s/files/1/0052/5395/5651/files/912_Troubleshooting_Guide.pdf",
        },
        {
            "label": "Enroll, delete or reset a Kwikset/Weiser Home Connect 620 (Alarm.com)",
            "url": "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/Kwikset/"
            "Kwikset-Weiser_Home_Connect_620/Enroll_delete_or_reset_a_Kwikset-Weiser_Home_Connect_620_Deadbolt",
        },
        {
            "label": "Enrolling Z-Wave locks: best practices (Alarm.com)",
            "url": "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/General_Lock_Information/"
            "Enrolling_Z-Wave_Locks_-_Best_Practices",
        },
        {
            "label": "Add, remove and rediscover Z-Wave devices on Qolsys IQ Panel 2/4 (Surety forum)",
            "url": "https://support.suretyhome.com/t/"
            "how-to-add-remove-z-wave-device-and-run-a-network-rediscovery-"
            "with-qolsys-iq-panel-2-2-and-iq-panel-4/9753",
        },
        {
            "label": "Troubleshooting the Kwikset 910 (Brinks Home dealer page)",
            "url": "https://brinkshome.com/help-center/articles/9-troubleshooting-the-kwikset-910-deadbolt",
        },
        {
            "label": "Kwikset HC620 constant Supervision chatter (Z-Wave JS GitHub discussion)",
            "url": "https://github.com/zwave-js/node-zwave-js/discussions/5566",
        },
        {
            "label": "Kwikset HC620 device config with Supervision removed (Z-Wave JS)",
            "url": "https://github.com/zwave-js/zwave-js/blob/master/packages/config/config/devices/0x0090/hc620.json",
        },
    ],
},
{
    "id": "schlage",
    "name": "Schlage (Allegion) Connect BE469 / BE469ZP, BE468 / BE468ZP, Connected Keypad FE599",
    "kind": "lock",
    "manufacturer_ids": [0x003B],
    "summary": (
        "Battery-powered Schlage Z-Wave locks: the Connect touchscreen deadbolts (BE468, BE469 and the "
        "Z-Wave Plus BE468ZP/BE469ZP) and the older FE599 keypad lever. The most common trouble is the lock "
        "dropping off the network or eating batteries when its route to the controller is weak, followed by "
        "secure inclusion that fails or falls back to a lower security level."
    ),
    "quirks": [
        "Every lock has its own 6-digit Programming Code on a sticker inside the lock (and on the back of the "
        "guide). Schlage customer service cannot retrieve lost default codes, so find it before you reset.",
        "The BE468, BE469 and FE599 are S0-only locks. The BE468ZP and BE469ZP are Z-Wave Plus with S2 Access "
        "Control (and SmartStart on the BE468ZP); S2 needs the DSK PIN printed with the lock.",
        "The ZP models add and remove with a button on the circuit board under the battery cover; the older "
        "models use a keypad sequence with the Programming Code.",
        "A factory reset does not remove the lock from the Z-Wave network. Schlage says you must also run an "
        "exclusion, or the controller keeps a dead node.",
        "On the BE469 the Z-Wave radio is off until the lock is first enrolled, to save battery.",
        "The lock is FLiRS (it sleeps and is woken by beams). Repeaters near it must support beaming, or "
        "commands fail and the lock burns battery retrying.",
        "Schlage says to use four alkaline AA batteries; lithium batteries 'may cause undesirable operation'.",
    ],
    "steps": {
        "include": A(
            "Put the controller in Add/Inclusion mode first. BE469ZP/BE468ZP: remove the battery cover and "
            "press the red button under it (on the circuit board); flashing yellow means working, solid green "
            "means success, red means it failed. BE468/BE469: extend the bolt, press the Schlage logo on the "
            "keypad, enter the 6-digit programming code, then press 0; a green check means success, a red X "
            "means it failed. FE599/BE369: enter the 6-digit programming code, press the Schlage button, then "
            "press 0; the Schlage button flashes green on success, red on failure.",
            "https://schlage-res.zendesk.com/hc/en-us/articles/38615271022484",
            "On S2 networks the controller asks for the DSK PIN of the ZP lock. Users report the add must "
            "finish within about 15 seconds and works best with the lock close to the controller; the FE599 "
            "steps are in https://schlage-res.zendesk.com/hc/en-us/articles/39137113948948.",
        ),
        "exclude": A(
            "Put the controller in Remove/Exclude mode first. Connect locks (BE468/BE469/BE469ZP): press the "
            "Schlage logo on the keypad, enter the 6-digit programming code, then press 0; a green check means "
            "excluded, a red X means it failed. ZP models: if that fails, press and hold the Enroll/Unenroll "
            "button under the battery cover until the light blinks green. FE599/BE369: enter the 6-digit "
            "programming code, then press 0; the Schlage button flashes green when excluded.",
            "https://schlage-res.zendesk.com/hc/en-us/articles/38619191907988",
            "Any Z-Wave controller can exclude the lock, not only the one it was added to. FE599 steps: "
            "https://schlage-res.zendesk.com/hc/en-us/articles/39138127721748.",
        ),
        "reset": A(
            "BE469/BE469ZP/BE468: disconnect the batteries, press and hold the Outside Schlage Button, reconnect "
            "the batteries while holding it, then release. Check by pressing the Outside Schlage Button and "
            "entering a default User Code; the lock runs a setup routine. This restores the default "
            "Programming and User Codes and erases all other User Codes. ZP models can also be reset by "
            "holding the circuit-board button for about 7 seconds until the LED lights again (three red "
            "blinks and a blinking green check mean success).",
            "https://www.gokeyless.com/wp-content/uploads/2021/05/BE469-User-Manual.pdf",
            "A reset does not exclude the lock; exclude it as well. The Z-Wave Alliance listing says to use the "
            "board-button reset only when the primary controller is missing or inoperable. FE599 reset (Wink "
            "help page, not Schlage): disconnect batteries, press and release the Schlage button, reconnect, "
            "wait until the button is dark, then within ten seconds hold it until it lights green and beeps.",
        ),
        "firmware": A(
            NONE,
            "https://products.z-wavealliance.org/?p=12732",
            "Schlage publishes no firmware files or update steps. The BE468ZP certification lists the Firmware "
            "Update Meta Data command class, but forum users report they could not update these locks.",
        ),
    },
    "problems": [
        {
            "title": "Lock goes offline or shows as dead after it is mounted on the door",
            "signs": "The lock works at the keypad but the controller marks it dead or offline; a sniffer shows "
                     "commands to the node with no ACK, or beams that never get an answer through a repeater.",
            "causes": [
                "Weak or many-hop route from the door to the controller (metal door, walls, distance).",
                "Nearby repeaters that do not support beaming, so the sleeping lock can't be woken.",
                "Low batteries: users report these locks start failing on the radio around 75%.",
                "Rarely, a bad Z-Wave radio in the lock; Schlage has replaced locks for this.",
            ],
            "fixes": [
                "Add a beaming-capable repeater or mains-powered Z-Wave Plus device within about 20 ft of the lock.",
                "Rebuild routes for the lock after adding repeaters; operate the lock a few times afterwards.",
                "Fit fresh alkaline AA batteries.",
                "If nothing helps, exclude, reset and re-add the lock near the controller, then move it back and "
                "rebuild its routes; contact Schlage if it still drops.",
            ],
            "kb": ["flirs-beam-failure", "route-through-dead-repeater", "too-few-neighbors-no-redundancy",
                   "metal-enclosure-attenuation", "marginal-link-low-power-margin"],
            "src": [
                "https://community.smartthings.com/t/schlage-connect-touchscreen-deadbolt-keep-going-offline/159330",
                "https://community.home-assistant.io/t/schlage-allegion-be469zp-node-repeatedly-dying/751126",
            ],
        },
        {
            "title": "Batteries drain in weeks instead of about a year",
            "signs": "Battery level drops fast after moving to a new hub or adding devices; a sniffer would show "
                     "repeated beams and retries to the lock, or the lock repeatedly searching for a route.",
            "causes": [
                "The lock can't find a good route and keeps trying (FLiRS wake-ups cost power).",
                "Routing through a repeater that does not support beaming.",
                "A faulty lock radio (swap locks between doors: if the drain follows the lock, it is the lock).",
            ],
            "fixes": [
                "Put a beaming repeater between the lock and the controller so it is the best path.",
                "Rebuild routes, then pull and reconnect the battery pack and operate the lock several times.",
                "Cut back any frequent polling of the lock by the controller.",
                "Use alkaline AA batteries, not lithium, as Schlage says.",
            ],
            "kb": ["battery-drain-from-reporting-or-retries", "flirs-beam-failure", "polling-storm", "battery-low"],
            "src": [
                "https://community.hubitat.com/t/revisiting-schlage-be469-battery-drain-issue/42248",
                "https://www.gokeyless.com/wp-content/uploads/2021/05/BE469-User-Manual.pdf",
            ],
        },
        {
            "title": "Secure inclusion fails or the lock is added without security",
            "signs": "The lock shows a red X or red light after adding, or the controller says S0 bootstrapping "
                     "failed and lock/unlock and user codes don't work; logs show security key exchange timeouts.",
            "causes": [
                "The lock was not factory reset before retrying, so leftover state breaks the key exchange.",
                "Too far from the controller, or weak batteries, during the key exchange.",
                "The controller has no network key, or a key that does not match an earlier inclusion.",
                "The controller or driver does not support S2 for a ZP lock.",
            ],
            "fixes": [
                "Exclude the lock, factory reset it, then add it again; reset before every retry.",
                "Do the add with fresh batteries and the lock within a few feet of the controller.",
                "Make sure the controller has its security keys set and supports S2 for ZP models; enter the "
                "DSK PIN when asked.",
                "Remove any failed node left over from the attempt before trying again.",
            ],
            "kb": ["s0-nonce-timeout", "s2-bootstrap-failure", "inclusion-fails-at-controller", "ghost-failed-node"],
            "src": [
                "https://community.home-assistant.io/t/schlage-allegion-be469-z-wave-lock/330274",
                "https://community.openhab.org/t/schlage-be469zp-zwave-secure-inclusion-failed-openhab-3-3/137503",
            ],
        },
        {
            "title": "BE469ZP joins as S0 instead of S2 ('Some security features not supported')",
            "signs": "The ZP lock works but the hub reports an S0 or downgraded security level rather than S2.",
            "causes": [
                "The hub or app added it with S0 by default, or the hub did not support S2 at the time.",
                "The DSK step was skipped, so S2 Access Control was not granted.",
                "The security level is fixed at inclusion and can't be changed later.",
            ],
            "fixes": [
                "Exclude and factory reset the lock, then add it again with S2 and enter the DSK or scan the QR "
                "code from the box.",
                "If the hub can't do S2, S0 still works but uses more radio traffic.",
            ],
            "kb": ["s0-downgrade-or-unintended-security-class"],
            "src": [
                "https://community.smartthings.com/t/schlage-connect-be469-zwave-plus-zwave-s0-downgrade/181233",
                "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/Schlage/"
                "Schlage_Z-Wave_Plus_Touchscreen_Deadbolt_(BE469ZP)",
            ],
        },
        {
            "title": "Lock or unlock status is wrong or never updates",
            "signs": "The lock moves but the controller keeps showing the old state or 'unknown', often after a "
                     "thumbturn or keypad use; a sniffer may show Notification (alarm) reports but no Door Lock "
                     "report.",
            "causes": [
                "The older BE469 reports state through its Alarm Reports lifeline (group 1); if that association "
                "is missing, nothing is sent.",
                "An incomplete interview left the lock's values unknown.",
                "Hub drivers that read only the Door Lock state and ignore the alarm/notification reports.",
            ],
            "fixes": [
                "Check that the controller is in association group 1 (lifeline) and re-interview the lock.",
                "Use the notification/alarm entity for status if the lock state lags.",
                "If it still fails, exclude, reset and re-include the lock securely.",
            ],
            "kb": ["lifeline-association-missing", "interview-incomplete-commandclasses", "get-acked-but-no-report"],
            "src": [
                "https://community.home-assistant.io/t/schlage-be469-lock-status-incorrect/386038",
                "https://github.com/zwave-js/zwave-js/blob/master/packages/config/config/devices/0x003b/be469.json",
            ],
        },
        {
            "title": "User codes set from the hub vanish, or commands to the BE469ZP time out",
            "signs": "A code written from the controller disappears seconds later or commands take very long to "
                     "answer; a sniffer showed the lock ignoring User Code commands sent inside Supervision.",
            "causes": [
                "The BE469ZP does not accept all commands wrapped in Supervision (seen on firmware 3.3).",
                "The lock is known to be slow to respond to some commands.",
            ],
            "fixes": [
                "Update the controller software: Z-Wave JS turns Supervision off for this lock and waits longer "
                "for replies.",
                "Locks added before that fix may need to be excluded, reset and re-added.",
            ],
            "kb": ["supervision-fail-nosupport-working"],
            "src": [
                "https://github.com/zwave-js/zwave-js/issues/5260",
                "https://github.com/zwave-js/zwave-js/blob/master/packages/config/config/devices/0x003b/"
                "be469zp.json",
            ],
        },
        {
            "title": "Built-in alarm goes off too often, or never sounds",
            "signs": "The deadbolt's alarm sounds on normal door use or knocks, or stays silent when expected.",
            "causes": [
                "The alarm is off by default and must be turned on at the lock.",
                "Sensitivity is set too high (1 or 2) or too low (4 or 5); changing the mode resets it to 3.",
                "Tamper mode has a 60-second delay so you can lock up and leave.",
                "Activity mode alarms on every open and close.",
            ],
            "fixes": [
                "Turn the alarm on: press and hold the Inside Schlage Button and release after the first flash "
                "(about 5 seconds).",
                "Change mode: press and hold, release after the first flash (about 2 seconds), then press and "
                "release until the light for Activity, Tamper or Forced Entry is lit.",
                "Change sensitivity: press and hold, release after the third flash (about 10 seconds), then press "
                "and release until the flashes/beeps match the level you want.",
                "On the BE469/BE469ZP the controller can also set alarm mode and sensitivity (parameters 7 to 10).",
            ],
            "src": [
                "https://www.gokeyless.com/wp-content/uploads/2021/05/BE469-User-Manual.pdf",
                "https://schlage-res.zendesk.com/hc/en-us/articles/35013463541908-How-to-Change-Alarm-Mode-on-the-"
                "Schlage-Connect",
            ],
        },
        {
            "title": "Old lock still shows on the controller after a factory reset",
            "signs": "After resetting or moving the lock, a dead copy of it stays in the controller's node list.",
            "causes": [
                "A factory reset clears codes but does not leave the Z-Wave network.",
            ],
            "fixes": [
                "Run an exclusion from any Z-Wave controller before or after the reset.",
                "If the lock is gone, remove the failed node from the controller.",
            ],
            "kb": ["ghost-failed-node", "node-included-twice-or-by-other-controller"],
            "src": [
                "https://schlage-res.zendesk.com/hc/en-us/articles/38619191907988",
                "https://alarmgrid.com/faq/how-do-i-exclude-my-schlage-z-wave-lock",
            ],
        },
    ],
    "docs": [
        {"label": "BE469 User's Guide (dealer copy, GoKeyless)",
         "url": "https://www.gokeyless.com/wp-content/uploads/2021/05/BE469-User-Manual.pdf"},
        {"label": "Schlage: Enroll a Connect lock onto a Z-Wave network",
         "url": "https://schlage-res.zendesk.com/hc/en-us/articles/38615271022484"},
        {"label": "Schlage: Exclude a Connect lock from a Z-Wave network",
         "url": "https://schlage-res.zendesk.com/hc/en-us/articles/38619191907988"},
        {"label": "Schlage: Enroll a discontinued Connected Keypad deadbolt or lever (BE369, FE599)",
         "url": "https://schlage-res.zendesk.com/hc/en-us/articles/39137113948948"},
        {"label": "Schlage: Exclude a discontinued Connected Keypad deadbolt or lever (BE369, FE599)",
         "url": "https://schlage-res.zendesk.com/hc/en-us/articles/39138127721748"},
        {"label": "Schlage: Change alarm mode on the Schlage Connect",
         "url": "https://schlage-res.zendesk.com/hc/en-us/articles/35013463541908-How-to-Change-Alarm-Mode-on-the-"
                "Schlage-Connect"},
        {"label": "Z-Wave Alliance: Schlage Connect Smart Deadbolt BE468ZP",
         "url": "https://products.z-wavealliance.org/?p=12732"},
        {"label": "Alarm.com partner guide: BE469 (third party)",
         "url": "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/Schlage/"
                "Schlage_Z-Wave_Touchscreen_Deadbolt_(BE469)"},
        {"label": "Alarm.com partner guide: BE469ZP (third party)",
         "url": "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/Schlage/"
                "Schlage_Z-Wave_Plus_Touchscreen_Deadbolt_(BE469ZP)"},
        {"label": "Z-Wave JS device configs for Allegion 0x003B",
         "url": "https://github.com/zwave-js/zwave-js/tree/master/packages/config/config/devices/0x003b"},
        {"label": "Z-Wave JS issue 5260: BE469ZP user codes and Supervision",
         "url": "https://github.com/zwave-js/zwave-js/issues/5260"},
        {"label": "Schlage keypad lever FE599 help (Wink, third party)",
         "url": "https://www.wink.com/help/products/schlage-keypad-lever-with-z-wave-technology"},
        {"label": "How do I exclude my Schlage Z-Wave lock? (Alarm Grid)",
         "url": "https://alarmgrid.com/faq/how-do-i-exclude-my-schlage-z-wave-lock"},
        {"label": "BE469 battery drain (Hubitat forum)",
         "url": "https://community.hubitat.com/t/revisiting-schlage-be469-battery-drain-issue/42248"},
        {"label": "Schlage Connect keeps going offline (SmartThings forum)",
         "url": "https://community.smartthings.com/t/schlage-connect-touchscreen-deadbolt-keep-going-offline/159330"},
        {"label": "BE469 Z-Wave lock secure inclusion (Home Assistant forum)",
         "url": "https://community.home-assistant.io/t/schlage-allegion-be469-z-wave-lock/330274"},
    ],
},
{
    "id": "yale",
    "name": "Yale Assure Lock, Assure Lock SL, Assure Lock 2 and Real Living locks with a Z-Wave module",
    "kind": "lock",
    "manufacturer_ids": [0x0129, 0x0109],
    "summary": (
        "Yale's keypad and touchscreen deadbolts and levers get Z-Wave from a swappable Smart Module that sits "
        "in a slot above the batteries. The most common complaint is that the lock stops reporting its state, "
        "or drops off the network, when it is operated at the door."
    ),
    "quirks": [
        "Z-Wave comes from a plug-in module. Yale says: \"Batteries must not be installed prior to inserting "
        "and/or removing the Yale Smart module.\" The \"Network Module Setting\" menu item only appears when "
        "a module is installed.",
        "The module has to match the lock. Assure Lock 2 (YRD410/420/430/450) needs the AYR-MOD-ZW2-USA "
        "(or the 700-series ZW3). Assure Lock and Lever (YRD216/226/256, YRL216/226) use a different module.",
        "Module generations: 300 and 500-series modules join with S0 only. The 700-series module (model "
        "suffix -ZW3) adds S2 and SmartStart. Alarm.com notes S2 and SmartStart work only on the 700 series.",
        "Some older Yale and Real Living locks report manufacturer ID 0x0109 (Vision Security) rather than "
        "Yale's 0x0129, so a controller may show them as a Vision device.",
        "Keypad locks with a # key use # in the menu sequences. Touchscreen Assure locks use the gear (settings) "
        "key in its place.",
        "Lock-state changes made at the door arrive as Notification (Alarm) reports. Some controllers read the "
        "AlarmType values for manual and keypad lock or unlock to tell how the lock was operated.",
        "On Assure Lock 2, the Yale Access app can still reach the lock over Bluetooth if Z-Wave is down. Yale "
        "recommends managing entry codes from one system only.",
    ],
    "steps": {
        "include": A(
            "Assure Lock (YRD2xx): with the module installed and the controller in add mode, enter the Master "
            "Entry Code, press the gear key, press 7 and the gear key, then press 1 and the gear key (\"Join "
            "the Network\"). 700-series modules ask for the first 5 digits of the DSK on the controller. "
            "Assure Lock 2: enter the programming code and gear, then 7 and gear, then 1 and gear, then gear "
            "again; the lock stays in inclusion mode for 30 seconds. Keypad models use # in place of the gear.",
            "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/Yale/"
            "Yale__Assure_Touchscreen_Deadbolt_(YRD256)",
            "Alarm Grid advises excluding the lock first, keeping it about one foot from the controller, and "
            "having the bolt unlocked. A 500-series module joins with S0; a 700-series module can use S2 or "
            "SmartStart. Assure Lock 2 can also be added through the Yale Access app (\"Lock Settings\" > "
            "\"Yale Smart Module\"), and Yale gives 30 seconds to finish enrollment after you select Done.",
        ),
        "exclude": A(
            "Put the controller in remove mode, then enter the Master Entry Code and the gear key, press 7 and "
            "the gear key, then press 3 and the gear key (\"Exit the Network\"). Keypad models: "
            "\"[Master PIN] + [#] + [7] + [#] + [3] + [#]\".",
            "https://www.alarmgrid.com/faq/how-do-i-exclude-my-yale-z-wave-lock",
            "Same sequence on Assure Lock 2 per the Z-Wave JS device notes. One third-party copy of the Smart "
            "Module guide prints 7 then 1 for removal, which looks like a misprint. For Assure Lock 2 paired "
            "through the app, unenroll from the module settings in the Yale Access app.",
        ),
        "reset": A(
            "YRD256: \"1. Remove battery cover and batteries. 2. Remove inside lock to access reset button. 3. "
            "Reset button ... is located beside cable adapter. 4. While pressing reset button reinstall "
            "batteries. Hold reset button a minimum of 3 seconds then release. 5. Replace battery cover.\" "
            "This deletes all entry codes, including the Master Entry Code, and returns all settings to default.",
            "https://cdn.shopify.com/s/files/1/0144/2912/6742/files/YRD256-MNL-0003.pdf",
            "After a reset you must create a Master Entry Code before anything else. Do it with the lock "
            "mounted on the door, because the lock re-learns its handing on power-up. Alarm Grid says the "
            "Master PIN returns to 12345678 on some models. Assure Lock 2 has a different sequence (hold the "
            "reset button on the back of the board while pulling and replacing one battery). A local reset "
            "does not always clear the controller's record, so exclude first or remove the failed node.",
        ),
        "firmware": A(
            "Lock firmware on Assure Lock 2 is updated through the Yale Access app, and Yale says to use the "
            "latest firmware (1.8.1) with the Z-Wave module. Yale does not document a way for users to update "
            "the Z-Wave module itself.",
            "https://support.shopyalehome.com/en_us/assure-lock-2-with-z-wave-faq-SkKFJXvXn.md",
            "In a Z-Wave JS discussion, users report Yale phone support said the 700-series module cannot be "
            "updated. Older Assure Lock and Real Living locks have no documented user firmware update.",
        ),
    },
    "problems": [
        {
            "title": "Lock state does not update when the lock is used at the door",
            "signs": (
                "Commands from the hub work, but turning the thumbturn or using a code does not change the "
                "state until you refresh the node; a sniffer would show no Notification or Door Lock report "
                "reaching the controller after the manual operation."
            ),
            "causes": [
                "The lock's unsolicited report is lost on a weak or long route to the controller.",
                "The Lifeline association does not point at the controller, so the lock has nowhere to send "
                "reports.",
                "The controller does not map Yale's AlarmType values for manual and keypad lock and unlock.",
                "Older lock firmware.",
            ],
            "fixes": [
                "Check that association group 1 (Lifeline) holds the controller's node ID.",
                "Add a mains-powered Z-Wave repeater near the door, then heal or rebuild routes.",
                "Read the Notification AlarmType values (21/22 manual, 24/25 Z-Wave command) as a fallback.",
                "Update the lock firmware where Yale offers it (Yale Access app on Assure Lock 2).",
            ],
            "kb": ["get-acked-but-no-report", "lifeline-association-missing", "route-through-dead-repeater",
                   "too-few-neighbors-no-redundancy"],
            "src": [
                "https://community.home-assistant.io/t/frustration-with-z-wave-yale-locks/782790",
                "https://community.home-assistant.io/t/yale-deadbolt-wrong-status-on-zwavejs/405922",
            ],
        },
        {
            "title": "Lock shows offline, unavailable or dead",
            "signs": (
                "The hub marks the lock unavailable or dead and commands time out; a sniffer would show "
                "repeated failed beams or route attempts to the lock with no acknowledgement."
            ),
            "causes": [
                "The lock is too far from the controller or from a repeater; locks rely on wake-up beams that "
                "only nearby repeaters can send.",
                "The metal door and frame weaken the signal.",
                "A failing Z-Wave module.",
            ],
            "fixes": [
                "Put a mains-powered Z-Wave device close to the lock (forum advice is within about 20 feet).",
                "Remove the batteries, reseat the module, put the batteries back, and test again.",
                "If it keeps dropping with good coverage, ask Yale for a replacement module.",
            ],
            "kb": ["flirs-beam-failure", "marginal-link-low-power-margin", "metal-enclosure-attenuation",
                   "too-few-neighbors-no-redundancy", "ghost-failed-node"],
            "src": [
                "https://community.home-assistant.io/t/frustration-with-z-wave-yale-locks/782790",
                "https://github.com/zwave-js/node-zwave-js/discussions/5391",
                "https://support.suretyhome.com/t/yrl-touchscreen-deadbolt-zwave-issue/15033",
            ],
        },
        {
            "title": "Batteries drain in days or weeks",
            "signs": (
                "Battery level falls far faster than Yale's \"up to 9-12 months\" with Z-Wave; a sniffer would "
                "show the lock talking every few seconds or minutes instead of a few times an hour."
            ),
            "causes": [
                "The hub polls the lock too often.",
                "Weak signal makes the radio retry over and over.",
                "A faulty Z-Wave module.",
                "Users also report faster drain on some locks joined with S2, though this is not confirmed.",
            ],
            "fixes": [
                "Turn off or slow down lock polling in the hub.",
                "Improve the route with a nearby repeater.",
                "Exclude, reset and re-include the lock; if drain continues, try a replacement module.",
                "Use fresh AA alkaline batteries, as the manual calls for, and check the bolt moves freely.",
            ],
            "kb": ["battery-drain-from-reporting-or-retries", "polling-storm", "battery-low"],
            "src": [
                "https://community.smartthings.com/t/yale-zwave2-bad-battery-life/165908",
                "https://support.shopyalehome.com/en_us/assure-lock-2-with-z-wave-faq-SkKFJXvXn.md",
                "https://github.com/zwave-js/node-zwave-js/discussions/5391",
            ],
        },
        {
            "title": "Lock joins but cannot be locked or unlocked, or shows no battery level",
            "signs": (
                "Inclusion seems to succeed but the lock is listed as not secure, with no command classes "
                "or Lifeline; a sniffer would show the S0 or S2 key exchange stop part way."
            ),
            "causes": [
                "The secure key exchange did not finish in time (S0 has about a 10-15 second window).",
                "Other Z-Wave traffic or distance during inclusion.",
                "The controller is not set up for security, or the S2 DSK was not entered.",
            ],
            "fixes": [
                "Exclude and factory reset the lock, then include it again within a few feet of the controller.",
                "Keep the network quiet during inclusion.",
                "With a 700-series module, enter the DSK or use SmartStart; with a 500-series module, make sure "
                "the controller has an S0 key.",
            ],
            "kb": ["s0-nonce-timeout", "s2-bootstrap-failure", "secure-device-communicating-insecurely",
                   "interview-incomplete-commandclasses", "inclusion-fails-at-controller"],
            "src": [
                "https://community.openhab.org/t/yale-yrd256-lock-in-secure-mode/81086",
                "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/Yale/"
                "Yale__Assure_Touchscreen_Deadbolt_(YRD256)",
            ],
        },
        {
            "title": "Lock will not pair, or the network menu is missing",
            "signs": (
                "The controller finds nothing, or the lock's menu has no \"Network Module Setting\" or only "
                "offers to exit the network."
            ),
            "causes": [
                "The module was inserted or removed with batteries in, or is not fully seated.",
                "The lock still thinks it belongs to an old network.",
                "The wrong module for that lock model, or a failed module.",
                "A missed # or gear key press at the end of the sequence.",
            ],
            "fixes": [
                "Remove the batteries, reseat the module, then reinstall the batteries.",
                "Run exclusion (7 then 3) before inclusion, with the lock unlocked and near the controller.",
                "Check the module part number against the lock model.",
                "If the menu still misbehaves after a factory reset, replace the module.",
            ],
            "kb": ["inclusion-no-device-found", "node-included-twice-or-by-other-controller"],
            "src": [
                "https://support.suretyhome.com/t/yrl-touchscreen-deadbolt-zwave-issue/15033",
                "https://cdn.shopify.com/s/files/1/0144/2912/6742/files/YRD256-MNL-0003.pdf",
                "https://www.alarmgrid.com/faq/how-do-i-include-my-yale-z-wave-lock",
            ],
        },
        {
            "title": "Lock still says it is on a network after a factory reset",
            "signs": (
                "After a reset the lock will not join a new controller, and the old controller still lists "
                "it as a dead node."
            ),
            "causes": [
                "A factory reset did not clear the Z-Wave pairing; the lock was never excluded.",
                "The lock was paired to a previous controller that is gone.",
            ],
            "fixes": [
                "Run exclusion from any controller (it works even if that controller did not add the lock).",
                "Remove the dead node from the old controller with remove-failed-node.",
            ],
            "kb": ["device-reset-locally", "ghost-failed-node", "node-included-twice-or-by-other-controller"],
            "src": [
                "https://community.home-assistant.io/t/resetting-yale-real-living-z-wave-module/727970",
                "https://community.home-assistant.io/t/frustration-with-z-wave-yale-locks/782790",
            ],
        },
        {
            "title": "\"Jammed\" or keypad lockout alert never clears",
            "signs": (
                "A jammed or keypad-limit sensor stays on after the lock is working again, because no idle "
                "Notification report follows."
            ),
            "causes": [
                "The lock does not send an idle event after a jam or lockout alarm.",
                "Bolt binding from a misaligned strike, which also wears the batteries.",
            ],
            "fixes": [
                "Use the lock state value, not the jam sensor, in automations.",
                "Align the strike plate so the bolt moves freely; rehand the lock from the Settings Menu.",
            ],
            "kb": [],
            "src": [
                "https://community.home-assistant.io/t/yale-deadbolt-wrong-status-on-zwavejs/405922",
                "https://cdn.shopify.com/s/files/1/0144/2912/6742/files/YRD256-MNL-0003.pdf",
            ],
        },
        {
            "title": "Door sensor (DoorSense) shows unknown on Assure Lock 2",
            "signs": "The door open or closed state stays undefined in the Z-Wave hub.",
            "causes": [
                "Door position alarms are off by default over Z-Wave.",
                "Yale support has said DoorSense only works in the Yale Access app.",
            ],
            "fixes": [
                "Users report that setting parameter 19 (\"DPS Alarms\") to 0xFF enables door reports on some "
                "models (YRD420/450). Results vary by model.",
            ],
            "kb": [],
            "src": ["https://github.com/zwave-js/node-zwave-js/discussions/5391"],
        },
    ],
    "docs": [
        {"label": "Assure Lock SL YRD256 installation and programming manual (Yale manual, retailer-hosted copy)",
         "url": "https://cdn.shopify.com/s/files/1/0144/2912/6742/files/YRD256-MNL-0003.pdf"},
        {"label": "Yale: FAQ, Assure Lock 2 with Z-Wave",
         "url": "https://support.shopyalehome.com/en_us/assure-lock-2-with-z-wave-faq-SkKFJXvXn.md"},
        {"label": "Yale: Smart Module FAQs",
         "url": "https://support.shopyalehome.com/en_us/yale-smart-module-faqs-rJyERPDZi.md"},
        {"label": "Yale: Z-Wave 700 module announcement",
         "url": "https://shopyalehome.com/blogs/news-room/yale-upgrades-smart-lock-connectivity-with-new-z-wave-700"},
        {"label": "Yale YRMZ Smart Module installation guide (Manuals+ copy)",
         "url": "https://manuals.plus/yale/yrmz-series-smart-module-manual.pdf"},
        {"label": "Yale Assure Touchscreen Deadbolt YRD256 (Alarm.com partner guide)",
         "url": "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Locks/Yale/"
                "Yale__Assure_Touchscreen_Deadbolt_(YRD256)"},
        {"label": "How do I include my Yale Z-Wave lock? (Alarm Grid)",
         "url": "https://www.alarmgrid.com/faq/how-do-i-include-my-yale-z-wave-lock"},
        {"label": "How do I factory default my Yale Z-Wave lock? (Alarm Grid)",
         "url": "https://alarmgrid.com/faq/how-do-i-factory-default-my-yale-z-wave-lock"},
        {"label": "Yale device configs (Z-Wave JS)",
         "url": "https://github.com/zwave-js/zwave-js/tree/master/packages/config/config/devices/0x0129"},
        {"label": "Assure Lock 2 with 700-series module experiences (Z-Wave JS discussion)",
         "url": "https://github.com/zwave-js/node-zwave-js/discussions/5391"},
        {"label": "Frustration with Z-Wave Yale locks (Home Assistant forum)",
         "url": "https://community.home-assistant.io/t/frustration-with-z-wave-yale-locks/782790"},
        {"label": "YRL touchscreen deadbolt Z-Wave issue (Surety forum)",
         "url": "https://support.suretyhome.com/t/yrl-touchscreen-deadbolt-zwave-issue/15033"},
    ],
},
{
    "id": "jasco",
    "name": "GE / Jasco in-wall switches and dimmers (Enbrighten, UltraPro, Honeywell; GE 12722, 12724, 14291, "
            "14294, 46201, 46203 and similar)",
    "kind": "switch",
    "manufacturer_ids": [0x0063, 0x0039],
    "summary": (
        "Jasco makes the GE-, Enbrighten-, UltraPro- and Honeywell-branded Z-Wave wall switches and dimmers, "
        "sold across three generations: classic (12xxx/45xxx), 500-series Z-Wave Plus (14xxx, 46xxx) and "
        "700-series (58xxx/59xxx, ZWA model numbers). The main complaint is that the hub does not see changes "
        "made at the wall on the older 12xxx models, followed by dimmers that flicker with LED bulbs."
    ),
    "quirks": [
        "Most units report manufacturer ID 0x0063 (Jasco Products). Honeywell-branded Jasco switches, such as "
        "39348 / ZW4005, report 0x0039 (Honeywell) but use the same hardware and product IDs.",
        "Model numbers tell the generation. Z-Wave JS lists the 12724 and 45609 as \"300S\", the 12722, 14291, "
        "14294, 46201 and 46203 as \"500S\", and the 58433 (ZWA4011) as \"700S\". Only the 700-series models "
        "support S2 and SmartStart.",
        "Every model needs a neutral wire except the no-neutral dimmers. Jasco's FAQ names the 1000-Watt "
        "Dimmer (14299, incandescent only); the Enbrighten ZW3012 is a newer no-neutral dimmer with a 2W "
        "minimum load.",
        "Add-on (auxiliary) switches only work with a Jasco primary switch, and the add-on model must match "
        "the primary (for example 12723 for the 12722; 12728 or 46200 for the 14291; 46199 for the ZW3012). "
        "Add-ons are not Z-Wave devices and never join the hub.",
        "500- and 700-series models have three association groups: Lifeline, local-load (single press) and "
        "double press. Z-Wave JS maps their Basic Set commands to events, so double taps show up as scene "
        "or button events, not as a state change.",
        "Many settings are set at the switch with tap sequences. On the 14293 toggle, \"Press up three times, "
        "then down one time quickly\" cycles the LED mode. The 700-series uses a menu button held for five "
        "seconds.",
        "700-series switches ship in add-on mode for 3-way wiring. To use a standard (dumb) 3-way switch you "
        "must change the mode at the switch with the air gap and top paddle.",
    ],
    "steps": {
        "include": A(
            "Put the controller in add mode, then on the switch \"press the top or bottom of the rocker\" "
            "(older toggles: \"press up and release the toggle\"). If the controller asks for the S2 code, "
            "enter the 5-digit PIN printed on the box or the QR label on the switch. SmartStart models join "
            "on their own \"within 10 minutes of being switched on\" once the QR code is scanned.",
            "https://enbrightenme.com/cdn/shop/files/58433_Quick_Start_Guide.pdf",
            "Differs by generation: classic 12xxx/45xxx and 500-series 14xxx/46xxx join with no security or "
            "S0; only 700-series (58xxx/59xxx, ZWA models) offer S2 and SmartStart. If a switch will not "
            "join, Jasco's FAQ says to \"toggle the switch up and down rapidly\" while the hub searches, or "
            "reset it and try again.",
        ),
        "exclude": A(
            "Put the controller in remove mode, then \"press the top or bottom of the rocker\" (older "
            "toggles: \"press up and release the toggle\").",
            "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Lighting_and_Appliance_Control/"
            "Jasco_and_GE/Jasco_Enbrighten_Z-Wave_In-Wall_Paddle_Switch_(76591)/"
            "Enroll%2C_delete%2C_or_reset_a_Jasco_Enbrighten_Z-Wave_In-Wall_Paddle_Switch_(76591)",
            "Same on every generation. Exclusion also clears the switch's network settings, so it is the "
            "only way to clear a classic 12xxx switch that has no local reset.",
        ),
        "reset": A(
            "500-series Z-Wave Plus: \"Quickly press ON (up) button three times, then immediately press the "
            "OFF (down) button three times.\" The blue LED flashes 5 times on paddle models. 700-series: "
            "\"Pull up the air gap switch.\" Then \"While pressing the OFF (bottom) button, push in the air "
            "gap and continue pressing the OFF button. The LED flashes through the eight colors once.\"",
            "https://byjasco.com/pages/z-wave-faq",
            "Jasco says older (classic) models have no local reset and must be removed from the hub. A reset "
            "erases the network ID and the switch's settings. Jasco says to use it only \"if your network's "
            "primary controller is missing or otherwise inoperable\", so the hub is left with a dead node to "
            "remove. Some newer no-neutral dimmers (ZW3012) use the tap sequence, and the Z-Wave Alliance "
            "listing for the 58433 says to hold the bottom button for 10 seconds, so check the model's manual.",
        ),
        "firmware": A(
            "Z-Wave Plus (500-series) and 700-series models can be updated over the air from the controller. "
            "Jasco posts tested files in its GitHub repository, sorted by brand, ZW number and product "
            "number, and supplies them to the Z-Wave JS update service. Classic non-Plus models (12xxx, "
            "45xxx) cannot be updated.",
            "https://byjasco.com/pages/connected-home-firmware-downloads",
            "Jasco warns that \"Downloading and applying the wrong firmware can cause irreperable damage to "
            "your device\", that it voids the warranty, and that it \"does not offer support on flashing "
            "firmware\". Its FAQ says only Z-Wave Plus devices \"support wireless upgrades\". Some hubs "
            "offer no OTA updates. Hubitat users report updates that fail or factory-reset the switch.",
        ),
    },
    "problems": [
        {
            "title": "The hub does not show the light turned on or off at the wall",
            "signs": (
                "Pressing the paddle works the light, but the app keeps the old state until it is refreshed; "
                "a sniffer shows no Switch Binary or Multilevel Report from the switch after a local press, "
                "only the reply to a Get."
            ),
            "causes": [
                "Classic GE models (model numbers starting with 12, such as 12722 and 12724) have no instant "
                "status. They do not send a report when pressed at the wall.",
                "On 500- and 700-series models, the Lifeline association (group 1) is missing or points at "
                "the wrong node, so reports go nowhere.",
                "A weak link drops the report when the switch is far from the hub.",
            ],
            "fixes": [
                "For 12xxx models, poll the state or refresh it from an automation (Z-Wave JS "
                "refresh_value). Keep polling light, since it can flood the network.",
                "Replace classic 12xxx switches with 14xxx or newer models, which report on their own.",
                "On Plus models, check that association group 1 holds the hub's node ID, then re-interview.",
            ],
            "kb": ["get-acked-but-no-report", "lifeline-association-missing", "polling-storm"],
            "src": [
                "https://community.home-assistant.io/t/"
                "z-wave-js-12722-zw4005-by-ge-jasco-not-updating-state/327238",
                "https://www.home-assistant.io/integrations/zwave_js/",
                "https://byjasco.com/cdn/shop/files/14293_QSG_v3.pdf",
            ],
        },
        {
            "title": "LED bulbs flicker, strobe or buzz on a Jasco dimmer",
            "signs": (
                "The light flickers at low levels or at one spot in the dimming range, or "
                "hums; the radio traffic looks normal."
            ),
            "causes": [
                "Mismatch between the bulb's driver and the dimmer. Jasco's ZW3012 manual says \"Not all LED "
                "bulbs behave the same across dimmer brands, which can cause flickering or strobing.\"",
                "Load is too small or too large for the dimmer (the ZW3012 needs 2W minimum and allows 300W "
                "of CFL/LED).",
                "A firmware bug: Hubitat users tied flicker on Enbrighten, UltraPro and Honeywell dimmers to "
                "firmware 5.54 and said 5.53 or 5.55 fixed it.",
            ],
            "fixes": [
                "Use dimmable LED bulbs and try a different brand.",
                "On the ZW3012, raise the minimum level (\"OFF four times, then ON once\") or lower the "
                "maximum level (\"ON four times, then OFF once\") and adjust with the rocker.",
                "If the dimmer runs firmware 5.54, apply the firmware file for that exact model from Jasco's "
                "repository, then power-cycle the switch.",
                "Use a switch, not a dimmer, for non-dimmable loads.",
            ],
            "kb": ["ota-firmware-update-failure"],
            "src": [
                "https://www.homecontrols.com/blogs/product-manuals-documentation/"
                "enbrighten-zw3012-52252-in-wall-no-neutral-smart-dimmer-instruction-manual",
                "https://community.hubitat.com/t/ge-enbrighten-jasco-honeywell-ultrapro-dimmer-flicker/129059",
            ],
        },
        {
            "title": "Switch works by hand but will not join the hub",
            "signs": (
                "The light works at the wall, but the controller finds nothing or the add stops part way; a "
                "sniffer shows no Node Info frame, or for 700-series models an S2 key exchange that ends early."
            ),
            "causes": [
                "The switch still belongs to an old network.",
                "The press came before the controller was in add mode, or the switch is too far from it.",
                "On 700-series models, the S2 PIN was wrong or the controller does not support S2.",
            ],
            "fixes": [
                "Run an exclusion first (controller in remove mode, press the rocker), then add again.",
                "Jasco's FAQ says to \"toggle the switch up and down rapidly\" while the hub searches.",
                "Reset the switch (tap sequence or air-gap method for your model) and try again.",
                "For S2, enter the 5-digit PIN from the box or the switch label, or use SmartStart with the "
                "QR code.",
            ],
            "kb": [
                "inclusion-no-device-found",
                "node-included-twice-or-by-other-controller",
                "s2-bootstrap-failure",
                "smartstart-inclusion-failure",
            ],
            "src": [
                "https://byjasco.com/pages/z-wave-faq",
                "https://enbrightenme.com/cdn/shop/files/58433_Quick_Start_Guide.pdf",
            ],
        },
        {
            "title": "3-way or add-on switch does nothing, or only turns the light one way",
            "signs": (
                "The main switch works but the second location does not, works only on or only off, or the "
                "main switch gets no power; nothing about it shows on the Z-Wave network."
            ),
            "causes": [
                "The add-on does not match the primary switch. Jasco add-ons work only with a Jasco primary.",
                "A standard (dumb) 3-way switch was left in place. Classic and 500-series primaries need a "
                "Jasco add-on. 700-series primaries ship in add-on mode.",
                "Wiring copied from the old 3-way layout. The traveler only carries a signal to the primary; "
                "line on the traveler can damage the switch.",
                "The primary is in the box without line (power), or there is no neutral at the primary.",
            ],
            "fixes": [
                "Buy the add-on model listed in the primary switch's manual.",
                "Wire the primary with line, load and neutral first and get it working with the traveler "
                "disconnected, then add the add-on.",
                "On 700-series models used with a standard 3-way switch: \"Pull out the air gap switch\", "
                "then \"While pressing the top paddle, push in the air gap switch\" until the LED flashes "
                "yellow three times.",
                "Turn off the breaker and check wires with a tester; call an electrician if the wiring is "
                "unclear.",
            ],
            "src": [
                "https://enbrightenme.com/cdn/shop/files/58433_Quick_Start_Guide.pdf",
                "https://byjasco.com/pages/z-wave-faq",
                "https://community.smartthings.com/t/faq-ge-3-way-wiring/74962",
                "https://community.smartthings.com/t/tried-installing-ge-14291-after-12722-stopped-working-help/"
                "178119",
            ],
        },
        {
            "title": "Switch keeps dropping off the network or shows as dead",
            "signs": (
                "The app marks the switch dead or commands fail, while the paddle may still work the light; "
                "a sniffer shows frames to the node with no ACK, or repeated retries and route changes."
            ),
            "causes": [
                "Weak link: distance, walls, appliances and no repeater between the switch and the hub.",
                "The switch is failing. Users report some Jasco switches dying after a few years, first losing "
                "the radio and later local control.",
                "Classic (non-Plus) models lack Z-Wave Plus routing features such as explorer frames, which "
                "the 700-series Z-Wave Alliance listing shows; old routes can go stale after devices move.",
            ],
            "fixes": [
                "Power-cycle the switch by pulling the air-gap tab out and pushing it back in, or flip the "
                "breaker.",
                "Run a network repair (heal), or add a mains-powered repeater between the switch and the hub.",
                "If it keeps failing, exclude it and replace it; Jasco support has replaced failed units "
                "under warranty.",
                "If the switch can no longer be reached, remove it from the hub as a failed node before "
                "adding a replacement.",
            ],
            "kb": [
                "marginal-link-low-power-margin",
                "route-through-dead-repeater",
                "too-few-neighbors-no-redundancy",
                "ghost-failed-node",
            ],
            "src": [
                "https://community.home-assistant.io/t/ge-jasco-z-wave-switches-dying/50220",
                "https://community.smartthings.com/t/ge-jasco-zwave-switch-problems/36257",
                "https://products.z-wavealliance.org/z-wave-product/"
                "enbrighten-z-wave-plus-in-wall-smart-switch-white-and-light-almond-paddles-700s-2",
            ],
        },
        {
            "title": "Lock or far device is unreliable when it routes through an older GE switch",
            "signs": (
                "A lock near an older GE switch misses about half its commands and works on the second try; "
                "a sniffer would show wake-up beams or routed frames failing at the repeater hop."
            ),
            "causes": [
                "Locks need a beaming-capable repeater nearby. Users could not confirm that older non-Plus "
                "GE switches beam reliably.",
                "Too few working repeaters between the lock and the hub.",
            ],
            "fixes": [
                "Add a known beaming repeater or newer Z-Wave Plus switch within 10 to 15 feet of the lock.",
                "Check the switch's Z-Wave Alliance listing for beaming and explorer-frame support.",
                "Run a network repair after adding or replacing repeaters.",
            ],
            "kb": ["flirs-beam-failure", "route-through-dead-repeater"],
            "src": [
                "https://community.smartthings.com/t/smartthings-and-schlage-connect-lock/93764",
            ],
        },
        {
            "title": "Firmware update fails or leaves the switch reset",
            "signs": (
                "The OTA transfer stops or reports failure, the version does not change, or the switch comes "
                "back factory-reset and must be added again."
            ),
            "causes": [
                "Classic 12xxx/45xxx models cannot be updated at all.",
                "Wrong file for the model; Jasco files are sorted by brand, ZW number and product number.",
                "Weak link during the transfer, or a hub that does not offer OTA updates.",
            ],
            "fixes": [
                "Match the brand, ZW number and product number printed on the switch to the firmware folder.",
                "Run the update with the switch close to the hub and a strong link.",
                "Power-cycle the switch afterward. If it reset, include it again and re-link automations.",
                "Report bad files through the Jasco firmware repository's bug report.",
            ],
            "kb": ["ota-firmware-update-failure", "device-reset-locally"],
            "src": [
                "https://byjasco.com/pages/connected-home-firmware-downloads",
                "https://github.com/jascoproducts/firmware",
                "https://community.hubitat.com/t/ge-enbrighten-jasco-honeywell-ultrapro-dimmer-flicker/129059",
            ],
        },
    ],
    "docs": [
        {"label": "Jasco Z-Wave FAQ", "url": "https://byjasco.com/pages/z-wave-faq"},
        {"label": "Jasco connected home firmware downloads",
         "url": "https://byjasco.com/pages/connected-home-firmware-downloads"},
        {"label": "Jasco firmware repository (GitHub)", "url": "https://github.com/jascoproducts/firmware"},
        {"label": "Enbrighten 58433 / ZWA4011 quick start guide (700-series)",
         "url": "https://enbrightenme.com/cdn/shop/files/58433_Quick_Start_Guide.pdf"},
        {"label": "Jasco 14293 toggle switch manual (500-series)",
         "url": "https://byjasco.com/cdn/shop/files/14293_QSG_v3.pdf"},
        {"label": "Enbrighten ZW3012 no-neutral dimmer manual (dealer copy, HomeControls)",
         "url": "https://www.homecontrols.com/blogs/product-manuals-documentation/"
                "enbrighten-zw3012-52252-in-wall-no-neutral-smart-dimmer-instruction-manual"},
        {"label": "Z-Wave Alliance listing: Enbrighten 58433 700S",
         "url": "https://products.z-wavealliance.org/z-wave-product/"
                "enbrighten-z-wave-plus-in-wall-smart-switch-white-and-light-almond-paddles-700s-2"},
        {"label": "Enroll, delete or reset Enbrighten 76591 (Alarm.com)",
         "url": "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Lighting_and_Appliance_Control/"
                "Jasco_and_GE/Jasco_Enbrighten_Z-Wave_In-Wall_Paddle_Switch_(76591)/"
                "Enroll%2C_delete%2C_or_reset_a_Jasco_Enbrighten_Z-Wave_In-Wall_Paddle_Switch_(76591)"},
        {"label": "Z-Wave JS device configs for Jasco (0x0063)",
         "url": "https://github.com/zwave-js/zwave-js/tree/master/packages/config/config/devices/0x0063"},
        {"label": "12722 not updating state (Home Assistant forum)",
         "url": "https://community.home-assistant.io/t/z-wave-js-12722-zw4005-by-ge-jasco-not-updating-state/327238"},
        {"label": "Jasco dimmer flicker and firmware (Hubitat forum)",
         "url": "https://community.hubitat.com/t/ge-enbrighten-jasco-honeywell-ultrapro-dimmer-flicker/129059"},
        {"label": "GE 3-way wiring FAQ (SmartThings forum)",
         "url": "https://community.smartthings.com/t/faq-ge-3-way-wiring/74962"},
    ],
},
{
    "id": "zooz",
    "name": "Zooz ZEN71/72/76/77 switches and dimmers, ZEN30 double switch, ZEN51/52 relays, ZSE40/ZSE44 sensors",
    "kind": "switch",
    "manufacturer_ids": [0x027A],
    "summary": (
        "Zooz makes in-wall paddle switches and dimmers, small in-box relays and battery sensors, sold in 500, "
        "700 and 800LR (Long Range) generations. The most common trouble is a device that will not add to the "
        "hub, followed by multi-tap scenes or status updates that never reach the hub, and sensors that eat "
        "batteries because they report too often."
    ),
    "quirks": [
        "Zooz says 800 series devices will not exclude before they have been included. On 700 series and "
        "earlier you can run exclusion on a new device; on 800LR you factory reset it instead.",
        "Z-Wave Long Range can only be added through SmartStart (scanning the QR code). Long Range devices talk "
        "straight to the hub: they do not repeat, and direct association between devices is not possible. "
        "Moving a device between mesh and Long Range needs exclusion and re-inclusion.",
        "Long Range nodes get node IDs from 256 up; mesh nodes use 2-255 (at most 232 of them). A node ID of "
        "256 or more tells you the device joined as Long Range.",
        "Scene control (multi-tap) is off by default on the ZEN77: Parameter 13 \"Scene Control\" defaults to "
        "0 (disabled). Parameter numbers differ between Zooz models, so check the advanced settings article "
        "for your exact model.",
        "Zooz publishes OTA files per model and per hardware version (for example ZEN77 10.40, 2.30, 3.20, "
        "4.80, 5.10). 500 series files are .otz or .hex; 700 and 800 series files are .gbl. The wrong file can "
        "make the device unusable, and Zooz does not cover bricked devices under warranty.",
        "Battery sensors (ZSE40, ZSE44) sleep and wake every 12 hours by default. Zooz says a long wake-up "
        "interval does not change how often they report; it only delays setting changes from the hub.",
        "The ZEN51 and ZEN52 Long Range versions report a different product type (0x0904) than the regular "
        "versions (0x0104), per the Z-Wave JS device files.",
    ],
    "steps": {
        "include": A(
            "Switches and dimmers (ZEN71/72/76/77, ZEN30): put the hub in add mode, then tap the upper paddle "
            "3 times quickly. On the ZEN77 the LED blinks blue, then turns green for 3 seconds on success or red "
            "for 3 seconds on failure. Relays (ZEN51/52): \"TAP THE Z-WAVE BUTTON 3 TIMES QUICKLY\", or scan "
            "the QR code / enter the 5-digit PIN for SmartStart. ZSE44: \"click the Z-Wave button 3 times as "
            "quickly as possible\". ZSE40 700: click the Z-Wave button once, or scan the QR code or enter the "
            "PIN under the back cover for SmartStart.",
            "https://github.com/zwave-js/zwave-js/blob/master/packages/config/config/devices/0x027a/zen77.json",
            "If 3 taps do not register, Zooz says to tap 4-5 times as quickly as possible. 500 series models "
            "join with S0 or no security; 700 and 800 series support S2 and SmartStart. Long Range needs "
            "SmartStart (QR code) and a hub that supports it. Older ZSE40 firmware is listed in Z-Wave JS as "
            "\"Click the Z-Wave button with a paperclip twice\", unlike the 700 manual's single click. Add "
            "sensors from where they will be mounted so the hub picks the right route.",
        ),
        "exclude": A(
            "Put the hub in exclusion (remove) mode. Switches and dimmers: tap the lower paddle 3 times quickly "
            "(ZEN77 LED turns green for 3 seconds). Relays: click the Z-Wave button 3 times quickly, or toggle "
            "the connected wall switch \"up-down, up-down, up-down\" very quickly. ZSE44: click the Z-Wave "
            "button 3 times as quickly as possible. ZSE40 700: \"Click the Z-Wave button with a paperclip "
            "once (it will blink green).\"",
            "https://www.support.getzooz.com/kb/article/1048-can-t-add-my-zen77-dimmer-to-my-z-wave-system",
            "Alarm.com's ZEN77 800LR page says to press the top paddle 3 times for delete; Zooz and Z-Wave JS "
            "say the lower paddle. On 800 series devices that were never included, exclusion does nothing, so "
            "factory reset instead. On Home Assistant, Zooz uses \"Remove foreign device\" to exclude a device "
            "left over from another hub.",
        ),
        "reset": A(
            "ZEN71/72/76/77: press and hold the lower paddle for 10 seconds until the LED starts blinking, "
            "release, then immediately tap the lower paddle 5 times (LED flashes blue 3 times, then red for 3 "
            "seconds). ZEN30: hold the lower paddle at least 15 seconds until the LEDs flash, release, then "
            "immediately hold the upper paddle at least 15 seconds. ZEN51: press the Z-Wave button once, then "
            "right away press and hold it for 15 seconds (solid red for 3 seconds). ZEN52: click the Z-Wave "
            "button twice and hold on the second click for 10-15 seconds. ZSE44: click the Z-Wave button twice "
            "and hold it the third time for 10 seconds, then click it twice more (LED flashes 3 times). "
            "ZSE40 700: remove the back cover to trigger the tamper switch, then press the Z-Wave button with a "
            "paperclip 10 times quickly (within 10 seconds).",
            "https://www.support.getzooz.com/kb/article/1025-how-do-i-perform-hard-reset-on-my-zen77-dimmer",
            "A reset erases all custom settings and recorded activity. It does not tell the hub, so the old node "
            "stays behind as a dead entry unless you remove it. Zooz's printed ZEN52 manual gives a slightly "
            "different sequence (one click, then hold 15 seconds) from its knowledge base article.",
        ),
        "firmware": A(
            "Yes. Download the file for your exact model, hardware version and region from \"Zooz OTA Firmware "
            "Files\", unzip it, and send it from the hub. In Home Assistant: open the device, click \"CONFIGURE "
            "DEVICE\", then \"Update Device Firmware\". Hubitat, HomeSeer and Z-Box have their own guides; other "
            "hubs need a USB stick and Silicon Labs' Z-Wave PC Controller.",
            "https://www.support.getzooz.com/kb/article/253/",
            "Updates take 5-15 minutes; move the hub closer if it runs longer. Wake battery sensors manually "
            "after starting the update (ZSE44: click the Z-Wave button 4 times). For a wrong fragment size "
            "error, set fragment size to 20. Zooz says you may need to include without security for the update "
            "to work, and to exclude and re-include the device afterward.",
        ),
    },
    "problems": [
        {
            "title": "Switch, relay or sensor will not add to the hub",
            "signs": (
                "The hub's add mode times out or fails partway; a sniffer often shows no Node Information "
                "Frame from the device, or an S2 key exchange that stops."
            ),
            "causes": [
                "The device is still paired to an old hub, or was reset without being removed.",
                "800 series devices ignore exclusion if they were never included, so the usual \"exclude first\" "
                "step does nothing.",
                "Taps were too slow to register.",
                "Range or interference, often from a metal switch box.",
                "A stale SmartStart provisioning entry for the device on the hub.",
            ],
            "fixes": [
                "Exclude the device first (lower paddle 3 times, or Z-Wave button 3 times). On 800LR, factory "
                "reset it instead.",
                "Retry inclusion tapping the upper paddle or button 4-5 times as quickly as possible, or add it "
                "in non-secure mode.",
                "Move the hub, or a handheld secondary controller, within direct range. Add a mains-powered "
                "repeater between the device and hub and heal the network.",
                "In Home Assistant, remove the device from Provisioned Devices (by its DSK), factory reset it, "
                "cut power at the breaker, then follow the inclusion steps.",
            ],
            "kb": ["inclusion-no-device-found", "inclusion-fails-at-controller", "s2-bootstrap-failure",
                   "node-included-twice-or-by-other-controller", "metal-enclosure-attenuation",
                   "smartstart-inclusion-failure"],
            "src": [
                "https://www.support.getzooz.com/kb/article/1048-can-t-add-my-zen77-dimmer-to-my-z-wave-system",
                "https://www.support.getzooz.com/kb/article/1069-can-t-add-my-zen77-s2-dimmer-to-home-assistant",
                "https://www.support.getzooz.com/kb/article/950-can-t-add-my-zen52-double-relay-to-my-z-wave-system",
            ],
        },
        {
            "title": "Double-tap, triple-tap or hold scenes do nothing in the hub",
            "signs": (
                "Single taps work but multi-tap automations never fire; no Central Scene Notification appears "
                "in the hub log, or it arrives as a raw number (\"4\") instead of \"KeyPressed3x\"."
            ),
            "causes": [
                "Scene control is disabled by default (ZEN77 Parameter 13 = 0).",
                "Multi-tap is turned off (ZEN77 Parameter 35 = 1).",
                "The hub's interview of the Central Scene command class was incomplete, so it cannot name the "
                "key presses.",
                "The hub's app hides the multi-tap choices until you build an automation (SmartThings).",
            ],
            "fixes": [
                "Set Parameter 13 \"Scene Control\" to 1 on the ZEN77 (check your model's advanced settings "
                "article; numbers differ by model). Leave Parameter 35 at 0.",
                "Update to the latest firmware; Zooz says some settings only exist in later versions.",
                "Re-interview the device, or exclude and re-include it. A Home Assistant user fixed raw \"4\" "
                "values this way.",
                "In SmartThings, create an automation; the x2, x3 and x4 choices appear there.",
            ],
            "kb": ["interview-incomplete-commandclasses"],
            "src": [
                "https://www.support.getzooz.com/kb/article/550-zen77-s2-dimmer-advanced-settings",
                "https://community.home-assistant.io/t/zen-77-scene-trigger/740976",
                "https://community.smartthings.com/t/zooz-zen77-not-seeing-the-toggle-up-x2-x3-x4-options/253176",
            ],
        },
        {
            "title": "Hub shows the wrong on/off state after a tap or a command",
            "signs": (
                "The light changes but the hub tile stays the same until you press Refresh; a sniffer shows the "
                "Set is acknowledged but no Binary Switch or Multilevel Report follows."
            ),
            "causes": [
                "Zooz firmware 3.70 (July 2025) \"optimized Z-Wave reporting behavior\" and stopped sending "
                "extra reports after a Set from the hub. Hubs that relied on those reports show stale state.",
                "Parameter 7 (Association Reports) changed from its default of 15, so some taps no longer "
                "report.",
                "Smart bulb mode (Parameter 15) on a ZEN77 800LR: one Home Assistant user saw paddle taps "
                "change the LED but send nothing. No cause was found.",
                "The hub's Lifeline association is missing.",
            ],
            "fixes": [
                "On Hubitat, a patch to the community Zooz ZEN Switch driver sends a Get right after each Set; "
                "this fixed it for one user.",
                "Check Parameter 7 is 15 and the Lifeline (group 1) points at the hub.",
                "Re-interview the device; if that fails, exclude, factory reset and re-include it.",
            ],
            "kb": ["get-acked-but-no-report", "lifeline-association-missing"],
            "src": [
                "https://community.hubitat.com/t/zooz-zen71-switch-state-not-updating/164498",
                "https://community.home-assistant.io/t/zooz-zen77-800lr-dimmer-switch-button-presses-dont-show-up-"
                "in-home-assitant-but-will-receive-commands/665730",
                "https://www.support.getzooz.com/kb/article/550-zen77-s2-dimmer-advanced-settings",
            ],
        },
        {
            "title": "ZSE44 or ZSE40 sensor drains its battery in weeks",
            "signs": (
                "Battery level falls far faster than the 12-14 months Zooz expects for the ZSE44; the hub log "
                "shows temperature or humidity reports every few seconds or minutes."
            ),
            "causes": [
                "Thresholds or intervals set too tight. ZSE44: Parameter 3 temperature threshold (default 20 = "
                "2 degrees), Parameter 4 humidity threshold (default 10%), Parameters 16/17 report intervals "
                "(default 240 minutes).",
                "Both threshold and time-interval reporting turned on at once.",
                "Wake-up interval shortened from the 12-hour default.",
                "ZSE40: short motion trigger interval (Parameter 5, default 15 seconds) or LED mode 2 "
                "(Parameter 7), which the manual says decrease battery life.",
                "Weak mesh signal causing retries, or a sensor moved after pairing.",
                "Rechargeable or Duracell cells; S2 security in rare cases.",
            ],
            "fixes": [
                "Use one reporting method: a 30-60 minute interval, or a 1-2 degree F / 3-5% RH threshold.",
                "Put the wake-up interval back to 12 hours.",
                "Use Long Range if the hub supports it, or add mains-powered repeaters. Re-include or heal "
                "after moving the sensor.",
                "Fit a fresh non-rechargeable cell (CR2450 for ZSE44, CR123A for ZSE40). Zooz names Energizer, "
                "Panasonic and Maxell.",
                "If the hub lets you choose, Zooz suggests including the sensor without security.",
            ],
            "kb": ["battery-drain-from-reporting-or-retries", "marginal-link-low-power-margin", "battery-low"],
            "src": [
                "https://www.support.getzooz.com/kb/article/2217-rapid-battery-drain-on-my-zse44-temperature-"
                "humidity-sensor",
                "https://www.support.getzooz.com/kb/article/1403-zse44-temp-humidity-xs-sensor-faqs",
                "https://doc.eedomus.com/files/zooz-zse40-700-manual-online.pdf",
            ],
        },
        {
            "title": "ZSE44 battery level jumps around or sticks at 1%",
            "signs": (
                "Battery reads 100, then 5, then 50, or shows 1% for months while the sensor keeps working."
            ),
            "causes": [
                "Early ZSE44 firmware (1.1) reported battery on a percentage threshold; firmware 1.20 changed "
                "this to a 12-hour time interval only.",
                "Cold locations lower coin-cell voltage.",
                "Readings swing during setup and testing; Zooz says to wait a day or two before judging.",
            ],
            "fixes": [
                "Update to firmware 1.20 or later (current files are 1.30, and 2.40 for 800LR hardware).",
                "Move the sensor out of extreme cold, or accept low readings there.",
                "On Hubitat, use Zooz's driver or the community \"Zooz Sensors Advanced\" driver.",
            ],
            "kb": ["battery-low"],
            "src": [
                "https://community.hubitat.com/t/zse44-reporting-going-nuts/106589",
                "https://www.support.getzooz.com/kb/article/1403-zse44-temp-humidity-xs-sensor-faqs",
            ],
        },
        {
            "title": "ZSE40 joins but shows no values or setting changes never apply",
            "signs": (
                "The sensor appears in the hub but temperature, light or motion values are blank, or new "
                "settings stay pending; the interview stops when the sensor goes back to sleep."
            ),
            "causes": [
                "The sensor fell asleep before the hub finished configuring it.",
                "The battery cover was not closed tightly when it was added.",
                "Settings only reach the sensor when it wakes (every 12 hours by default).",
            ],
            "fixes": [
                "After it joins, click the Z-Wave button once every 15 seconds for 2 minutes to keep it awake.",
                "Close the battery cover tightly before adding.",
                "After changing settings, press the Z-Wave button once to wake it (LED flashes once). For the "
                "ZSE44, click the Z-Wave button 4 times.",
            ],
            "kb": ["interview-stuck-early-stage", "interview-incomplete-commandclasses"],
            "src": [
                "https://doc.eedomus.com/files/zooz-zse40-700-manual-online.pdf",
                "https://cdn.shopify.com/s/files/1/0218/7704/files/zooz-z-wave-long-range-800-series-temperature-"
                "humidity-xs-sensor-zse44-800lr-manual.pdf",
            ],
        },
        {
            "title": "800LR device joined as mesh, not Long Range, or Long Range features missing",
            "signs": (
                "The node ID is below 256 instead of 256 or higher, or associations to other devices do nothing "
                "on a Long Range node."
            ),
            "causes": [
                "Long Range can only be added by SmartStart. Classic tap inclusion always joins as mesh.",
                "The hub software or USB stick does not support Long Range, so the device falls back to mesh.",
                "Older QR codes use the non-LR format.",
                "Long Range is direct to the hub: no repeating and no device-to-device association.",
            ],
            "fixes": [
                "Exclude the device, then add it by scanning its QR code and choosing Long Range. Zooz says Home "
                "Assistant can switch the boot mode to Long Range after scanning an older QR code.",
                "Confirm both hub and device support Long Range.",
                "Keep devices that need direct association (for example, to control another switch) on mesh.",
            ],
            "kb": ["smartstart-inclusion-failure"],
            "src": [
                "https://www.support.getzooz.com/kb/article/1768-z-wave-long-range-faq-s",
            ],
        },
        {
            "title": "Firmware update fails or the device misbehaves afterwards",
            "signs": (
                "The update stalls, the hub reports a fragment size error or \"did not respond to firmware "
                "metadata request\", or the device acts oddly after a successful update."
            ),
            "causes": [
                "The file does not match the model, hardware version or region.",
                "Hub too far from the device.",
                "A battery sensor fell asleep during the transfer.",
                "Secure inclusion getting in the way on some hubs.",
            ],
            "fixes": [
                "Check the label and current version, and use the matching file (some files are \"800LR hardware "
                "version only\").",
                "Set fragment size to 20 for a wrong fragment size error.",
                "Move the hub closer; wake battery sensors after starting the update.",
                "If needed, include without security for the update.",
                "Afterwards, exclude and re-include. If it misbehaves, exclude, factory reset and re-include.",
            ],
            "kb": ["ota-firmware-update-failure"],
            "src": [
                "https://www.support.getzooz.com/kb/article/253/",
                "https://www.support.getzooz.com/kb/article/1158",
                "https://community.hubitat.com/t/zse44-reporting-going-nuts/106589",
            ],
        },
    ],
    "docs": [
        {"label": "Zooz: Can't add my ZEN77 dimmer to my Z-Wave system",
         "url": "https://www.support.getzooz.com/kb/article/1048-can-t-add-my-zen77-dimmer-to-my-z-wave-system"},
        {"label": "Zooz: Can't add my ZEN77 S2 dimmer to Home Assistant",
         "url": "https://www.support.getzooz.com/kb/article/1069-can-t-add-my-zen77-s2-dimmer-to-home-assistant"},
        {"label": "Zooz: ZEN77 hard reset",
         "url": "https://www.support.getzooz.com/kb/article/1025-how-do-i-perform-hard-reset-on-my-zen77-dimmer"},
        {"label": "Zooz: ZEN77 S2 dimmer advanced settings",
         "url": "https://www.support.getzooz.com/kb/article/550-zen77-s2-dimmer-advanced-settings"},
        {"label": "Zooz: ZEN30 double switch hard reset",
         "url": "https://www.support.getzooz.com/kb/article/336-how-do-i-perform-hard-reset-on-my-zen30-"
                "double-switch/"},
        {"label": "Zooz: ZEN51 dry contact relay hard reset",
         "url": "https://www.support.getzooz.com/kb/article/938-how-do-i-perform-hard-reset-on-my-zen51-"
                "dry-contact-relay"},
        {"label": "Zooz: ZEN52 double relay hard reset",
         "url": "https://www.support.getzooz.com/kb/article/953-how-do-i-perform-hard-reset-on-my-zen52-double-relay"},
        {"label": "Zooz: Can't add my ZEN52 double relay",
         "url": "https://www.support.getzooz.com/kb/article/950-can-t-add-my-zen52-double-relay-to-my-z-wave-system"},
        {"label": "Zooz: ZSE44 FAQs",
         "url": "https://www.support.getzooz.com/kb/article/1403-zse44-temp-humidity-xs-sensor-faqs"},
        {"label": "Zooz: Rapid battery drain on ZSE44",
         "url": "https://www.support.getzooz.com/kb/article/2217-rapid-battery-drain-on-my-zse44-temperature-"
                "humidity-sensor"},
        {"label": "Zooz: ZSE44 800LR user manual (PDF)",
         "url": "https://cdn.shopify.com/s/files/1/0218/7704/files/zooz-z-wave-long-range-800-series-temperature-"
                "humidity-xs-sensor-zse44-800lr-manual.pdf"},
        {"label": "Zooz ZSE40 700 user manual (third-party copy, eedomus)",
         "url": "https://doc.eedomus.com/files/zooz-zse40-700-manual-online.pdf"},
        {"label": "Zooz: Z-Wave Long Range FAQs",
         "url": "https://www.support.getzooz.com/kb/article/1768-z-wave-long-range-faq-s"},
        {"label": "Zooz: How to perform an OTA firmware update on Zooz devices",
         "url": "https://www.support.getzooz.com/kb/article/253/"},
        {"label": "Zooz: OTA firmware update in Home Assistant",
         "url": "https://www.support.getzooz.com/kb/article/1126-how-to-perform-an-ota-firmware-update-on-zooz-"
                "devices-in-home-assistant/"},
        {"label": "Zooz: OTA firmware files",
         "url": "https://www.support.getzooz.com/kb/article/1158"},
        {"label": "Enroll, delete, or reset a Zooz ZEN77 800LR (Alarm.com dealer site)",
         "url": "https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Lighting_and_Appliance_Control/"
                "Zooz/Zooz_ZEN77_800LR_In-Wall_Switch/Enroll%2C_delete%2C_or_reset_a_Zooz_ZEN77_800LR_In-Wall_Switch"},
        {"label": "Z-Wave JS device files for Zooz (0x027a) (GitHub, Z-Wave JS)",
         "url": "https://github.com/zwave-js/zwave-js/tree/master/packages/config/config/devices/0x027a"},
        {"label": "ZEN77 scene trigger fixed by re-interview (Home Assistant forum)",
         "url": "https://community.home-assistant.io/t/zen-77-scene-trigger/740976"},
        {"label": "ZEN71 800LR state not updating after firmware 3.70 (Hubitat forum)",
         "url": "https://community.hubitat.com/t/zooz-zen71-switch-state-not-updating/164498"},
        {"label": "ZEN77 800LR paddle presses not reported (Home Assistant forum)",
         "url": "https://community.home-assistant.io/t/zooz-zen77-800lr-dimmer-switch-button-presses-dont-show-up-"
                "in-home-assitant-but-will-receive-commands/665730"},
        {"label": "ZSE44 erratic battery and reporting (Hubitat forum)",
         "url": "https://community.hubitat.com/t/zse44-reporting-going-nuts/106589"},
        {"label": "ZEN77 multi-tap options missing (SmartThings forum)",
         "url": "https://community.smartthings.com/t/zooz-zen77-not-seeing-the-toggle-up-x2-x3-x4-options/253176"},
    ],
},
]


def device(did: str | None) -> dict | None:
    return next((d for d in DEVICES if d["id"] == did), None)


def catalogue() -> dict:
    return {"steps": STEPS, "kinds": KINDS, "devices": DEVICES}
