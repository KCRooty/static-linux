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
# sl-theme comes with staticlinux-base and themes every environment (XFCE,
# KDE, Hyprland, Openbox). `--system` does the machine-wide part: login
# screen, GRUB menu and Plymouth splash. The initramfs is built by the
# initcpio job right after this one, so it is not rebuilt here.

import os

import libcalamares

SL_THEME = "/usr/share/static-linux/themes/sl-theme"
DEFAULT = "ambar"


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
    rc = libcalamares.utils.target_env_call(["python3", SL_THEME, theme, "--skel"])
    if rc != 0:
        return ("No se pudo aplicar el tema", f"sl-theme --skel terminó con {rc}")
    if login:
        libcalamares.utils.target_env_call(["python3", SL_THEME, theme, "--user", login])
    rc = libcalamares.utils.target_env_call(["python3", SL_THEME, theme, "--system", "--no-initramfs"])
    if rc != 0:
        libcalamares.utils.warning(f"sl-theme --system ended with {rc}; login/boot keep the defaults")

    libcalamares.utils.debug(f"theme applied: {theme}")
    return None
