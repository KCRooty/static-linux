"""System-wide pieces of a theme: login screen, GRUB menu and boot splash.

Called by `sl-theme <id> --system` (root): the installer runs it once, and
`sl-ctl theme` runs it again when the theme changes. Each piece is skipped
when its program is not installed, and every system file it replaces is
copied first to /var/backups/static-linux/theme/<timestamp>/.
"""

from __future__ import annotations

import re
import shutil
import struct
import subprocess
import time
import zlib
from pathlib import Path
from typing import Callable

import xfwm4  # _mix: colour blending

REBUILD_INITRAMFS = True
BACKUP = Path("/var/backups/static-linux/theme") / time.strftime("%Y%m%d-%H%M%S")
LOGO = Path("/usr/share/static-linux/logo/sf-static-forge.png")
GREETER_THEME = Path("/usr/share/themes/StaticLinux-Greeter/gtk-3.0/gtk.css")
GREETER_CONF = Path("/etc/lightdm/lightdm-gtk-greeter.conf.d/55-static-linux-theme.conf")
SDDM_BREEZE = Path("/usr/share/sddm/themes/breeze")
GRUB_DEFAULT = Path("/etc/default/grub")
GRUB_THEME = Path("/boot/grub/themes/static-linux")
PLYMOUTH_THEME = Path("/usr/share/plymouth/themes/static-linux")
MKINITCPIO = Path("/etc/mkinitcpio.conf")


def _backup(path: Path) -> None:
    if path.is_file():
        saved = BACKUP / path.relative_to("/")
        if not saved.exists():
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, saved)


def _write(path: Path, data: str | bytes) -> None:
    _backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data)


def png_solid(width: int, height: int, hex_colour: str, alpha: int = 255) -> bytes:
    """A flat RGBA PNG, no image library needed (GRUB and Plymouth pieces)."""
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (0, 2, 4))
    row = b"\0" + bytes((r, g, b, alpha)) * width
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * height, 9))
            + chunk(b"IEND", b""))


def _image(src: str, dest: Path, brightness: float, blur: float = 0) -> bool:
    """Scale (max 1920 wide), dim or lighten and re-encode an image with ffmpeg."""
    if not src or not shutil.which("ffmpeg"):
        return False
    _backup(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    chain = f"scale='min(1920,iw)':-2,eq=brightness={brightness}"
    if blur:
        chain += f",gblur=sigma={blur}"
    rc = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-vf", chain,
                         "-frames:v", "1", *(["-q:v", "3"] if dest.suffix == ".jpg" else []), str(dest)], check=False).returncode
    return rc == 0 and dest.is_file()


def _set_var(text: str, key: str, value: str) -> str:
    """Set KEY=value in a shell-style config, uncommenting or appending it."""
    line = f"{key}={value}"
    pattern = re.compile(rf"^#?\s*{key}=.*$", re.M)
    if pattern.search(text):
        return pattern.sub(line, text, count=1)
    return text.rstrip("\n") + "\n" + line + "\n"


def _font_file(family: str) -> str | None:
    if not shutil.which("fc-match"):
        return None
    out = subprocess.run(["fc-match", "-f", "%{file}", family], capture_output=True,
                         text=True, check=False).stdout.strip()
    return out if out.lower().endswith((".ttf", ".otf")) else None


def _pf2_name(path: Path) -> str | None:
    """The font name GRUB knows a .pf2 by (its NAME chunk)."""
    data = path.read_bytes()
    i = data.find(b"NAME")
    if i < 0:
        return None
    size = struct.unpack(">I", data[i + 4:i + 8])[0]
    return data[i + 8:i + 8 + size].rstrip(b"\0").decode()


# ---------------------------------------------------------------------------
def greeter(theme: dict, render: Callable, tpl: Path, log: Callable) -> None:
    if Path("/etc/lightdm").is_dir():
        _write(GREETER_THEME, render((tpl / "greeter-gtk.css.in").read_text(), theme))
        _write(GREETER_CONF, render((tpl / "greeter.conf.in").read_text(), theme))
        log("LightDM greeter: theme wallpaper and palette")
    if SDDM_BREEZE.is_dir():
        _write(SDDM_BREEZE / "theme.conf.user",
               f"[General]\nbackground={theme['wallpaper']}\ntype=image\ncolor=#{theme['bg']}\n"
               f"accentColor=#{theme['accent']}\n")
        log("SDDM (Breeze): theme wallpaper")


