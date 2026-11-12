#!/usr/bin/env python3
"""Check every theme in branding/themes/ against DESIGN.md before it ships.

Contrast is WCAG 2.x. A theme fails if any text pair the system actually
draws is below AA (4.5:1), or a non-text mark (accent on bg, borders of a
focused control) is below 3:1. Terminal colours are checked against the
terminal background (`surface`): normal colours at 4.5:1, except colour 0
(black) and 7/15 (white), which are background shades by convention.

    branding/themes/check.py            # all themes
    branding/themes/check.py papel      # one theme
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUIRED = ("name", "mode", "bg", "surface", "line", "text", "text_dim",
            "accent", "accent_fg", "danger", "warning", "term", "term_bright")


def load(path: Path) -> dict[str, str]:
    theme = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            theme[key.strip()] = value.strip()
    return theme


def luminance(hexstr: str) -> float:
    rgb = [int(hexstr[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def ratio(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def check(theme_id: str, theme: dict[str, str]) -> list[str]:
    missing = [k for k in REQUIRED if k not in theme]
    if missing:
        return [f"missing keys: {', '.join(missing)}"]
    errors = []
    text_pairs = [
        ("text", "bg"), ("text", "surface"), ("text_dim", "bg"), ("text_dim", "surface"),
        ("accent_fg", "accent"), ("accent", "bg"), ("accent", "surface"),
        ("danger", "bg"), ("danger", "surface"), ("warning", "surface"),
    ]
    for fg, bg in text_pairs:
        r = ratio(theme[fg], theme[bg])
        if r < 4.5:
            errors.append(f"{fg} on {bg}: {r:.1f}:1 < 4.5")
    # the focus ring / selected border has to be seen against the window
    r = ratio(theme["accent"], theme["line"])
    if r < 1.5:
        errors.append(f"accent vs line: {r:.1f}:1, focus would not stand out from borders")
    for label, key in (("term", "term"), ("term_bright", "term_bright")):
        colours = theme[key].split(",")
        if len(colours) != 8:
            errors.append(f"{key}: {len(colours)} colours, need 8")
            continue
        for i, c in enumerate(colours):
            if i in (0, 7):
                continue
            r = ratio(c, theme["surface"])
            if r < 4.5:
                errors.append(f"{label}[{i}] #{c} on surface: {r:.1f}:1 < 4.5")
    return errors


def main(argv: list[str]) -> int:
    ids = argv or sorted(p.name for p in HERE.iterdir() if (p / "theme.conf").is_file())
    failed = 0
    for theme_id in ids:
        errors = check(theme_id, load(HERE / theme_id / "theme.conf"))
        if errors:
            failed += 1
            print(f"FAIL {theme_id}")
            for e in errors:
                print(f"     {e}")
        else:
            print(f"ok   {theme_id}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
