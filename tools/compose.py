"""Lay the face and a small title over a white-on-black ASCII city.
The face sits on the left with a feathered black patch behind it, and the name sits small right under it.
usage: compose.py city.svg face-source.svg out.svg   (face-source.svg is the old face-and-title banner, kept in tools/)"""
import re, sys
from ansi_title import ansi_title, width

CITY, BANNER, OUT = sys.argv[1:4]
city, banner = open(CITY).read(), open(BANNER).read()
banner = re.sub(r'<g id="city".*?</g>', "", banner, flags=re.S)

# the face is everything in the banner before the title's block letters
body = banner[banner.index("</style>") + 8:banner.rindex("</svg>")]
face = body[:body.index('<g fill="#e8e4da"><rect')]
FACE_X, FACE_Y, FACE_S = 112, 128, 0.8
face = face.replace('<g transform="translate(200.0 150.0)">',
                    f'<g transform="translate({FACE_X} {FACE_Y}) scale({FACE_S})">', 1)

# the city starts with its black ground
city_style = re.search(r"<style>.*?</style>", city, re.S).group(0)
city_body = city[city.index("</style>") + 8:city.rindex("</svg>")]
bg, rest = city_body.split("/>", 1)

# small title centred under the chin
TCW, TCH = 3.3, 6.1
title = ansi_title("Eric Zou", FACE_X - width("Eric Zou", TCW) / 2, 250, TCW, TCH, "#e8e4da", "#9a9690")

patch = ('<filter id="feather" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="12"/></filter>'
         f'<ellipse cx="{FACE_X}" cy="{FACE_Y}" rx="{128*FACE_S:.0f}" ry="{132*FACE_S:.0f}" fill="#000" opacity="0.88" filter="url(#feather)"/>')

svg = (city[:city.index("<style>")] + city_style.replace("</style>", '.pm{font-family:"PM",Menlo,monospace}</style>')
       + bg + "/>" + rest + patch + face + title + "</svg>")
open(OUT, "w").write(svg)
print(f"{len(svg)//1024} KB")
