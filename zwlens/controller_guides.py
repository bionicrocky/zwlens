"""Controller guide data.

Menu labels are quoted from the documentation linked on each item. Where the maker documents
nothing, the text says so rather than guessing. Where a maker's own manual was not reachable, a copy
hosted by a dealer (Surety, Alarm Grid), a retailer or the Z-Wave Alliance product database was used,
and the note or docs label says so.
"""

HA = "https://www.home-assistant.io/integrations/zwave_js"
ZUI = "https://zwave-js.github.io/zwave-js-ui/"
HE_ZD = "https://docs2.hubitat.com/en/user-interface/settings/zwave-details"
HE_ADD = "https://docs2.hubitat.com/en/user-interface/devices/add-device"
HE_MESH = "https://docs2.hubitat.com/en/how-to/build-a-solid-zwave-mesh"
HE_BK = "https://docs2.hubitat.com/en/user-interface/settings/backup-and-restore"
ST_HUB = "https://support.smartthings.com/hc/en-us/articles/360052390151-SmartThings-Enabled-Hubs"
ST_ZW = "https://support.smartthings.com/hc/en-us/articles/204392790-Z-Wave-General-Info"
AEO_1 = "https://aeotec.freshdesk.com/support/solutions/articles/6000240427-installing-removing-devices-smart-home-hub"
AEO_2 = "https://aeotec.freshdesk.com/support/solutions/articles/6000245641-aeotec-smart-home-hub-troubleshooting"
IQ4 = "https://suretyhome.com/wp-content/uploads/IQ-Panel-4-Installation-Manual.pdf"
IQ2 = "https://suretyhome.com/wp-content/uploads/IQ-Panel-2-Plus-Installation-Manual.pdf"
GC3 = "https://www.alarmgrid.com/documents/2gig-gc3-gc3e-installation-and-program-guide-rev-b"
EDGE_I = "https://www.alarmgrid.com/documents/2gig-edge-install-guide-dated-031921-rev-a"
EDGE_SH = "https://alarmgrid.com/documents/2gig-edge-smart-home-manual-dated-031921-rev-a"
SUR_2GIG = "https://support.suretyhome.com/t/how-to-add-remove-z-wave-device-and-run-a-network-rediscovery-with-2gig/9755"
ADC_SUPP = "https://products.z-wavealliance.org/wp-content/uploads/products/80621/Alarm.com-SupplementalZ-WaveDocumentationv6_24.pdf"
ADC_WIZ = "https://answers.alarm.com/Customer/Website_and_App/System_Management/System_Usage/Z-Wave_Troubleshooting_Wizard"
ADC_TS = ("https://answers.alarm.com/Partner/Installation_and_Troubleshooting/Z-Wave%C2%AE/"
          "General_Z-Wave%C2%AE_Information/Z-Wave_device_is_not_functioning_consistently")
SUR_SM = "https://support.suretyhome.com/t/surety-system-manager/30073"
SUR_REDISC = "https://support.suretyhome.com/t/z-wave-network-rediscovery/10588"
RING_ZWA = "https://products.z-wavealliance.org/wp-content/uploads/products/51273/Ring_Base_Station_-_Manual.pdf"
RING_OFF = "https://ring.com/support/articles/ove2l/fixing-offline-ring-alarm-or-z-wave-devices"
RING_SET = "https://ring.com/us/en/support/articles/2vv98/Set-Up-Manage-Alarm-Devices-Ring-App"

NONE = "Not documented by the maker."
QOLSYS_PATH = ("Swipe down > Settings > Advanced Settings > enter the installer or dealer code > Installation > "
               "Devices > Z-Wave Devices")


def A(how, src="", note=""):
    return {"how": how, "src": src, "note": note}


