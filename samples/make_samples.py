"""Write the synthetic sample captures to this folder.

    python samples/make_samples.py

The same samples can be loaded from the app's Data tab without running this.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zwlens.parsers.zlf import write_zlf  # noqa: E402
from zwlens.sample_data import sdr_text, sniffer_entries, zwavejs_log  # noqa: E402,F401


def main():
    here = Path(__file__).resolve().parent
    (here / "zniffer-sample.zlf").write_bytes(write_zlf(sniffer_entries()))
    (here / "sdr-sample.txt").write_text(sdr_text(), encoding="utf-8")
    (here / "zwavejs-sample.log").write_text(zwavejs_log(), encoding="utf-8")
    print("wrote", ", ".join(p.name for p in sorted(here.glob("*-sample.*"))))


if __name__ == "__main__":
    main()
