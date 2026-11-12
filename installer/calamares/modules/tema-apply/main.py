#!/usr/bin/env python3
# Static Linux — Calamares "tema-apply" job
#
# Applies the theme picked on the "Tema" page (packagechooser instance `tema`)
# inside the installed system: /etc/skel for every future user, then the
# user created by the installer.
#
# Input:  globalStorage["packagechooser_tema"]: a folder name under
#         /usr/share/static-linux/themes/ (default: "ambar").
#
# sl-theme comes with staticlinux-base. The older accent tool still runs
# first, with the accent closest to the theme, because the LightDM greeter,
# the Hyprland bar and Openbox read its files until they move to sl-theme;
# sl-theme then rewrites everything both tools touch.

import os

import libcalamares

SL_THEME = "/usr/share/static-linux/themes/sl-theme"
ACCENT_SH = "/usr/lib/static-linux/accents/apply.sh"
DEFAULT = "ambar"
# nearest of the 10 old accents, for the parts sl-theme does not draw yet
ACCENT_FOR = {"ambar": "yellow", "papel": "grey", "nordico": "blue", "bosque": "green",
              "sakura": "pink", "violeta": "purple", "aero": "blue", "ventanas": "blue"}


def pretty_name():
    return "Aplicando el tema"


def run():
    gs = libcalamares.globalstorage
    theme = (gs.value("packagechooser_tema") or DEFAULT).split(",")[0].strip()
    if not theme.replace("-", "").isalnum():
        libcalamares.utils.warning(f"bad theme id {theme!r}; using {DEFAULT}")
        theme = DEFAULT

    root = gs.value("rootMountPoint")
    if not root:
        return ("No target", "rootMountPoint is not set")
    if not os.path.isfile(os.path.join(root, SL_THEME.lstrip("/"))):
        libcalamares.utils.warning(f"{SL_THEME} missing in target; skipping theme")
        return None
    if not os.path.isfile(os.path.join(root, f"usr/share/static-linux/themes/{theme}/theme.conf")):
        libcalamares.utils.warning(f"theme {theme!r} not installed; using {DEFAULT}")
        theme = DEFAULT

    os.makedirs(os.path.join(root, "etc/static-linux"), exist_ok=True)
    with open(os.path.join(root, "etc/static-linux/theme"), "w", encoding="utf-8") as fh:
        fh.write(theme + "\n")

    login = gs.value("username")  # set by the users module
    accent = ACCENT_FOR.get(theme, "purple")
    if os.path.isfile(os.path.join(root, ACCENT_SH.lstrip("/"))):
        with open(os.path.join(root, "etc/static-linux/accent"), "w", encoding="utf-8") as fh:
            fh.write(accent + "\n")
        libcalamares.utils.target_env_call(["bash", ACCENT_SH, accent, "--skel"])
        if login:
            libcalamares.utils.target_env_call(["bash", ACCENT_SH, accent, "--user", login])

    rc = libcalamares.utils.target_env_call(["python3", SL_THEME, theme, "--skel"])
    if rc != 0:
        return ("No se pudo aplicar el tema", f"sl-theme --skel terminó con {rc}")
    if login:
        libcalamares.utils.target_env_call(["python3", SL_THEME, theme, "--user", login])

    libcalamares.utils.debug(f"theme applied: {theme}")
    return None
