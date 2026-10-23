#!/usr/bin/env python3
"""
Static Linux — brand wallpaper generator.

Pure standard library (no PIL / ImageMagick), so it runs on the live ISO
build host. One wallpaper per accent (see ../accents/palette.conf): a dark
ground with a faint glow towards the bottom, and 70s "groovy" stripes in
five tones of the accent: a band that comes in from the left and curves
down into the bottom edge, plus a small rainbow in the top-right corner.

    python3 gen-wallpaper.py                     # every accent, 3840x2160
    python3 gen-wallpaper.py --accent purple
    python3 gen-wallpaper.py --accent all --size 2560x1440
"""
from __future__ import annotations

import argparse
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--accent", default="all")
    ap.add_argument("--size", default="3840x2160")  # 4K: sharp on every screen, scaled down elsewhere
    args = ap.parse_args()

    w, h = (int(n) for n in args.size.lower().split("x"))
    palette = load_palette()
    names = list(palette) if args.accent == "all" else [args.accent]

    for name in names:
        if name not in palette:
            raise SystemExit(f"unknown accent '{name}' (see {PALETTE})")
        out = HERE / name / f"void-{name}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(render(w, h, palette[name]))
        print(f"wrote {out.relative_to(HERE.parent.parent)}  "
              f"({out.stat().st_size // 1024} KiB, {w}x{h})")


if __name__ == "__main__":
    main()
