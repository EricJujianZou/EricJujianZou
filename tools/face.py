"""Face point-cloud SVG banners from a cut-out photo.
Port of waterlooagi.com assets/members.js sampleFace(); the yaw turn is baked in as SMIL keyframes on depth layers.
usage: face.py photo.webp outdir"""
import math, sys, json, base64, os
from PIL import Image
from ansi_title import ansi_title

SRC, OUT = sys.argv[1], sys.argv[2]
G = 192
HERE = os.path.dirname(os.path.abspath(__file__))

def rng(seed):
    s = [seed & 0xffffffff]
    def r():
        s[0] = (s[0] + 0x6D2B79F5) & 0xffffffff
        t = s[0]
        t = ((t ^ (t >> 15)) * (1 | t)) & 0xffffffff
        t = (t + (((t ^ (t >> 7)) * (61 | t)) & 0xffffffff) ^ t) & 0xffffffff
        return ((t ^ (t >> 14)) & 0xffffffff) / 4294967296
    return r

def box_blur(src, R):
    tmp = [0.0]*(G*G); out = [0.0]*(G*G)
    for j in range(G):
        for i in range(G):
            a = max(0, i-R); b = min(G-1, i+R)
            tmp[j*G+i] = sum(src[j*G+a:j*G+b+1])/(b-a+1)
    for j in range(G):
        for i in range(G):
            a = max(0, j-R); b = min(G-1, j+R)
            out[j*G+i] = sum(tmp[y*G+i] for y in range(a, b+1))/(b-a+1)
    return out

