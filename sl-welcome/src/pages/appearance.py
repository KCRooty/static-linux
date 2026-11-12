"""Appearance page — the 10-accent picker, delegates to branding/accents/apply.sh.

Applying an accent as the logged-in user needs no root (apply.sh defaults to
$HOME mode), so this page runs the script directly — no pkexec here.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from paths import accent_apply_path, accent_palette_path  # noqa: E402


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


def build(toast_overlay: Adw.ToastOverlay) -> Gtk.Widget:
    page = Adw.PreferencesPage()
    group = Adw.PreferencesGroup(
        title="Acento de color",
        description="Recolorea fastfetch, GTK, borde de ventanas, terminal, "
                     "greeter y fondo de pantalla a la vez. Sin sudo.",
    )
    page.add(group)

    current = _current_accent()
    flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,
                        max_children_per_line=5, row_spacing=12, column_spacing=12,
                        margin_top=8, margin_bottom=8)

    swatches: dict[str, Gtk.Widget] = {}

    def mark_selected(name: str) -> None:
        for n, btn in swatches.items():
            if n == name:
                btn.add_css_class("selected")
            else:
                btn.remove_css_class("selected")

    def on_click(_btn, accent_name: str) -> None:
        apply_sh = accent_apply_path()
        if not apply_sh.exists():
            toast_overlay.add_toast(Adw.Toast(title="No encuentro branding/accents/apply.sh"))
            return

        def run():
            result = subprocess.run(["bash", str(apply_sh), accent_name],
                                     capture_output=True, text=True)
            GLib.idle_add(after_run, result)

        def after_run(result):
            if result.returncode == 0:
                mark_selected(accent_name)
                toast_overlay.add_toast(Adw.Toast(title=f"Acento aplicado: {accent_name}"))
            else:
                toast_overlay.add_toast(Adw.Toast(title="No se pudo aplicar el acento"))

        import threading
        threading.Thread(target=run, daemon=True).start()

    for acc in _load_palette():
        btn = Gtk.Button(css_classes=["sl-accent-swatch"], tooltip_text=acc["label"])
        css = Gtk.CssProvider()
        css.load_from_string(
            f"button {{ background-color: #{acc['accent']}; }}"
        )
        btn.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        btn.connect("clicked", on_click, acc["name"])
        swatches[acc["name"]] = btn
        flow.append(btn)

    mark_selected(current)
    group.add(flow)

    page.add(_style_group(toast_overlay, current))
    return page


STYLES = [
    ("retro", "void", "Retro 70s", "Rayas groovy cálidas y esquinas suaves (el de serie)."),
    ("cyberpunk", "neon", "Cyberpunk", "Rejilla neón, bordes duros y brillos."),
    ("liquid", "liquid", "Líquido", "Minimalista y translúcido, al estilo Apple, con Inter."),
]
WALLPAPERS = Path("/usr/share/static-linux/wallpapers")


def _current_style() -> str:
    apply_sh = accent_apply_path()
    try:
        out = subprocess.run(["bash", str(apply_sh), "--current-style"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or "retro"
    except (OSError, subprocess.SubprocessError):
        return "retro"


def _style_group(toast_overlay: Adw.ToastOverlay, accent: str) -> Adw.PreferencesGroup:
    group = Adw.PreferencesGroup(
        title="Estilo",
        description="El aspecto de todo el sistema: fondo, forma de ventanas y controles, "
                    "tipografía. Se combina con cualquier color de acento.",
    )
    current = _current_style()
    first = None
    for key, prefix, title, desc in STYLES:
        row = Adw.ActionRow(title=title, subtitle=desc)
        thumb = WALLPAPERS / accent / f"{prefix}-{accent}.png"
        if thumb.exists():
            pic = Gtk.Picture.new_for_filename(str(thumb))
            pic.set_size_request(112, 63)
            pic.set_content_fit(Gtk.ContentFit.COVER)
            frame = Gtk.Frame(child=pic, valign=Gtk.Align.CENTER, css_classes=["sl-card"])
            row.add_suffix(frame)
        radio = Gtk.CheckButton(valign=Gtk.Align.CENTER, active=(key == current))
        if first is None:
            first = radio
        else:
            radio.set_group(first)
        row.add_prefix(radio)
        row.set_activatable_widget(radio)
        radio.connect("toggled", _on_style, key, accent, toast_overlay)
        group.add(row)
    return group


def _on_style(radio: Gtk.CheckButton, style: str, accent: str, toast_overlay) -> None:
    if not radio.get_active():
        return
    apply_sh = accent_apply_path()

    def run():
        res = subprocess.run(["bash", str(apply_sh), accent, "--style", style],
                             capture_output=True, text=True)
        GLib.idle_add(lambda: toast_overlay.add_toast(Adw.Toast(
            title=f"Estilo aplicado: {style}" if res.returncode == 0
            else "No se pudo aplicar el estilo")))

    import threading
    threading.Thread(target=run, daemon=True).start()
