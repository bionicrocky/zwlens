"""Regenerate seewave/web/favicon.ico from the logo's geometry. Developer tool; needs Pillow."""
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
for cx in (17, 47):  # the two lenses
    d.ellipse([(cx - 12) * S, (36 - 12) * S, (cx + 12) * S, (36 + 12) * S], outline=GREY, width=5 * S)
stroke(d, [(28 + 8 * i / 20, 33 - 6 * 2 * (i / 20) * (1 - i / 20)) for i in range(21)], 4, GREY)  # bridge
stroke(d, [(5.5, 31.5), (2.5, 24)], 4, GREY)  # temples
stroke(d, [(58.5, 31.5), (61.5, 24)], 4, GREY)
for left in (9, 39):  # a wave in each lens: four quadratic arcs, alternating up and down, as in the SVG path
    wave = []
    for k in range(4):
        x0, sign = left + 4 * k, (-1 if k % 2 == 0 else 1)
        for i in range(21):
            u = i / 20
            wave.append((x0 + 4 * u, 36 + sign * 7 * 2 * u * (1 - u)))
    stroke(d, wave, 3.5, BLUE)
out = Path(__file__).resolve().parent.parent / "seewave" / "web" / "favicon.ico"
img.resize((256, 256), Image.LANCZOS).save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote", out, out.stat().st_size, "bytes")