GUIDES = [
    {
        "id": "home-assistant", "name": "Home Assistant (Z-Wave JS / Z-Wave JS UI)",
        "summary": "The most open option: full access to routes, statistics, logs, device parameters and backups. "
                   "zwlens can also follow it live, or read its logs and Zniffer captures.",
        "quirks": [
            "Do not move the adapter around the house to include devices; include them where they will live.",
            "Rebuilding all routes generates a lot of traffic and should be used sparingly; prefer rebuilding one device.",
            "The radio region can only be changed on 700/800-series adapters.",
            "Polling should only be used as a last resort.",
        ],
        "actions": {
            "include": A("Settings > Connectivity > Z-Wave > Add device. For SmartStart choose Scan QR code. "
                         "In Z-Wave JS UI: Control Panel > + > Node Manager > Inclusion > Next.", HA,
                         "S2 devices ask for the PIN from the device label. Network keys must be set first."),
            "exclude": A("Device page > three-dot menu > Delete > Remove a working device. For a device from another "
                         "network: Settings > Connectivity > Z-Wave > Options > Remove foreign device > Remove > Start "
                         "exclusion. In Z-Wave JS UI: "
                         "Node Manager > Exclusion.", HA),
            "remove_failed": A("Device page > three-dot menu > Delete, and choose to remove it as a failed device. In "
                               "Z-Wave JS UI: Node Manager > Replace Failed Node or Remove Failed Node.", ZUI,
                               "Only works once the node is Dead, Asleep or Unknown and does not answer a ping."),
            "rebuild": A("One device: device page > Rebuild routes. Whole network: Settings > Connectivity > Z-Wave > Options > Discover and "
                         "assign new routes.", HA, "The device may be less responsive while its routes are rebuilt."),
            "routes": A("Z-Wave > Show map, and Statistics on the integration and device pages. In Z-Wave JS UI: the "
                        "Network Graph shows the priority, last working and next-to-last working routes; a node's "
                        "Diagnose button runs the Lifeline and Route health checks.", ZUI),
            "logs": A("Z-Wave integration > three-dot menu > Enable debug logging; disabling it downloads the log. In "
                      "Z-Wave JS UI: Settings > Z-Wave > Log enabled, Log To File, Log Level = Debug; the file is "
                      "zwavejs_<date>.log in store/logs. Load either into zwlens.", ZUI,
                      "For a full air capture, set up a second stick under Settings > Zniffer."),
            "config": A("Device page > Configure for parameters. Polling in Z-Wave JS UI: Settings > General > Device "
                        "values configuration > New value > Enable Poll.", HA),
            "firmware": A("Device page > Update > Begin firmware update, for device and adapter firmware. Backup: "
                          "Settings > Connectivity > Z-Wave > Download backup; restore with Restore from backup; move to a new stick with Migrate adapter.",
                          HA, "A 500-series stick needs SDK 6.61 or later before its backup can be migrated."),
        },
        "docs": [{"label": "Home Assistant Z-Wave", "url": HA}, {"label": "Z-Wave JS UI", "url": ZUI}],
    },
    {
        "id": "hubitat", "name": "Hubitat Elevation",
        "summary": "A local hub with a good diagnostics page (Settings > Z-Wave Details) showing routes, neighbours, "
                   "signal and error rates per node.",
        "quirks": [
            "Up to 232 devices and 4 hops. C-8 and C-8 Pro use an 800-series radio; C-5 and earlier have no S2.",
            "Local backups do not include the Z-Wave radio; only the cloud backup subscription does.",
            "A full network rebuild is very network-intensive, does not revive failed devices, and only repairs "
            "mains-powered nodes. Hubitat recommends rebuilding single routes instead.",
            "Force Remove can leave a ghost node behind; use it only as a last resort.",
            "Long Range needs SmartStart, a C-8 or newer, and the US region.",
        ],
        "actions": {
            "include": A("Devices > Add Device > Z-Wave > Start Z-Wave Inclusion. SmartStart (C-7 and later): choose "
                         "SmartStart > Scan QR > Add QR code.", HE_ADD, "Include one device at a time."),
            "exclude": A("Device page > Remove, then put the device in exclusion mode. For any device, including one "
                         "from another network: Settings > Z-Wave Details > Z-Wave exclude.", HE_ZD),
            "remove_failed": A("Settings > Z-Wave Details: find the node, press Refresh once or twice until Remove "
                               "appears, then Remove. Replace appears the same way and reuses the node ID.", HE_MESH,
                               "Ghosts are usually the most recently added node IDs."),
            "rebuild": A("One node: Settings > Z-Wave Details > Rebuild route in the Actions column. Whole network: "
                         "Rebuild network.", HE_ZD),
            "routes": A("Settings > Z-Wave Details shows per-node Stats (error rate, neighbours, response time, RSSI) "
                        "and Route (hops and speed). View device graph and View device topology draw the mesh.", HE_ZD,
                        "Long Range nodes have no neighbour or route statistics."),
            "logs": A("Settings > Z-Wave Details > View Logs shows live routing, signal and channel information.",
                      HE_ZD, "No log file export or Zniffer mode is documented; use a separate Zniffer stick with zwlens."),
            "config": A(NONE + " Parameters are normally on the device's own page, depending on its driver."),
            "firmware": A("The hub's radio: a Firmware update button appears on Z-Wave Details when one is available. "
                          "Devices: the Device firmware updater app > Start update.", HE_ZD,
                          "Back up the radio with the cloud backup subscription before major changes."),
        },
        "docs": [{"label": "Z-Wave Details", "url": HE_ZD}, {"label": "Build a solid Z-Wave mesh", "url": HE_MESH},
                 {"label": "Backup and restore", "url": HE_BK}],
    },
    {
        "id": "smartthings", "name": "SmartThings / Aeotec Smart Home Hub",
        "summary": "Simple to use but shows little: there is a network repair and an exclusion tool, and almost no "
                   "official routing or log information.",
        "quirks": [
            "No official way to see routes, signal or Z-Wave logs. A Zniffer stick with zwlens fills that gap.",
            "Community reports say the Advanced Web App (my.smartthings.com/advanced) shows a device's last route.",
            "Devices joined before the hub supported S2 stay on S0 until they are excluded and re-included.",
            "No Z-Wave network backup is documented; 'Replace Hub' moves devices to a new hub instead.",
            "SmartThings' Z-Wave help article is several years old, so some of its steps may be out of date.",
        ],
        "actions": {
            "include": A("Devices tab > Add (+) > Add device > select the brand and device > Start, then scan the QR "
                         "code or enter the first 5 digits of the DSK. Or use Scan for nearby devices.", ST_ZW),
            "exclude": A("Hub > More options (⋮) > Z-Wave utilities > Z-Wave Exclusion. This also works for devices "
                         "from another network. To delete one of your own devices: long-press it > Remove.", ST_HUB),
            "remove_failed": A("Long-press the device > Remove device, wait about 30 seconds, then Force Delete.", AEO_1,
                               "Only do this if the device no longer exists. A replace-failed-node function is not documented."),
            "rebuild": A("Hub > More options (⋮) > Z-Wave utilities > Repair Z-Wave network.", ST_HUB,
                         "Avoid using Z-Wave devices until 'Z-Wave network repair finished' appears. Whole network only."),
            "routes": A(NONE),
            "logs": A(NONE + " Developers can stream driver logs with the SmartThings CLI."),
            "config": A(NONE + " Settings appear on the device's page only if its driver exposes them."),
            "firmware": A("Hub firmware installs automatically (the LED blinks magenta while downloading).", AEO_2,
                          "No Z-Wave network backup is documented."),
        },
        "docs": [{"label": "SmartThings hubs", "url": ST_HUB}, {"label": "Z-Wave general info", "url": ST_ZW},
                 {"label": "Aeotec hub troubleshooting", "url": AEO_2}],
    },
    {
        "id": "qolsys", "name": "Qolsys IQ Panel 2 / 2+ / 4 (Alarm.com)",
        "summary": "An Alarm.com security panel with better built-in Z-Wave diagnostics than most: neighbour lists, "
                   "acknowledgement counters, a network map and a health test, all behind the installer menu.",
        "quirks": [
            "Z-Wave menus need the installer or dealer code. The manuals print the defaults (installer 1111, dealer "
            "2222); change them. The master code only works if the dealer enabled Z-Wave access for it.",
            "IQ Panel 4: Z-Wave Plus 700/800, up to 167 devices with per-type limits (80 lights, 20 locks, 40 "
            "thermostats, 6 garage doors, 21 other). IQ Panel 2+ limits are lower (10 thermostats).",
            "No device parameters or wake-up settings on the panel; only associations can be edited. Parameters are "
            "dealer-side in Alarm.com.",
            "The manual says to run Rediscover Network after installing or moving any device.",
            "'Remove All Devices' resets the controller and orphans every device.",
            "Qolsys aims for at least 98% acknowledged frames in the Counters screen.",
            "Long Range needs an IQ Panel 4 on software 4.5.0 or later and SmartStart (per Surety).",
        ],
        "actions": {
            "include": A(QOLSYS_PATH + " > Add Device > Include, press the device's pair button, then Add. SmartStart: "
                         "SmartStart > Include > scan the QR code or enter the DSK > Add DSK.", IQ4,
                         "Clear the device first (see exclude) if it was ever paired elsewhere."),
            "exclude": A(QOLSYS_PATH + " > Clear Device, then press the device's pair button.", IQ4,
                         "Works for devices from another controller, and deletes it from the panel if it was paired."),
            "remove_failed": A(QOLSYS_PATH + " > Delete Failed Device > Delete Failed Device From Panel > tick the "
                               "devices > Delete. To replace one, enable Advanced Z-Wave Settings under Z-Wave Settings "
                               "to get Replace Failed Node.", IQ4, "Only works once the panel considers the node failed."),
            "rebuild": A("Settings > Advanced Settings > System Tests > Z-Wave Tests > Rediscover Network: select one "
                         "device or all, then Rediscover.", IQ4, "Per-device rediscovery is available; prefer it."),
            "routes": A("Settings > Advanced Settings > System Tests > Z-Wave Tests: Neighbor Info > View, Counters "
                        "(acknowledged and failed counts), Z-Wave Diagnostics (map and last working route), and "
                        "Advanced Z-Wave Diagnostics (Network Health Test, Repeater Test, Last Working Route).", IQ4),
            "logs": A("Advanced Settings: Upload logs to the server, and Log Level.", IQ4,
                      "Logs go to Qolsys and your dealer, not to you. For your own view, use a Zniffer stick with zwlens."),
            "config": A(QOLSYS_PATH + " > View/Edit Associations > View > Edit > Save.", IQ4,
                        "Device parameters and wake-up intervals are not available on the panel; ask your dealer."),
            "firmware": A("Settings > Advanced Settings > Upgrade Software > Upgrade Using Network.", IQ4,
                          "No separate Z-Wave radio update or Z-Wave network backup is documented."),
        },
        "docs": [{"label": "IQ Panel 4 installation manual", "url": IQ4},
                 {"label": "IQ Panel 2+ installation manual", "url": IQ2}],
    },
    {
        "id": "2gig", "name": "2GIG GC2 / GC3 / Edge (Alarm.com)",
        "summary": "An Alarm.com security panel with basic Z-Wave tools: add, remove, check network and rediscover. "
                   "It shows no routes or signal levels.",
        "quirks": [
            "Smart Home Settings need the installer code unless the installer granted the master user access. The "
            "manuals print the default installer code (1561) and warn you to change it.",
            "GC3 and Edge support up to 232 devices; the Edge supports S2.",
            "The manuals say to run Rediscover Network after every add or remove, and to remove a device before adding it.",
            "Check Network can take several minutes, and some smart home functions are unavailable while it runs.",
            "Reset Controller wipes the Z-Wave network and cannot be reversed.",
            "The Edge does not manage associations from its screen.",
        ],
        "actions": {
            "include": A("GC3: Installer Toolbox > Smart Home Settings > Add Devices, trigger the device, OK. Edge: "
                         "Settings > Smart Home Settings > Add Device (S2 devices ask for the DSK). GC2: Services > "
                         "Z-Wave > wrench icon > installer code > Add Devices.", GC3),
            "exclude": A("GC3: Smart Home Settings > Remove Devices, then trigger the device. Edge: Remove Device. "
                         "GC2: wrench icon > Remove Devices.", GC3),
            "remove_failed": A("GC3: Smart Home Settings > View All Devices > the device's menu > Remove or Replace. "
                               "Edge: Remove a Failed Smart Home Device > Remove > OK. GC2: Failed Devices > Remove "
                               "Failed Device.", GC3,
                               "The options only appear for a device that is not communicating. Replace keeps the node number."),
            "rebuild": A("GC3 and Edge: Smart Home Settings > Rediscover Network > Start. GC2: wrench icon > Advanced "
                         "Toolbox > Rediscover Network.", EDGE_SH, "Whole network only."),
            "routes": A("Smart Home Settings > Check Network lists unresponsive and failed nodes. Routes, neighbours "
                        "and signal levels are not shown.", GC3,
                        "A Zniffer stick with zwlens is the only way to see routing on these panels."),
            "logs": A(NONE),
            "config": A("GC3 only: View All Devices > the device's menu > Configure > Set Value > Set, and Device "
                        "Association > Manage > Edit Group.", GC3, "Wake-up intervals are not documented."),
            "firmware": A("Edge: update from a USB thumb drive > Update.", EDGE_I, "No Z-Wave network backup is documented."),
        },
        "docs": [{"label": "GC3 installation guide", "url": GC3}, {"label": "Edge smart home manual", "url": EDGE_SH},
                 {"label": "Surety: 2GIG Z-Wave how-to", "url": SUR_2GIG}],
    },
    {
        "id": "alarmcom", "name": "Alarm.com website and app / SuretyDIY",
        "summary": "Remote Z-Wave tools for Alarm.com panels. Most are in the dealer's Partner Portal; customers get "
                   "a troubleshooting wizard, and Surety DIY customers get a few extra commands in System Manager.",
        "quirks": [
            "Most Z-Wave commands (add, delete, remove failed, rediscover, parameters, backup) are dealer-only. As a "
            "SuretyDIY customer, do them at the panel or ask Surety to send them.",
            "Alarm.com's guidance: keep every device within about 25 feet of the nearest mains-powered node, and run "
            "Network Rediscovery twice.",
            "A node is marked failed after three consecutive failed transmissions.",
            "All lock user codes are erased when the first code is pushed from Alarm.com.",
            "The troubleshooting wizard does not work for sleeping (battery) devices.",
            "Remove SmartStart devices from the provisioning list before deleting them, or they re-join.",
            "No routing table or signal view is documented, for dealers or customers.",
        ],
        "actions": {
            "include": A("Customer: website Settings > Manage Devices > Add Device, or the app's Add Device (certain "
                         "devices only). Dealer: Equipment > Z-Wave Devices > Manage Devices > Add a Z-Wave Device; "
                         "SmartStart under Manage S2 & SmartStart Keys.", ADC_SUPP,
                         "For Long Range the QR code must be scanned; a typed DSK joins as ordinary mesh."),
            "exclude": A("Dealer: Equipment > Z-Wave Devices > Manage Devices > Delete a Z-Wave Device. Customers "
                         "exclude at the panel.", ADC_SUPP),
            "remove_failed": A("Dealer: expand the device > Device Commands > Remove Failed Device (wait a minute, "
                               "then Get Equipment List) or Replace Failed Device.", ADC_SUPP),
            "rebuild": A("Dealer: Z-Wave Devices tab > Troubleshooting > Rediscover Network. Customers run it at the "
                         "panel.", ADC_SUPP,
                         "Surety staff have said rediscovery has to be done at the panel and is not in System Manager."),
            "routes": A("Customer: Manage Devices > the device's menu > Troubleshoot > Get Started runs the Z-Wave "
                        "Troubleshooting Wizard. No route or signal view is documented.", ADC_WIZ,
                        "Do not operate the devices while the wizard runs."),
            "logs": A("Dealer only: a Z-Wave event history page in the Partner Portal. Nothing for customers.", ADC_SUPP),
            "config": A("Dealer only: Device Commands > Configure Parameter Values. Wake-up is handled automatically.",
                        ADC_SUPP),
            "firmware": A("Dealer only: Advanced Z-Wave Commands > Backup Network / Restore Z-Wave Network, on "
                          "Alarm.com-built modules.", "", "Reported not to cover Qolsys or 2GIG panels."),
        },
        "docs": [{"label": "Alarm.com Z-Wave documentation", "url": ADC_SUPP},
                 {"label": "Troubleshooting wizard", "url": ADC_WIZ},
                 {"label": "Device not functioning consistently", "url": ADC_TS},
                 {"label": "Surety System Manager", "url": SUR_SM},
                 {"label": "Surety on rediscovery", "url": SUR_REDISC}],
    },
    {
        "id": "ring", "name": "Ring Alarm Base Station",
        "summary": "Very widely installed, but it exposes almost no Z-Wave tooling: no repair, routes, logs or "
                   "parameters are documented.",
        "quirks": [
            "No route rebuild, routing view, logs, device parameters or backup are documented.",
            "'Reset Z-Wave Network' is irreversible.",
            "With so little built in, a Zniffer stick with zwlens is the practical way to see what the network is doing.",
        ],
        "actions": {
            "include": A("Ring app > Set Up a Device and follow the guided flow; SmartStart devices are added by "
                         "scanning their QR code. Otherwise add manually > Z-Wave > Add.", RING_SET),
            "exclude": A("Alarm tile > Connected Devices > the device > Device Settings > Remove > Remove Device.",
                         RING_SET, "Excluding a device from another network is not documented."),
            "remove_failed": A("The device's Advanced Options: try Retry Connection, then Reconfigure Device, then "
                               "Remove Device.", RING_OFF),
            "rebuild": A(NONE), "routes": A(NONE), "logs": A(NONE), "config": A(NONE), "firmware": A(NONE),
        },
        "docs": [{"label": "Ring Z-Wave manual", "url": RING_ZWA}, {"label": "Fixing offline devices", "url": RING_OFF}],
    },
    {
        "id": "homey-pro", "name": "Homey Pro (2019 / 2023) and Homey Bridge (Athom)",
        "summary": "The apps cover adding, removing and device settings. The real Z-Wave tooling is on the Homey Developer "
                   "Tools page: per-node routes, Tx/Rx error counters, failed-node removal, route updates and a raw log.",
        "quirks": [
            "Homey Pro is always node 1 and the primary SUC/SIS. It cannot be included in another Z-Wave network.",
            "Adding always runs an exclusion first. If the device is already clean, use Advanced options > Skip to "
            "inclusion. S0 is off by default; turn it on with Enable legacy Security S0 pairing only if needed.",
            "Update Z-Wave Routes can take a very long time, the network is unavailable meanwhile, and battery nodes "
            "are skipped; update those one at a time afterwards.",
            "Removing a node that is only temporarily offline does not take it out of the network; when it comes back "
            "it may flood Homey with messages that go unanswered.",
            "Reset Z-Wave network and a factory reset (pin in the reset hole for 30 s) orphan devices that miss the "
            "reset notice. A factory reset sends no notice at all, so every device must be excluded before re-adding.",
            "Homey Bridge in Satellite Mode only acts as a Z-Wave repeater for Homey Pro. With Homey Cloud it is the "
            "controller itself (about 240 Z-Wave devices). Z-Wave Long Range is not documented.",
        ],
        "actions": {
            "include": A("Devices > + > New device > Z-Wave, in the mobile or web app. For SmartStart choose Connect via "
                         "SmartStart instead, then scan the QR code or enter the DSK.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/80647/HomeyPro-Z-WaveUserManual-1.5.pdf",
                         "S2 Authenticated or Access Control devices ask for the first 5 DSK digits. QR scanning is mobile-app only."),
            "exclude": A("Mobile app: device settings > Remove device. Web app: right-click the device > Delete. For a "
                         "device from another network: Developer Tools (tools.developer.homey.app/tools/zwave) > Remove "
                         "Any Node, then put the device in learn mode.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/80647/HomeyPro-Z-WaveUserManual-1.5.pdf"),
            "remove_failed": A("Developer Tools > Nodes > three dots next to the node > Test. If it is unreachable, Remove "
                               "is enabled; click it. Remove unknown nodes tests and removes every node with no Homey device.",
                               "https://products.z-wavealliance.org/wp-content/uploads/products/80647/HomeyPro-Z-WaveUserManual-1.5.pdf",
                               "Replacing a failed node is not documented."),
            "rebuild": A("One node: Developer Tools > Nodes > three dots > Update Route. Whole network: Developer Tools > "
                         "Update Z-Wave Routes.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/80647/HomeyPro-Z-WaveUserManual-1.5.pdf",
                         "Prefer Update Route per node; the full update makes the network unavailable and skips battery nodes."),
            "routes": A("Developer Tools > Nodes shows each node's Route (type and hop list), Tx Queued, Tx Sent, Tx Error "
                        "(count and %), Rx, and flags such as NoAck and Unreachable.",
                        "https://products.z-wavealliance.org/wp-content/uploads/products/80647/HomeyPro-Z-WaveUserManual-1.5.pdf",
                        "No network map or signal strength is documented."),
            "logs": A("Developer Tools > Log shows low-level Z-Wave logging. Developer Tools > State shows the Z-Wave "
                      "module state.",
                      "https://products.z-wavealliance.org/wp-content/uploads/products/80647/HomeyPro-Z-WaveUserManual-1.5.pdf",
                      "No log download is documented. For a full air capture, use a Zniffer stick with zwlens."),
            "config": A("Device settings screen: set the wake-up interval or turn wake-up on or off, and add, edit or "
                        "remove associations (nodes as nodeId or nodeId.endpointId, comma-separated).",
                        "https://products.z-wavealliance.org/wp-content/uploads/products/80647/HomeyPro-Z-WaveUserManual-1.5.pdf",
                        "Configuration parameters and polling are not covered by the Z-Wave manual."),
            "firmware": A(NONE + " The device settings screen shows each device's firmware version. Homey Pro Backups "
                          "(paid) makes automatic nightly backups of devices, Flows and Insights; subscribe in the "
                          "mobile app under More > Backups.", "https://homey.app/homey-pro-backups/",
                          "Whether a backup restores the Z-Wave network on a new Homey is not documented."),
        },
        "docs": [{"label": "Homey Pro Z-Wave user manual (Z-Wave Alliance)",
                  "url": "https://products.z-wavealliance.org/wp-content/uploads/products/80647/HomeyPro-Z-WaveUserManual-1.5.pdf"},
                 {"label": "Homey Pro Backups", "url": "https://homey.app/homey-pro-backups/"},
                 {"label": "Homey Bridge", "url": "https://homey.app/homey-bridge/"}],
    },
    {
        "id": "fibaro-hc3", "name": "FIBARO Home Center 3 / HC3 Lite / Yubii Home",
        "summary": "A capable web interface: parameters, associations, polling, mesh reconfiguration, device "
                   "firmware upload and a live Console. There is no documented route or neighbour view.",
        "quirks": [
            "One manual covers Home Center 3 (HC3-001), Home Center 3 Lite (HC3L-001) and Yubii Home (YH-001). The "
            "HC3 radio is listed as Z-Wave 500 series. Long Range is not documented.",
            "Reset Z-Wave removes every Z-Wave device from the gateway, and scenes that used them stop working.",
            "Backup space is limited: 2 local backups and 10 MB in the cloud. Download local backups to keep more. "
            "Cloud backups need Remote Access.",
            "Migrating from HC2 or HC Lite is irreversible and resets the source gateway's Z-Wave chip. If it fails, "
            "contact FIBARO support and do not repeat it. Wake all battery devices afterwards.",
            "The gateway can join an existing Z-Wave network only while it has no Z-Wave devices of its own.",
            "Connected gateways extend range, but only a Home Center 3 can be the master and all must run the same "
            "firmware.",
        ],
        "actions": {
            "include": A("Settings > Devices > + > Z-Wave Device. Choose NWI, Add in S2 Security mode, or Allow "
                         "inclusion only in near proximity, then Start adding. SmartStart: Settings > Z-Wave > "
                         "SmartStart > Add DSK.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/60181/YH-HC3-HC3L-ZW-1.1.pdf",
                         "For S2 Authenticated, enter the PIN (the underlined part of the DSK) and click Send."),
            "exclude": A("Settings > Devices > + > Z-Wave Device, then run the removal procedure on the device. A device "
                         "already on the gateway can also be removed from its own menu in Settings > Devices.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/60181/YH-HC3-HC3L-ZW-1.1.pdf",
                         "Works for devices from another Z-Wave network too."),
            "remove_failed": A("Settings > Devices > Z-Wave tab > menu next to the device > Force remove.",
                               "https://products.z-wavealliance.org/wp-content/uploads/products/60181/YH-HC3-HC3L-ZW-1.1.pdf",
                               "The gateway tries the device first and cancels if it answers. Replacing a failed node "
                               "is not documented."),
            "rebuild": A("Settings > Z-Wave > Reconfigure mesh network, for the entire network or single devices.",
                         "https://www.taloon.com/media/attachments/heatit/fibaro_home_center_3_manual.pdf",
                         "Prefer single devices. Source is FIBARO's online manual as reprinted by a retailer."),
            "routes": A(NONE + " The Diagnostics screen's Z-Wave tab only lists devices that are not configured or "
                        "lack templates.", "https://www.taloon.com/media/attachments/heatit/fibaro_home_center_3_manual.pdf"),
            "logs": A("Open the Console from the sidebar and set Tag to Z-Wave to see adding, removing and "
                      "reconfiguration messages. Settings > General > Generate system report gives a printable report.",
                      "https://www.taloon.com/media/attachments/heatit/fibaro_home_center_3_manual.pdf",
                      "A tag appears in the filter only after it has been used once."),
            "config": A("Settings > Devices > open the device: Parameters tab (or Copy configuration from another "
                        "device), Associations tab, and Device configuration > Reconfigure device. Polling: Settings > "
                        "Z-Wave > Enable devices polling, Poll unavailable devices, and the polling time interval.",
                        "https://products.z-wavealliance.org/wp-content/uploads/products/60181/YH-HC3-HC3L-ZW-1.1.pdf",
                        "Battery devices apply changes at the next wake-up. A wake-up interval setting is not documented."),
            "firmware": A("Gateway: Update > Home Center > Download Update > Install Update. Devices: Update > Devices, "
                          "or Settings > Z-Wave > Firmware update tab > Upload File > Start update. Backup: Settings > "
                          "Backup > Local Backup or Cloud Backup > Create backup.",
                          "https://products.z-wavealliance.org/wp-content/uploads/products/60181/YH-HC3-HC3L-ZW-1.1.pdf",
                          "Device updates do not work over Remote Access. The update offers a cloud or local backup first."),
        },
        "docs": [{"label": "HC3 / HC3 Lite / Yubii Home Z-Wave manual (Z-Wave Alliance)",
                  "url": "https://products.z-wavealliance.org/wp-content/uploads/products/60181/YH-HC3-HC3L-ZW-1.1.pdf"},
                 {"label": "Home Center 3 online manual (retailer reprint)",
                  "url": "https://www.taloon.com/media/attachments/heatit/fibaro_home_center_3_manual.pdf"}],
    },
    {
        "id": "ezlo-vera", "name": "Ezlo / Vera (VeraPlus, VeraEdge, Vera Secure, Ezlo Plus, Ezlo Secure, Ezlo Atom)",
        "summary": "Basic Z-Wave tooling: pairing wizards, device parameters and a Z-Wave backup, but no route, neighbour "
                   "or signal view and no manual heal. The classic Vera UI keeps a few extras under Settings > Z-Wave "
                   "Settings > Advanced; Ezlo hubs are run from the Ezlo or Vera mobile app.",
        "quirks": [
            "Settings > Z-Wave Settings > Advanced > Reset Z-Wave network clears all user configuration and assigns a "
            "new Z-Wave HouseID. A factory reset of an Ezlo hub also creates new S0/S2 keys and orphans every device. "
            "Both are irreversible.",
            "Delete only hides a device from the dashboard. A device that is still powered will add itself back; use "
            "Unpair to really exclude it.",
            "Community reports say the classic Vera UI lost its manual Heal/Repair button in release 7.10 and heals "
            "nightly instead.",
            "Ezlo Plus has a Z-Wave 700-series chip and supports SmartStart and S2. S2 Access is selected by default "
            "when pairing.",
            "Vera's old help center (support.getvera.com) is offline; Ezlo's is at support.ezlo.com.",
            "Verbose logging on Vera can slow the engine; turn it on only while reproducing a problem.",
        ],
        "actions": {
            "include": A("Vera UI: Devices > Add Device > + on the device's category, then follow the Device Wizard; "
                         "choose Generic Z-Wave Device if yours is not listed. Ezlo app: Devices > + > pick the device "
                         "or Generic Z-Wave device. SmartStart: Devices > + > Z-Wave SmartStart, then scan the QR code "
                         "or tap Enter DSK code.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/60379/Ezlo%20Plus%20User%20Manual.pdf",
                         "If the device was paired with another system, press Retry in the wizard to exclude it first."),
            "exclude": A("Vera UI: start the Device Wizard as for inclusion and press Retry to start exclusion. Ezlo app: "
                         "open the device > settings > Delete device > Unpair, then do the device's pairing steps.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/60379/Ezlo%20Plus%20User%20Manual.pdf",
                         "Unpair needs physical access to the device and may need repeating."),
            "remove_failed": A("Ezlo app: open the device > settings > Delete device > Delete, for a device that is no "
                               "longer connected.",
                               "https://products.z-wavealliance.org/wp-content/uploads/products/60379/Ezlo%20Plus%20User%20Manual.pdf",
                               "Replacing a failed node, and the classic Vera UI steps, are not documented by the maker."),
            "rebuild": A(NONE + " There is no manual heal in the classic Vera UI or the Ezlo app.",
                         "https://community.ezlo.com/t/where-heal-gone/189402",
                         "Community reports say Vera release 7.10 removed the old Heal/Repair process, and the 7.0.30 "
                         "release notes added Nightly Heal Maintenance settings. The Ezlo manual's Z-Wave "
                         "settings > General settings > Rediscover device (in the device's settings) works on one device; it does not say whether "
                         "routes are rebuilt."),
            "routes": A(NONE + " Neither the Vera UI nor the Ezlo app documents a route, neighbour or signal view."),
            "logs": A("Vera UI: Settings > Logs; tick Verbose logging to record all low-level Z-Wave traffic. View the "
                      "log at http://<vera-ip>/cgi-bin/cmh/log.sh?Device=LuaUPnP.",
                      "https://www.vesternet.com/pages/apnt-105-vera-ui7-diagnostics",
                      "From Vesternet, a Vera distributor, since Vera's own help center is offline. No log access is "
                      "documented for Ezlo hubs."),
            "config": A("Ezlo app: Devices > open the device's settings > Z-Wave Settings > Edit next to a parameter, or + to add one. Vera UI: "
                        "Devices > open the device's settings > Device Options > Add configuration settings > Save Changes, then Advanced > "
                        "Configure Node Right Now. Ezlo associations: the Device Associations area of EZLogic.",
                        "https://support.ezlo.com/hc/en-us/articles/7509951348508-How-to-customize-your-Z-Wave-device-parameters-Guide-for-the-advanced-users/",
                        "Battery devices show Pending device wake-up until they wake. The Vera UI steps are from "
                        "Vesternet (APNT-102). Wake-up interval and polling settings are not documented."),
            "firmware": A("Vera UI: Settings > Firmware for the hub. Z-Wave network backup: Settings > Z-Wave Settings > "
                          "Advanced > Backup Z-Wave Network. Ezlo: Settings > Backups > Create Backup; hubs also back up "
                          "daily at 3 AM.",
                          "https://products.z-wavealliance.org/wp-content/uploads/products/50187/Z-Wave_Overview%20and_QSG.pdf",
                          "The Vera firmware path is from Vesternet (KB-78), which advises a backup first. Ezlo's backup "
                          "list does not say it includes the Z-Wave network. No Ezlo hub or device firmware update is "
                          "documented."),
        },
        "docs": [{"label": "Ezlo Plus user manual (Z-Wave Alliance)",
                  "url": "https://products.z-wavealliance.org/wp-content/uploads/products/60379/Ezlo%20Plus%20User%20Manual.pdf"},
                 {"label": "VeraEdge quick start guide (Z-Wave Alliance)",
                  "url": "https://products.z-wavealliance.org/wp-content/uploads/products/50187/Z-Wave_Overview%20and_QSG.pdf"},
                 {"label": "Ezlo: customize Z-Wave device parameters",
                  "url": "https://support.ezlo.com/hc/en-us/articles/7509951348508-How-to-customize-your-Z-Wave-device-parameters-Guide-for-the-advanced-users/"},
                 {"label": "Ezlo: Backups", "url": "https://support.ezlo.com/hc/en-us/articles/8061902884124-Backups/"}],
    },
    {
        "id": "z-way", "name": "Z-Way by Z-Wave.Me (RaZberry, Z-Station, UZB)",
        "summary": "Very open: the Expert UI shows neighbours, a route map with link signal, per-device timing "
                   "statistics, link tests and full network backups. The log is a plain file on the controller.",
        "quirks": [
            "The Smart Home UI backup (Management > Backup & Restore) does not include the Z-Wave network stored in "
            "the chip. Use Expert UI Network > Control > Backup and Restore for that.",
            "Restoring a network backup overwrites the existing network. Ticking the option to overwrite the chip can "
            "lose all network relationships and force re-inclusion. The manual says \"Handle with care!\"",
            "Sleeping battery devices are not detected as failed automatically. Use Mark battery device as failed "
            "manually before removing one.",
            "The Route Map shows full routes and per-link signal only for devices with SDK 6.71 or later.",
            "The Analytics menu (background noise, network statistics) only appears when unlocked in the radio "
            "firmware.",
            "Long Range on RaZberry 7 firmware is listed as requiring a license.",
        ],
        "actions": {
            "include": A("Smart Home UI: Configuration > Devices > Z-Wave > + on the Z-Wave part, then pick the vendor "
                         "or the generic device. Expert UI: Network > Control > Device Management > Include Device.",
                         "https://z-wave.me/manual/z-way/Web_Browser_User_Interface.html",
                         "Secure inclusion is the default; a small button next to it switches to unsecure. The QR-code "
                         "(SmartStart) button only shows if the controller supports it."),
            "exclude": A("Smart Home UI: Devices > Z-Wave Device Management > Manage > x > Reset and Remove. Expert UI: "
                         "Network > Control > Device Management > Exclude Device.",
                         "https://z-wave.me/manual/z-way/Web_Browser_User_Interface.html",
                         "Reset and Remove needs the device to still work."),
            "remove_failed": A("Smart Home UI: Manage > x > Remove. Expert UI: Network > Control > Network Maintenance > "
                               "Remove Failed Node, or Replace a Failed node to keep the same node ID.",
                               "https://z-wave.me/manual/z-way/Z_Wave_Expert_User_Interfac.html",
                               "Only failed nodes are listed. For a battery device, use Mark battery device as failed "
                               "manually first."),
            "rebuild": A("Expert UI: Network > Reorganization; tick the stages to run and start it. The result log can "
                         "be downloaded.", "https://z-wave.me/manual/z-way/Z_Wave_Expert_User_Interfac.html",
                         "Each node re-detects its neighbours. Battery devices are queued until mains devices are done "
                         "and only update while awake."),
            "routes": A("Expert UI: Network > Neighbors, Network > Route Map (line colour is signal, thickness is "
                        "traffic, dotted means it sometimes fails), Network > Link Status > Test link, and Network > "
                        "Timing Info (packets and success rate per device). Analytics > Background Noise shows the "
                        "noise floor per channel.",
                        "https://z-wave.me/manual/z-way/Troubleshoot_Z_Wave_Network.html",
                        "Failures in Timing Info are not always serious; a battery device may have gone back to sleep."),
            "logs": A("The log is /var/log/z-way-server.log on the controller. Set <log-level> in config.xml in the "
                      "Z-Way folder: 0 logs everything, 9 almost nothing.",
                      "https://z-wave.me/files/manual/z-way/Develop_Code_Z_Way.html",
                      "For a bug report, delete the log, restart Z-Way, reproduce the problem, then stop Z-Way and send "
                      "the log (see z-wave.me/support/how-to-report-a-bug)."),
            "config": A("Expert UI: Configuration > Configuration for parameters and wake-up; Configuration > "
                        "Association for associations. Device > Active Associations gives an overview.",
                        "https://z-wave.me/manual/z-way/Z_Wave_Expert_User_Interfac.html"),
            "firmware": A("Z-Way: Management > Firmware Update > Open Updater. Radio: Expert UI Network > Controller "
                          "Info > Firmware Update. Device: Expert UI Configuration > Firmware Update. Network backup: "
                          "Expert UI Network > Control > Backup and Restore.",
                          "https://z-wave.me/manual/z-way/Z_Wave_Expert_User_Interfac.html",
                          "A device update can take up to 10 minutes; do nothing else meanwhile. The Expert UI is at "
                          "http://<ip>:8083/expert (per the UZB/RaZberry firmware page)."),
        },
        "docs": [{"label": "Z-Way manual: Expert User Interface",
                  "url": "https://z-wave.me/manual/z-way/Z_Wave_Expert_User_Interfac.html"},
                 {"label": "Z-Way manual: Web Browser User Interface",
                  "url": "https://z-wave.me/manual/z-way/Web_Browser_User_Interface.html"},
                 {"label": "Z-Way manual: Troubleshoot the Z-Wave network",
                  "url": "https://z-wave.me/manual/z-way/Troubleshoot_Z_Wave_Network.html"},
                 {"label": "UZB/RaZberry firmwares", "url": "https://z-wave.me/support/uzbrazberry-firmwares/"}],
    },
    {
        "id": "homeseer", "name": "HomeSeer HS4 / HomeTroller (Z-Wave Plus plug-in, Z-NET)",
        "summary": "The current Z-Wave Plus plug-in runs on Z-Wave JS UI and exposes ping, route rebuilds, associations, "
                   "device firmware and controller backups. Route maps and parameters are not covered in HomeSeer's own docs.",
        "quirks": [
            "The older Z-Wave plug-in is no longer developed; Z-Wave Plus replaces it. Z-Wave Plus does not run on "
            "HomeTroller SEL or S6 hubs.",
            "When migrating, run Plugins > Z-Wave > Advanced Functions > Node Test first. Failed nodes do not convert "
            "to Z-Wave Plus.",
            "S2 is recommended. SmartStart (mesh or Long Range) needs the full 40-digit DSK. Skipping the PIN prompt "
            "adds the device with S0.",
            "Restore Interface erases the controller first. Reset and Erase Interface wipes all nodes; use it only "
            "to start from scratch.",
            "A quiet log does not mean a healthy network. Run Ping All Nodes to test every device.",
            "The Z-Wave JS Front-End is hidden by default and HomeSeer does not support it.",
        ],
        "actions": {
            "include": A("Plugins > Z-Wave Plus > Add Device: pick the network and inclusion method (S2, SmartStart, "
                         "S0 or No encryption), then put the device in inclusion mode.",
                         "https://docs.homeseer.com/products/add-device",
                         "S2 asks for the 5-digit PIN from the device label."),
            "exclude": A("Plugins > Z-Wave Plus > Remove Device: pick the network, then put the device in exclusion mode.",
                         "https://docs.homeseer.com/products/remove-device",
                         "Works for devices from another network too. If it fails, restart the network or move closer."),
            "remove_failed": A("Plugins > Z-Wave Plus > Device Diagnostics > Remove Failed Node. To replace it, factory "
                               "reset the device and add it again with Add Device.",
                               "https://docs.homeseer.com/products/device-diagnostics",
                               "Use it only when normal exclusion cannot remove the device."),
            "rebuild": A("One device: Plugins > Z-Wave Plus > Device Diagnostics > Rebuild Routes. Whole network: "
                         "Plugins > Z-Wave Plus > Advanced Functions > Rebuild All Routes.",
                         "https://docs.homeseer.com/products/advanced-functions",
                         "HomeSeer suggests rebuilding a nearby working device first, then re-running Ping All Nodes."),
            "routes": A(NONE + " Ping Node and Ping All Nodes test reachability. The Z-Wave JS Front-End (enable "
                        "Show ZWave JS Front-End under Manage Networks) is Z-Wave JS UI, but HomeSeer does not "
                        "describe its views.", "https://docs.homeseer.com/products/z-wave-js-front-end"),
            "logs": A("Plugins > Z-Wave Plus > Settings: Log Level = Debug, and tick Log To File. To read it: Tools > Log, "
                      "FROM FILTER > ZWavePlus, TYPE FILTER > Error.",
                      "https://docs.homeseer.com/products/settings",
                      "The log file location is not documented."),
            "config": A("Associations: Plugins > Z-Wave Plus > Manage Associations > pick the device > Add or Remove > "
                        "group > targets > START.", "https://docs.homeseer.com/products/manage-associations",
                        "Parameters, wake-up and polling are not in HomeSeer's Z-Wave Plus docs. Zooz support says to "
                        "use the device page's Configuration section or the Z-Wave JS Front-End."),
            "firmware": A("Devices: Plugins > Z-Wave Plus > Update Firmware (.hex, .otz, .hec or .gbl from the maker). "
                          "Backup: Plugins > Z-Wave Plus > Advanced Functions > Backup Interface; move to a new stick "
                          "with Restore Interface.", "https://docs.homeseer.com/products/update-firmware",
                          "Z-NET radio firmware is flashed from a Windows PC with ZWaveControllerUI.exe > OTW Firmware "
                          "Update; back up the interface and HS4 first."),
        },
        "docs": [{"label": "Z-Wave Plus plug-in", "url": "https://docs.homeseer.com/products/z-wave-plus"},
                 {"label": "Troubleshooting Z-Wave devices and networks",
                  "url": "https://docs.homeseer.com/products/troubleshooting-z-wave-devices-networks"},
                 {"label": "Migrating from Z-Wave to Z-Wave Plus",
                  "url": "https://docs.homeseer.com/products/migrating-from-z-wave-to-z-wave-plus"},
                 {"label": "Z-NET firmware updates", "url": "https://docs.homeseer.com/products/z-net-firmware-updates"}],
    },
    {
        "id": "openhab", "name": "openHAB (Z-Wave binding)",
        "summary": "The Z-Wave binding exposes inclusion, per-node route rebuilds, failed-node removal, a neighbour map "
                   "and full debug logs. Device firmware updates and controller backups are not covered.",
        "quirks": [
            "No Z-Wave Long Range: 800-series sticks work for Classic inclusion (nodes 1-232) only.",
            "Secure inclusion must be started from the binding, which stays in inclusion mode for only 30 seconds.",
            "The network map shows neighbours found during a heal, not the routes actually used.",
            "A mesh heal takes nodes offline while it runs and does not update battery devices.",
            "Changing Inclusion Mode Timeout reinitialises the controller and briefly takes devices offline.",
            "A separate Z-Wave JS binding exists; it needs a running Z-Wave JS UI and its docs do not cover inclusion, "
            "heal or backup.",
        ],
        "actions": {
            "include": A("Things > + > Z-Wave Binding > Scan, then press the device's inclusion button.",
                         "https://www.openhab.org/addons/bindings/zwave/",
                         "Set the controller's Inclusion Mode (Low Power, High Power or Network Wide) to match distance."),
            "exclude": A("Things > Controller Thing (for example Z-Wave Serial Controller) > Exclude Devices, then "
                         "press the device's button.", "https://www.openhab.org/addons/bindings/zwave/"),
            "remove_failed": A("On the device's Thing page, run Check if node is failed (advanced), then Remove failed "
                               "node from the controller (advanced), then Remove Thing. To swap hardware: Replace failed "
                               "node with a new device, reusing the node ID (advanced).",
                               "https://www.openhab.org/addons/bindings/zwave/",
                               "Not for battery devices; the controller must already see the node as failed."),
            "rebuild": A("One device: Thing page > Rebuild routing tables (nee Heal). Network-wide heal runs nightly "
                         "at the controller's Heal Time.", "https://www.openhab.org/addons/bindings/zwave/",
                         "The node must be fully initialised. Battery nodes rebuild at their next wake-up."),
            "routes": A("View Z-Wave Network Map shows nodes and their neighbours.",
                        "https://www.openhab.org/addons/bindings/zwave/",
                        "It is built during a heal and does not show real routes."),
            "logs": A("Console: log:set DEBUG org.openhab.binding.zwave (back with log:set INFO). Since openHAB 4.0: "
                      "Settings > Add-ons Settings > ZWave > DEBUG. Optionally add a ZWAVE appender in "
                      "userdata/etc/log4j2.xml for a separate file.", "https://www.openhab.org/addons/bindings/zwave/",
                      "Send the full, unfiltered log when reporting problems."),
            "config": A("Parameters are set on each device's Thing; the binding docs give no menu path. Controller Thing: "
                        "Default Wakeup Period and Battery Device Awake Duration. Polling: Command Poll Period (ms, "
                        "0 = off).", "https://www.openhab.org/addons/bindings/zwave/",
                        "Wake battery devices several times near the controller after inclusion. Keep polling slow; "
                        "the Lifeline group is usually enough."),
            "firmware": A(NONE + " Device firmware updates and controller backups are not covered by the binding docs."),
        },
        "docs": [{"label": "openHAB Z-Wave binding", "url": "https://www.openhab.org/addons/bindings/zwave/"},
                 {"label": "openHAB Z-Wave JS binding", "url": "https://www.openhab.org/addons/bindings/zwavejs/"}],
    },
    {
        "id": "resideo-proseries-lyric", "name": "Resideo / Honeywell Home ProSeries (PROA7PLUS / PROA7) and Lyric Controller",
        "summary": "Security panels with basic Z-Wave tools: include, exclude, remove failed devices and a network update. "
                   "There is no route, neighbour or parameter view on the panel.",
        "quirks": [
            "PROA7PLUS has Z-Wave through the PROWIFIZW module; the PROA7 needs it added. Up to 78 Z-Wave devices, "
            "with at most 60 light modules, 6 door locks and 6 thermostats.",
            "Failed devices are removed all at once. PROA7: Remove All Failed Devices. Lyric: Fix All. Neither guide "
            "offers removing or replacing a single failed node.",
            "Reset the Controller orphans every device. The devices get no exclusion signal, so each must be excluded "
            "before it can be included again.",
            "The 12/22 PROA7 guide no longer lists Network Wide Inclusion or Shift Controller; the 10/20 guide did.",
            "Lyric: include door locks first and close to the panel; secure devices enrol at low power (about 6 feet).",
            "Lyric: AlarmNet360 remote management stopped in April 2026. Resideo TN-150 restored it until June 1, 2028 "
            "(per Alarm Grid).",
        ],
        "actions": {
            "include": A("PROA7: Menu > Devices > Z-Wave Device Management, enter the Master code, then Inclusion Mode "
                         "and activate the device. Remotely: AlarmNet360 > Z-Wave Devices > Include Devices. Lyric: "
                         "Automation > down arrow > Tools > Include Devices, then press the device's function button "
                         "within 60 seconds.",
                         "https://alarmgrid.com/documents/honeywell-home-proa7-and-proa7plus-install-guide-dated-12-22-rev-a",
                         "Exclude the device first if it was ever paired elsewhere. Dealer-hosted copy of the Resideo guide."),
            "exclude": A("PROA7: Z-Wave Device Management > Exclusion Mode, then press the device's function button. "
                         "Remotely: AlarmNet360 > Z-Wave Devices > Exclude Devices. Lyric: Automation > down arrow > "
                         "Tools > Exclude Devices.",
                         "https://cdn.nwe.io/files/x/82/28/53bf61d197069e3b29689275e0ce.pdf"),
            "remove_failed": A("PROA7: Z-Wave Device Management > Remove All Failed Devices. Lyric: Automation > View "
                               "Failed Devices > OK > Fix All > Yes.",
                               "https://cdn.nwe.io/files/x/82/28/53bf61d197069e3b29689275e0ce.pdf",
                               "Removes every failed device. Use only when a device has been proven bad. With Total "
                               "Connect, make sure a panel sync follows (Alarm Grid)."),
            "rebuild": A("PROA7: Z-Wave Device Management > Update Network. Use it after adding, removing or moving a "
                         "device. Lyric: no manual option.",
                         "https://cdn.nwe.io/files/x/82/28/53bf61d197069e3b29689275e0ce.pdf",
                         "GeoArm (a dealer) says the Lyric rediscovers routes on its own after a command fails."),
            "routes": A(NONE + " PROA7: Enrolled Devices shows each device's status and Local Controller Info shows "
                        "the controller. Lyric: Tools > Advanced Tools > View Enrolled Devices shows node numbers and "
                        "security. No neighbour or route view.",
                        "https://gvtc.com/GVTC/media/Documents/lyric-controller-user-guide.pdf"),
            "logs": A(NONE + " The guides describe no Z-Wave log or diagnostics export.", "",
                      "For your own view, use a Zniffer stick with zwlens."),
            "config": A(NONE + " Neither guide has parameter, wake-up or association screens.", "",
                        "The PROA7 can push user codes to Z-Wave locks (Z-Wave Lock Control on each user)."),
            "firmware": A("PROA7: your dealer pushes panel firmware over the air from AlarmNet360. Lyric: Security > "
                          "Tools > Advanced; most updates ask you to Accept. The version is under System Information.",
                          "https://www.alarmgrid.com/documents/mywebtech-technical-notification-141-pro-series-aio-firmware-update-04-28-26",
                          "PROA7 updates need Wi-Fi, a disarmed panel and no AC loss. No Z-Wave radio update or network "
                          "backup is documented."),
        },
        "docs": [{"label": "PROA7/PROA7PLUS install guide 12/22 (Alarm Grid copy)",
                  "url": "https://alarmgrid.com/documents/honeywell-home-proa7-and-proa7plus-install-guide-dated-12-22-rev-a"},
                 {"label": "PROA7/PROA7PLUS install guide 10/20 (PDF)",
                  "url": "https://cdn.nwe.io/files/x/82/28/53bf61d197069e3b29689275e0ce.pdf"},
                 {"label": "Lyric Controller user guide (PDF)",
                  "url": "https://gvtc.com/GVTC/media/Documents/lyric-controller-user-guide.pdf"},
                 {"label": "Removing failed Z-Wave devices (Alarm Grid)",
                  "url": "https://www.alarmgrid.com/faq/how-do-i-remove-a-non-functioning-z-wave-device-from-my-honeywel"}],
    },
    {
        "id": "vivint", "name": "Vivint Smart Hub (V-SH1)",
        "summary": "The Smart Hub panel has good Z-Wave tools, including per-node diagnostics and a topology map, but "
                   "they sit in the Installer Toolbox. The Vivint app's Z-Wave options are not documented.",
        "quirks": [
            "The full Installer Toolbox is meant for Vivint technicians and needs the installer code.",
            "The manual says to run Rediscover Network after installing all devices, and after adding or moving any device.",
            "Reset Controller clears every device from the Z-Wave network; they must be added again.",
            "Do not power cycle the panel during a firmware update; keep the power supply and battery connected.",
            "The older Vivint Master Control Panel (CP01) is certified with a 300-series chip (Z-Wave 4.55) and S0 security only.",
        ],
        "actions": {
            "include": A("Menu > Settings > Installer Toolbox > Z-Wave > Add Node. Press the device's Learn button "
                         "when prompted, then name it.",
                         "https://www.manualslib.com/manual/1302219/Vivint-V-Sh1.html?page=62#manual",
                         "Vivint's V-SH1 setup manual, read on ManualsLib."),
            "exclude": A("Menu > Settings > Installer Toolbox > Z-Wave > Remove Node, then press the device's Learn button.",
                         "https://www.manualslib.com/manual/1302219/Vivint-V-Sh1.html?page=62#manual"),
            "remove_failed": A("Menu > Settings > Installer Toolbox > Z-Wave > Remove Failed Nodes.",
                               "https://www.manualslib.com/manual/1302219/Vivint-V-Sh1.html?page=62#manual",
                               "For a device that can no longer talk to the panel. No replace option is documented."),
            "rebuild": A("Menu > Settings > Installer Toolbox > Z-Wave > Rediscover Network.",
                         "https://www.manualslib.com/manual/1302219/Vivint-V-Sh1.html?page=63#manual",
                         "Afterwards each device is listed with its alignment to its nearest nodes."),
            "routes": A("Installer Toolbox > Z-Wave > Diagnostics: View All Nodes, then select a node for its health, "
                        "neighbours, route changes and errors. Press Topology for a map of routing relationships.",
                        "https://www.manualslib.com/manual/1302219/Vivint-V-Sh1.html?page=63#manual"),
            "logs": A(NONE + " Diagnostics results are shown on the panel only.", "",
                      "For your own view, use a Zniffer stick with zwlens."),
            "config": A(NONE + " The only device setting is Z-Wave > Anti-theft > Enable, for devices that support it.",
                        "https://www.manualslib.com/manual/1302219/Vivint-V-Sh1.html?page=63#manual"),
            "firmware": A("Menu > Settings > Installer Toolbox > Update. If a Broadband Update is available, press Update.",
                          "https://www.manualslib.com/manual/1302219/Vivint-V-Sh1.html?page=76#manual",
                          "No Z-Wave backup is documented. To move devices to a new panel, use Add Node, Learn "
                          "Controller and Shift Controller."),
        },
        "docs": [{"label": "Vivint Smart Hub (V-SH1) setup manual: Z-Wave",
                  "url": "https://www.manualslib.com/manual/1302219/Vivint-V-Sh1.html?page=62#manual"},
                 {"label": "Vivint Smart Hub (V-SH1) setup manual: Update",
                  "url": "https://www.manualslib.com/manual/1302219/Vivint-V-Sh1.html?page=76#manual"},
                 {"label": "Z-Wave Alliance: Vivint Master Control Panel (CP01)",
                  "url": "https://products.z-wavealliance.org/z-wave-product/vivint-master-control-panel-cp01/"}],
    },
    {
        "id": "adt-command", "name": "ADT Command / ADT+ (ADT Base)",
        "summary": "Very little on ADT Command: its Z-Wave runs on an add-on module, and the installer adds and removes "
                   "devices from ADT's dealer tools. The newer ADT+ Base has add, remove, failed-device and network "
                   "update steps in the ADT+ app, but no route view, logs or parameter editor.",
        "quirks": [
            "ADT Command needs the ADTZWM Wi-Fi and Z-Wave module. The ADTZWMX version needs panel firmware 4.5 or later.",
            "On ADT Command, the installer adds and removes Z-Wave devices through ADT 3rd Party Services and Alarm.com "
            "MobileTech. ADT's public Command quick guides have no Z-Wave steps.",
            "ADT+ Base: 800-series radio with S2, SmartStart and Long Range. The system takes 128 devices in total, "
            "counting ULE and Z-Wave devices together.",
            "ADT+: if a secure (S2) add fails, the device may join unsecured with reduced functionality. Delete it and "
            "add it again.",
            "ADT+: Z-Wave Reset Controller orphans every device. Each one must be reset before it can be added again.",
            "ADT+: Replace Failed Node gives the new device the old one's permissions, so use the same model.",
        ],
        "actions": {
            "include": A("ADT+ app: Settings > Devices > add button > Z-Wave device, then choose General Inclusion or "
                         "SmartStart. For SmartStart, tap + > Manually or Scan QR Code; a long-range option is offered "
                         "for Long Range devices.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/80619/ADTSecuritySystemOwnersManualv3.21.pdf",
                         "S2 devices ask for the first 5 digits of the DSK. ADT Command: the installer does this through "
                         "ADT 3rd Party Services and Alarm.com MobileTech."),
            "exclude": A("ADT+ app: Settings > Devices > your device > remove, then put the device in exclusion mode. "
                         "For a device from another system: Settings > Devices > your ADT Base > advanced settings > "
                         "General Exclusion.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/80619/ADTSecuritySystemOwnersManualv3.21.pdf",
                         "ADT Command: done by the installer, not on the panel."),
            "remove_failed": A("ADT+ app: open the failed device's advanced Z-Wave settings > Remove Failed Device. To "
                               "swap it: Settings > Devices > your device > Replace Failed Node, then add the new device.",
                               "https://products.z-wavealliance.org/wp-content/uploads/products/80619/ADTSecuritySystemOwnersManualv3.21.pdf",
                               "If the removed device comes back, reset it with General Exclusion before adding it "
                               "again. Not documented for ADT Command."),
            "rebuild": A("ADT+ app: Settings > Devices > Base > Advanced Settings > Z-Wave Network Update > Confirm.",
                         "https://products.z-wavealliance.org/wp-content/uploads/products/80619/ADTSecuritySystemOwnersManualv3.21.pdf",
                         "It can take several minutes. Not documented for ADT Command."),
            "routes": A(NONE + " Neither the ADT+ manual nor the Command guides describe a route, neighbour or signal view."),
            "logs": A(NONE),
            "config": A("ADT+ app: Settings > Devices > your device, then request a status update in the advanced "
                        "section if the device's capabilities have changed.",
                        "https://products.z-wavealliance.org/wp-content/uploads/products/80619/ADTSecuritySystemOwnersManualv3.21.pdf",
                        "The Base only supports some configuration settings, for preferred devices, and has no screen "
                        "for device parameters. Wake-up, polling and associations are not documented."),
            "firmware": A(NONE + " The ADT+ manual says adding another controller with the normal add process copies the "
                          "network to it; no backup or firmware update steps are given."),
        },
        "docs": [{"label": "ADT+ (ADT Base) owner's manual, Z-Wave section",
                  "url": "https://products.z-wavealliance.org/wp-content/uploads/products/80619/ADTSecuritySystemOwnersManualv3.21.pdf"},
                 {"label": "ADT Base on the Z-Wave Alliance product database",
                  "url": "https://products.z-wavealliance.org/z-wave-product/base-3/"},
                 {"label": "ADTZWM Z-Wave module installation guide (third-party copy, manuals.plus)",
                  "url": "https://manuals.plus/adt/adtzwm-series-wi-fi-and-z-wave-module-manual"},
                 {"label": "ADT system manuals and user guides",
                  "url": "https://help.adt.com/article/System-Manuals-User-Guides-FAQs"}],
    },
    {
        "id": "control4", "name": "Control4 (CORE 3 / CORE 5, CA-1, EA series) with Composer Pro",
        "summary": "Dealer-only Z-Wave tools in Composer Pro: add, remove, remove or replace a failed node, and an "
                   "online or offline status list. No route view, rebuild, Z-Wave log or parameter editor is documented.",
        "quirks": [
            "Only one Z-Wave controller can be set up in a project, and only one Z-Wave mesh can run at a time.",
            "S2 needs the built-in 700-series radio in a CORE 3 or CORE 5 on OS 3.3.1 or later. EA controllers use a "
            "USB dongle with a Z-Wave module and do not get S2. The CORE 1 has no Z-Wave.",
            "Moving Z-Wave from an EA dongle to a CORE controller stops every device until it is unidentified and "
            "identified again on the new mesh.",
            "Reset Defaults clears the Home ID and orphans every node. Learn joins another mesh and also changes the "
            "Home ID.",
            "Use Remove Failed and Replace Failed only for devices that have physically failed.",
            "Do not mount the Z-Wave USB dongle on a metal surface.",
        ],
        "actions": {
            "include": A("Connections > Network > Z-Wave Network: double-click the Z-Wave device driver (or select it "
                         "and click Identify), then press the device's Z-Wave button within 60 seconds.",
                         "https://docs.control4.com/help/c4/software/cpro/dealer-composer-help/content/composerpro_userguide/connecting_z_wave_devices.htm",
                         "Do not close the window or click Next while the driver finishes setting up the device. "
                         "First enable the controller under the project's Z-Wave Configuration tab > Z-Wave Enabled."),
            "exclude": A("Connections > Network > Z-Wave Network > Remove (in Available Devices), then press the "
                         "device's Z-Wave button within 60 seconds.",
                         "https://docs.control4.com/help/c4/software/cpro/dealer-composer-help/content/composerpro_userguide/removing_z_wave_devices.htm",
                         "Works for devices from any network. If a device will not identify, remove it first and try again."),
            "remove_failed": A("Connections > Z-Wave Network: right-click the failed device's Node ID > Remove Failed. "
                               "To keep the Node ID, choose Replace Failed and add the new device before the timer runs out.",
                               "https://docs.control4.com/help/c4/software/cpro/dealer-composer-help/content/composerpro_userguide/removing_z_wave_devices.htm",
                               "The controller tries the device once more; if it answers, use Remove instead. Reset the "
                               "removed device to defaults before using it again."),
            "rebuild": A(NONE + " Network Update on the Z-Wave Configuration tab only asks the main controller for "
                         "topology updates when Control4 is an inclusion controller on another mesh."),
            "routes": A("Tools > Network Tools > Z-Wave Network lists the Z-Wave devices. Green means online, yellow "
                        "means identified but offline, red means not identified or offline for a long time.",
                        "https://docs.control4.com/docs/product/composer-pro/dealer-user-guide/english/latest",
                        "No Z-Wave route, neighbour or signal view is documented. The health dashboard and RSSI "
                        "columns are for Zigbee only."),
            "logs": A(NONE + " Tools > System Diagnostics covers the controller as a whole, not the Z-Wave radio."),
            "config": A(NONE + " Device settings come from each device's driver. A Generic Z-Wave driver only offers "
                        "Basic Command Class control on its properties page. The controller's Lifeline group takes 1 "
                        "association."),
            "firmware": A("Tools > Update Manager > Update updates the controller software. Back up the project with "
                          "File > Back Up, or schedule backups in Agents > Backup.",
                          "https://docs.control4.com/docs/product/composer-pro/dealer-user-guide/english/latest",
                          "Z-Wave device firmware updates are not documented, and the guide does not say whether the "
                          "project backup includes the Z-Wave network."),
        },
        "docs": [{"label": "Composer Pro: removing Z-Wave devices",
                  "url": "https://docs.control4.com/help/c4/software/cpro/dealer-composer-help/content/composerpro_userguide/removing_z_wave_devices.htm"},
                 {"label": "Composer Pro: connecting Z-Wave devices",
                  "url": "https://docs.control4.com/help/c4/software/cpro/dealer-composer-help/content/composerpro_userguide/connecting_z_wave_devices.htm"},
                 {"label": "Control4 Z-Wave setup guide",
                  "url": "https://docs.control4.com/docs/product/z-wave/dealer-setup-guide/english/latest"},
                 {"label": "OS 3.3.1 release notes (Z-Wave S2 on CORE 3 and CORE 5)",
                  "url": "https://docs.control4.com/docs/product/control4-software/dealer-release-notes/english/revision/AN"}],
    },
]

# Grouping for the controller picker.
PANELS = {'2gig', 'adt-command', 'alarmcom', 'qolsys', 'resideo-proseries-lyric', 'ring', 'vivint'}
for _g in GUIDES:
    _g["kind"] = "panel" if _g["id"] in PANELS else "hub"
