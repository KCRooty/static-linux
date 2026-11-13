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
import subprocess

import libcalamares

ENVS = {
    "xfce-themed": ("packages/lists/xfce.list", "entornos/xfce-themed/install.sh"),
    "openbox-minimal": ("packages/lists/openbox.list", "entornos/openbox-minimal/install.sh"),
    "hyprland-astal-lite": ("packages/lists/hyprland-lite.list", "entornos/hyprland-astal-lite/install.sh"),
    "hyprland-astal-full": ("packages/lists/hyprland-full.list", "entornos/hyprland-astal-full/install.sh"),
    "kde-plasma": ("packages/lists/kde.list", "entornos/kde-plasma/install.sh"),
    "gnome": ("packages/lists/gnome.list", "entornos/gnome/install.sh"),
    "cinnamon": ("packages/lists/cinnamon.list", "entornos/cinnamon/install.sh"),
    "i3": ("packages/lists/i3.list", "entornos/i3/install.sh"),
    "bspwm": ("packages/lists/bspwm.list", "entornos/bspwm/install.sh"),
    "sway": ("packages/lists/sway.list", "entornos/sway/install.sh"),
}
# The live ISO carries the local repo (Astal for Hyprland, Brave, ...) at this
# path — see iso/build.sh. The target's own pacman.conf doesn't know it, so
# while installing it is bind-mounted in and a temporary pacman.conf adds it.
LIVE_REPO = "/opt/staticlinux-repo"
LIVE_REPO_NAME = "staticlinux-local"
TMP_CONF = "/tmp/sl-entorno-pacman.conf"
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


def _install_with_local_repo(root, pkgs):
    """pacman -S in the target, with the live ISO's local repo reachable."""
    mnt = root.rstrip("/") + LIVE_REPO
    mounted = False
    conf_args = []
    if os.path.isdir(LIVE_REPO):
        os.makedirs(mnt, exist_ok=True)
        mounted = subprocess.run(["mount", "--bind", "-o", "ro", LIVE_REPO, mnt]).returncode == 0
        if mounted:
            with open(os.path.join(root, "etc/pacman.conf"), encoding="utf-8") as fh:
                base = fh.read()
            with open(root.rstrip("/") + TMP_CONF, "w", encoding="utf-8") as fh:
                fh.write(base + f"\n[{LIVE_REPO_NAME}]\nSigLevel = Optional TrustAll\n"
                              f"Server = file://{LIVE_REPO}\n")
            conf_args = ["--config", TMP_CONF, "-Sy"]
    try:
        return libcalamares.utils.target_env_call(
            ["pacman", *(conf_args or ["-S"]), "--needed", "--noconfirm", *pkgs]
        )
    finally:
        if mounted:
            subprocess.run(["umount", mnt])
            try:
                os.rmdir(mnt)  # /opt itself belongs to the filesystem package
            except OSError:
                pass
            try:
                os.remove(root.rstrip("/") + TMP_CONF)
            except OSError:
                pass


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root:
        return ("No target", "rootMountPoint is not set")

    chosen = (gs.value("packagechooser_entorno") or "").split(",")[0].strip()
    slug = chosen if chosen in ENVS else "xfce-themed"
    if chosen and chosen not in ENVS:
        libcalamares.utils.warning(f"entorno-pkgs: unknown id {chosen!r}, falling back to xfce-themed")

    # the theme picked on the "Tema" page: written first, so the environment's
    # install.sh themes /etc/skel with it; tema-apply then themes the user
    theme = (gs.value("packagechooser_tema") or "ambar").split(",")[0].strip()
    if not theme.replace("-", "").isalnum():
        theme = "ambar"
    os.makedirs(os.path.join(root, "etc/static-linux"), exist_ok=True)
    with open(os.path.join(root, "etc/static-linux/theme"), "w", encoding="utf-8") as fh:
        fh.write(theme + "\n")

    list_rel, install_rel = ENVS[slug]
    list_path = os.path.join(root, TARGET_PREFIX, list_rel)
    install_target = f"/{TARGET_PREFIX}/{install_rel}"
    install_host_path = os.path.join(root, TARGET_PREFIX, install_rel)

    if not os.path.exists(list_path):
        return ("Environment package list missing", f"expected it at {list_path}")

    pkgs, aur_pkgs = _parse_list(list_path)
    if pkgs:
        rc = _install_with_local_repo(root, pkgs)
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

    # the user doesn't exist yet at this point (users runs later and copies
    # /etc/skel, which --skel above already filled); only for re-runs
    login = gs.value("username")
    if login:
        libcalamares.utils.target_env_call(["bash", install_target, "--home", "--user", login])

    gs.insert("slEntornoApplied", slug)
    libcalamares.utils.debug(f"entorno-pkgs: installed {slug} ({len(pkgs)} packages)")
    return None
