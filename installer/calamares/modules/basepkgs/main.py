#!/usr/bin/env python3
# Static Linux — Calamares "basepkgs" job
#
# Installs packages/lists/base.list into the target — the packages every
# Static Linux install needs regardless of chosen environment/flavor/privacy
# profile. Kept as its own job (not inlined into the core "packages"
# module's static `operations:` list) so base.list stays the single source
# of truth instead of two copies drifting apart — same reasoning as
# sabores/main.py and privacidad's packages.list pointer files.
#
# AUR packages are never installed here: pacman can't build them as root
# during the install. Recorded in globalStorage["slBaseAurPending"] for a
# later `paru` run, same policy as sabores/main.py and sl-welcome's catalog.

import os
import re

import libcalamares

LIST_PATH = "usr/lib/static-linux/packages/lists/base.list"  # relative to target root
AUR_RE = re.compile(r"^#\s*(\S+)\s*\(AUR\)\s*$")


def pretty_name():
    return "Installing base packages"


def _parse_list(path):
    pkgs, aur_pkgs = [], []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            m = AUR_RE.match(line)
            if m:
                aur_pkgs.append(m.group(1))
                continue
            if line.startswith("#"):
                continue
            pkgs.append(line)
    return pkgs, aur_pkgs


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root:
        return ("No target", "rootMountPoint is not set")

    list_path = os.path.join(root, LIST_PATH)
    if not os.path.exists(list_path):
        return ("base.list missing", f"expected it at {list_path}")

    pkgs, aur_pkgs = _parse_list(list_path)
    if not pkgs:
        return ("base.list is empty", f"no installable packages found in {list_path}")

    rc = libcalamares.utils.target_env_call(
        ["pacman", "-S", "--needed", "--noconfirm", *pkgs]
    )
    if rc != 0:
        return ("Base package install failed", f"pacman exited {rc}")

    if aur_pkgs:
        gs.insert("slBaseAurPending", sorted(set(aur_pkgs)))
        libcalamares.utils.warning(
            "basepkgs: AUR packages need `paru -S <pkg>` after first boot: "
            + ", ".join(sorted(set(aur_pkgs)))
        )

    libcalamares.utils.debug(f"basepkgs: installed {len(pkgs)} package(s)")
    return None
