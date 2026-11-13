#!/usr/bin/env python3
"""Draw the wallpapers that are not prints: they are original, made by code.

    branding/themes/gen_wallpaper.py aero       -> aero/wallpaper.jpg
    branding/themes/gen_wallpaper.py ventanas   -> ventanas/wallpaper.jpg
    branding/themes/gen_wallpaper.py violeta    -> violeta/wallpaper.jpg (provisional)
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


def violeta(rng: np.random.Generator) -> Image.Image:
    """Provisional: violet ridges at dusk, until Core picks one of his pieces."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = x / W, y / H
    img = _grad([(0, "14121D"), (0.45, "2E2350"), (0.7, "6A4C9C"), (0.82, "C89BD8"), (1, "C89BD8")], v)
    # stars in the upper sky
    for _ in range(420):
        sx, sy = rng.uniform(0, W), rng.uniform(0, H * 0.45)
        r = rng.uniform(0.8, 2.4)
        d = np.hypot(x[int(max(sy - 6, 0)):int(sy + 6), int(max(sx - 6, 0)):int(sx + 6)] - sx,
                     y[int(max(sy - 6, 0)):int(sy + 6), int(max(sx - 6, 0)):int(sx + 6)] - sy)
        a = np.clip(1 - d / r, 0, 1) * rng.uniform(0.3, 0.9) * (1 - sy / (H * 0.45))
        sl = img[int(max(sy - 6, 0)):int(sy + 6), int(max(sx - 6, 0)):int(sx + 6)]
        sl[:] = _over(sl, _hex("EDE6FF"), a)
    # moon
    d = np.hypot(x - W * 0.72, y - H * 0.24)
    img = _over(img, _hex("F4ECFF"), np.clip((90 - d) / 2, 0, 1))
    img = _over(img, _hex("B9A6F0"), np.exp(-(d / 420) ** 2) * 0.25)
    # five ridges, far (light, hazy) to near (dark)
    layers = [("8F7AC8", 0.66), ("6B57A6", 0.72), ("4A3C80", 0.79), ("2D2556", 0.86), ("17132A", 0.93)]
    for i, (col, base) in enumerate(layers):
        ph = rng.uniform(0, 6.28)
        ridge = (base - 0.06 * np.sin(u * rng.uniform(2, 4) + ph) - 0.03 * np.sin(u * rng.uniform(7, 11) + ph * 1.7)
                 - 0.012 * np.sin(u * rng.uniform(23, 31) + ph * 2.3))
        inside = np.clip((v - ridge) * H / 2.5, 0, 1)
        img = _over(img, _hex(col), inside)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))


def nube(rng: np.random.Generator) -> Image.Image:
    """Nube: a pale morning sky with big soft clouds and two pastel hills. Light theme."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = x / W, y / H
    img = _grad([(0, "BFD9F6"), (0.55, "E3EEFB"), (1, "F4F7FC")], v)
    glow = np.exp(-(((u - 0.78) / 0.30) ** 2 + ((v - 0.18) / 0.25) ** 2))
    img = _over(img, _hex("FFF6E6"), glow * 0.55)
    # clouds: clusters of soft discs, each cluster a cloud
    for _ in range(7):
        cx, cy = rng.uniform(0.0, 1.0), rng.uniform(0.12, 0.55)
        scale = rng.uniform(0.05, 0.11)
        cloud = np.zeros_like(u)
        for _ in range(6):
            dx, dy = rng.normal(0, scale * 1.4), rng.normal(0, scale * 0.35)
            r = scale * rng.uniform(0.6, 1.1)
            d = ((u - cx - dx) * W / H) ** 2 + (v - cy - dy) ** 2
            cloud = np.maximum(cloud, np.clip(1.2 - d / (r * r), 0, 1))
        img = _over(img, _hex("FFFFFF"), cloud * rng.uniform(0.55, 0.85))
    # hills: two sine horizons, back one bluish, front one soft green
    for base, amp, col, a in ((0.78, 0.05, "AFC8EA", 0.85), (0.86, 0.04, "B9DDC6", 0.95)):
        phase = rng.uniform(0, 6.28)
        edge = base + amp * np.sin(u * rng.uniform(2.0, 3.5) + phase) + 0.012 * np.sin(u * 11 + phase)
        hill = np.clip((v - edge) * H / 6.0, 0, 1)
        img = _over(img, _grad([(0, col), (1, "FFFFFF")], np.clip((v - base) * 3, 0, 1)), hill * a)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0))


MAKERS = {"aero": aero, "ventanas": ventanas, "violeta": violeta, "nube": nube}


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
