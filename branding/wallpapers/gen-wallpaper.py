#!/usr/bin/env python3
"""
Static Linux — brand wallpaper generator.

Pure standard library (no PIL / ImageMagick), so it runs on the live ISO
build host. One wallpaper per accent (see ../accents/palette.conf): a dark
ground with a faint glow towards the bottom, and 70s "groovy" stripes in
five tones of the accent: a band that comes in from the left and curves
down into the bottom edge, plus a small rainbow in the top-right corner.

    python3 gen-wallpaper.py                     # every accent, retro, 3840x2160
    python3 gen-wallpaper.py --accent purple --style cyberpunk
    python3 gen-wallpaper.py --style all         # retro (void-*), cyberpunk (neon-*), liquid (liquid-*)
    python3 gen-wallpaper.py --accent all --size 2560x1440
"""
from __future__ import annotations

import argparse
import math
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
PALETTE = HERE.parent / "accents" / "palette.conf"


def _hex(s: str) -> tuple[int, int, int]:
    s = s.strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def load_palette() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in PALETTE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "|" not in line:
            continue
        name, accent, dim, detail, text, bg, *_ = [p.strip() for p in line.split("|")]
        out[name] = {
            "accent": _hex(accent), "dim": _hex(dim), "detail": _hex(detail),
            "text": _hex(text), "bg": _hex(bg),
        }
    return out


def _mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def stripe_colors(pal: dict) -> list[tuple[int, int, int]]:
    """Five 70s-style stripe tones from the accent, outer -> inner."""
    white = (255, 255, 255)
    return [_mix(pal["dim"], pal["bg"], 0.35), pal["dim"], pal["accent"],
            _mix(pal["accent"], white, 0.35), pal["detail"]]


def _band(s: float, r_out: float, sw: float, gap: float, cols, n: int):
    """Colour + coverage for distance `s` inside a band of n stripes that
    starts at radius r_out and steps inwards; None outside any stripe."""
    pitch = sw + gap
    p = r_out - s
    if p < 0 or p >= n * pitch:
        return None
    i = int(p // pitch)
    q = p - i * pitch                     # 0..pitch across this stripe+gap
    cov = min(q, sw - q) + 0.5            # 1px anti-aliasing on both edges
    if cov <= 0:
        return None
    return cols[i], min(1.0, cov)


def render(w: int, h: int, pal: dict) -> bytes:
    bg = pal["bg"]
    cols = stripe_colors(pal)
    n = len(cols)
    k = min(w, h) / 1080
    sw, gap = 30 * k, 5 * k               # stripe width / gap between stripes
    band = n * (sw + gap)

    # main band: comes in from the left, turns down into the bottom edge
    cx, cy = w * 0.64, float(h)
    r_out = h * 0.36
    # small rainbow in the top-right corner
    c_out = h * 0.20

    bottom = _mix(bg, pal["accent"], 0.05 if sum(bg) < 384 else -0.03)
    bottom = tuple(max(0, min(255, c)) for c in bottom)

    rows = bytearray()
    for y in range(h):
        rows.append(0)
        base = _mix(bg, bottom, (y / h) ** 2)      # faint glow towards the bottom
        row = bytearray(bytes(base) * w)

        # straight part of the main band (same colour across the row)
        hit = _band(cy - y, r_out, sw, gap, cols, n)
        if hit:
            px = bytes(_mix(base, hit[0], hit[1]))
            row[0:int(cx) * 3] = px * int(cx)
        # curved part of the main band
        dy = y - cy
        if -r_out <= dy:
            for x in range(int(cx), min(w, int(cx + r_out) + 2)):
                hit = _band(((x - cx) ** 2 + dy * dy) ** 0.5, r_out, sw, gap, cols, n)
                if hit:
                    o = x * 3
                    row[o:o + 3] = bytes(_mix(base, hit[0], hit[1]))
        # corner rainbow
        if y <= c_out + 1:
            for x in range(max(0, int(w - c_out) - 2), w):
                hit = _band(((x - w) ** 2 + y * y) ** 0.5, c_out, sw * 0.7, gap * 0.7, cols, n)
                if hit:
                    o = x * 3
                    row[o:o + 3] = bytes(_mix(base, hit[0], hit[1]))
        rows.extend(row)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(rows), 9))
            + chunk(b"IEND", b""))


