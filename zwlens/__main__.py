"""Command line entry point: `python -m zwlens serve` or `python -m zwlens analyze`."""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from . import __version__
from .aliases import AliasStore
from .analysis import analyze, report_markdown
from .parsers import parse_bytes
from .server import Session, serve


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to a legacy code page
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(prog="zwlens", description="Z-Wave traffic analyzer")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd")

    def common(sp):
        sp.add_argument("files", nargs="*", help="Z-Wave JS logs, .zlf Zniffer captures, SDR text or pcap files")
        sp.add_argument("--aliases", help="path of the aliases JSON file")
        sp.add_argument("--zniffer-chip", choices=["500", "700"], default="700",
                        help="chip series of the Zniffer stick, for RSSI conversion (default 700/800)")

    s = sub.add_parser("serve", help="start the web UI (default)")
    common(s)
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8377)
    s.add_argument("--live", metavar="WS_URL", help="connect to a Z-Wave JS server, e.g. ws://localhost:3000")
    s.add_argument("--zniffer", metavar="PORT",
                   help="capture live from a Zniffer stick, e.g. /dev/ttyUSB0 or COM5")
    s.add_argument("--zniffer-frequency", type=int, metavar="ID",
                   help="switch the Zniffer stick to this frequency/region id before capturing")
    s.add_argument("--no-browser", action="store_true")

    a = sub.add_parser("analyze", help="print a report and exit")
    common(a)
    a.add_argument("--format", choices=["text", "json"], default="text")

    sub.add_parser("ports", help="list serial ports that may be a Zniffer stick")

    args = p.parse_args(argv if argv is not None else sys.argv[1:] or ["serve"])
    if args.cmd is None:
        p.print_help()
        return 2
    if args.cmd == "ports":
        from .zniffer_live import list_ports
        ports = list_ports()
        for port in ports:
            print(f"{port['path']}\t{port['label']}")
        if not ports:
            print("No serial ports found.", file=sys.stderr)
        return 0
    aliases = AliasStore(args.aliases)

    if args.cmd == "analyze":
        if not args.files:
            a.error("give at least one capture file")
        frames = []
        for name in args.files:
            try:
                res = parse_bytes(Path(name).read_bytes(), Path(name).name, args.zniffer_chip)
            except OSError as exc:
                print(f"{name}: {exc}", file=sys.stderr)
                return 1
            for w in res.warnings:
                print(f"{name}: {w}", file=sys.stderr)
            frames += res.frames
        result = analyze(frames, aliases.name)
        print(json.dumps(result, indent=1) if args.format == "json" else report_markdown(result))
        return 0

    session = Session(aliases, args.zniffer_chip)
    for name in args.files:
        try:
            info = session.add(Path(name).name, Path(name).read_bytes())
        except OSError as exc:
            print(f"{name}: {exc}", file=sys.stderr)
            continue
        print(f"{name}: {info['frames']} frames ({info['kind']})")
        for w in info["warnings"]:
            print(f"  note: {w}")
    if args.live and args.zniffer:
        s.error("use either --live or --zniffer, not both")
    if args.live:
        session.start_live(args.live)
    if args.zniffer:
        from .zniffer_live import port_holders
        for h in port_holders(args.zniffer):
            print(f"note: {args.zniffer} is in use by {h['name']} (process {h['pid']}). Close that program, "
                  f"or run 'kill {h['pid']}', then press Capture in the Data tab.")
        session.start_live(args.zniffer, args.zniffer_frequency)
    try:
        httpd = serve(session, args.host, args.port)
    except OSError as exc:
        print(f"Could not listen on {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 1
    shown = "localhost" if args.host in ("127.0.0.1", "0.0.0.0") else args.host
    url = f"http://{shown}:{httpd.server_address[1]}/"
    print(f"zwlens {__version__} running at {url}  (Ctrl+C to stop)")
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print("warning: listening on a non-loopback address; anyone who can reach it can load captures.")
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        session.stop_live()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
