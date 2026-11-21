"""In-app help: how to use zwlens, how Z-Wave works, a glossary and answers to "why does zwlens say...".

Served by GET /api/help and rendered by the Help tab. Plain data only.

Body markup (kept tiny so the browser can render it safely after escaping):
  - a string is a paragraph, a list of strings is a bullet list;
  - **bold**, *italic*, `code`, and [[section-id]] or [[section-id|link text]] to link to another help section
    (glossary terms are linked as [[g-term-id|text]]).
Further-reading links must be https and point at pages that were opened and confirmed to exist.
"""
from __future__ import annotations

import re

GROUPS = [
    ("use", "Using zwlens"),
    ("zwave", "How Z-Wave works"),
    ("faq", "Why does zwlens say…"),
    ("ref", "Reference"),
]

# Further reading, all opened and confirmed to exist.
ZJS_DOCS = {"label": "Z-Wave JS documentation", "url": "https://zwave-js.github.io/zwave-js/"}
ZJS_TROUBLE = {"label": "Z-Wave JS: troubleshooting",
               "url": "https://github.com/zwave-js/zwave-js/blob/master/docs/troubleshooting/index.md"}
ZJS_FIRST = {"label": "Z-Wave JS: first steps for a stable network (placement, reports, routes)",
             "url": "https://github.com/zwave-js/zwave-js/blob/master/docs/troubleshooting/first-steps.md"}
ZJS_COMMON = {"label": "Z-Wave JS: common issues (dead nodes, failed inclusion, jammed controller)",
              "url": "https://github.com/zwave-js/zwave-js/blob/master/docs/troubleshooting/common-issues.md"}
ZJS_ZNIFFER = {"label": "Z-Wave JS: creating a Zniffer",
               "url": "https://github.com/zwave-js/zwave-js/blob/master/docs/troubleshooting/zniffer.md"}
ZJS_S2 = {"label": "Z-Wave JS: Security S2, inclusion and SmartStart",
          "url": "https://github.com/zwave-js/zwave-js/blob/master/docs/getting-started/security-s2.md"}
ZJS_LR = {"label": "Z-Wave JS: Z-Wave Long Range",
          "url": "https://github.com/zwave-js/zwave-js/blob/master/docs/getting-started/long-range.md"}
SL_FUND = {"label": "Silicon Labs: Z-Wave fundamentals and specifications",
           "url": "https://docs.silabs.com/z-wave/8.0.0/zwave-fundamentals/"}
SL_NET = {"label": "Silicon Labs: Z-Wave networking basics",
          "url": "https://docs.silabs.com/z-wave/8.0.0/z-wave-networking-basics/"}
SL_BATT = {"label": "Silicon Labs: battery support basics (sleeping and FLiRS nodes)",
           "url": "https://docs.silabs.com/z-wave/8.0.0/z-wave-battery-support-basics/"}
SL_ASSOC = {"label": "Silicon Labs: association basics",
            "url": "https://docs.silabs.com/z-wave/8.0.0/z-wave-association-basics/"}
SL_MC = {"label": "Silicon Labs: multi channel basics",
         "url": "https://docs.silabs.com/z-wave/8.0.0/z-wave-multi-channel-basics/"}
ZWA = {"label": "Z-Wave Alliance", "url": "https://z-wavealliance.org/"}
ZWA_LR = {"label": "Z-Wave Alliance: Z-Wave Long Range", "url": "https://z-wavealliance.org/z-wave-long-range/"}
HA_ZW = {"label": "Home Assistant: Z-Wave integration", "url": "https://www.home-assistant.io/integrations/zwave_js/"}
HA_ADAPTERS = {"label": "Home Assistant: Z-Wave adapters", "url": "https://www.home-assistant.io/docs/z-wave/controllers/"}