def _png(w: int, h: int, rows: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9))
            + chunk(b"IEND", b""))


def render_neon(w: int, h: int, pal: dict) -> bytes:
    """Cyberpunk (the legacy look): dark sky, a sun fading accent -> detail
    with cut-out bands, and a neon perspective grid under a glowing horizon."""
    bg, acc, det, dim = pal["bg"], pal["accent"], pal["detail"], pal["dim"]
    black = (4, 4, 8)
    y0 = int(h * 0.60)                    # horizon
    cx = w / 2
    r_sun = h * 0.24
    k = min(w, h) / 1080
    lw = max(1.0, 1.6 * k)                # grid line half-width
    glow = 7 * k
    n_v = 26                              # vertical grid lines each side
    spacing_bottom = w * 0.11

    def blend(base, col, a):
        return _mix(base, col, max(0.0, min(1.0, a)))

    rows = bytearray()
    for y in range(h):
        rows.append(0)
        if y < y0:                                         # sky
            t = y / y0
            base = blend(_mix(bg, acc, 0.03), _mix(bg, acc, 0.16), t ** 3)
            d = (y0 - y) / (h * 0.05)
            base = blend(base, acc, 0.35 * 2.718 ** (-d))  # horizon glow
            row = bytearray(bytes(base) * w)
            dy = y0 - y
            if dy <= r_sun:                                # sun
                half = (r_sun * r_sun - dy * dy) ** 0.5
                f = 1 - dy / r_sun                          # 0 top -> 1 horizon
                # bands cut out of the lower half, wider towards the horizon
                band = int(dy / (h * 0.022))
                gap = f > 0.45 and (dy % (h * 0.022)) < (h * 0.022) * (f - 0.45) * 1.4
                if not gap:
                    col = bytes(_mix(det, acc, f))
                    x1, x2 = int(cx - half), int(cx + half)
                    row[x1 * 3:x2 * 3] = col * (x2 - x1)
        else:                                              # ground + grid
            depth = (y - y0) / (h - y0)                    # 0 horizon -> 1 bottom
            base = blend(_mix(bg, black, 0.4), acc, 0.10 * (1 - depth))
            row = bytearray(bytes(base) * w)
            # horizontal lines, perspective spacing
            lw_d = max(0.6, lw * (0.4 + depth))       # thinner near the horizon
            glow_d = max(lw_d + 1, glow * depth)
            for i in range(1, 13):
                ly = y0 + (h - y0) * (i / 12) ** 1.8
                dd = abs(y - ly)
                if dd < glow_d:
                    a = 1.0 if dd <= lw_d else 0.45 * (1 - (dd - lw_d) / (glow_d - lw_d))
                    row[:] = bytes(blend(base, acc, a * (0.25 + 0.75 * depth))) * w
                    break
            # vertical lines towards the vanishing point
            for j in range(-n_v, n_v + 1):
                x = cx + j * spacing_bottom * depth
                lo, hi = int(x - glow_d - 1), int(x + glow_d + 2)
                for xi in range(max(0, lo), min(w, hi)):
                    dd = abs(xi - x)
                    a = 1.0 if dd <= lw_d else 0.45 * (1 - (dd - lw_d) / (glow_d - lw_d))
                    if a <= 0:
                        continue
                    o = xi * 3
                    cur = tuple(row[o:o + 3])
                    row[o:o + 3] = bytes(blend(cur, acc, a * (0.15 + 0.85 * depth)))
        rows.extend(row)
    return _png(w, h, bytes(rows))


