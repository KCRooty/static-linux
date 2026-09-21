"""Catálogo page — extra apps beyond the base environment lists.

AUR-tagged apps are shown but not checkable here: pacman can't build AUR
packages as root, so those need `paru <pkg>` from a real terminal as a normal
user (same rule docs/PROYECTO.md gives for xfce.list).
"""

from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from catalog_loader import load_categories  # noqa: E402
from privileged import PrivilegedActionError, install_packages  # noqa: E402


def build(toast_overlay: Adw.ToastOverlay) -> Gtk.Widget:
    page = Adw.PreferencesPage()
    checks: list[tuple[Gtk.CheckButton, str]] = []

    categories = load_categories()
    if not categories:
        empty = Adw.PreferencesGroup(
            title="Catálogo",
            description="No se encontró ningún catálogo en sl-welcome/catalog/.",
        )
        page.add(empty)
        return page

    for cat in categories:
        group = Adw.PreferencesGroup(title=cat["category"])
        for app in cat.get("apps", []):
            is_aur = bool(app.get("aur"))
            subtitle = app.get("desc", "")
            if is_aur:
                subtitle = (subtitle + "  ·  AUR: instala con "
                            f"`paru -S {app['pkg']}` desde una terminal").strip()
            row = Adw.ActionRow(title=app["name"], subtitle=subtitle)
            check = Gtk.CheckButton(valign=Gtk.Align.CENTER, sensitive=not is_aur)
            row.add_prefix(check)
            row.set_activatable_widget(check)
            group.add(row)
            if not is_aur:
                checks.append((check, app["pkg"]))
        page.add(group)

    action_group = Adw.PreferencesGroup()
    install_row = Adw.ActionRow(title="Instalar los paquetes marcados")
    spinner = Gtk.Spinner(visible=False)
    install_btn = Gtk.Button(label="Instalar", valign=Gtk.Align.CENTER,
                              css_classes=["suggested-action"])
    install_row.add_suffix(spinner)
    install_row.add_suffix(install_btn)
    action_group.add(install_row)
    page.add(action_group)

    def on_install(_btn):
        pkgs = [pkg for check, pkg in checks if check.get_active()]
        if not pkgs:
            toast_overlay.add_toast(Adw.Toast(title="No has marcado ningún paquete"))
            return
        install_btn.set_sensitive(False)
        spinner.set_visible(True)
        spinner.start()

        def run():
            try:
                result = install_packages(pkgs)
                ok, msg = result.returncode == 0, result.stderr[-300:]
            except PrivilegedActionError as exc:
                ok, msg = False, str(exc)
            GLib.idle_add(done, ok, msg, len(pkgs))

        def done(ok, msg, n):
            spinner.stop()
            spinner.set_visible(False)
            install_btn.set_sensitive(True)
            title = f"{n} paquete(s) instalados" if ok else f"Falló: {msg or 'ver logs'}"
            toast_overlay.add_toast(Adw.Toast(title=title))

        threading.Thread(target=run, daemon=True).start()

    install_btn.connect("clicked", on_install)
    return page