SECTIONS = [
    # ------------------------------------------------------------------ using zwlens
    {
        "id": "start", "group": "use", "title": "Getting started",
        "summary": "What zwlens does and the three ways to give it something to look at.",
        "body": [
            "zwlens listens to your Z-Wave network, turns the radio traffic into readable conversations, "
            "and tells you what is wrong and what to fix first. Everything runs on this computer; nothing is "
            "uploaded anywhere.",
            "There are three ways to give it traffic:",
            [
                "**Capture live from a Zniffer stick.** The most complete view: you see every message on air, "
                "including retries, routes and signal strength. See [[live-zniffer]].",
                "**Connect to a Z-Wave JS controller** (Z-Wave JS UI or the Home Assistant add-on). You see what "
                "your controller sends and receives, without extra hardware. See [[live-controller]].",
                "**Open a saved file**: a Zniffer capture (.zlf), a Z-Wave JS driver log, or SDR output. "
                "See [[files]].",
            ],
            "No hardware yet? On the **Sources** tab press **Sample Zniffer capture** to explore the app with "
            "invented traffic.",
            "Once traffic is loaded, start on **Overview**: the [[health-score|health score]] and the "
            "suggestions list tell you where to look. Each suggestion links to a troubleshooter with a "
            "checklist.",
        ],
        "links": [],
    },
    {
        "id": "live-zniffer", "group": "use", "title": "Capturing live from a Zniffer stick",
        "summary": "Plug in a stick, pick its port on the Sources tab, press Capture.",
        "body": [
            "A Zniffer is a Z-Wave USB stick running special firmware that listens to everything on air "
            "instead of joining your network. zwlens talks to it directly; no other capture software is "
            "needed. Why you need a separate stick is explained in [[zniffer]].",
            [
                "Open **Sources** and find *Live from a Zniffer stick*.",
                "Pick the stick's port from the list (Linux: `/dev/ttyACM0` or `/dev/ttyUSB0`; Windows: `COM3` "
                "and so on; macOS: `/dev/cu.usbmodem…`). Press **Rescan** if you plugged it in after opening "
                "the page.",
                "Press **Capture**. Frames appear within a second or two and every tab updates as they arrive.",
                "Once capturing, a **Radio region** list appears. It must match your network's region "
                "(see [[frequencies]]), or you will hear nothing.",
                "Press **Stop** when you are done. What was captured is kept as an ordinary capture, so you can "
                "still browse it and [[saving|save it as .zlf]].",
            ],
            "**If the port is busy**, zwlens names the program holding it (for example Z-Wave JS UI) and "
            "offers **Stop it and capture**. That closes the whole program, so only use it if you are sure. "
            "You can also free the stick yourself and press **Check again**.",
            "**One-time setup:** on Linux, allow your user to open serial ports with "
            "`sudo usermod -aG dialout $USER`, then log out and back in. On Windows, live capture needs "
            "`py -m pip install pyserial` once.",
            "Put the Zniffer roughly where your controller is, or next to the device you are investigating. "
            "Signal levels are measured where the Zniffer sits, not where your devices are.",
        ],
        "links": [ZJS_ZNIFFER],
    },
    {
        "id": "live-controller", "group": "use", "title": "Following a Z-Wave JS controller",
        "summary": "Connect read-only to Z-Wave JS UI or the Home Assistant add-on.",
        "body": [
            "If your controller runs Z-Wave JS (Z-Wave JS UI, or Home Assistant's Z-Wave integration), "
            "zwlens can connect to its server and follow the driver log live. Nothing is changed on your "
            "controller; the connection is read-only.",
            [
                "Open **Sources** and find *Live from a controller*.",
                "Enter the server address, usually `ws://localhost:3000` or `ws://<your-server>:3000`, "
                "and press **Connect**.",
                "In Z-Wave JS UI or the add-on, set the driver **log level to debug**. At lower levels the log "
                "does not include the commands, and zwlens has little to work with.",
            ],
            "This view shows only what the controller itself sends and receives. It cannot see messages "
            "between other devices, signal strength of every hop, or traffic from neighbouring networks. For "
            "that you need a [[zniffer|Zniffer]].",
        ],
        "links": [HA_ZW, ZJS_TROUBLE],
    },
    {
        "id": "files", "group": "use", "title": "Opening saved captures and logs",
        "summary": "Drag files onto the page. Supported formats and the chip setting.",
        "body": [
            "Drop one or more files anywhere on the page, or use **Data > Choose files…**. Files are read "
            "on this computer only.",
            [
                "**Zniffer captures (.zlf)** from the Silicon Labs Zniffer, Z-Wave JS UI's Zniffer page or "
                "zwlens itself.",
                "**Z-Wave JS driver logs** (.log or .txt). Debug level gives the most detail.",
                "**SDR output**: text containing hex frames, or a .pcap file.",
            ],
            "Several files can be loaded at once; they are analysed together. **Remove** drops one, "
            "**Clear all** drops everything (your [[aliases]] are kept).",
            "**Signal conversion** on the Sources tab tells zwlens which chip recorded your .zlf files "
            "(700/800-series or 500-series). The two report signal strength on different scales; the wrong "
            "setting makes every signal look too strong or too weak. It applies to files loaded after you "
            "change it.",
        ],
        "links": [],
    },
    {
        "id": "tab-overview", "group": "use", "title": "The Overview tab",
        "summary": "Health score, what kind of network you have, a map and a prioritised to-do list.",
        "body": [
            "**Health score** (0 to 100): a quick summary of how many problems were found. See "
            "[[health-score]].",
            "**Cards**: number of nodes, messages and conversations; the share of messages *not delivered* "
            "and that *needed a retry* (see [[acks]]); how busy the radio channel was; and the "
            "[[signal|noise floor]].",
            "**Network category** describes the network: its [[ids|home ID]], size, topology (star, light "
            "mesh, deep mesh), and how many nodes fall into each health, power, security, device-type and "
            "role group. *Data rates* shows how much traffic used each [[data-rates|speed]].",
            "**Network map**: the controller sits in the middle; each ring outwards is one more "
            "[[routing|repeater]] hop. Solid lines are routes seen in the traffic; dashed lines mean "
            "zwlens assumed a direct link because it saw no route. Click a node to see its conversations.",
            "**Suggestions** lists what to do, most important first. Each links to the troubleshooter or "
            "known issue that raised it.",
        ],
        "links": [],
    },
    {
        "id": "tab-conversations", "group": "use", "title": "The Conversations tab",
        "summary": "Traffic grouped into exchanges between two nodes, shown like a chat.",
        "body": [
            "zwlens groups messages between the same two nodes into a conversation until there are a few "
            "seconds of silence. Pick one on the left to see it message by message on the right.",
            [
                "Messages from the first node are on the left, replies on the right.",
                "✓ lines are [[acks|acknowledgements]].",
                "A dashed border marks a **retransmission** (the same message sent again). A red border marks "
                "a message that was not delivered or arrived corrupted.",
                "The grey line under each message shows time, gap since the previous message, [[data-rates|data "
                "rate]], [[signal|signal strength]], the [[routing|route]] (\"via\"), sequence number and "
                "delivery result.",
                "Small grey tags such as *S2*, *Supervision* or *MultiChannel* show how the message was "
                "wrapped (see [[g-encapsulation|encapsulation]]).",
                "Blue centred lines are [[flirs|wake-up beams]]; orange ones are controller events from a log.",
                "Click a message to see its raw bytes.",
            ],
            "Filter by text, by node, or by outcome (*Clean*, *With retries or warnings*, *Failed*). "
            "\"Other networks\" shows neighbours' traffic that the Zniffer also heard.",
        ],
        "links": [],
    },
    {
        "id": "tab-troubleshoot", "group": "use", "title": "The Troubleshoot tab",
        "summary": "Five troubleshooters, controller directions and the known-issue library.",
        "body": [
            "**Your controller**: pick your hub and every checklist gains its exact menu path. See "
            "[[controller-guides]].",
            "**Five troubleshooters** check the capture for the most common Z-Wave problems: "
            "[[faq-unreachable|unreachable nodes]], [[faq-signal|weak signal]], [[faq-routing|routing]], "
            "[[faq-congestion|congestion]] and [[faq-security|security overhead]]. Each shows what it found, "
            "with severity, and a checklist. Tick steps off as you go; ticks are remembered in this browser.",
            "**Known-issue library**: 85 failure modes collected from Z-Wave JS and Silicon Labs "
            "documentation and user forums. Each is marked *Detected*, *Not seen* (checked, not found), or "
            "*Check by hand* (traffic cannot show it, such as a stick in a metal rack). Search it, or filter "
            "to *Detected only*.",
        ],
        "links": [],
    },
    {
        "id": "tab-nodes", "group": "use", "title": "The Nodes tab",
        "summary": "Every node, categorised by what its traffic shows. Rename nodes here.",
        "body": [
            "One row per node. The columns:",
            [
                "**Type**: guessed from the [[command-classes|command classes]] the node uses, for example "
                "switch, sensor or lock.",
                "**Role**: *Controller*, *Repeater* (zwlens saw it forward messages for others) or *End device*.",
                "**Power**: *Mains*, *Battery, sleeping* ([[sleeping|wakes up on a schedule]]), or *Battery, "
                "FLiRS* ([[flirs|woken by a beam]], typical for locks).",
                "**Security**: *S2*, *S0 (legacy)*, *None*, or *+ unencrypted traffic* when a secure node also "
                "sent plain messages. See [[security]].",
                "**Health**: see [[faq-node-health]].",
                "**Traffic**: *Chatty* nodes send far more than the rest; *Quiet* ones sent two messages or "
                "fewer. See [[faq-congestion]].",
                "**Signal**: median [[signal|signal strength]] at the Zniffer, in dBm.",
                "**Sent / Received / Undelivered**: message counts and the share that never got through.",
                "**Route from controller**: the repeaters on the most-used route, or *direct*. See [[routing]].",
            ],
            "**Rename** gives a node an alias, location and notes. See [[aliases]].",
        ],
        "links": [],
    },
    {
        "id": "tab-frames", "group": "use", "title": "The Frames tab",
        "summary": "Every decoded radio frame, searchable, with raw bytes.",
        "body": [
            "The lowest level: one row per [[g-frame|frame]], 200 per page. Type in the filter box and press "
            "Enter to search command names, text and hex bytes. *Problems only* keeps retransmissions, "
            "failed deliveries, corrupted frames and routing errors.",
            "Click a row to jump to its conversation.",
        ],
        "links": [],
    },
    {
        "id": "tab-data", "group": "use", "title": "The Sources tab",
        "summary": "Load files, start or stop live capture, save and export.",
        "body": [
            "Everything about getting traffic in and out: [[files|loading files]] and sample data, "
            "[[live-controller|connecting to a controller]], [[live-zniffer|capturing from a Zniffer]], the "
            "list of loaded captures, and [[saving|saving and exporting]].",
        ],
        "links": [],
    },
    {
        "id": "controller-guides", "group": "use", "title": "Controller guides",
        "summary": "Exact menu paths for your hub, next to every checklist.",
        "body": [
            "Advice such as \"rebuild routes\" or \"re-interview the node\" is only useful if you know where "
            "that is on your hub. At the top of **Troubleshoot**, choose your controller from 17 hubs and "
            "security panels, from Home Assistant, Hubitat and Homey to Qolsys, Ring, Vivint and ADT.",
            "Each troubleshooter then shows *How to do this on…* with the menu path, quoted from the "
            "maker's documentation, and a link to the source. *Good to know* lists the hub's quirks, such as "
            "operations it does not offer.",
            "Menus change with firmware updates; if a path no longer matches, follow the source link.",
        ],
        "links": [],
    },
    {
        "id": "aliases", "group": "use", "title": "Naming your devices (aliases)",
        "summary": "Give nodes names like Kitchen light; they are reused for every capture.",
        "body": [
            "Node numbers are hard to remember. On **Nodes**, press **Rename** on a row and enter a name, a "
            "location and notes. Press **Save** (or Enter). Leave all three empty to remove the alias.",
            "Aliases are stored in a small file on this computer (its path is shown on the Nodes tab) and are "
            "keyed by [[ids|home ID and node ID]], so they apply to every capture of the same network and "
            "survive **Clear all**.",
            "When zwlens follows a Z-Wave JS controller it also picks up the names and locations set there.",
        ],
        "links": [],
    },
    {
        "id": "saving", "group": "use", "title": "Saving captures and exporting reports",
        "summary": "Keep a live capture as .zlf; export a report or the raw analysis.",
        "body": [
            "Buttons on the **Sources** tab, next to *Loaded captures*:",
            [
                "**Save as .zlf** saves the radio frames (from a Zniffer or SDR) as a Zniffer capture file. "
                "Open it later in zwlens, Z-Wave JS UI or the Silicon Labs Zniffer. Log-only traffic is not "
                "included.",
                "**Export report** opens a Markdown summary: health score, findings and suggestions. Handy to "
                "paste into a forum post or support ticket.",
                "**Export JSON** downloads the full analysis for your own scripts.",
            ],
            "Before sharing a capture publicly, remember it contains your [[ids|home ID]] and, for "
            "unencrypted devices, what they did and when.",
        ],
        "links": [],
    },
    {
        "id": "health-score", "group": "use", "title": "Reading the health score",
        "summary": "How the 0 to 100 score is worked out, and what the grades mean.",
        "body": [
            "The score starts at 100. Every finding from the five troubleshooters and the known-issue "
            "library takes points off:",
            [
                "**Critical**: 15 points.",
                "**Warning**: 6 points.",
                "**Note**: 1 point.",
            ],
            "It never goes below 0. **85 or more** is *Healthy*, **60 to 84** *Needs attention*, and "
            "**below 60** *Unhealthy*.",
            "The score measures *what this capture shows*. A short capture of a quiet network may score 100 "
            "simply because little happened; capture for at least a few minutes while you use your devices. "
            "Equally, one badly placed device can cost many points while the rest of the network is fine. "
            "Read the suggestions, not just the number.",
            "Node health (Healthy, Marginal, Failing) is separate from this score; see [[faq-node-health]].",
        ],
        "links": [],
    },
    {
        "id": "privacy", "group": "use", "title": "Privacy and safety",
        "summary": "Captures stay on this computer; the app only listens on this machine.",
        "body": [
            "zwlens runs a small web server that, by default, only answers this computer "
            "(`localhost`). Captures, logs and aliases never leave it. There is no account and no "
            "tracking.",
            "A Zniffer only listens; it never transmits on your network. Connecting to a Z-Wave JS "
            "controller is read-only.",
        ],
        "links": [],
    },

    # ------------------------------------------------------------------ how Z-Wave works
    {
        "id": "zwave", "group": "zwave", "title": "Z-Wave in one page",
        "summary": "A low-power radio network for smart-home devices, run by one controller.",
        "body": [
            "Z-Wave is a radio standard for smart-home devices: lights, switches, sensors, locks, "
            "thermostats. It uses a frequency below 1 GHz, which passes through walls better than Wi-Fi, "
            "and sends small messages at low speed to save power.",
            "Every network has one **controller** (your hub or USB stick) that adds devices, keeps the list "
            "of who is in the network and works out how to reach them. Devices are called **nodes**.",
            "Messages can hop through other devices on the way, which is what makes Z-Wave a "
            "[[mesh|mesh network]]. Battery devices mostly [[sleeping|sleep]] to make their batteries last.",
            "What a device can do is described by [[command-classes|command classes]], and devices from "
            "different makers work together because they are certified against the same specification by "
            "the Z-Wave Alliance.",
        ],
        "links": [ZWA, SL_FUND, ZJS_DOCS],
    },
    {
        "id": "mesh", "group": "zwave", "title": "Mesh networking and repeaters",
        "summary": "Mains-powered devices pass messages on; battery devices do not.",
        "body": [
            "If a device is too far from the controller to hear it directly, another device in between can "
            "forward the message. That forwarding device is called a **repeater**. A network where devices "
            "relay for each other is a **mesh**.",
            "**Only mains-powered devices repeat.** A repeater has to keep its radio on all the time, which "
            "a battery device cannot afford. Plug-in switches, wall switches and in-wall modules make good "
            "repeaters; battery sensors, remotes and locks never repeat.",
            "That is why a network of mostly battery devices far from the controller struggles, and why "
            "adding a plug-in switch half-way often fixes a device that keeps dropping out.",
            "On the Nodes tab, *Role: Repeater* means zwlens actually saw that node forward messages.",
        ],
        "links": [SL_NET, ZJS_FIRST],
    },
    {
        "id": "ids", "group": "zwave", "title": "Home ID and node IDs",
        "summary": "Every message carries the network's ID and the sender's and receiver's numbers.",
        "body": [
            "The **home ID** is a 32-bit number (shown as 8 hex characters, like `c0ffee01`) that identifies "
            "your network. Every message carries it, so devices ignore traffic from your neighbours' "
            "networks. When a Zniffer hears more than one home ID, zwlens shows the extra ones as *other "
            "networks*.",
            "Each device gets a **node ID** when it joins. Classic mesh nodes are numbered 1 to 232; the "
            "controller is usually node 1. [[long-range|Long Range]] nodes are numbered from 256 upwards. "
            "Node 255 means *broadcast* (everyone).",
            "IDs are not reused straight away: if you remove and re-add a device, it gets a new number, so "
            "rename it again (see [[aliases]]).",
        ],
        "links": [SL_NET],
    },
    {
        "id": "routing", "group": "zwave", "title": "Routing: how messages find their way",
        "summary": "Up to four repeaters, the last working route first, explorer frames as a last resort.",
        "body": [
            "When the controller sends to a device it cannot reach directly, it puts a **route** in the "
            "message: the list of repeaters to pass through. A route can have **up to 4 repeaters** "
            "(5 hops).",
            "The controller builds routes from each device's **neighbour list**: who can hear whom, measured "
            "when the device joined or when routes were last rebuilt. To pick a route it typically:",
            [
                "tries the **last working route** (LWR): the route that succeeded last time;",
                "then other routes from its table, and any **priority route** you set by hand;",
                "and as a last resort sends an **explorer frame**: a search message that floods through the "
                "mesh to discover a new path. Explorer frames work but are slow and fill the airtime.",
            ],
            "When devices move or are added, the neighbour lists go stale. **Rebuilding routes** (called "
            "*heal* in older software) asks every device to measure its neighbours again and gives each one "
            "fresh routes back to the controller. Do it after moving the controller or several devices, not "
            "as routine maintenance, and expect battery devices to update only when they next wake.",
            "Signs of routing trouble in zwlens: frequent route changes, long routes, many explorer frames, "
            "and messages that only succeed on a second route. See [[faq-routing]].",
        ],
        "links": [SL_NET, ZJS_FIRST, ZJS_COMMON],
    },
    {
        "id": "acks", "group": "zwave", "title": "Acknowledgements and retransmissions",
        "summary": "Each message is confirmed; missing confirmations cause retries.",
        "body": [
            "Most messages ask for an **ACK** (acknowledgement): a tiny reply that says \"got it\". On a "
            "routed message each hop confirms to the previous one, and the destination sends a **routed ACK** "
            "back along the route so the controller knows the whole trip worked.",
            "If no ACK arrives within a few milliseconds, the sender **retransmits**: it sends the same "
            "message again, a few times, with random pauses so two devices do not keep colliding. If that "
            "still fails, the controller may try another route, and finally reports the message as **not "
            "delivered**.",
            "A few retries are normal on any radio network. Many retries mean weak signal, interference or "
            "bad routes, and every retry uses airtime that other devices then cannot use.",
            "In zwlens, *Needed a retry* and *Not delivered* on the Overview, dashed messages in "
            "Conversations, and *Undelivered* on Nodes all come from this.",
        ],
        "links": [SL_NET],
    },
    {
        "id": "data-rates", "group": "zwave", "title": "Data rates and speed fallback",
        "summary": "9.6, 40 and 100 kbit/s; a link falls back to a slower speed when it struggles.",
        "body": [
            "Z-Wave has three speeds:",
            [
                "**9.6 kbit/s**: the original rate, still used by very old devices and for some wake-up beams.",
                "**40 kbit/s**: used by most older (300 and 400-series) devices.",
                "**100 kbit/s**: used by 500, 700 and 800-series devices and by [[long-range|Long Range]].",
            ],
            "A message travels at the fastest speed that **every hop** on its route supports. Slower "
            "messages take longer on air, so they leave less room for everyone else.",
            "Controllers also **fall back** to a slower speed when a fast attempt fails, because slower "
            "transmissions are a little more robust. A device that could use 100 kbit/s but often ends up "
            "at 40 or 9.6 kbit/s is a hint that its link is weak. zwlens flags this in the "
            "[[faq-signal|signal troubleshooter]].",
        ],
        "links": [SL_NET],
    },
    {
        "id": "frequencies", "group": "zwave", "title": "Frequencies and regions",
        "summary": "Z-Wave uses different frequencies in different countries; hardware must match.",
        "body": [
            "Z-Wave works below 1 GHz, on frequencies set by each country's radio rules. Some examples:",
            [
                "**Europe** (and many other countries): around 868 MHz.",
                "**USA and Canada**: around 908 and 916 MHz; Long Range uses its own channels "
                "near 912 and 920 MHz.",
                "**Australia and New Zealand**: around 920 and 921 MHz.",
                "**Japan, Korea, India, Israel, Russia, China, Hong Kong** and others have their own "
                "frequencies.",
            ],
            "A device is built for one region and cannot talk to a controller set to another. A Zniffer "
            "also has to be set to your network's region, or it hears nothing at all. In zwlens, set it "
            "with the **Radio region** list while capturing.",
            "Because Z-Wave does not share the crowded 2.4 GHz band with Wi-Fi, Bluetooth and Zigbee, "
            "interference usually comes from nearby electronics instead: USB 3 ports and cables, cheap "
            "power supplies, and other 800–900 MHz devices.",
        ],
        "links": [HA_ADAPTERS, ZWA],
    },
    {
        "id": "signal", "group": "zwave", "title": "Signal strength, noise floor and margin",
        "summary": "RSSI in dBm, the background noise, and the gap between them.",
        "body": [
            "**RSSI** (received signal strength indicator) is how strong a message was when it arrived, in "
            "**dBm**. The numbers are negative: closer to zero is stronger.",
            [
                "around **−60 dBm** or stronger: excellent;",
                "around **−75 dBm**: fine;",
                "weaker than **−85 dBm**: weak, zwlens marks the node *Marginal*;",
                "weaker than **−92 dBm**: very weak, messages often get lost.",
            ],
            "The **noise floor** is the background level the receiver hears when nobody is transmitting. "
            "A quiet site is below about −95 dBm. A high noise floor (−85 dBm or above) means something "
            "nearby is drowning out weak devices.",
            "**Signal margin** is the difference between the two: how far a message stands above the noise. "
            "zwlens wants at least 10 dB. A strong signal in a noisy place can be worse than a weaker one in "
            "a quiet place.",
            "Important: a Zniffer measures signal **where the Zniffer is**, not between two devices. A device "
            "can sound weak at the Zniffer and still reach its neighbour well. Zniffer RSSI conversion is "
            "also approximate; see the chip setting in [[files]].",
        ],
        "links": [ZJS_FIRST],
    },
    {
        "id": "sleeping", "group": "zwave", "title": "Sleeping battery devices and wake-up intervals",
        "summary": "Battery sensors sleep, wake on a timer, and only then accept commands.",
        "body": [
            "Most battery devices (motion and door sensors, remotes, thermostatic radiator valves) spend "
            "nearly all their time **asleep** with the radio off. They still send a report instantly when "
            "something happens, such as motion.",
            "To receive anything, they **wake up** on a timer, the **wake-up interval** (often hours). On "
            "waking they send a *Wake Up Notification*; the controller then sends any queued commands or "
            "settings and tells the device it can sleep again.",
            "So changing a setting on a sleeping device takes effect at its next wake-up, not immediately. "
            "To hurry it, wake the device by hand (often a button press; see its manual).",
            "Waking too often drains the battery; waking too rarely means slow configuration and late "
            "battery reports. zwlens flags wake-up problems in the known-issue library.",
        ],
        "links": [SL_BATT],
    },
    {
        "id": "flirs", "group": "zwave", "title": "FLiRS devices and wake-up beams",
        "summary": "Locks and sirens that sleep but can be woken within about a second.",
        "body": [
            "**FLiRS** (frequently listening routing slave) devices, mainly door locks, sirens and some "
            "thermostats, sleep most of the time but briefly switch their radio on every 250 ms or 1 second "
            "to check for a **wake-up beam**.",
            "To send a command, the controller (or the last repeater on the route) first transmits a beam: a "
            "burst of short messages lasting up to about a second. The device notices it, wakes up and "
            "receives the real command.",
            "This lets a lock respond within a second or so while running for months on batteries. The cost "
            "is airtime: each beam occupies the channel for much longer than the command itself, and every "
            "command to a lock is usually [[security|encrypted]] too.",
            "In zwlens, FLiRS devices show *Battery, FLiRS (beam wake-up)* in the Power column, and beams "
            "appear as blue lines in Conversations. A beam followed by a successful exchange is normal, not "
            "a failure.",
        ],
        "links": [SL_BATT],
    },
    {
        "id": "inclusion", "group": "zwave", "title": "Inclusion, exclusion and SmartStart",
        "summary": "How devices join and leave a network.",
        "body": [
            "**Inclusion** adds a device: you put the controller into add mode, then press the device's "
            "button (or power it on). The controller gives it a [[ids|node ID]], decides its "
            "[[security|security level]], and then **interviews** it: asks what it is and what it can do. "
            "Battery devices may need waking several times before the interview finishes.",
            "**Exclusion** removes a device and resets it so it can join another network. Excluding works "
            "with any controller, which is handy for a second-hand device still tied to an old network.",
            "A device that died or was thrown away without being excluded leaves a **failed** (or *ghost*) "
            "node behind. The controller keeps trying to reach it, wasting airtime; remove it with your "
            "controller's *remove failed node* option.",
            "**SmartStart** makes inclusion automatic: you scan the QR code on the device (or its box) into "
            "your controller first, and the device joins securely as soon as it is powered on, no button "
            "presses needed.",
        ],
        "links": [ZJS_S2, ZJS_COMMON],
    },
    {
        "id": "security", "group": "zwave", "title": "Security: S0 and S2",
        "summary": "Encryption keeps commands private; S0 costs three times the airtime, S2 does not.",
        "body": [
            "Z-Wave can encrypt messages so that nobody nearby can read or fake them. There are two "
            "generations:",
            [
                "**S0** (legacy) uses one shared key and a weak key exchange. Worse, every encrypted command "
                "needs a fresh random number (a **nonce**) from the receiver first: *ask for a nonce*, *get "
                "the nonce*, *send the command*. That is three messages instead of one, so S0 roughly "
                "**triples the traffic**.",
                "**S2** uses modern key exchange and keeps nonces in sync on both ends, so a normal command "
                "is a single message. It has three levels: *Unauthenticated*, *Authenticated* and *Access "
                "Control* (locks, garage doors).",
            ],
            "For S2 Authenticated and Access Control you confirm the device during inclusion by typing the "
            "first five digits of its **DSK** (device specific key), printed on the device or its QR code.",
            "Encrypt what needs it: locks, garage doors, alarm sensors. Plain lights and power meters gain "
            "little from S0 and pay for it in airtime. If a device supports S2, use S2.",
            "A Zniffer cannot read encrypted messages without the network keys, so zwlens labels them "
            "*encrypted* and shows only the wrapper. See [[faq-security]].",
        ],
        "links": [ZJS_S2],
    },
    {
        "id": "command-classes", "group": "zwave", "title": "Command classes",
        "summary": "The vocabulary devices speak: Binary Switch, Battery, Meter and so on.",
        "body": [
            "Every Z-Wave message belongs to a **command class**: a group of related commands for one "
            "feature. For example *Binary Switch* has *Set*, *Get* and *Report*; *Battery* reports the "
            "level; *Meter* reports energy use; *Door Lock* locks and unlocks.",
            "During the [[inclusion|interview]] a device lists the command classes it supports in its "
            "**node information frame** (NIF). zwlens uses the command classes it sees to guess each node's "
            "*Type* on the Nodes tab.",
            "Some command classes wrap others (see [[g-encapsulation|encapsulation]]): *Security 2* encrypts "
            "a command, *Multi Channel* addresses one socket of a power strip, [[supervision|Supervision]] "
            "asks for confirmation, *Transport Service* splits a long message into pieces.",
        ],
        "links": [SL_FUND, SL_MC],
    },
    {
        "id": "associations", "group": "zwave", "title": "Associations and the lifeline",
        "summary": "Who a device reports to; group 1 must point at the controller.",
        "body": [
            "An **association** tells a device who to send its reports or commands to. Associations are "
            "organised in numbered **groups**.",
            "**Group 1, the lifeline**, is where a device sends its status updates: \"I turned on\", "
            "\"motion detected\", \"battery 80%\". It must point at the controller. If it does not, the "
            "device works when you control it but never reports changes made by hand, and its state in "
            "your app goes stale.",
            "Other groups let devices control each other directly, for example a switch that turns on a "
            "lamp module without going through the controller.",
            "Most controllers set the lifeline automatically during inclusion. If a device stops reporting, "
            "a re-interview usually repairs it.",
        ],
        "links": [SL_ASSOC, ZJS_COMMON],
    },
    {
        "id": "supervision", "group": "zwave", "title": "Supervision",
        "summary": "An application-level \"done\" receipt on top of the radio ACK.",
        "body": [
            "An [[acks|ACK]] only proves the radio received a message. **Supervision** goes further: the "
            "sender wraps the command in a *Supervision Get* and the device answers with a *Supervision "
            "Report* saying whether it actually carried the command out (success, failure, or working on "
            "it).",
            "That makes control more reliable, especially for encrypted commands. It also means two extra "
            "messages per command, which you will see in Conversations tagged *Supervision*.",
        ],
        "links": [SL_FUND],
    },
    {
        "id": "multicast", "group": "zwave", "title": "Singlecast, multicast and broadcast",
        "summary": "One receiver, a group, or everyone.",
        "body": [
            [
                "**Singlecast**: one sender, one receiver, with an [[acks|ACK]]. Almost all traffic.",
                "**Multicast**: one message addressed to a list of nodes at once, for example to switch a "
                "group of lights together. There is no ACK, so controllers usually follow up with a "
                "singlecast to each device.",
                "**Broadcast**: addressed to node 255, heard by every node in range. Used for things like "
                "\"I just woke up\" or network discovery.",
            ],
        ],
        "links": [SL_NET],
    },
    {
        "id": "long-range", "group": "zwave", "title": "Z-Wave Long Range",
        "summary": "Direct links of a kilometre or more, no mesh, node IDs from 256.",
        "body": [
            "**Z-Wave Long Range** (LR) is a newer mode supported by 800-series (and some 700-series) "
            "hardware. Instead of a mesh, it uses a **star**: every LR device talks **directly** to the "
            "controller, with no repeaters, over distances that can exceed a kilometre outdoors.",
            [
                "LR runs at 100 kbit/s on its own channels and adjusts transmit power automatically.",
                "LR node IDs start at **256**, so you can tell them apart at a glance.",
                "LR devices must use [[security|S2]] and are normally added with [[inclusion|SmartStart]].",
                "Classic mesh devices and LR devices can share one controller.",
            ],
            "Because there are no repeaters, an LR device that cannot hear the controller has no fallback; "
            "the fix is controller placement or antenna, not more devices.",
        ],
        "links": [ZWA_LR, ZJS_LR],
    },
    {
        "id": "zniffer", "group": "zwave", "title": "Controllers vs Zniffers: why you need a second stick",
        "summary": "A controller only hears messages for itself; a Zniffer hears everything.",
        "body": [
            "Your **controller** is a member of the network. Its radio filters out everything not addressed "
            "to it, so it never sees messages between other devices, retries it did not send, or "
            "neighbouring networks. Its logs show only its own side of each conversation.",
            "A **Zniffer** is a Z-Wave stick with sniffer firmware. It does not join any network and never "
            "transmits; it records every frame it hears on its region's frequency, with signal strength and "
            "data rate.",
            "One stick cannot be both at once, so troubleshooting with a Zniffer needs **a second stick**. "
            "Many 700 and 800-series sticks can be switched to Zniffer firmware and back. Keep your real "
            "controller stick as it is: reflashing it wipes your network unless you have a backup.",
            "A Zniffer only hears what reaches it. Place it near the controller for an overall view, or near "
            "a problem device to see that device's side.",
        ],
        "links": [ZJS_ZNIFFER, HA_ADAPTERS],
    },

    # ------------------------------------------------------------------ why does zwlens say...
    {
        "id": "faq-unreachable", "group": "faq", "title": "\"Unreachable or dead nodes\"",
        "summary": "A node did not answer, was marked dead, or failed its interview.",
        "body": [
            "This troubleshooter looks for nodes the controller struggles to reach:",
            [
                "**Marked dead** (critical): the controller gave up on the node after repeated failures.",
                "**Messages not delivered**: at least 3 attempts and 15% or more failed (critical at 50%).",
                "**Accepted commands but did not answer**: the radio [[acks|ACK]] arrived but the expected "
                "report never did; often a device firmware problem or a full queue.",
                "**Interview failed**: the controller could not finish asking the device what it is.",
            ],
            "Common causes: the device lost power or its battery is flat; it is out of range with no "
            "[[mesh|repeater]] in between; it was removed without exclusion (a ghost node, see "
            "[[inclusion]]); or a repeater on its [[routing|route]] has gone.",
            "Battery devices that are simply [[sleeping|asleep]] are not dead; controllers that mark them "
            "dead between wake-ups are misbehaving.",
        ],
        "links": [ZJS_COMMON],
    },
    {
        "id": "faq-signal", "group": "faq", "title": "\"Weak signal and interference\"",
        "summary": "Weak devices, a noisy channel, or speed fallback.",
        "body": [
            "This troubleshooter reads the [[signal|signal strength]] recorded by a Zniffer:",
            [
                "**High noise floor**: background noise of −85 dBm or more (critical above −75 dBm). Look for "
                "USB 3 ports or hubs near the stick, cheap power supplies, LED drivers, and other 800–900 MHz "
                "radios. A short USB extension cable to move the stick away from the computer often helps.",
                "**Weak node**: heard weaker than −85 dBm (critical below −92 dBm), or less than 10 dB above "
                "the noise.",
                "**Speed fallback**: a node that supports 100 kbit/s often used a slower "
                "[[data-rates|rate]], a sign its link is marginal.",
                "**The sniffer hears every node weakly**, the controller included: the Zniffer is probably "
                "badly placed (far away, behind metal) or its chip setting is wrong, so zwlens skips the "
                "per-node weak-signal checks. Move it or fix the setting in [[files]].",
            ],
            "Remember the Zniffer measures signal where it sits. Before moving devices, put the Zniffer "
            "near the controller and capture again.",
        ],
        "links": [ZJS_FIRST],
    },
    {
        "id": "faq-routing", "group": "faq", "title": "\"Routing problems\"",
        "summary": "Broken routes, routes that keep changing, long paths, explorer frames.",
        "body": [
            "This troubleshooter looks at the [[routing|routes]] messages took:",
            [
                "**A route broke**: a repeater along the way could not pass the message on.",
                "**Switched routes many times**: more than two changes during the capture means the "
                "controller keeps searching for something that works.",
                "**Long routes**: 3 repeaters is a note, 4 (the maximum) a warning. Each hop adds delay and "
                "another chance to fail.",
                "**Needed retries but got through**: over 30% retries for a node whose messages are still "
                "delivered: its first route usually fails and a fallback saves it.",
                "**Explorer frames**: the controller had to search the whole mesh for a path (warning from "
                "10).",
            ],
            "Usual fixes: add a mains-powered [[mesh|repeater]] between the controller and the far "
            "devices, move the controller to a central spot, remove ghost nodes, then rebuild routes for "
            "the affected nodes.",
        ],
        "links": [ZJS_FIRST, SL_NET],
    },
    {
        "id": "faq-congestion", "group": "faq", "title": "\"Congestion and chatty devices\"",
        "summary": "Too much traffic for the channel, often from one or two devices.",
        "body": [
            "Z-Wave is slow, and only one device can talk at a time in range. This troubleshooter checks "
            "whether the channel is getting crowded:",
            [
                "**Channel busy**: the share of time someone was transmitting. Above 5% is a warning, above "
                "15% critical; at that point commands start to queue and feel laggy.",
                "**Chatty device**: a node sending over 30% of all device traffic, or more than 20 messages a "
                "minute. Power meters reporting every few seconds are the classic culprit.",
                "**Slow commands**: a median of over 300 ms from sending a command to its delivery.",
                "**Transmission failed with status 'Fail'**: the controller could not get airtime at all.",
                "**Many retransmissions**: over 10% of all messages needed a retry.",
            ],
            "Fixes: raise the reporting interval or threshold on chatty devices (in their configuration "
            "parameters), turn off polling in your controller, and move chatty devices from "
            "[[security|S0]] to S2 or no encryption.",
        ],
        "links": [ZJS_FIRST],
    },
    {
        "id": "faq-security", "group": "faq", "title": "\"Security overhead and failures\"",
        "summary": "Unencrypted locks, S2 resyncs, decryption failures, S0 overhead.",
        "body": [
            "This troubleshooter looks at [[security|encryption]]:",
            [
                "**Lock or garage door without encryption** (critical): anyone nearby could replay or forge "
                "its commands. Exclude and re-include it securely.",
                "**Lost S2 synchronisation**: both ends had to resynchronise their nonces repeatedly; "
                "usually a sign of lost messages or a device firmware bug.",
                "**Could not be decrypted / no valid nonce**: the device and controller disagree about keys "
                "or nonces. Re-including the device usually fixes it.",
                "**Chatty S0 device** or **much of the traffic uses S0**: every S0 command costs three "
                "messages, so busy S0 devices triple their airtime. Re-include them with S2, or without "
                "encryption if they do not need it.",
            ],
            "A Zniffer cannot read encrypted content without your network keys, so encrypted messages show "
            "only as *encrypted* in Conversations. That is expected, not an error.",
        ],
        "links": [ZJS_S2, ZJS_COMMON],
    },
    {
        "id": "faq-node-health", "group": "faq", "title": "\"Healthy\", \"Marginal\" and \"Failing\" nodes",
        "summary": "How each node's health label on the Nodes tab is decided.",
        "body": [
            [
                "**Failing**: the controller marked the node dead, or at least half of 3 or more messages to "
                "it were not delivered.",
                "**Marginal**: 15% or more undelivered; or heard weaker than −85 dBm; or a route to it broke; "
                "or it accepted a command without answering; or its route changed more than twice.",
                "**Healthy**: traffic seen and none of the above.",
                "**Unknown**: zwlens saw no traffic from or to this node in the capture.",
            ],
            "Node health describes one node; the [[health-score|health score]] summarises the whole network.",
        ],
        "links": [],
    },
    {
        "id": "faq-score", "group": "faq", "title": "\"Needs attention\" or \"Unhealthy\"",
        "summary": "Why the health score is low, and why it may be high but wrong.",
        "body": [
            "The score drops by 15 for each critical finding, 6 for each warning and 1 for each note. Open "
            "**Troubleshoot** to see every finding, or follow the **Suggestions** on Overview, which list "
            "the worst first. Fixing one critical problem often clears several warnings with it.",
            "A perfect score from a 30-second capture of an idle network proves little. Capture for several "
            "minutes while you switch lights, open doors and trigger sensors. See [[health-score]].",
        ],
        "links": [],
    },
    {
        "id": "faq-encrypted", "group": "faq", "title": "\"encrypted\" on messages",
        "summary": "Why some message content cannot be shown.",
        "body": [
            "Messages protected by [[security|S0 or S2]] can only be read with your network's keys, which "
            "zwlens does not have. It still shows who sent the message, when, its route, signal and whether "
            "it was delivered, which is what most troubleshooting needs.",
            "With a Z-Wave JS log or live controller connection, zwlens sees the decrypted commands because "
            "the controller logs them after decrypting.",
        ],
        "links": [ZJS_S2],
    },
    {
        "id": "faq-other-networks", "group": "faq", "title": "\"other networks\" or unknown home IDs",
        "summary": "Your Zniffer is also hearing your neighbours.",
        "body": [
            "A Zniffer hears every Z-Wave network in range. zwlens treats the [[ids|home ID]] with the most "
            "traffic as yours and labels the rest *other networks*. They are hidden by default; tick *Other "
            "networks* to see them.",
            "Neighbouring networks share the same channel, so a very busy neighbour can add to "
            "[[faq-congestion|congestion]], but you cannot control their devices.",
        ],
        "links": [],
    },
    {
        "id": "faq-no-traffic", "group": "faq", "title": "Capture running but no frames",
        "summary": "Wrong region, wrong chip, busy port or simply a quiet network.",
        "body": [
            [
                "Check the **Radio region** matches your network ([[frequencies]]).",
                "Make sure the stick really runs Zniffer firmware, not controller firmware.",
                "Operate a device (switch a light) to generate traffic: idle networks can be silent for "
                "minutes.",
                "If zwlens says the port is in use, another program has the stick; see [[live-zniffer]].",
                "On Linux, a permission error means your user is not yet in the `dialout` group.",
            ],
        ],
        "links": [ZJS_ZNIFFER],
    },
]