def render_liquid(w: int, h: int, pal: dict) -> bytes:
    """Liquid / minimal: large soft blobs of the accent's tones on the dark
    ground, like the macOS wallpapers. Computed on a coarse grid and
    interpolated (it's all smooth), ordered-dithered against banding."""
    bg, acc, det, dim = pal["bg"], pal["accent"], pal["detail"], pal["dim"]
    white = (255, 255, 255)
    light = _mix(acc, white, 0.45)
    deep = _mix(dim, (0, 0, 0), 0.25)
    blobs = [  # (x, y, radius, colour, strength) in 0..1 units
        (0.15, 0.90, 0.65, deep, 0.95),
        (0.80, 0.25, 0.60, acc, 0.85),
        (0.55, 0.70, 0.45, dim, 0.70),
        (0.95, 0.90, 0.40, light, 0.55),
        (0.35, 0.20, 0.35, _mix(acc, dim, 0.5), 0.45),
    ]
    gw, gh = 97, 55                       # coarse grid
    aspect = w / h
    grid = []
    for gy in range(gh):
        line = []
        for gx in range(gw):
            u, v = gx / (gw - 1), gy / (gh - 1)
            col = list(_mix(bg, (0, 0, 0), 0.3))
            for bx, by, br, bc, bs in blobs:
                d2 = ((u - bx) * aspect) ** 2 + (v - by) ** 2
                a = bs * 2.718 ** (-d2 / (2 * (br * 0.55) ** 2))
                col = [col[i] + (bc[i] - col[i]) * a for i in range(3)]
            # a soft ribbon of light flowing across, the "liquid" sheen
            wave = 0.52 + 0.13 * math.sin(math.pi * 2 * (u * 0.9 + 0.15)) + 0.05 * math.sin(math.pi * 5 * u)
            a = 0.38 * 2.718 ** (-((v - wave) ** 2) / (2 * 0.045 ** 2))
            col = [col[i] + (light[i] - col[i]) * a for i in range(3)]
            line.append(col)
        grid.append(line)

    bayer = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    rows = bytearray()
    for y in range(h):
        rows.append(0)
        fy = y / (h - 1) * (gh - 1)
        y1 = min(int(fy), gh - 2)
        ty = fy - y1
        r0, r1 = grid[y1], grid[y1 + 1]
        row = bytearray(w * 3)
        for x in range(w):
            fx = x / (w - 1) * (gw - 1)
            x1 = min(int(fx), gw - 2)
            tx = fx - x1
            a, b, c, d = r0[x1], r0[x1 + 1], r1[x1], r1[x1 + 1]
            n = bayer[y & 3][x & 3] / 16 - 0.47     # ordered dither, compresses well
            o = x * 3
            for i in range(3):
                top = a[i] + (b[i] - a[i]) * tx
                bot = c[i] + (d[i] - c[i]) * tx
                row[o + i] = max(0, min(255, int(top + (bot - top) * ty + n)))
        rows.extend(row)
    return _png(w, h, bytes(rows))


STYLES = {  # style -> (file prefix, renderer, default size)
    "retro": ("void", lambda w, h, p: render(w, h, p), "3840x2160"),
    "cyberpunk": ("neon", render_neon, "3840x2160"),
    "liquid": ("liquid", render_liquid, "1920x1080"),   # all gradients: upscales cleanly
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--accent", default="all")
    ap.add_argument("--style", default="retro", help="retro | cyberpunk | liquid | all")
    ap.add_argument("--size", default="", help="WxH (default: 4K, liquid 1080p)")
    args = ap.parse_args()

    palette = load_palette()
    names = list(palette) if args.accent == "all" else [args.accent]
    styles = list(STYLES) if args.style == "all" else [args.style]

    for style in styles:
        if style not in STYLES:
            raise SystemExit(f"unknown style '{style}' ({', '.join(STYLES)})")
        prefix, renderer, default_size = STYLES[style]
        w, h = (int(n) for n in (args.size or default_size).lower().split("x"))
        for name in names:
            if name not in palette:
                raise SystemExit(f"unknown accent '{name}' (see {PALETTE})")
            out = HERE / name / f"{prefix}-{name}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(renderer(w, h, palette[name]))
            print(f"wrote {out.relative_to(HERE.parent.parent)}  "
                  f"({out.stat().st_size // 1024} KiB, {w}x{h})")


if __name__ == "__main__":
    main()
