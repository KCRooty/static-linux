#!/usr/bin/env python3
# Static Linux — Calamares "display" job
#
# The live session already measured this machine's screen (sl-display-scale,
# from pixels and the monitor's physical size) and scaled the installer with
# it. The installed system runs on the same screen, so the value is recorded
# in the target and the login screens get it right away:
#
#   /etc/static-linux/display-scale     read by XFCE/Openbox on first login
#   LightDM greeter                     xft-dpi
#   SDDM greeter                        QT_SCALE_FACTOR
#
# Hyprland and KDE scale themselves from the monitor's EDID.

import os

import libcalamares

SCALES = {"1": 96, "1.25": 120, "1.5": 144, "2": 192}


def pretty_name():
    return "Display scaling"


def _write(root, path, text):
    full = os.path.join(root, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)


def run():
    root = libcalamares.globalstorage.value("rootMountPoint")
    if not root:
        return ("No target", "rootMountPoint is not set")
    try:
        with open("/run/sl-display-scale", encoding="utf-8") as fh:
            scale = fh.read().strip()
    except OSError:
        scale = "1"
    if scale not in SCALES:
        scale = "1"
    dpi = SCALES[scale]

    _write(root, "/etc/static-linux/display-scale", scale + "\n")
    if scale == "1":
        return None

    if os.path.isdir(os.path.join(root, "etc/lightdm")):
        _write(root, "/etc/lightdm/lightdm-gtk-greeter.conf.d/60-static-linux-dpi.conf",
               f"# Static Linux — HiDPI screen measured by the installer\n[greeter]\nxft-dpi = {dpi}\n")
    if os.path.isdir(os.path.join(root, "etc/sddm.conf.d")) or \
            os.path.exists(os.path.join(root, "usr/bin/sddm")):
        env = f"QT_SCALE_FACTOR={scale}"
        kde = os.path.join(root, "etc/sddm.conf.d/10-static-linux.conf")
        if os.path.exists(kde):  # keep KDE's Wayland greeter setting next to it
            env += ",QT_WAYLAND_SHELL_INTEGRATION=layer-shell"
        _write(root, "/etc/sddm.conf.d/20-static-linux-scale.conf",
               f"# Static Linux — HiDPI screen measured by the installer\n[General]\nGreeterEnvironment={env}\n")
    libcalamares.utils.debug(f"display: scale {scale} (dpi {dpi})")
    return None
