#!/usr/bin/env python3
# Static Linux — Calamares "privacidad-apply" job
#
# Runs the privacy profile apply.sh matching what the user picked on the
# "privacidad" packagechooser page (globalStorage["packagechooser_privacidad"]).
# Same profile-id -> folder mapping as sl-welcome/src/privileged.py, kept in
# sync by hand since Calamares Python jobs and sl-welcome aren't part of the
# same importable package.
#
# Reversibility is the profile script's own job (privacidad/scripts/lib.sh
# backs up before touching anything) — this module just picks which one to
# run.

import os

import libcalamares

PROFILE_FOLDERS = {
    "basico": "perfil-basico",
    "mejorado": "perfil-mejorado",
    "maximo": "perfil-maximo",
}
TARGET_PREFIX = "usr/lib/static-linux"


def pretty_name():
    return "Applying the privacy profile"


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root:
        return ("No target", "rootMountPoint is not set")

    chosen = (gs.value("packagechooser_privacidad") or "").split(",")[0].strip()
    folder = PROFILE_FOLDERS.get(chosen)
    if not folder:
        libcalamares.utils.warning(
            f"privacidad-apply: unknown or empty profile id {chosen!r}, "
            "falling back to basico"
        )
        chosen, folder = "basico", PROFILE_FOLDERS["basico"]

    apply_target = f"/{TARGET_PREFIX}/privacidad/{folder}/apply.sh"
    apply_host_path = os.path.join(root, TARGET_PREFIX, "privacidad", folder, "apply.sh")
    if not os.path.exists(apply_host_path):
        return ("Privacy profile script missing", f"expected it at {apply_host_path}")

    rc = libcalamares.utils.target_env_call(["bash", apply_target])
    if rc != 0:
        return ("Privacy profile apply failed", f"{folder}/apply.sh exited {rc}")

    gs.insert("slPrivacyApplied", chosen)
    libcalamares.utils.debug(f"privacidad-apply: applied {chosen}")
    return None
