#!/bin/sh
# Start SeeWave and open it in your browser. Linux and macOS.
cd "$(dirname "$0")" || exit 1
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then exec "$py" -m seewave "$@"; fi
done
echo "Python 3.9 or newer is required: https://www.python.org/downloads/"
exit 1
