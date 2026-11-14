#!/usr/bin/env python3
# Static Linux — Calamares "sabores" (flavor) job
#
# Installs the flavors picked on the "Sabores" page (packagechooser instance
# `sabores`, mode optionalmultiple -> globalStorage["packagechooser_sabores"],
# comma-separated) and tunes the system for each one. Runs right after the
# `users` job, so the new user can be put in the groups the flavors need.
#
# Per flavor, from packages/lists/sabor-<slug>.list:
#   plain lines            official packages, pacman -S in the target
#   "# flatpak: <app-id>"  Flathub apps, installed system-wide here
#   "# <pkg> (AUR)"        not buildable as root during the install: recorded
#                          in /etc/static-linux/pending-aur, which sl-welcome's
#                          catalog offers to install with paru on first boot
#
# Performance/compat setup (cheap — nothing extra stays resident):
#   gaming            32-bit Vulkan driver for the detected GPU, gamemode
#                     group, ntsync module (Wine/Proton)
#   content-creation  realtime group (low-latency audio for the DAWs)
#   development       docker.socket (socket-activated) + docker group
#   vm                libvirtd.socket + libvirt group
#   server            nothing enabled by default (exposed services stay off)

import os
import re
import subprocess

import sys

import libcalamares

sys.path.insert(0, "/etc/calamares/lib")
import slinstall  # noqa: E402

VALID_SLUGS = (
    "gaming", "content-creation", "development", "cybersecurity",
    "office", "server", "vm", "education",
)
LISTS_DIR = "usr/lib/static-linux/packages/lists"  # relative to target root
AUR_RE = re.compile(r"^#\s*(\S+)\s*\(AUR\)\s*$")
FLATPAK_RE = re.compile(r"^#\s*flatpak:\s*(\S+)\s*$")
FLATHUB = "https://dl.flathub.org/repo/flathub.flatpakrepo"

GROUPS = {"gaming": ["gamemode"], "content-creation": ["realtime"],
          "development": ["docker"], "vm": ["libvirt"]}
SOCKETS = {"development": ["docker.socket"], "vm": ["libvirtd.socket"]}

def _tr(text: str) -> str:
    """Spanish source string -> the installer's language (gettext domain
    static-linux, from staticlinux-base); English if there is no catalogue."""
    import gettext
    try:
        import libcalamares
        langs = list(libcalamares.utils.gettext_languages())
    except Exception:  # outside Calamares (tests)
        langs = []
    if not langs or langs[0].startswith("es"):
        return text
    tr = gettext.translation("static-linux", "/usr/share/locale",
                             languages=langs + ["en"], fallback=True)
    return tr.gettext(text)


def pretty_name():
    return _tr("Instalando los sabores")


def _parse_list(path):
    pkgs, flatpaks, aur = [], [], []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            m = FLATPAK_RE.match(line)
            if m:
                flatpaks.append(m.group(1))
                continue
            m = AUR_RE.match(line)
            if m:
                aur.append(m.group(1))
                continue
            if not line.startswith("#"):
                pkgs.append(line)
    return pkgs, flatpaks, aur


def _gpu_lib32(gs):
    """32-bit Vulkan/GL userspace matching the GPU sl-detect found."""
    report = gs.value("slDetect") or {}
    driver = ((report.get("gpu") or {}).get("driver") or "").lower()
    if "nvidia" in driver and "nouveau" not in driver:
        return ["lib32-nvidia-utils"]
    if "amdgpu" in driver or "radeon" in driver:
        return ["lib32-vulkan-radeon"]
    if "i915" in driver or "xe" == driver or "intel" in driver:
        return ["lib32-vulkan-intel"]
    return []


def _pacman(root, pkgs):
    """pacman -Sy in the target: the mirrors plus the live ISO's local repo."""
    return slinstall.target_pacman(root, pkgs, use_mirrors=True)


