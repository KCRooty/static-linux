#!/usr/bin/env python3
# Static Linux — preview cards for the installer's "Entorno" and "Privacidad"
# pages (packagechooser `screenshot:`). Writes SVGs; render each with
#   magick -background none card.svg -strip -depth 8 PNG32:card.png
#
#   python3 branding/logo/gen-installer-cards.py installer/calamares/branding/staticlinux/cards
import html
import sys
from pathlib import Path

W, H = 600, 340
VOID, PANEL, LINE, TEXT, MUTED = "#0B0C10", "#161920", "#262A34", "#E6E8EE", "#8A8F9C"
GROOVY = ["#6B3A1F", "#C2452D", "#E8792B", "#F2B33D", "#2A9D8F"]


def stripes(r0=130, sw=12):
    """Groovy quarter-rainbow tucked into the bottom-right corner."""
    out = []
    for i, col in enumerate(GROOVY):
        r = r0 - i * sw - sw / 2
        out.append(f'<path d="M {W - r} {H + 10} A {r} {r} 0 0 1 {W + 10} {H - r}" '
                   f'fill="none" stroke="{col}" stroke-width="{sw - 2}"/>')
    return "".join(out)


def frame(title, subtitle, chip, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="22"/></clipPath>
<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#14161D"/><stop offset="1" stop-color="{VOID}"/></linearGradient></defs>
<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="url(#g)"/>
{stripes()}
{body}
<text x="32" y="292" font-family="JetBrains Mono" font-weight="800" font-size="26" fill="{TEXT}">{html.escape(title)}</text>
<text x="32" y="318" font-family="Noto Sans" font-size="15" fill="{MUTED}">{html.escape(subtitle)}</text>
<rect x="{W - 32 - 11 * len(chip) - 24}" y="24" width="{11 * len(chip) + 24}" height="30" rx="15" fill="#00C8A0"/>
<text x="{W - 32 - (11 * len(chip) + 24) / 2}" y="44" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" font-size="15" fill="{VOID}">{html.escape(chip)}</text>
</g><rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="{LINE}"/></svg>'''


def win(x, y, w, h, accent, rx=8, title=True):
    t = f'<rect x="{x}" y="{y}" width="{w}" height="18" rx="{rx}" fill="{accent}"/>' if title else ""
    lines = "".join(f'<rect x="{x + 12}" y="{y + 30 + i * 14}" width="{(w - 24) * (0.9 - 0.18 * (i % 3))}" height="6" rx="3" fill="{LINE}"/>'
                    for i in range(max(0, (h - 40) // 14)))
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{PANEL}" stroke="{LINE}"/>{t}{lines}'


ENVS = {
    "xfce-themed": ("XFCE", "Clásico, ligero y estable · Xorg", "≥ 1 GB",
        f'<rect x="32" y="74" width="380" height="16" rx="5" fill="{PANEL}"/>'
        f'<circle cx="44" cy="82" r="4" fill="#00C8A0"/>'
        f'<rect x="40" y="104" width="22" height="22" rx="5" fill="#2A9D8F"/><rect x="40" y="138" width="22" height="22" rx="5" fill="#F2B33D"/>'
        + win(110, 108, 250, 130, "#2A9D8F")),
    "openbox-minimal": ("Openbox", "Lo mínimo para equipos muy modestos", "≥ 512 MB",
        win(60, 84, 260, 140, "#F2B33D", rx=3)
        + f'<rect x="32" y="236" width="380" height="14" rx="3" fill="{PANEL}" stroke="{LINE}"/>'),
    "hyprland-astal-lite": ("Hyprland lite", "Wayland en mosaico, sin efectos pesados", "≥ 2 GB",
        f'<rect x="32" y="74" width="380" height="16" rx="8" fill="{PANEL}"/>'
        + win(32, 100, 186, 140, "#E8792B", rx=10) + win(226, 100, 186, 140, "#E8792B", rx=10)),
    "hyprland-astal-full": ("Hyprland full", "Wayland con blur, sombras y animaciones", "≥ 4 GB",
        f'<rect x="32" y="74" width="380" height="16" rx="8" fill="{PANEL}"/>'
        f'<rect x="28" y="96" width="390" height="152" rx="14" fill="#C2452D" opacity="0.18"/>'
        + win(32, 100, 186, 140, "#C2452D", rx=12) + win(226, 100, 186, 66, "#C2452D", rx=12)
        + win(226, 174, 186, 66, "#C2452D", rx=12)
        + f'<rect x="150" y="226" width="150" height="20" rx="10" fill="{PANEL}" stroke="#C2452D"/>'),
    "kde-plasma": ("KDE Plasma", "El escritorio completo y familiar · Wayland", "≥ 4 GB",
        win(70, 80, 300, 140, "#2A9D8F", rx=6)
        + f'<rect x="32" y="234" width="380" height="18" rx="6" fill="{PANEL}" stroke="{LINE}"/>'
        f'<circle cx="46" cy="243" r="6" fill="#00C8A0"/>'
        f'<rect x="60" y="238" width="16" height="10" rx="3" fill="#F2B33D"/>'
        f'<rect x="82" y="238" width="16" height="10" rx="3" fill="#E8792B"/>'
        f'<rect x="372" y="238" width="30" height="10" rx="3" fill="{LINE}"/>'),
}


def shield(level):
    out = [f'<path d="M 200 70 L 290 100 V 160 C 290 210 250 236 200 250 C 150 236 110 210 110 160 V 100 Z" '
           f'fill="{PANEL}" stroke="#00C8A0" stroke-width="3"/>']
    for i in range(3):
        on = i < level
        out.append(f'<rect x="150" y="{196 - i * 34}" width="100" height="24" rx="12" '
                   f'fill="{GROOVY[2 + i] if on else LINE}"/>')
    return "".join(out)


PRIV = {
    "basico": ("Básico", "DNS cifrado, cortafuegos y MAC aleatoria", "linux-zen", 1),
    "mejorado": ("Mejorado", "+ Firejail, AppArmor y USBGuard", "linux-zen", 2),
    "maximo": ("Máximo", "+ Tor, kloak y swap cifrado", "hardened", 3),
}

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for key, (t, s, chip, body) in ENVS.items():
    (out / f"{key}.svg").write_text(frame(t, s, chip, body))
for key, (t, s, chip, lvl) in PRIV.items():
    (out / f"{key}.svg").write_text(frame(t, s, chip, shield(lvl)))
print("\n".join(sorted(str(p) for p in out.glob("*.svg"))))
