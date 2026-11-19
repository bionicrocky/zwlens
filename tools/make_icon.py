"""Regenerate zwlens/web/favicon.ico from the logo's geometry. Developer tool; needs Pillow."""
import math
from pathlib import Path

from PIL import Image, ImageDraw

S = 16  # supersampling: draw at 64*S pixels, then scale down
GREY, BLUE = (122, 134, 153, 255), (37, 99, 217, 255)


def stroke(d, pts, width, colour):
    w = width * S
    d.line([(x * S, y * S) for x, y in pts], fill=colour, width=int(w), joint="curve")
    for x, y in (pts[0], pts[-1]):  # round caps
        d.ellipse([x * S - w / 2, y * S - w / 2, x * S + w / 2, y * S + w / 2], fill=colour)


img = Image.new("RGBA", (64 * S, 64 * S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.ellipse([(27 - 19) * S, (27 - 19) * S, (27 + 19) * S, (27 + 19) * S], outline=GREY, width=5 * S)
stroke(d, [(41, 41), (57, 57)], 7, GREY)
wave = []
for k in range(4):  # four quadratic arcs, alternating up and down, as in the SVG path
    x0, sign = 13 + 7 * k, (-1 if k % 2 == 0 else 1)
    for i in range(21):
        t = i / 20
        wave.append((x0 + 7 * t, 27 + sign * 10 * 2 * t * (1 - t)))
stroke(d, wave, 4, BLUE)
out = Path(__file__).resolve().parent.parent / "zwlens" / "web" / "favicon.ico"
img.resize((256, 256), Image.LANCZOS).save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote", out, out.stat().st_size, "bytes")
