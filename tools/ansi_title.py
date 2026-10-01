"""Draw text in the ANSI Shadow figlet style that the Claude Code welcome logo uses, as SVG rects and lines so no font is needed."""

GLYPHS = {
    "E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    "R": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "C": [" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"],
    "Z": ["███████╗", "╚══███╔╝", "  ███╔╝ ", " ███╔╝  ", "███████╗", "╚══════╝"],
    "O": [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    "U": ["██╗   ██╗", "██║   ██║", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    " ": ["  "] * 6,
}

def lines(text):
    return ["".join(GLYPHS[c][r] for c in text.upper()) for r in range(6)]

def ansi_title(text, x, y, cw, ch, block, edge):
    """Top left at (x, y), each terminal cell cw by ch. Blocks fill in `block`, the double-line shadow strokes in `edge`."""
    d = cw * 0.2
    rects, path = [], []
    for r, row in enumerate(lines(text)):
        for c, g in enumerate(row):
            x0, y0 = x + c * cw, y + r * ch
            cx, cy, x1, y1 = x0 + cw / 2, y0 + ch / 2, x0 + cw, y0 + ch
            if g == "█":
                rects.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{cw+0.3:.1f}" height="{ch+0.3:.1f}"/>')
            elif g == "═":
                path.append(f"M{x0:.1f} {cy-d:.1f}H{x1:.1f}M{x0:.1f} {cy+d:.1f}H{x1:.1f}")
            elif g == "║":
                path.append(f"M{cx-d:.1f} {y0:.1f}V{y1:.1f}M{cx+d:.1f} {y0:.1f}V{y1:.1f}")
            elif g == "╗":
                path.append(f"M{x0:.1f} {cy-d:.1f}H{cx+d:.1f}V{y1:.1f}M{x0:.1f} {cy+d:.1f}H{cx-d:.1f}V{y1:.1f}")
            elif g == "╔":
                path.append(f"M{x1:.1f} {cy-d:.1f}H{cx-d:.1f}V{y1:.1f}M{x1:.1f} {cy+d:.1f}H{cx+d:.1f}V{y1:.1f}")
            elif g == "╝":
                path.append(f"M{x0:.1f} {cy+d:.1f}H{cx+d:.1f}V{y0:.1f}M{x0:.1f} {cy-d:.1f}H{cx-d:.1f}V{y0:.1f}")
            elif g == "╚":
                path.append(f"M{x1:.1f} {cy+d:.1f}H{cx-d:.1f}V{y0:.1f}M{x1:.1f} {cy-d:.1f}H{cx+d:.1f}V{y0:.1f}")
    return (f'<g fill="{block}">{"".join(rects)}</g>'
            f'<path d="{"".join(path)}" stroke="{edge}" stroke-width="{cw*0.13:.2f}"/>')

def width(text, cw):
    return len(lines(text)[0]) * cw
