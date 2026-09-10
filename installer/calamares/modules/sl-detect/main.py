#!/usr/bin/env python3
# Static Linux — Calamares "sl-detect" job module
#
# Runs the standalone sl-detect tool on the live system and writes its findings
# into Calamares globalStorage. Runs early (before the partition page) so the
# UI can highlight the recommended environment / filesystem and so headless
# automated installs get sane defaults.
#
# globalStorage keys published:
#   slDetect            full JSON report (dict)
#   slRecommendedEnv    e.g. "xfce-themed"
#   slRecommendedFs     e.g. "ext4"
#   slRecommendedKernel e.g. "linux-lts"
#   slForceXfce         bool  — hide the Wayland environments in the UI
#   slCreateSwapfile    bool  — 2 GB swapfile needed (RAM < 4 GB)
#   slEfiFallback       bool  — copy grubx64.efi to /EFI/BOOT/BOOTX64.EFI
#   slIoScheduler       "bfq" | "none"

import json
import os
import subprocess

import libcalamares

_CANDIDATES = (
    "/usr/lib/static-linux/sl-detect/detect.py",
    "/usr/bin/sl-detect",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..",
                 "sl-detect", "detect.py"),
)


def pretty_name():
    return "Detecting hardware (sl-detect)"


def _locate():
    for path in _CANDIDATES:
        if os.path.exists(path):
            return os.path.abspath(path)
    return None


def run():
    """Calamares entry point. Return None on success, or (title, msg) tuple."""
    tool = _locate()
    if tool is None:
        libcalamares.utils.warning("sl-detect not found; using safe defaults")
        report = {
            "recommend": {"env": "xfce-themed", "fs": "ext4",
                          "kernel": "linux-lts", "io_scheduler": "bfq"},
            "installer_actions": {"force_xfce": True,
                                  "create_swapfile_2g": True,
                                  "efi_bootx64_fallback": True},
        }
    else:
        try:
            out = subprocess.run(
                ["python3", tool, "--json"] if tool.endswith(".py") else [tool, "--json"],
                capture_output=True, text=True, timeout=30, check=True,
            ).stdout
            report = json.loads(out)
        except (subprocess.SubprocessError, ValueError) as exc:
            return ("Hardware detection failed",
                    f"sl-detect could not complete: {exc}")

    gs = libcalamares.globalstorage
    rec = report.get("recommend", {})
    act = report.get("installer_actions", {})

    gs.insert("slDetect", report)
    gs.insert("slRecommendedEnv", rec.get("env", "xfce-themed"))
    gs.insert("slRecommendedFs", rec.get("fs", "ext4"))
    gs.insert("slRecommendedKernel", rec.get("kernel", "linux-lts"))
    gs.insert("slIoScheduler", rec.get("io_scheduler", "bfq"))
    gs.insert("slForceXfce", bool(act.get("force_xfce", True)))
    gs.insert("slCreateSwapfile", bool(act.get("create_swapfile_2g", True)))
    gs.insert("slEfiFallback", bool(act.get("efi_bootx64_fallback", True)))

    libcalamares.utils.debug(
        f"sl-detect: env={rec.get('env')} fs={rec.get('fs')} "
        f"kernel={rec.get('kernel')} forceXfce={act.get('force_xfce')}"
    )
    return None
