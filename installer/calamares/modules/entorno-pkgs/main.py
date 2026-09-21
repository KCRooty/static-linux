#!/usr/bin/env python3
# Static Linux — Calamares "entorno-pkgs" job
#
# Installs the desktop environment the user picked on the "entorno"
# packagechooser page (globalStorage["packagechooser_entorno"], a
# comma-separated string per packagechooser's "legacy" method — one value
# here since that instance is mode: required, single-select) and deploys
# its dotfiles with the environment's own install.sh — a plain package
# list can't do the theming/config part, so this can't just be a
# `method: packages` packagechooser like a generic DE picker would use.

import os
import re

import libcalamares

ENVS = {
    "xfce-themed": ("packages/lists/xfce.list", "entornos/xfce-themed/install.sh"),
    "openbox-minimal": ("packages/lists/openbox.list", "entornos/openbox-minimal/install.sh"),
    "hyprland-astal-lite": ("packages/lists/hyprland-lite.list", "entornos/hyprland-astal-lite/install.sh"),
    "hyprland-astal-full": ("packages/lists/hyprland-full.list", "entornos/hyprland-astal-full/install.sh"),
}
TARGET_PREFIX = "usr/lib/static-linux"  # where staticlinux-base ships repo data, relative to target root
AUR_RE = re.compile(r"^#\s*(\S+)\s*\(AUR\)\s*$")


def pretty_name():
    return "Installing the desktop environment"


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

    chosen = (gs.value("packagechooser_entorno") or "").split(",")[0].strip()
    slug = chosen if chosen in ENVS else "xfce-themed"
    if chosen and chosen not in ENVS:
        libcalamares.utils.warning(f"entorno-pkgs: unknown id {chosen!r}, falling back to xfce-themed")

    list_rel, install_rel = ENVS[slug]
    list_path = os.path.join(root, TARGET_PREFIX, list_rel)
    install_target = f"/{TARGET_PREFIX}/{install_rel}"
    install_host_path = os.path.join(root, TARGET_PREFIX, install_rel)

    if not os.path.exists(list_path):
        return ("Environment package list missing", f"expected it at {list_path}")

    pkgs, aur_pkgs = _parse_list(list_path)
    if pkgs:
        rc = libcalamares.utils.target_env_call(
            ["pacman", "-S", "--needed", "--noconfirm", *pkgs]
        )
        if rc != 0:
            return ("Environment package install failed", f"pacman exited {rc} for {slug}")

    if aur_pkgs:
        gs.insert("slEntornoAurPending", sorted(set(aur_pkgs)))
        libcalamares.utils.warning(
            f"entorno-pkgs: AUR packages for {slug} need `paru -S <pkg>` after "
            "first boot: " + ", ".join(sorted(set(aur_pkgs)))
        )

    if not os.path.exists(install_host_path):
        libcalamares.utils.warning(f"{install_target} missing in target; skipping dotfiles")
        gs.insert("slEntornoApplied", slug)
        return None

    rc = libcalamares.utils.target_env_call(["bash", install_target, "--skel"])
    if rc != 0:
        return ("Environment install.sh failed", f"--skel exited {rc} for {slug}")

    users = gs.value("createdUser") or {}
    login = users.get("username") if isinstance(users, dict) else None
    if login:
        libcalamares.utils.target_env_call(["bash", install_target, "--home", "--user", login])

    gs.insert("slEntornoApplied", slug)
    libcalamares.utils.debug(f"entorno-pkgs: installed {slug} ({len(pkgs)} packages)")
    return None