im = Image.open(SRC).convert("RGBA")
s = min(im.size); im = im.crop(((im.width-s)//2, (im.height-s)//2, (im.width-s)//2+s, (im.height-s)//2+s)).resize((G, G), Image.LANCZOS)
d = im.load()
L0 = [0.0]*(G*G); A = [0.0]*(G*G)
for j in range(G):
    for i in range(G):
        r, g, b, a = d[i, j]
        A[j*G+i] = a/255
        L0[j*G+i] = (0.2126*r + 0.7152*g + 0.0722*b)/255
hist = sorted(L0[i] for i in range(0, G*G, 3) if A[i] > 0.5)
lo = hist[int(len(hist)*0.03)]; hi = hist[int(len(hist)*0.985)]
L0 = [max(0, min(1, (v-lo)/max(0.05, hi-lo))) for v in L0]

def sample(count, seed, invert, dome=0.34):
    """invert=False: light points on dark ground (bright skin dense). invert=True: dark ink on paper (dark features dense)."""
    L = [1-v for v in L0] if invert else L0
    B = box_blur(L, 5)
    T = [max(0, min(1, 0.55*L[i] + 2.6*(L[i]-B[i]) + 0.12)) for i in range(G*G)]
    r = rng(seed); P = []; taken = bytearray(G*G); tries = 0
    while len(P) < count and tries < count*120:
        tries += 1
        u = r(); v = r(); px = int(u*G); py = int(v*G); k = py*G+px
        if taken[k] or A[k] < 0.4: continue
        t = T[k]
        if r() > A[k]*(0.035+0.965*t*t): continue
        taken[k] = 1
        dx = (u-.5)/.44; dy = (v-.47)/.52; rr = dx*dx+dy*dy
        z = dome*math.sqrt(max(0, 1-rr)) + (t-.5)*0.12
        P.append(((u-.5)*2.3, -(v-.47)*2.3, z, 0.2+0.8*t))
    cell = 0.09; grid = {}; edges = []
    for i, (x, y, z, t) in enumerate(P):
        grid.setdefault((math.floor(x/cell), math.floor(y/cell)), []).append(i)
    for i, (ax, ay, az, at) in enumerate(P):
        cx, cy = math.floor(ax/cell), math.floor(ay/cell); best = [(1e9, -1), (1e9, -1)]
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                for j in grid.get((cx+ox, cy+oy), ()):
                    if j == i: continue
                    dd = (P[j][0]-ax)**2 + (P[j][1]-ay)**2
                    if dd < best[0][0]: best = [(dd, j), best[0]]
                    elif dd < best[1][0]: best[1] = (dd, j)
        for dd, j in best:
            if j > i and dd < cell*cell: edges.append((i, j))
    return P, edges

NL = 24; STEPS = 48; DUR = 14
def yaw_at(t): return 0.55*math.sin(2*math.pi*t)**3
YAWS = [yaw_at(k/STEPS) for k in range(STEPS)] + [yaw_at(0)]
KT = ";".join(f"{k/STEPS:.4f}" for k in range(STEPS+1))
SCALE_VALS = ";".join(f"{math.cos(y):.4f} 1" for y in YAWS)

def motion(mode):
    if mode == "spin":
        n = 64; ts = [k/n for k in range(n+1)]
        yaws = [2*math.pi*(t - 0.18*math.sin(2*math.pi*t)) for t in ts]; dur = 16
    else:
        n = STEPS; ts = [k/n for k in range(n+1)]; yaws = [yaw_at(t) for t in ts]; dur = DUR
    kt = ";".join(f"{t:.4f}" for t in ts)
    return yaws, kt, dur

def face_group(P, edges, ink, F, cx, cy, with_edges, mode="turn"):
    yaws, kt, dur = motion(mode)
    zs = [p[2] for p in P]; zmin, zmax = min(zs), max(zs)
    def layer(z): return min(NL-1, int((z-zmin)/(zmax-zmin+1e-9)*NL))
    zc = [zmin + (k+0.5)*(zmax-zmin)/NL for k in range(NL)]
    sc = ";".join(f"{math.cos(y):.4f} 1" for y in yaws)
    op = ";".join(f"{0.25+0.75*(0.5+0.5*math.cos(y)):.3f}" for y in yaws)
    o = [f'<g transform="translate({cx:.1f} {cy:.1f})"><g>',
         f'<animate attributeName="opacity" values="{op}" keyTimes="{kt}" dur="{dur}s" repeatCount="indefinite"/>']
    for k in range(NL):
        tv = ";".join(f"{zc[k]*math.sin(y)*F:.1f} 0" for y in yaws)
        o.append(f'<g><animateTransform attributeName="transform" type="translate" values="{tv}" keyTimes="{kt}" dur="{dur}s" repeatCount="indefinite"/>'
                 f'<g><animateTransform attributeName="transform" type="scale" values="{sc}" keyTimes="{kt}" dur="{dur}s" repeatCount="indefinite"/>')
        if with_edges:
            seg = [f"M{P[i][0]*F:.0f} {-P[i][1]*F:.0f}L{P[j][0]*F:.0f} {-P[j][1]*F:.0f}" for i, j in edges if layer((P[i][2]+P[j][2])/2) == k]
            if seg: o.append(f'<path d="{"".join(seg)}" stroke="{ink}" stroke-opacity="0.22" stroke-width="0.6"/>')
        o.append("".join(f'<circle cx="{x*F:.0f}" cy="{-y*F:.0f}" r="{0.7+1.1*t:.1f}" fill="{ink}" fill-opacity="{0.35+0.65*t:.2f}"/>' for x, y, z, t in P if layer(z) == k) + "</g></g>")
    o.append("</g></g>")
    return "".join(o)

def b64(path): return base64.b64encode(open(path, "rb").read()).decode()
FONTS = ('<style>@font-face{font-family:"NR";src:url(data:font/woff2;base64,' + b64(os.path.join(HERE, "fonts/newsreader-latin.woff2")) + ') format("woff2")}'
         '@font-face{font-family:"PM";src:url(data:font/woff2;base64,' + b64(os.path.join(HERE, "fonts/ibm-plex-mono-400.woff2")) + ') format("woff2")}'
         '.nr{font-family:"NR",Georgia,serif}.pm{font-family:"PM",Menlo,monospace}</style>')
FONTS_PM = ('<style>@font-face{font-family:"PM";src:url(data:font/woff2;base64,' + b64(os.path.join(HERE, "fonts/ibm-plex-mono-400.woff2")) + ') format("woff2")}'
            '.pm{font-family:"PM",Menlo,monospace}</style>')
CURSOR = '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/>'

def svg(W, H, body, fonts=False):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" fill="none">'
            + ({True: FONTS, "pm": FONTS_PM}.get(fonts, "")) + body + "</svg>")

def build(theme):
    invert = theme == "light"
    ink = "#1a1a1a" if invert else "#e8e4da"
    soft = "#6b6b6b" if invert else "#9a9690"
    pen = "#1d6fd1" if invert else "#79a7ff"
    P3, E3 = sample(3000, 7, invert)
    P18, E18 = sample(1600, 11, invert)
    P45, E45 = sample(4500, 5, invert)
    out = {}
    # A. face only, centred
    out["a-face"] = svg(880, 300, face_group(P3, E3, ink, 118, 440, 150, True))
    # B. face left, name and one line right, serif
    # title in the ANSI Shadow block letters of the Claude Code welcome logo, subtitle in terminal mono
    name = (ansi_title("Eric Zou", 418, 98, 7, 13, ink, soft)
            + f'<text class="pm" x="418" y="210" font-size="15" fill="{soft}">I love to be proven wrong</text>')
    out["b-name"] = svg(880, 300, face_group(P3, E3, ink, 118, 200, 150, True) + name, fonts="pm")
    PD, ED = sample(3000, 7, invert, dome=0.55)
    out["b-spin"] = svg(880, 300, face_group(PD, ED, ink, 118, 200, 150, True, mode="spin") + name, fonts="pm")
    # C. face left, lab status in mono with a live cursor
    lines = ["running   ugmi, watnow, optimal", "last      scaffold-bench round 5, scaffold won", "proven wrong  3 times this year"]
    txt = "".join(f'<text class="pm" xml:space="preserve" x="400" y="{118+i*30}" font-size="15" fill="{ink if i==0 else soft}">{l}</text>' for i, l in enumerate(lines))
    txt += f'<rect x="400" y="206" width="9" height="17" fill="{pen}">{CURSOR}</rect>'
    out["c-status"] = svg(880, 300, face_group(P3, E3, ink, 118, 200, 150, True) + txt, fonts=True)
    # D. points only, denser, no edges
    out["d-points"] = svg(880, 300, face_group(P45, E45, ink, 118, 440, 150, False))
    # E. sparse constellation
    out["e-sparse"] = svg(880, 300, face_group(P18, E18, ink, 118, 440, 150, True))
    # F. editorial: big face right, bleeding off the bottom, name bottom left
    out["f-editorial"] = svg(880, 360, face_group(P45, E45, ink, 170, 640, 230, False)
        + f'<text class="nr" x="40" y="300" font-size="84" fill="{ink}" letter-spacing="-2">Eric Zou</text>'
        + f'<text class="pm" x="44" y="335" font-size="14" fill="{soft}">waterloo ee · ugmi · ericzou.dev</text>', fonts=True)
    return out

os.makedirs(OUT, exist_ok=True)
sizes = {}
for theme in ("dark", "light"):
    for k, v in build(theme).items():
        p = os.path.join(OUT, f"{k}-{theme}.svg"); open(p, "w").write(v); sizes[f"{k}-{theme}"] = len(v)
print(json.dumps(sizes))
