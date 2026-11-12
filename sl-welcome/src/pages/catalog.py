"""Catálogo page — extra apps beyond the base environment lists.

Every app in sl-welcome/catalog/*.yaml has one or more sources; the first
one available is used:

    pkg      official repos  -> pkexec pacman -S          (one password prompt)
    flatpak  Flathub app id  -> flatpak install --user    (no password)
    aur      AUR package     -> paru -S in a terminal     (paru asks for sudo
                                                           itself, and builds
                                                           as the normal user)
    sf       Static Forge    -> makepkg -si in a terminal (PKGBUILD shipped in
                                                           packages/sf/, builds
                                                           from the official
                                                           release)

Apps already on the system are shown as installed. Whatever a flavor couldn't
install during setup (/etc/static-linux/pending-aur, written by the installer)
is listed first and pre-ticked.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from catalog_loader import load_categories  # noqa: E402
from paths import sf_pkgbuild_dir  # noqa: E402
from privileged import PrivilegedActionError, install_packages  # noqa: E402

PENDING = Path("/etc/static-linux/pending-aur")
FLATHUB = "https://dl.flathub.org/repo/flathub.flatpakrepo"
SOURCE_LABEL = {"pkg": "repos oficiales", "flatpak": "Flathub", "aur": "AUR", "sf": "Static Forge"}

# terminal -> argv prefix that runs a command
TERMINALS = [
    ("kitty", ["kitty"]),
    ("konsole", ["konsole", "-e"]),
    ("xfce4-terminal", ["xfce4-terminal", "-x"]),
    ("gnome-terminal", ["gnome-terminal", "--"]),
    ("alacritty", ["alacritty", "-e"]),
    ("foot", ["foot"]),
    ("lxterminal", ["lxterminal", "-e"]),
]


def _installed() -> tuple[set[str], set[str]]:
    pkgs, flatpaks = set(), set()
    try:
        out = subprocess.run(["pacman", "-Qq"], capture_output=True, text=True, timeout=10).stdout
        pkgs = set(out.split())
    except (OSError, subprocess.SubprocessError):
        pass
    if shutil.which("flatpak"):
        try:
            out = subprocess.run(["flatpak", "list", "--app", "--columns=application"],
                                 capture_output=True, text=True, timeout=10).stdout
            flatpaks = set(out.split())
        except (OSError, subprocess.SubprocessError):
            pass
    return pkgs, flatpaks


def _source(app: dict) -> tuple[str, list[str]] | None:
    """(kind, names) for the first usable source of an app."""
    for kind in ("sf", "pkg", "flatpak", "aur"):
        value = app.get(kind)
        if not value:
            continue
        if kind == "flatpak" and not shutil.which("flatpak"):
            continue
        if kind == "aur" and not shutil.which("paru"):
            continue
        if kind == "sf" and not all((sf_pkgbuild_dir(n) / "PKGBUILD").is_file()
                                    for n in str(value).split()):
            continue
        return kind, str(value).split()
    return None


def _run_in_terminal(command: str) -> bool:
    for name, prefix in TERMINALS:
        if shutil.which(name):
            hold = f"{command}; echo; read -rp 'Listo. Pulsa Intro para cerrar… '"
            subprocess.Popen([*prefix, "bash", "-lc", hold], start_new_session=True)
            return True
    return False


def _pending() -> list[str]:
    try:
        return [x.strip() for x in PENDING.read_text().splitlines() if x.strip()]
    except OSError:
        return []


def build(toast_overlay: Adw.ToastOverlay) -> Gtk.Widget:
    page = Adw.PreferencesPage()
    checks: list[tuple[Gtk.CheckButton, str, list[str]]] = []
    have_pkgs, have_flatpaks = _installed()

    def add_row(group, title, subtitle, kind, names, active=False):
        done = all(n in (have_pkgs if kind == "pkg" else have_flatpaks) for n in names) \
            if kind in ("pkg", "flatpak") else all(n in have_pkgs for n in names)
        row = Adw.ActionRow(title=title, subtitle=subtitle)
        tag = Gtk.Label(label="instalado" if done else SOURCE_LABEL[kind],
                        css_classes=["dim-label", "caption"], valign=Gtk.Align.CENTER)
        row.add_suffix(tag)
        check = Gtk.CheckButton(valign=Gtk.Align.CENTER, sensitive=not done, active=active and not done)
        row.add_prefix(check)
        row.set_activatable_widget(check)
        group.add(row)
        if not done:
            checks.append((check, kind, names))

    pending = _pending()
    if pending:
        group = Adw.PreferencesGroup(
            title="Pendiente de tus sabores",
            description="Lo que no se pudo instalar durante la instalación. Ya está marcado.")
        for item in pending:
            kind, name = ("flatpak", item.split(":", 1)[1]) if item.startswith("flatpak:") else ("aur", item)
            if kind == "aur" and not shutil.which("paru"):
                continue
            add_row(group, name, "", kind, [name], active=True)
        page.add(group)

    categories = load_categories()
    if not categories:
        page.add(Adw.PreferencesGroup(title="Catálogo",
                                      description="No se encontró ningún catálogo."))
        return page

    for cat in categories:
        group = Adw.PreferencesGroup(title=cat["category"])
        for app in cat.get("apps", []):
            src = _source(app)
            if src:
                add_row(group, app["name"], app.get("desc", ""), *src)
        page.add(group)

    action_group = Adw.PreferencesGroup()
    install_row = Adw.ActionRow(
        title="Instalar lo marcado",
        subtitle="Repos oficiales: pide tu contraseña · Flathub: sin contraseña · AUR y Static Forge: se abre una terminal")
    spinner = Gtk.Spinner(visible=False)
    install_btn = Gtk.Button(label="Instalar", valign=Gtk.Align.CENTER,
                             css_classes=["suggested-action"])
    install_row.add_suffix(spinner)
    install_row.add_suffix(install_btn)
    action_group.add(install_row)
    page.add(action_group)

    def on_install(_btn):
        chosen = [(kind, names) for check, kind, names in checks if check.get_active()]
        if not chosen:
            toast_overlay.add_toast(Adw.Toast(title="No has marcado nada"))
            return
        pkgs = [n for kind, names in chosen if kind == "pkg" for n in names]
        flatpaks = [n for kind, names in chosen if kind == "flatpak" for n in names]
        aur = [n for kind, names in chosen if kind == "aur" for n in names]
        sf = [n for kind, names in chosen if kind == "sf" for n in names]

        if sf:
            # build each PKGBUILD in a scratch copy as the normal user;
            # makepkg -si asks for sudo only to install the result
            steps = [f"d=$(mktemp -d) && cp -r {shlex.quote(str(sf_pkgbuild_dir(n)))}/. \"$d\" "
                     f"&& (cd \"$d\" && makepkg -si --needed --noconfirm); rm -rf \"$d\""
                     for n in sf]
            cmd = " ; ".join(steps)
            if not _run_in_terminal(cmd):
                toast_overlay.add_toast(Adw.Toast(title="Sin terminal para instalar las apps de Static Forge"))

        if aur:
            cmd = "paru -S --needed " + " ".join(shlex.quote(a) for a in aur)
            if not _run_in_terminal(cmd):
                toast_overlay.add_toast(Adw.Toast(title=f"Sin terminal: ejecuta «{cmd}»"))

        if not pkgs and not flatpaks:
            return
        install_btn.set_sensitive(False)
        spinner.set_visible(True)
        spinner.start()

        def run():
            errors = []
            if pkgs:
                try:
                    res = install_packages(pkgs)
                    if res.returncode != 0:
                        errors.append(res.stderr[-200:] or "pacman falló")
                except PrivilegedActionError as exc:
                    errors.append(str(exc))
            if flatpaks:
                subprocess.run(["flatpak", "remote-add", "--user", "--if-not-exists", "flathub", FLATHUB],
                               capture_output=True)
                res = subprocess.run(["flatpak", "install", "--user", "-y", "--noninteractive",
                                      "flathub", *flatpaks], capture_output=True, text=True)
                if res.returncode != 0:
                    errors.append(res.stderr[-200:] or "flatpak falló")
            GLib.idle_add(done, errors, len(pkgs) + len(flatpaks))

        def done(errors, n):
            spinner.stop()
            spinner.set_visible(False)
            install_btn.set_sensitive(True)
            title = f"{n} app(s) instaladas" if not errors else f"Falló: {errors[0]}"
            toast_overlay.add_toast(Adw.Toast(title=title))

        threading.Thread(target=run, daemon=True).start()

    install_btn.connect("clicked", on_install)
    return page
