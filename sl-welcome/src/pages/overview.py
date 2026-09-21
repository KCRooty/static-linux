"""Overview page — branding header + live sl-detect readout + project links."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

import system_info  # noqa: E402

_LINKS = [
    ("Wiki", "https://github.com/KCRooty/static-linux/wiki"),
    ("Repositorio (GitHub)", "https://github.com/KCRooty/static-linux"),
    ("Reportar un problema", "https://github.com/KCRooty/static-linux/issues/new"),
]


def _row(title: str, value: str) -> Adw.ActionRow:
    row = Adw.ActionRow(title=title)
    val = Gtk.Label(label=value, css_classes=["sl-mono", "dim-label"])
    row.add_suffix(val)
    return row


def build() -> Gtk.Widget:
    page = Adw.PreferencesPage()

    header = Adw.PreferencesGroup()
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4,
                   margin_top=24, margin_bottom=8, halign=Gtk.Align.CENTER)
    box.append(Gtk.Label(label="STATIC LINUX", css_classes=["sl-wordmark"]))
    box.append(Gtk.Label(label="by Static Forge — fast. private. yours.",
                          css_classes=["sl-tagline"]))
    header.add(box)
    page.add(header)

    info = system_info.read()
    cpu = info.get("cpu", {})
    gpu = info.get("gpu", {})
    rec = info.get("recommend", {})

    sys_group = Adw.PreferencesGroup(title="Este equipo")
    sys_group.add(_row("CPU", cpu.get("model", "n/a")))
    sys_group.add(_row("RAM", f"{info.get('ram_mb', '?')} MB"))
    sys_group.add(_row("GPU", gpu.get("model", "n/a")))
    sys_group.add(_row("Driver gráfico", gpu.get("driver", "n/a")))
    sys_group.add(_row("Wayland", "Sí" if info.get("wayland") else "No"))
    sys_group.add(_row("Firmware", info.get("firmware", "n/a")))
    sys_group.add(_row("Almacenamiento", info.get("storage", "n/a")))
    sys_group.add(_row("Arquitectura", info.get("arch", "n/a")))
    page.add(sys_group)

    rec_group = Adw.PreferencesGroup(
        title="Recomendación de sl-detect",
        description="Calculada para este hardware — puedes cambiarla en Apariencia/Privacidad.",
    )
    rec_group.add(_row("Entorno", rec.get("env", "n/a")))
    rec_group.add(_row("Sistema de archivos", rec.get("fs", "n/a")))
    rec_group.add(_row("Kernel", rec.get("kernel", "n/a")))
    page.add(rec_group)

    links_group = Adw.PreferencesGroup(title="Enlaces")
    for label, url in _LINKS:
        row = Adw.ActionRow(title=label, activatable=True)
        row.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        row.connect("activated", lambda _r, u=url: Gtk.UriLauncher(uri=u).launch())
        links_group.add(row)
    page.add(links_group)

    return page
