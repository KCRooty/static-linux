#!/usr/bin/env python3
"""Wallpapers made from free photos (Wikimedia Commons), not drawn by code.

    branding/themes/photo_wallpaper.py aero   -> aero/wallpaper.jpg
    branding/themes/photo_wallpaper.py nube   -> nube/wallpaper.jpg
    branding/themes/photo_wallpaper.py all

Downloads the original once (~/.cache/static-linux/photos/), crops it to
16:9, scales it to 3840x2160 with Lanczos, a light sharpen and a small colour
lift, and for Aero adds glass bubbles on top. The photo's author and licence
go in <theme>/CREDITS; both licences ask for attribution, nothing else.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from gen_wallpaper import _hex, _over

HERE = Path(__file__).resolve().parent
CACHE = Path.home() / ".cache/static-linux/photos"
W, H = 3840, 2160
UA = "StaticLinuxWallpaper/1.0 (https://staticforge.me)"

PHOTOS = {
    # theme: (original file, vertical crop anchor 0=top..1=bottom, credits)
    "aero": ("https://upload.wikimedia.org/wikipedia/commons/0/0b/"
             "Malapascua_%28island%29%2C_Tropical_lagoon%2C_Philippines.jpg", 0.55,
             "Malapascua (island), Tropical lagoon, Philippines — Vyacheslav Argenberg, "
             "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).\n"
             "https://commons.wikimedia.org/wiki/File:Malapascua_(island),_Tropical_lagoon,_Philippines.jpg\n"
             "Cambios: recorte 16:9, escalado a 3840x2160, color y burbujas de cristal "
             "dibujadas por código (branding/themes/photo_wallpaper.py)."),
    "nube": ("https://upload.wikimedia.org/wikipedia/commons/f/fc/Palouse_hills_near_Moscow.jpg", 0.5,
             "Palouse hills near Moscow — Cheryl Dudley (Idaho, EE. UU.), "
             "CC BY 2.0 (https://creativecommons.org/licenses/by/2.0/).\n"
             "https://commons.wikimedia.org/wiki/File:Palouse_hills_near_Moscow.jpg\n"
             "Cambios: recorte 16:9, escalado a 3840x2160 y color "
             "(branding/themes/photo_wallpaper.py)."),
}


def _source(url: str) -> Image.Image:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / url.rsplit("/", 1)[1].replace("%", "_")
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        path.write_bytes(urllib.request.urlopen(req).read())
    return Image.open(path).convert("RGB")


def _fit(img: Image.Image, anchor: float) -> Image.Image:
    """Crop to 16:9 (keeping the anchor row band) and scale to W x H."""
    w, h = img.size
    if w / h > W / H:
        cw = round(h * W / H)
        img = img.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
    else:
        ch = round(w * H / W)
        top = round((h - ch) * anchor)
        img = img.crop((0, top, w, top + ch))
    img = img.resize((W, H), Image.LANCZOS)
    return img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))


def _bubbles(img: Image.Image, rng: np.random.Generator, sky_bottom: float) -> Image.Image:
    """Frutiger Aero glass bubbles, only in the sky band."""
    a = np.asarray(img).astype(np.float32)
    for _ in range(13):
        cx, cy = rng.uniform(0.36, 0.97) * W, rng.uniform(0.05, sky_bottom) * H
        r = rng.uniform(36, 170)
        x0, x1 = int(max(cx - r - 4, 0)), int(min(cx + r + 4, W))
        y0, y1 = int(max(cy - r - 4, 0)), int(min(cy + r + 4, H))
        y, x = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.hypot(x - cx, y - cy) / r
        patch = a[y0:y1, x0:x1]
        body = np.clip(1 - d, 0, 1) ** 0.15 * (d < 1)
        patch = _over(patch, _hex("E4F6FF"), body * 0.10)
        rim = np.exp(-((d - 0.96) / 0.035) ** 2)
        patch = _over(patch, _hex("FFFFFF"), rim * 0.55)
        hl = np.exp(-(((x - (cx - r * 0.38)) / (r * 0.22)) ** 2 + ((y - (cy - r * 0.42)) / (r * 0.13)) ** 2))
        patch = _over(patch, _hex("FFFFFF"), hl * 0.8)
        a[y0:y1, x0:x1] = patch
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def make(theme: str) -> Image.Image:
    url, anchor, _ = PHOTOS[theme]
    img = _fit(_source(url), anchor)
    if theme == "aero":
        img = ImageEnhance.Color(img).enhance(1.18)
        img = ImageEnhance.Contrast(img).enhance(1.04)
        img = _bubbles(img, np.random.default_rng(7), 0.42)
    else:
        img = ImageEnhance.Color(img).enhance(1.10)
    return img


def main(argv: list[str]) -> int:
    ids = list(PHOTOS) if argv in ([], ["all"]) else argv
    for theme in ids:
        img = make(theme)
        out = HERE / theme / "wallpaper.jpg"
        img.save(out, quality=90, optimize=True, progressive=True)
        (HERE / theme / "CREDITS").write_text("Fondo: " + PHOTOS[theme][2] + "\n", encoding="utf-8")
        print(f"{out} {img.size[0]}x{img.size[1]} {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
