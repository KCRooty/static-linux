#!/usr/bin/env python3
"""
Static Linux — brand wallpaper generator.

Pure standard library (no PIL / ImageMagick), so it runs on the live ISO
build host. One wallpaper per accent (see ../accents/palette.conf): a dark
ground, a faint diagonal split (a nod to the Static Forge SF monogram), a
thin accent seam along the split and a small mark in the corner.

    python3 gen-wallpaper.py                     # every accent, 1920x1080
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


def render(w: int, h: int, pal: dict) -> bytes:
    bg = pal["bg"]
    # lighter half of the split: nudge bg toward the accent, very slightly
    half = _mix(bg, pal["accent"], 0.06 if sum(bg) < 384 else -0.04)
    half = tuple(max(0, min(255, c)) for c in half)
    edge = pal["accent"]
    dot = pal["detail"]

    feather = 1.6 / min(w, h)
    # small corner mark: a short accent tick + a dot, bottom-right
    mark_x0, mark_y0 = w - int(w * 0.14), h - int(h * 0.11)

    rows = bytearray()
    for y in range(h):
        rows.append(0)
        yn = y / h
        row = bytearray(w * 3)
        for x in range(w):
            d = (x / w) + yn - 1.0
            if d > feather:
                px = half
            elif d < -feather:
                px = bg
            else:
                t = 1.0 - abs(d) / feather
                px = _mix(_mix(bg, half, 0.5), edge, 0.6 * t)

            # corner mark
            if y >= mark_y0 and x >= mark_x0:
                lx, ly = x - mark_x0, y - mark_y0
                if 0 <= ly - lx <= 2:                       # thin diagonal tick
                    px = edge
                elif (lx - int(w * 0.10)) ** 2 + (ly - int(h * 0.055)) ** 2 <= 9:
                    px = dot                                 # small dot

            o = x * 3
            row[o], row[o + 1], row[o + 2] = px
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
    ap.add_argument("--size", default="1920x1080")
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
