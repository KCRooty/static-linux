"""Appearance page — the 10-accent picker, delegates to branding/accents/apply.sh.

Applying an accent as the logged-in user needs no root (apply.sh defaults to
$HOME mode), so this page runs the script directly — no pkexec here.
"""

from __future__ import annotations

import subprocess

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
    return page
