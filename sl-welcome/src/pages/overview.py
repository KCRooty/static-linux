"""Overview page — branding header + live sl-detect readout + project links."""

from __future__ import annotations

from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

import system_info  # noqa: E402
try:
    from banner import GroovyBanner  # noqa: E402
except ImportError:  # python-cairo missing
    GroovyBanner = None
from pages import appearance  # noqa: E402

OFFLINE_WIKI = Path("/usr/share/doc/static-linux/wiki/index.html")

_LINKS = [
    ("Wiki online", "https://staticforge.dpdns.org/linux/"),
    ("Repositorio (GitHub)", "https://github.com/KCRooty/static-linux"),
    ("Reportar un problema", "https://github.com/KCRooty/static-linux/issues/new/choose"),
]


def _row(title: str, value: str) -> Adw.ActionRow:
    row = Adw.ActionRow(title=title)
    val = Gtk.Label(label=value, css_classes=["sl-mono", "dim-label"])
    row.add_suffix(val)
    return row


def build() -> Gtk.Widget:
    page = Adw.PreferencesPage()

    header = Adw.PreferencesGroup()
    accents = {a["name"]: a for a in appearance._load_palette()}
    acc = accents.get(appearance._current_accent()) or accents.get("purple")
    if acc and GroovyBanner:
        header.add(GroovyBanner(acc))
    else:  # no palette (broken install): plain wordmark
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4,
                       margin_top=24, margin_bottom=8, halign=Gtk.Align.CENTER)
        box.append(Gtk.Label(label="STATIC LINUX", css_classes=["sl-wordmark"]))
        box.append(Gtk.Label(label="by Static Forge · fast. private. yours.",
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
        description="Calculada para este hardware. Puedes cambiarla en Apariencia y Privacidad.",
    )
    rec_group.add(_row("Entorno", rec.get("env", "n/a")))
    rec_group.add(_row("Sistema de archivos", rec.get("fs", "n/a")))
    rec_group.add(_row("Kernel", rec.get("kernel", "n/a")))
    page.add(rec_group)

    links_group = Adw.PreferencesGroup(title="Enlaces")
    if OFFLINE_WIKI.exists():  # the local copy works without a connection
        wiki = Adw.ActionRow(title="Wiki", subtitle="Copia local, funciona sin conexión",
                             activatable=True)
        wiki.add_suffix(Gtk.Image(icon_name="help-contents-symbolic"))
        wiki.connect("activated", lambda _r: Gtk.UriLauncher(uri=OFFLINE_WIKI.as_uri()).launch())
        links_group.add(wiki)
    for label, url in _LINKS:
        row = Adw.ActionRow(title=label, activatable=True)
        row.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        row.connect("activated", lambda _r, u=url: Gtk.UriLauncher(uri=u).launch())
        links_group.add(row)
    page.add(links_group)

    return page
