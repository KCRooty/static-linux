#!/usr/bin/env python3
# Static Linux — Calamares "rendimiento" job
#
# The static tuning (sysctl, zram, I/O schedulers, journald, earlyoom drop-in,
# shader caches…) ships in staticlinux-base, see rendimiento/README.md. This
# job only does what depends on the machine or on the choices made:
#
#   slCreateSwapfile (sl-detect, RAM < 4 GB)
#       2 GB /swapfile with priority 10 under zram's 100, added to fstab, so a
#       big build (paru, Rust) still has somewhere to go. Skipped on btrfs: a
#       swapfile inside the snapshotted @ subvolume breaks snapper, and btrfs
#       is only picked with 4 GB or more anyway.
#   btrfs root
#       Snapper config for / (snap-pac then takes a pre/post snapshot around
#       every pacman transaction, sl-ctl update included), at most 10 kept,
#       no hourly timeline; grub-btrfsd lists them in the GRUB menu so a
#       broken update can be booted around.
#   Gaming flavor
#       /etc/scx_loader/config.toml (scx_lavd, Auto) + scx_loader.service, so
#       the sched_ext scheduler runs from the first boot. `sl-game` switches
#       it to Gaming mode while a game runs.

import os
import shutil

import libcalamares

SCX_SRC = "usr/share/static-linux/rendimiento/scx/config.toml"  # target-relative
SWAPFILE = "/swapfile"
FSTAB_LINE = "/swapfile none swap defaults,pri=10 0 0\n"


def _tr(text: str) -> str:
    """Spanish source string -> the installer's language (gettext domain
    static-linux, from staticlinux-base); English if there is no catalogue."""
    import gettext
    try:
        langs = list(libcalamares.utils.gettext_languages())
    except Exception:  # outside Calamares (tests)
        langs = []
    if not langs or langs[0].startswith("es"):
        return text
    tr = gettext.translation("static-linux", "/usr/share/locale",
                             languages=langs + ["en"], fallback=True)
    return tr.gettext(text)


def pretty_name():
    return _tr("Ajustando el rendimiento")


def _root_fstype(root):
    with open("/proc/mounts", encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) > 2 and parts[1] == root.rstrip("/"):
                return parts[2]
    return ""


def _swapfile(root):
    if os.path.exists(os.path.join(root, SWAPFILE.lstrip("/"))):
        return
    fstype = _root_fstype(root)
    if fstype == "btrfs":
        libcalamares.utils.debug("rendimiento: btrfs root, no swapfile (zram only)")
        return
    rc = libcalamares.utils.target_env_call(
        ["mkswap", "--file", SWAPFILE, "--size", "2G"])
    if rc != 0:
        libcalamares.utils.warning(f"rendimiento: mkswap --file failed ({rc})")
        return
    fstab = os.path.join(root, "etc/fstab")
    with open(fstab, encoding="utf-8") as fh:
        current = fh.read()
    if SWAPFILE not in current:
        with open(fstab, "a", encoding="utf-8") as fh:
            fh.write("\n# Static Linux: 2 GB swapfile (RAM < 4 GB), below zram\n" + FSTAB_LINE)


SNAPPER_SET = {"TIMELINE_CREATE": "no", "NUMBER_LIMIT": "10",
               "NUMBER_LIMIT_IMPORTANT": "5", "ALLOW_GROUPS": "wheel"}


def _snapper(root):
    if _root_fstype(root) != "btrfs":
        return
    if not os.path.exists(os.path.join(root, "usr/bin/snapper")):
        libcalamares.utils.warning("rendimiento: btrfs root but snapper is not installed")
        return
    call = libcalamares.utils.target_env_call
    conf = os.path.join(root, "etc/snapper/configs/root")
    if not os.path.exists(conf):
        rc = call(["snapper", "--no-dbus", "-c", "root", "create-config", "/"])
        if rc != 0 or not os.path.exists(conf):
            libcalamares.utils.warning(f"rendimiento: snapper create-config failed ({rc})")
            return
    with open(conf, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    out = []
    for line in lines:
        key = line.split("=", 1)[0]
        out.append(f'{key}="{SNAPPER_SET[key]}"' if key in SNAPPER_SET else line)
    with open(conf, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    for unit in ("snapper-cleanup.timer", "grub-btrfsd.service"):
        call(["systemctl", "enable", unit])
    libcalamares.utils.debug("rendimiento: snapper config for / (snap-pac, grub-btrfs)")


def _scx(root):
    src = os.path.join(root, SCX_SRC)
    if not os.path.exists(os.path.join(root, "usr/bin/scx_loader")) or not os.path.exists(src):
        libcalamares.utils.warning("rendimiento: scx-tools not installed, no sched_ext scheduler")
        return
    dst = os.path.join(root, "etc/scx_loader/config.toml")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        shutil.copyfile(src, dst)
    libcalamares.utils.target_env_call(["systemctl", "enable", "scx_loader.service"])


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root:
        return ("No target", "rootMountPoint is not set")

    if gs.value("slCreateSwapfile"):
        _swapfile(root)
    _snapper(root)

    chosen = gs.value("packagechooser_sabores") or ""
    slugs = [s.strip() for s in chosen.split(",") if s.strip()] or (gs.value("slSabores") or [])
    if "gaming" in slugs:
        _scx(root)
    return None
