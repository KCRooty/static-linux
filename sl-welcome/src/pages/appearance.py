"""Appearance page — the theme picker (wallpaper + palette + style), delegates
to sl-theme, plus the old accent helpers the overview banner still reads.

Applying a theme as the logged-in user needs no root (sl-theme writes only to
$HOME and talks to the running session), so this page runs it directly.
"""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from paths import accent_apply_path, accent_palette_path, themes_dir  # noqa: E402


def _load_palette() -> list[dict]:
    accents = []
    path = accent_palette_path()
    if not path.exists():
        return accents
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = [f.strip() for f in line.split("|")]
        if len(fields) != 7:
            continue
        name, accent, dim, detail, text, bg, label = fields
        accents.append({"name": name, "accent": accent, "dim": dim, "detail": detail,
                        "bg": bg, "label": label})
    return accents


def _current_accent() -> str:
    apply_sh = accent_apply_path()
    if not apply_sh.exists():
        return "purple"
    try:
        out = subprocess.run(["bash", str(apply_sh), "--current"],
                              capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or "purple"
    except subprocess.SubprocessError:
        return "purple"


STYLE_LABEL = {"minimal": "barra fina arriba", "aero": "Frutiger Aero, barra abajo",
               "ventanas": "como Windows, barra abajo"}


def _themes() -> list[dict]:
    out = []
    root = themes_dir()
    if not root.is_dir():
        return out
    for conf in sorted(root.glob("*/theme.conf")):
        theme = {"id": conf.parent.name, "dir": conf.parent}
        for line in conf.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") and "comment" not in theme:
                theme["comment"] = line.lstrip("# ").split(":", 1)[-1].strip().split(". ")[0].rstrip(".")
            elif "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                theme[key.strip()] = value.strip()
        out.append(theme)
    # the default first, then alphabetical
    out.sort(key=lambda t: (t["id"] != "ambar", t.get("name", t["id"])))
    return out


def _current_theme() -> str:
    path = Path.home() / ".config/static-linux/theme"
    try:
        return path.read_text().strip() or "ambar"
    except OSError:
        return "ambar"


def build(toast_overlay: Adw.ToastOverlay) -> Gtk.Widget:
    page = Adw.PreferencesPage()
    group = Adw.PreferencesGroup(
        title="Tema",
        description="Cada tema es un fondo, una paleta sacada de él y un estilo de ventanas "
                    "y barra. Cambia todo a la vez y guarda copia de lo que sustituye. Sin sudo.",
    )
    page.add(group)
    tool = themes_dir() / "sl-theme"
    current = _current_theme()
    first = None
    for theme in _themes():
        mode = "claro" if theme.get("mode") == "light" else "oscuro"
        style = STYLE_LABEL.get(theme.get("style", "minimal"), "")
        row = Adw.ActionRow(title=theme.get("name", theme["id"]),
                            subtitle=f"{mode} · {style}" + (f" · {theme['comment']}" if theme.get("comment") else ""))
        preview = theme["dir"] / "preview.jpg"
        if preview.exists():
            pic = Gtk.Picture.new_for_filename(str(preview))
            pic.set_size_request(128, 72)
            pic.set_content_fit(Gtk.ContentFit.COVER)
            row.add_suffix(Gtk.Frame(child=pic, valign=Gtk.Align.CENTER, css_classes=["sl-card"]))
        radio = Gtk.CheckButton(valign=Gtk.Align.CENTER, active=(theme["id"] == current))
        if first is None:
            first = radio
        else:
            radio.set_group(first)
        row.add_prefix(radio)
        row.set_activatable_widget(radio)
        radio.connect("toggled", _on_theme, theme, tool, toast_overlay)
        group.add(row)
    if first is None:
        group.set_description("No encuentro los temas de Static Linux (sl-theme).")
    return page


def _on_theme(radio: Gtk.CheckButton, theme: dict, tool: Path, toast_overlay) -> None:
    if not radio.get_active():
        return

    def run():
        res = subprocess.run(["python3", str(tool), theme["id"]], capture_output=True, text=True)
        name = theme.get("name", theme["id"])
        GLib.idle_add(lambda: toast_overlay.add_toast(Adw.Toast(
            title=f"Tema aplicado: {name}" if res.returncode == 0 else "No se pudo aplicar el tema")))

    threading.Thread(target=run, daemon=True).start()
