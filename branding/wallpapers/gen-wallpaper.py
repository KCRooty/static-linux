#!/usr/bin/env python3
"""
Static Linux — brand wallpaper generator.

Pure standard library (no PIL / ImageMagick), so it runs on the live ISO
build host. Produces a minimal wallpaper: Void ground, a barely-there
diagonal split (a nod to the Static Forge SF monogram) and one thin
Signal Green edge along the split.

    python3 gen-wallpaper.py                       # 1920x1080 dark + light
    python3 gen-wallpaper.py --size 2560x1440
    python3 gen-wallpaper.py --only dark -o out.png
"""
from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

# Palette
VOID = (0x0B, 0x0C, 0x10)
DEEP = (0x12, 0x14, 0x1D)      # lighter half of the split
GREEN = (0x00, 0xC8, 0xA0)
LIGHT_BG = (0xEC, 0xEE, 0xF2)
LIGHT_HALF = (0xDD, 0xE1, 0xE8)


def _mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def render(w: int, h: int, variant: str) -> bytes:
    if variant == "light":
        base, half, edge = LIGHT_BG, LIGHT_HALF, GREEN
    else:
        base, half, edge = VOID, DEEP, GREEN

    # Split line: from (0, h) to (w, 0)  ->  x/w + y/h = 1 on the line.
    # Pixels "above" the line (x/w + y/h > 1) get the lighter half.
    rows = bytearray()
    edge_soft = 1.6 / min(w, h)          # ~1.6px feather
    for y in range(h):
        rows.append(0)                    # PNG filter: none
        yn = y / h
        row = bytearray(w * 3)
        for x in range(w):
            d = (x / w) + yn - 1.0        # signed distance-ish to the split
            if d > edge_soft:
                px = half
            elif d < -edge_soft:
                px = base
            else:
                # thin Signal Green seam, feathered
                t = 1.0 - abs(d) / edge_soft
                px = _mix(_mix(base, half, 0.5), edge, 0.55 * t)
            o = x * 3
            row[o], row[o + 1], row[o + 2] = px
        rows.extend(row)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)   # 8-bit RGB
    idat = zlib.compress(bytes(rows), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--only", choices=["dark", "light"])
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    w, h = (int(n) for n in args.size.lower().split("x"))
    here = Path(__file__).resolve().parent
    variants = [args.only] if args.only else ["dark", "light"]

    for v in variants:
        out = Path(args.output) if args.output else here / v / f"void-{v}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(render(w, h, v))
        print(f"wrote {out}  ({out.stat().st_size // 1024} KiB, {w}x{h})")


if __name__ == "__main__":
    main()