def _flatpaks(apps):
    if not apps:
        return []
    call = libcalamares.utils.target_env_call
    if call(["flatpak", "remote-add", "--if-not-exists", "--system", "flathub", FLATHUB]) != 0:
        return apps
    failed = []
    for app in apps:
        if call(["flatpak", "install", "--system", "--noninteractive", "-y", "flathub", app]) != 0:
            failed.append(app)
    return failed


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root:
        return ("No target", "rootMountPoint is not set")

    chosen = gs.value("packagechooser_sabores") or ""
    selected = [s.strip() for s in chosen.split(",") if s.strip()] or (gs.value("slSabores") or [])
    # the "servidor" environment brings its flavor even if it wasn't ticked
    selected += [s for s in (gs.value("slSaboresExtra") or []) if s not in selected]
    slugs = [s for s in selected if s in VALID_SLUGS]
    if not slugs:
        libcalamares.utils.debug("sabores: none selected")
        return None

    pkgs, flatpaks, aur = [], [], []
    for slug in slugs:
        path = os.path.join(root, LISTS_DIR, f"sabor-{slug}.list")
        if not os.path.exists(path):
            libcalamares.utils.warning(f"sabores: missing {path}, skipping {slug}")
            continue
        p, f, a = _parse_list(path)
        pkgs += [x for x in p if x not in pkgs]
        flatpaks += [x for x in f if x not in flatpaks]
        aur += [x for x in a if x not in aur]
    if "gaming" in slugs:
        pkgs += [x for x in _gpu_lib32(gs) if x not in pkgs]

    # Universal ISO with no network: the flavors aren't on it (they'd double
    # its size). Recorded so sl-welcome / `sl-ctl flavor add` finish the job.
    if slinstall.offline_repo() and not slinstall.online():
        path = os.path.join(root, "etc/static-linux/pending-flavors")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(slugs) + "\n")
        gs.insert("slSaboresPending", slugs)
        libcalamares.utils.warning(f"sabores: no network, pending for after first boot: {slugs}")
        return None
    # Installed from the ISO's snapshot: catch up with the mirrors first, so
    # the flavors don't pull libraries newer than what the snapshot has
    if slinstall.offline_repo():
        if slinstall.target_upgrade(root) != 0:
            libcalamares.utils.warning("sabores: pacman -Syu failed, installing flavors anyway")

    if pkgs:
        rc = _pacman(root, pkgs)
        if rc != 0:
            return ("Flavor package install failed", f"pacman exited {rc} while installing {slugs}")

    # Flathub needs the network; a failure here isn't fatal, the apps stay
    # listed in sl-welcome's catalog
    failed = _flatpaks(flatpaks)
    if failed:
        libcalamares.utils.warning(f"sabores: flatpak install failed for {failed}")

    login = gs.value("username")
    call = libcalamares.utils.target_env_call
    for slug in slugs:
        for group in GROUPS.get(slug, []):
            call(["groupadd", "-f", group])
            if login:
                call(["usermod", "-aG", group, login])
        for unit in SOCKETS.get(slug, []):
            call(["systemctl", "enable", unit])
    if "gaming" in slugs:
        modules = os.path.join(root, "etc/modules-load.d/ntsync.conf")
        os.makedirs(os.path.dirname(modules), exist_ok=True)
        with open(modules, "w", encoding="utf-8") as fh:
            fh.write("# Static Linux gaming flavor: Wine/Proton NT sync primitives\nntsync\n")

    pending = sorted(set(aur) | {f"flatpak:{x}" for x in failed})
    if pending:
        path = os.path.join(root, "etc/static-linux/pending-aur")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(pending) + "\n")
        gs.insert("slSaboresAurPending", pending)

    with open(os.path.join(root, "etc/static-linux/flavors"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(slugs) + "\n")
    gs.insert("slSaboresApplied", slugs)
    libcalamares.utils.debug(f"sabores: {slugs}: {len(pkgs)} pkgs, {len(flatpaks)} flatpaks")
    return None
