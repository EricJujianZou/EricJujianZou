"""High-fidelity ASCII art of a building photo, white on black, for the profile banner.
Each cell's glyph density and its grey level both follow the photo's brightness there,
with local contrast boosted so facade detail survives at this size.
toronto: "Sunset Toronto Skyline Panorama Crop from Snake Island" by Jchmrt, CC BY-SA 4.0, Wikimedia Commons.
e7: Engineering 7, University of Waterloo, at dusk.
usage: ascii_art.py toronto|e7 out.svg [rows]  (rows caps the height and right-aligns the art)"""
import base64, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PRESET, OUT = sys.argv[1], sys.argv[2]
FIT_ROWS = int(sys.argv[3]) if len(sys.argv) > 3 else None   # optional cap on the art height in rows
W, H = 880, 300
FS = 4.8                       # font size in the svg
CW, LH = FS * 0.6, 5.2         # Plex Mono advance, line height
COLS, ROWS = int(W / CW), int(H / LH)
FONT = os.path.join(HERE, "fonts/ibm-plex-mono-400.woff2")
RAMP = ".'`,:;-~=+*xo%#8@"     # sparse to dense, like the reference city
GREYS = 12                     # grey steps from dim to white

PRESETS = {
    "toronto": dict(photo="skyline-toronto.jpg", crop=(0, 80, 1920, 630), seg="darker", local=1.6, gamma=0.75, floor=0.32),
    "e7": dict(photo="skyline-e7.jpg", crop=(0, 200, 1650, 900), seg="colour", local=1.4, gamma=0.85, floor=0.3),
}
P = PRESETS[PRESET]

# fit the crop inside the banner, keeping its aspect, bottom-aligned and centred
im = Image.open(os.path.join(HERE, P["photo"])).convert("RGB").crop(P["crop"])
cell_aspect = LH / CW
gw = COLS
gh = round(gw * im.size[1] / im.size[0] / cell_aspect)
if gh > (FIT_ROWS or ROWS):
    gh = FIT_ROWS or ROWS
    gw = round(gh * cell_aspect * im.size[0] / im.size[1])
ox, oy = (COLS - gw) // 2 if not FIT_ROWS else COLS - gw, ROWS - gh

# sky mask per cell, walking down each column until the photo leaves the sky
rgb = np.asarray(im.filter(ImageFilter.GaussianBlur(2)).resize((gw, gh), Image.BOX), dtype=np.float32)
LUM = np.array([0.299, 0.587, 0.114], dtype=np.float32)
mask = np.zeros((gh, gw), bool)
for x in range(gw):
    sky = rgb[0, x].copy()
    for y in range(gh):
        c = rgb[y, x]
        if P["seg"] == "darker":
            hit = c @ LUM < 0.72 * (sky @ LUM)
            if not hit: sky = c if c.sum() > sky.sum() else sky * 0.97
        else:
            hit = np.linalg.norm(c - sky) > 30
            if not hit: sky = 0.5 * sky + 0.5 * c
        if hit:
            mask[y:, x] = True
            break

# tone per cell: boost local contrast so facade detail survives, stretch the building's own range, sky is black
L = im.convert("L")
Lf = np.asarray(L, dtype=np.float32)
big = np.asarray(L.filter(ImageFilter.GaussianBlur(max(L.size) / 60)), dtype=np.float32)
Lf = np.clip(Lf + P["local"] * (Lf - big), 0, 255).astype(np.uint8)
t = np.asarray(Image.fromarray(Lf).resize((gw, gh), Image.BOX), dtype=np.float32) / 255
lo, hi = np.percentile(t[mask], [2, 99.7])
t = np.clip((t - lo) / (hi - lo + 1e-6), 0, 1) ** P["gamma"]
t = np.where(mask, P["floor"] + (1 - P["floor"]) * t, 0)   # buildings read as solid against the black sky

# density and grey both follow tone; one text row per grey step so each glyph keeps its own grey
idx = np.clip((t * len(RAMP)).astype(int), 0, len(RAMP) - 1)
level = np.clip((t * GREYS).astype(int), 0, GREYS - 1)
rows = {g: [[" "] * COLS for _ in range(ROWS)] for g in range(GREYS)}
for y in range(gh):
    for x in range(gw):
        if mask[y, x]: rows[level[y, x]][oy + y][ox + x] = RAMP[idx[y, x]]

def grey(g): v = round(70 + (255 - 70) * (g / (GREYS - 1)) ** 0.9); return f"#{v:02x}{v:02x}{v:02x}"
def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

font = base64.b64encode(open(FONT, "rb").read()).decode()
# black silhouette of the building, so anything layered under it (the big title) reads as behind
runs = []
for y in range(gh):
    x = 0
    while x < gw:
        if mask[y, x]:
            x1 = x
            while x1 < gw and mask[y, x1]: x1 += 1
            runs.append(f'<rect x="{(ox + x) * CW:.1f}" y="{(oy + y) * LH:.1f}" width="{(x1 - x) * CW + 0.3:.1f}" height="{LH + 0.3:.1f}"/>')
            x = x1
        else: x += 1
body = [f'<g id="occluder" fill="#000" opacity="0.8">{"".join(runs)}</g>']
for g in range(GREYS):
    lines = "".join(f'<text x="0" y="{(y + 1) * LH - 1.2:.1f}">{esc("".join(r).rstrip())}</text>'
                    for y, r in enumerate(rows[g]) if "".join(r).strip())
    if lines: body.append(f'<g fill="{grey(g)}">{lines}</g>')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
       f'<style>@font-face{{font-family:"PM";src:url(data:font/woff2;base64,{font}) format("woff2")}}'
       f'text{{font-family:"PM",Menlo,monospace;font-size:{FS}px;white-space:pre}}</style>'
       f'<rect width="{W}" height="{H}" fill="#000"/>{"".join(body)}</svg>')
open(OUT, "w").write(svg)
print(f"{PRESET}: {gw}x{gh} cells at ({ox},{oy}), {int(mask.sum())} glyphs, {len(svg)//1024} KB")