def grub(theme: dict, render: Callable, tpl: Path, log: Callable) -> None:
    if not GRUB_DEFAULT.is_file() or not shutil.which("grub-mkfont"):
        return
    light = theme["mode"] == "light"
    GRUB_THEME.mkdir(parents=True, exist_ok=True)
    # PNG: GRUB's JPEG reader rejects ffmpeg's chroma sampling
    for old in GRUB_THEME.glob("background.jpg"):
        old.unlink()
    if not _image(theme["wallpaper"], GRUB_THEME / "background.png", 0.25 if light else -0.30, 2):
        _write(GRUB_THEME / "background.png", png_solid(16, 16, theme["bg"]))
    fonts = {}
    for key, family, size in (("grub_font_small", theme["font_ui"], 18), ("grub_font_big", "Outfit:bold", 32),
                              ("grub_font_mono", "JetBrains Mono", 16)):
        src = _font_file(family)
        out = GRUB_THEME / f"{key}.pf2"
        if src and subprocess.run(["grub-mkfont", "-s", str(size), "-o", str(out), src],
                                  check=False, stderr=subprocess.DEVNULL).returncode == 0:
            fonts[key] = _pf2_name(out) or "Unknown Regular 16"
        else:
            fonts[key] = "Unifont Regular 16"
    menu, select = theme["surface"], theme["accent"]
    pieces = {"menu_c.png": png_solid(8, 8, menu, 225), "select_c.png": png_solid(8, 8, select),
              "thumb_c.png": png_solid(4, 8, theme["accent"])}
    for name, data in pieces.items():
        _write(GRUB_THEME / name, data)
    _write(GRUB_THEME / "theme.txt", render((tpl / "grub-theme.txt.in").read_text(), {**theme, **fonts}))

    text = GRUB_DEFAULT.read_text()
    new = _set_var(text, "GRUB_THEME", f'"{GRUB_THEME}/theme.txt"')
    new = _set_var(new, "GRUB_TERMINAL_OUTPUT", "gfxterm")
    new = _set_var(new, "GRUB_GFXMODE", "auto")
    if shutil.which("plymouth"):
        # Calamares writes this line in single quotes, the grub package in double
        m = re.search(r"""^GRUB_CMDLINE_LINUX_DEFAULT=(["'])(.*)\1""", new, re.M)
        if m and "splash" not in m.group(2).split():
            q = m.group(1)
            new = new.replace(m.group(0), f"GRUB_CMDLINE_LINUX_DEFAULT={q}{(m.group(2) + ' splash').strip()}{q}")
    if new != text:
        _write(GRUB_DEFAULT, new)
    if Path("/boot/grub/grub.cfg").is_file() and shutil.which("grub-mkconfig"):
        _backup(Path("/boot/grub/grub.cfg"))
        subprocess.run(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log(f"GRUB: theme in {GRUB_THEME}")


def plymouth(theme: dict, render: Callable, tpl: Path, log: Callable) -> None:
    if not shutil.which("plymouth-set-default-theme"):
        return
    # the splash is always a dark scene (dimmed wallpaper, white mark), so a
    # light theme swaps its text and background colours here
    light = theme["mode"] == "light"
    splash = {"splash_bg": theme["text"] if light else theme["bg"],
              "splash_text": theme["bg"] if light else theme["text"]}
    splash["splash_dim"] = xfwm4._mix(splash["splash_text"], splash["splash_bg"], 0.35)
    keys = dict(theme)
    for key, value in splash.items():
        keys[key] = value
        keys[f"{key}_r"], keys[f"{key}_g"], keys[f"{key}_b"] = (str(int(value[i:i + 2], 16)) for i in (0, 2, 4))
    PLYMOUTH_THEME.mkdir(parents=True, exist_ok=True)
    if not _image(theme["wallpaper"], PLYMOUTH_THEME / "background.png", -0.45, 3):
        _write(PLYMOUTH_THEME / "background.png", png_solid(16, 16, splash["splash_bg"]))
    if LOGO.is_file():
        _write(PLYMOUTH_THEME / "logo.png", LOGO.read_bytes())
    else:
        _write(PLYMOUTH_THEME / "logo.png", png_solid(1, 1, "000000", 0))
    _write(PLYMOUTH_THEME / "track.png", png_solid(8, 4, splash["splash_dim"], 140))
    _write(PLYMOUTH_THEME / "fill.png", png_solid(8, 4, theme["accent"]))
    _write(PLYMOUTH_THEME / "static-linux.plymouth", render((tpl / "plymouth.plymouth.in").read_text(), keys))
    _write(PLYMOUTH_THEME / "static-linux.script", render((tpl / "plymouth.script.in").read_text(), keys))
    subprocess.run(["plymouth-set-default-theme", "static-linux"], check=False)

    # the splash lives in the initramfs: the hook must be there, after udev
    if MKINITCPIO.is_file():
        text = MKINITCPIO.read_text()
        m = re.search(r"^HOOKS=\(([^)]*)\)", text, re.M)
        if m and "plymouth" not in m.group(1).split():
            hooks = m.group(1).split()
            at = hooks.index("systemd") + 1 if "systemd" in hooks else \
                hooks.index("udev") + 1 if "udev" in hooks else len(hooks)
            hooks.insert(at, "plymouth")
            _write(MKINITCPIO, text.replace(m.group(0), f"HOOKS=({' '.join(hooks)})"))
    if REBUILD_INITRAMFS and shutil.which("mkinitcpio") and any(Path("/boot").glob("initramfs-*.img")):
        log("Plymouth: rebuilding the initramfs (this takes a moment)")
        subprocess.run(["mkinitcpio", "-P"], check=False, stdout=subprocess.DEVNULL)
    log("Plymouth: boot splash in the theme")


def apply(theme: dict, render: Callable, tpl: Path, log: Callable) -> None:
    greeter(theme, render, tpl, log)
    plymouth(theme, render, tpl, log)
    grub(theme, render, tpl, log)  # last: grub-mkconfig sees the splash param
    if BACKUP.is_dir():
        log(f"replaced system files saved in {BACKUP}")
