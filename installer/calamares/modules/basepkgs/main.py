#!/usr/bin/env python3
# Static Linux — Calamares "basepkgs" job
#
# Bootstraps the target: pacstraps packages/lists/base.list, the kernel
# sl-detect recommended, and staticlinux-base into the freshly mounted (and
# still empty) root. Everything after this in the sequence — entorno-pkgs,
# sabores, privacidad-apply, accent — runs pacman and Static Linux scripts
# *inside* the target, which only works once this job has put a system there.
#
# Has to be pacstrap from the live session, not `pacman` in the target: there
# is no pacman, no keyring and no /usr/lib/static-linux in an empty mount.
# base.list is therefore read from the live system's own copy.
#
# staticlinux-base isn't in any official repo: the ISO carries it in the
# local repo iso/build.sh sets up (/opt/staticlinux-repo), which the live
# pacman.conf — the one pacstrap uses — points at.
#
# AUR packages are never installed here: pacman can't build them as root
# during the install. Recorded in globalStorage["slBaseAurPending"] for a
# later `paru` run, same policy as sabores/main.py and sl-welcome's catalog.

import os
import re
import shutil
import subprocess

import libcalamares

LIST_PATH = "/usr/lib/static-linux/packages/lists/base.list"  # in the live system
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

    if not os.path.exists(LIST_PATH):
        return ("base.list missing", f"expected it at {LIST_PATH} in the live system")

    pkgs, aur_pkgs = _parse_list(LIST_PATH)
    if not pkgs:
        return ("base.list is empty", f"no installable packages found in {LIST_PATH}")

    kernel = gs.value("slRecommendedKernel") or "linux-lts"
    for extra in (kernel, f"{kernel}-headers", "staticlinux-base"):
        if extra not in pkgs:
            pkgs.append(extra)

    # -K: give the target its own fresh pacman keyring instead of copying
    # the live session's.
    # Plain subprocess: this runs in the live session, and libcalamares only
    # has helpers for running things inside the target.
    proc = subprocess.run(
        ["pacstrap", "-K", root, *pkgs],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    if proc.returncode != 0:
        tail = "\n".join(proc.stdout.splitlines()[-15:])
        libcalamares.utils.warning(f"basepkgs: pacstrap output (tail):\n{tail}")
        return ("Base system install failed",
                f"pacstrap exited {proc.returncode}\n\n{tail}")

    # The jobs after this one run pacman in a plain chroot of the target
    # (unlike arch-chroot, Calamares doesn't bind the live resolv.conf in),
    # and a fresh pacstrap only has `filesystem`'s comment-only stub: every
    # download failed with "Could not resolve host". NetworkManager takes
    # the file over on first boot.
    resolv = os.path.join(root, "etc/resolv.conf")
    try:
        with open(resolv, encoding="utf-8") as fh:
            has_dns = any(line.startswith("nameserver") for line in fh)
    except OSError:
        has_dns = False
    if not has_dns:
        if os.path.islink(resolv):
            os.unlink(resolv)
        shutil.copyfile("/etc/resolv.conf", resolv)

    if aur_pkgs:
        gs.insert("slBaseAurPending", sorted(set(aur_pkgs)))
        libcalamares.utils.warning(
            "basepkgs: AUR packages need `paru -S <pkg>` after first boot: "
            + ", ".join(sorted(set(aur_pkgs)))
        )

    libcalamares.utils.debug(f"basepkgs: installed {len(pkgs)} package(s)")
    return None
