#!/usr/bin/env python3
# Static Linux — renders the installer welcome image (70s retro, ASCII title).
#   python3 branding/logo/gen-installer-welcome.py installer/calamares/branding/staticlinux/welcome.svg
#   magick -background none <svg> -strip -depth 8 PNG32:<same dir>/welcome.png
import html, sys
ART = r"""
 __ _        _   _          __ _
/ _\ |_ __ _| |_(_) ___    / /(_)_ __  _   ___  __
\ \| __/ _` | __| |/ __|  / / | | '_ \| | | \ \/ /
_\ \ || (_| | |_| | (__  / /__| | | | | |_| |>  <
\__/\__\__,_|\__|_|\___| \____/_|_| |_|\__,_/_/\_\
""".strip("\n").split("\n")
W, H = 960, 540
STRIPES = ["#6B3A1F", "#C2452D", "#E8792B", "#F2B33D", "#2A9D8F"]  # outer -> inner
CREAM, INK = "#F4E6C8", "#3A2213"
SW = 18
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<defs><clipPath id="c"><rect width="960" height="540" rx="28"/></clipPath></defs>',
       '<g clip-path="url(#c)">', f'<rect width="{W}" height="{H}" fill="{CREAM}"/>']
# bottom band: runs in from the left, turns down into the bottom edge
cx, cy, r0 = 700, H, 190
for i, col in enumerate(STRIPES):
    r = r0 - i * SW - SW / 2
    out.append(f'<path d="M -10 {cy - r} H {cx} A {r} {r} 0 0 1 {cx + r} {cy + 10}" '
               f'fill="none" stroke="{col}" stroke-width="{SW - 3}"/>')
# top-right corner rainbow
for i, col in enumerate(STRIPES):
    r = 150 - i * SW - SW / 2
    out.append(f'<path d="M {W - r} -10 A {r} {r} 0 0 0 {W + 10} {r}" '
               f'fill="none" stroke="{col}" stroke-width="{SW - 3}"/>')
# ASCII title, orange drop shadow then ink
fs, lh = 21, 25
cols = max(len(l) for l in ART)
x0 = (W - cols * fs * 0.6) / 2
y0 = 130
def text(dx, dy, fill):
    t = [f'<text font-family="JetBrains Mono" font-weight="800" font-size="{fs}" fill="{fill}" xml:space="preserve">']
    for n, line in enumerate(ART):
        t.append(f'<tspan x="{x0 + dx:.1f}" y="{y0 + dy + n * lh}">{html.escape(line)}</tspan>')
    t.append('</text>')
    return "".join(t)
out.append(text(2.5, 2.5, "#E8792B"))
out.append(text(0, 0, INK))
out.append(f'<text x="{W/2}" y="{y0 + len(ART) * lh + 34}" text-anchor="middle" font-family="JetBrains Mono" '
           f'font-weight="700" font-size="20" letter-spacing="6" fill="{STRIPES[1]}">fast · private · yours</text>')
out.append('</g></svg>')
open(sys.argv[1], "w").write("\n".join(out) + "\n")
