"""Controller guide data.

Menu labels are quoted from the documentation linked on each item. Where the maker documents
nothing, the text says so rather than guessing. Several panel manuals were read from copies
hosted by dealers (Surety, AlarmGrid) because the manufacturers' own PDFs were not reachable.
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
            "include": A("Settings > Devices & services > Z-Wave > Add device. For SmartStart choose Scan QR code. "
                         "In Z-Wave JS UI: Control Panel > + > Node Manager > Inclusion > Next.", HA,
                         "S2 devices ask for the PIN from the device label. Network keys must be set first."),
            "exclude": A("Device page > three-dot menu > Delete > Remove a working device. For a device from another "
                         "network: Z-Wave > Options > Remove foreign device > Start exclusion. In Z-Wave JS UI: "
                         "Node Manager > Exclusion.", HA),
            "remove_failed": A("Device page > three-dot menu > Delete, and choose to remove it as a failed device. In "
                               "Z-Wave JS UI: Node Manager > Replace Failed Node or Remove Failed Node.", ZUI,
                               "Only works once the node is Dead, Asleep or Unknown and does not answer a ping."),
            "rebuild": A("One device: device page > Rebuild routes. Whole network: Z-Wave > Options > Discover and "
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
            "firmware": A("Device page > three-dot menu > Update for device and adapter firmware. Backup: Z-Wave > "
                          "Download backup; restore with Restore from backup; move to a new stick with Migrate adapter.",
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
]
