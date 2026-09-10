#!/usr/bin/env python3
# Static Linux — Calamares "accent" job
#
# Applies the accent colour the user picked (fastfetch / GTK / xfwm4 / terminal
# / LightDM greeter / wallpaper) inside the freshly installed system.
#
# Input:  globalStorage["slAccent"]  — one of the ids in
#         /usr/lib/static-linux/accents/palette.conf  (default: "purple")
#
# The accent tool must be present in the target at
#   /usr/lib/static-linux/accents/apply.sh
# (shipped by the staticlinux-base package / the ISO airootfs).

import libcalamares

APPLY = "/usr/lib/static-linux/accents/apply.sh"
DEFAULT = "purple"


def pretty_name():
    return "Applying accent colour"


def run():
    gs = libcalamares.globalstorage
    accent = (gs.value("slAccent") or DEFAULT).strip()

    # sanity: only [a-z0-9-]
    if not accent.replace("-", "").isalnum():
        libcalamares.utils.warning(f"bad slAccent {accent!r}; using {DEFAULT}")
        accent = DEFAULT

    root = libcalamares.globalstorage.value("rootMountPoint")
    if not root:
        return ("No target", "rootMountPoint is not set")

    import os
    if not os.path.exists(os.path.join(root, APPLY.lstrip("/"))):
        libcalamares.utils.warning(f"{APPLY} missing in target; skipping accent")
        return None

    # apply.sh --skel writes /etc/skel + /etc inside the target; the first-boot
    # user already exists, so also run it against that user's home.
    users = libcalamares.globalstorage.value("createdUser") or {}
    login = users.get("username") if isinstance(users, dict) else None

    rc = libcalamares.utils.target_env_call(["bash", APPLY, accent, "--skel"])
    if rc != 0:
        return ("Accent failed", f"apply.sh --skel exited {rc}")

    if login:
        libcalamares.utils.target_env_call(
            ["bash", APPLY, accent, "--user", login]
        )

    libcalamares.utils.debug(f"accent applied: {accent}")
    return None
