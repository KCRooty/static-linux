"""Privacy page — pick one of the 3 profiles. Needs root, goes through pkexec."""

from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from privileged import PrivilegedActionError, apply_privacy_profile  # noqa: E402

_PROFILES = [
    ("basico", "Básico",
     "Defaults de día 0 + UFW + aleatorización de MAC. Kernel linux-zen."),
    ("mejorado", "Mejorado",
     "+ Firejail + AppArmor + USBGuard. Kernel linux-zen."),
    ("maximo", "Máximo",
     "+ Tor + kloak + swap cifrado. Kernel linux-hardened."),
]


def build(toast_overlay: Adw.ToastOverlay) -> Gtk.Widget:
    page = Adw.PreferencesPage()
    group = Adw.PreferencesGroup(
        title="Perfil de privacidad",
        description="Cada perfil hace backup automático de lo que toca "
                     "(/var/backups/static-linux/privacy/), así que todo se puede deshacer. "
                     "Pide contraseña de administrador.",
    )
    page.add(group)

    for slug, label, desc in _PROFILES:
        row = Adw.ActionRow(title=label, subtitle=desc)
        button = Gtk.Button(label="Aplicar", valign=Gtk.Align.CENTER,
                             css_classes=["suggested-action"])
        spinner = Gtk.Spinner(visible=False)
        row.add_suffix(spinner)
        row.add_suffix(button)

        def on_clicked(_btn, slug=slug, label=label, button=button, spinner=spinner):
            button.set_sensitive(False)
            spinner.set_visible(True)
            spinner.start()

            def run():
                try:
                    result = apply_privacy_profile(slug)
                    ok, msg = result.returncode == 0, result.stderr[-300:]
                except PrivilegedActionError as exc:
                    ok, msg = False, str(exc)
                GLib.idle_add(done, ok, msg)

            def done(ok, msg):
                spinner.stop()
                spinner.set_visible(False)
                button.set_sensitive(True)
                title = f"Perfil {label} aplicado" if ok else f"Falló: {msg or 'ver logs'}"
                toast_overlay.add_toast(Adw.Toast(title=title))

            threading.Thread(target=run, daemon=True).start()

        button.connect("clicked", on_clicked)
        group.add(row)

    return page