GLOSSARY = [
    ("ACK", "Acknowledgement: a short reply confirming a message arrived over the radio.", "acks"),
    ("Airtime / channel busy", "The share of time someone was transmitting. Only one device in range can "
     "talk at a time, so high airtime means waiting.", "faq-congestion"),
    ("Association", "A setting telling a device who to send reports or commands to, organised in groups.",
     "associations"),
    ("Beam (wake-up beam)", "A burst of short messages that wakes a FLiRS device before a command is sent.",
     "flirs"),
    ("Broadcast", "A message to node 255, heard by every node in range.", "multicast"),
    ("Command class (CC)", "A group of related commands for one feature, such as Binary Switch or Battery.",
     "command-classes"),
    ("Controller", "The device that runs the network: adds and removes devices and computes routes. "
     "Usually your hub or USB stick.", "zwave"),
    ("Conversation", "zwlens's grouping of messages between the same two nodes until a few seconds of "
     "silence.", "tab-conversations"),
    ("CRC / checksum", "A few bytes that let the receiver detect a corrupted message. \"Bad checksum\" means "
     "the frame was damaged on the way.", "acks"),
    ("Data rate", "Transmission speed: 9.6, 40 or 100 kbit/s.", "data-rates"),
    ("dBm", "The unit for signal strength. Negative numbers; closer to zero is stronger.", "signal"),
    ("Dead node", "A node the controller has given up on after repeated failures.", "faq-unreachable"),
    ("DSK", "Device specific key: a code printed on S2 devices. You type its first five digits to confirm "
     "the device during secure inclusion.", "security"),
    ("Encapsulation", "Wrapping one command inside another, for example to encrypt it (S0, S2), address an "
     "endpoint (Multi Channel), ask for confirmation (Supervision) or split it (Transport Service). zwlens "
     "shows these as small tags.", "command-classes"),
    ("End device", "A node that only sends and receives for itself and never repeats for others.", "mesh"),
    ("Exclusion", "Removing a device from a network and resetting it so it can join another.", "inclusion"),
    ("Explorer frame", "A search message the controller floods through the mesh when no known route works.",
     "routing"),
    ("Failed (ghost) node", "A node still listed by the controller although the device is gone.",
     "inclusion"),
    ("FLiRS", "Frequently listening routing slave: a battery device, typically a lock, that sleeps but "
     "checks for a wake-up beam every 250 ms or 1 s.", "flirs"),
    ("Frame", "One radio transmission: a message, an ACK, a beam fragment.", "tab-frames"),
    ("Health score", "zwlens's 0 to 100 summary of the problems found in a capture.", "health-score"),
    ("Home ID", "A 32-bit number identifying one Z-Wave network, carried in every message.", "ids"),
    ("Hop", "One step of a route: from one device to the next.", "routing"),
    ("Inclusion", "Adding a device to a network.", "inclusion"),
    ("Interview", "After inclusion, the controller asking a device what it is and what it supports.",
     "inclusion"),
    ("Jammed", "A controller reporting it cannot transmit because the channel is never free, usually due to "
     "interference or a misbehaving device.", "faq-congestion"),
    ("Lifeline", "Association group 1, where a device sends its status reports. Must point at the "
     "controller.", "associations"),
    ("Long Range (LR)", "A star-topology Z-Wave mode with direct links over long distances, no repeaters, "
     "and node IDs from 256.", "long-range"),
    ("LWR (last working route)", "The route that succeeded most recently; the controller tries it first.",
     "routing"),
    ("Mains-powered", "Plugged in or wired, so always listening and able to repeat.", "mesh"),
    ("Mesh", "A network in which devices relay messages for each other.", "mesh"),
    ("Multi Channel", "A command class for devices with several endpoints, like a double switch or power "
     "strip.", "command-classes"),
    ("Multicast", "One message addressed to several nodes at once, without ACKs.", "multicast"),
    ("NIF (node information frame)", "A message in which a device lists its type and supported command "
     "classes.", "command-classes"),
    ("Node / node ID", "A device in the network, and its number (1 to 232 for mesh, 256 and up for Long "
     "Range).", "ids"),
    ("Noise floor", "The background radio level when nobody is transmitting. Lower (more negative) is "
     "better.", "signal"),
    ("Nonce", "A one-time random number used in encryption. S0 fetches one per command; S2 keeps them in "
     "sync.", "security"),
    ("NoAck / Fail", "Delivery results: NoAck means the receiver never confirmed; Fail means the controller "
     "could not transmit at all.", "acks"),
    ("NVM", "Non-volatile memory: where a controller stores the network (home ID, nodes, routes, keys). "
     "Back it up before firmware updates or swapping sticks.", "zniffer"),
    ("Priority route", "A route you assign by hand that the controller tries first.", "routing"),
    ("Rebuild routes (heal)", "Asking devices to re-measure their neighbours and receive fresh routes.",
     "routing"),
    ("Region", "The set of frequencies a network uses, fixed by country.", "frequencies"),
    ("Repeater", "A mains-powered node that forwards messages for others.", "mesh"),
    ("Retransmission (retry)", "Sending the same message again because no ACK came back.", "acks"),
    ("Route", "The list of repeaters a message passes through, up to four.", "routing"),
    ("Routed ACK", "The end-to-end confirmation sent back along a route by the destination.", "acks"),
    ("RSSI", "Received signal strength indicator: how strong a message was on arrival, in dBm.", "signal"),
    ("S0", "Legacy Z-Wave encryption. Every command needs a nonce exchange, so it triples traffic.",
     "security"),
    ("S2", "Current Z-Wave encryption, with Unauthenticated, Authenticated and Access Control levels.",
     "security"),
    ("SDR", "Software-defined radio: a general-purpose radio receiver that can also capture Z-Wave.",
     "files"),
    ("Sequence number", "A counter in each message that lets receivers spot duplicates.", "acks"),
    ("Signal margin", "How far a signal stands above the noise floor, in dB. zwlens wants at least 10.",
     "signal"),
    ("Singlecast", "A message from one node to one other node, acknowledged.", "multicast"),
    ("Sleeping device", "A battery device that keeps its radio off and wakes on a timer.", "sleeping"),
    ("SmartStart", "Inclusion by scanning a QR code in advance; the device joins when powered on.",
     "inclusion"),
    ("SOS (S2 resync)", "An S2 device telling the sender its nonces are out of step, forcing a "
     "resynchronisation.", "faq-security"),
    ("SUC / SIS", "Static update controller / SUC ID server: the controller role that keeps the master "
     "list of nodes and hands out node IDs. Usually your main controller.", "zwave"),
    ("Supervision", "A command class that confirms a command was actually carried out.", "supervision"),
    ("Transport Service", "A command class that splits long messages into pieces.", "command-classes"),
    ("Wake-up interval", "How often a sleeping device wakes to collect queued commands.", "sleeping"),
    ("Z-Wave JS", "Open-source Z-Wave software used by Home Assistant and Z-Wave JS UI.", "live-controller"),
    ("Z-Wave Plus", "A certification level requiring newer features, such as the lifeline and better "
     "range.", "zwave"),
    ("ZLF", "The Zniffer capture file format (.zlf).", "saving"),
    ("Zniffer", "A Z-Wave stick with sniffer firmware that records all traffic without joining a network.",
     "zniffer"),
    ("500 / 700 / 800 series", "Generations of Silicon Labs Z-Wave chips. 700 and 800 have better range and "
     "power use; 800 adds Long Range in more regions.", "zniffer"),
]


def _slug(text: str) -> str:
    return "g-" + re.sub(r"[^a-z0-9]+", "-", text.lower().split(" (")[0].split(" / ")[0]).strip("-")


def glossary() -> list:
    return [{"id": _slug(term), "term": term, "text": text, "see": see} for term, text, see in GLOSSARY]


def help_data() -> dict:
    """Everything the Help tab needs, as plain JSON-ready data."""
    sections = [dict(s) for s in SECTIONS]
    sections.append({"id": "glossary", "group": "ref", "title": "Glossary",
                     "summary": "Every Z-Wave and zwlens term used in the app, in one place.",
                     "body": [], "links": [ZJS_DOCS]})
    return {"groups": [{"id": g, "title": t} for g, t in GROUPS], "sections": sections,
            "glossary": glossary()}
