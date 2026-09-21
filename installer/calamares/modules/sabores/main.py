#!/usr/bin/env python3
# Static Linux — Calamares "sabores" (flavor) job
#
# Installs the extra packages for whichever flavor presets the user picked
# (Gaming, Development, Cybersecurity, ...). Daily Driver needs no entry here
# — it's the baseline (base.list + chosen environment), always installed by
# the core "packages" module.
#
# Input:  globalStorage["slSabores"] — list of slugs, e.g. ["gaming", "development"]
#         (set by a flavor selection page — not built yet; defaults to [])
#
# Canonical package lists: packages/lists/sabor-<slug>.list (same format as
# base.list — one pkg per line, AUR ones commented as "# pkgname (AUR)").
# Shipped in the target at /usr/lib/static-linux/packages/lists/.
#
# AUR packages are never installed here: pacman can't build them as root
# during the install. They're recorded in globalStorage["slSaboresAurPending"]
# so a first-boot step (sl-welcome, or a summary note) can tell the user to
# run `paru -S <pkg>` themselves — same policy sl-welcome's own catalog page
# uses for its AUR-tagged entries.

import os
import re

import libcalamares

VALID_SLUGS = (
    "gaming", "content-creation", "development", "cybersecurity",
    "office", "server", "vm", "education",
)
LISTS_DIR = "usr/lib/static-linux/packages/lists"  # relative to target root
AUR_RE = re.compile(r"^#\s*(\S+)\s*\(AUR\)\s*$")


def pretty_name():
    return "Installing flavor packages"


def _parse_list(path):
    """Return (pkgs, aur_pkgs) from one packages/lists/*.list file."""
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

    selected = gs.value("slSabores") or []
    slugs = [s for s in selected if s in VALID_SLUGS]
    skipped = [s for s in selected if s not in VALID_SLUGS]
    if skipped:
        libcalamares.utils.warning(f"sabores: ignoring unknown slug(s) {skipped}")

    if not slugs:
        libcalamares.utils.debug("sabores: none selected, nothing to do")
        return None

    all_pkgs, all_aur = [], []
    seen = set()
    for slug in slugs:
        list_path = os.path.join(root, LISTS_DIR, f"sabor-{slug}.list")
        if not os.path.exists(list_path):
            libcalamares.utils.warning(f"sabores: missing {list_path}, skipping {slug}")
            continue
        pkgs, aur_pkgs = _parse_list(list_path)
        for p in pkgs:
            if p not in seen:
                seen.add(p)
                all_pkgs.append(p)
        all_aur.extend(aur_pkgs)

    if all_pkgs:
        rc = libcalamares.utils.target_env_call(
            ["pacman", "-S", "--needed", "--noconfirm", *all_pkgs]
        )
        if rc != 0:
            return ("Flavor package install failed",
                     f"pacman exited {rc} while installing {slugs}")

    if all_aur:
        aur_sorted = sorted(set(all_aur))
        gs.insert("slSaboresAurPending", aur_sorted)
        libcalamares.utils.warning(
            "sabores: AUR packages need `paru -S <pkg>` after first boot: "
            + ", ".join(aur_sorted)
        )

    gs.insert("slSaboresApplied", slugs)
    libcalamares.utils.debug(f"sabores: installed {len(all_pkgs)} package(s) for {slugs}")
    return None
