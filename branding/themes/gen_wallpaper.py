#!/usr/bin/env python3
"""Draw the wallpapers that are not prints: they are original, made by code.

    branding/themes/gen_wallpaper.py aero       -> aero/wallpaper.jpg
    branding/themes/gen_wallpaper.py ventanas   -> ventanas/wallpaper.jpg
    branding/themes/gen_wallpaper.py all

Same seed, same image. 3840x2160, like the prints.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
W, H = 3840, 2160


def _hex(h: str) -> np.ndarray:
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def _grad(stops: list[tuple[float, str]], t: np.ndarray) -> np.ndarray:
    """Colour ramp: stops [(pos, hex)], t in 0..1 of any shape -> (..., 3)."""
    pos = np.array([p for p, _ in stops])
    cols = np.stack([_hex(c) for _, c in stops])
    out = np.empty(t.shape + (3,), dtype=np.float32)
    for k in range(3):
        out[..., k] = np.interp(t, pos, cols[:, k])
    return out


def _over(img: np.ndarray, colour: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    a = alpha[..., None]
    return img * (1 - a) + colour * a


def aero(rng: np.random.Generator) -> Image.Image:
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = x / W, y / H
    # sky: deep blue at the top, cyan, almost white at the horizon
    img = _grad([(0, "0B4F9C"), (0.35, "2A8FDB"), (0.62, "8FD3F4"), (0.78, "E6F7FF"), (1, "E6F7FF")], v)
    # light rays fanning from the top left
    ang = np.arctan2(y + 300, x + 300)
    rays = (0.5 + 0.5 * np.sin(ang * 46)) ** 6 * np.clip(1 - np.hypot(u, v) / 1.3, 0, 1)
    img = _over(img, _hex("FFFFFF"), rays * 0.22)
    # soft sun glow
    glow = np.exp(-(((u - 0.12) / 0.22) ** 2 + ((v - 0.05) / 0.3) ** 2))
    img = _over(img, _hex("FFFFFF"), glow * 0.55)
    # two grass hills
    for base, amp, freq, phase, top, low in ((0.80, 0.05, 1.3, 0.4, "8EDB4B", "2F8A1E"),
                                             (0.86, 0.04, 2.1, 2.0, "6CC93A", "1E6E14")):
        ridge = base - amp * np.sin(u * np.pi * freq + phase) - 0.02 * np.sin(u * 9 + phase)
        depth = np.clip((v - ridge) / (1 - ridge + 1e-3), 0, 1)
        inside = np.clip((v - ridge) * H / 3, 0, 1)  # 3 px antialiased edge
        img = _over(img, _grad([(0, top), (1, low)], depth), inside)
        # a glossy rim along the ridge
        rim = np.exp(-((v - ridge - 0.006) * H / 10) ** 2) * inside
        img = _over(img, _hex("E9FFD0"), rim * 0.6)
    # bubbles: a tinted body, a bright rim and a highlight
    for _ in range(26):
        cx, cy = rng.uniform(0.05, 0.95) * W, rng.uniform(0.08, 0.72) * H
        r = rng.uniform(40, 230) * (0.6 + 0.6 * cy / H)
        d = np.hypot(x - cx, y - cy) / r
        body = np.clip(1 - d, 0, 1) ** 0.15 * (d < 1)
        img = _over(img, _hex("D9F3FF"), body * 0.10)
        rim = np.exp(-((d - 0.96) / 0.035) ** 2)
        img = _over(img, _hex("FFFFFF"), rim * 0.55)
        hl = np.exp(-(((x - (cx - r * 0.38)) / (r * 0.22)) ** 2 + ((y - (cy - r * 0.42)) / (r * 0.13)) ** 2))
        img = _over(img, _hex("FFFFFF"), hl * 0.8)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))


def ventanas(rng: np.random.Generator) -> Image.Image:
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = x / W, y / H
    img = _grad([(0, "0A0E16"), (1, "121A28")], v)
    vignette = np.exp(-(((u - 0.55) / 0.55) ** 2 + ((v - 0.55) / 0.6) ** 2))
    img = _over(img, _hex("16243A"), vignette * 0.8)
    # silk ribbons: bands along slow sine paths, bright core, soft falloff
    colours = ["1F6FD1", "3A9BF0", "4CC2FF", "8AD8FF", "2B5FC4"]
    for i in range(9):
        phase = rng.uniform(0, 6.28)
        centre = 0.5 + 0.18 * np.sin(u * rng.uniform(1.6, 3.2) + phase) + 0.05 * np.sin(u * 7 + phase * 2)
        centre += (i - 4) * 0.018
        width = rng.uniform(0.012, 0.05) * (0.6 + 0.8 * np.sin(u * 2.4 + phase) ** 2)
        dist = (v - centre) / width
        band = np.exp(-dist ** 2) * (0.35 + 0.65 * np.exp(-((u - 0.5) / 0.6) ** 4))
        img = _over(img, _hex(colours[i % len(colours)]), band * rng.uniform(0.35, 0.7))
        core = np.exp(-(dist * 4) ** 2) * band
        img = _over(img, _hex("CFEFFF"), core * 0.35)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))


MAKERS = {"aero": aero, "ventanas": ventanas}


def main(argv: list[str]) -> int:
    ids = list(MAKERS) if argv in ([], ["all"]) else argv
    for theme_id in ids:
        img = MAKERS[theme_id](np.random.default_rng(1))
        out = HERE / theme_id / "wallpaper.jpg"
        img.save(out, quality=92, optimize=True)
        print(f"{out} {img.size[0]}x{img.size[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
