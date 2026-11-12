#!/usr/bin/env python3
# Static Linux — Calamares "luks" job
#
# Static Linux doesn't build its own LUKS2 setup — Calamares' core partition
# module already does that (passphrase UI, initcpiocfg, dracutlukscfg,
# bootloader cmdline). This job is Static-Linux-specific glue on top of it:
#
#   1. If the target ended up LUKS-encrypted on hardware sl-detect flagged as
#      J1900-class (HDD, <2 GB RAM, or a pre-2015 CPU) — warn. docs/PROYECTO.md:
#      "ENCRYPTION -> LUKS2 optional (not for J1900-class hardware)". This is
#      advice, not a block: the user already confirmed encryption on the
#      partition page, so we only leave a clear note, not fail the install.
#   2. If Secure Boot is on in the *live* firmware — warn. docs/PROYECTO.md:
#      "Secure Boot -> not supported". GRUB + LUKS on an SB-enforcing board
#      can end up unbootable; better to say so now than after reboot.
#   3. Sanity-check /etc/mkinitcpio.conf HOOKS in the target has "encrypt"
#      before "filesystems". Calamares' own initcpiocfg module is supposed to
#      have already done this — we only check and warn on mismatch, we never
#      rewrite it ourselves (that module owns it, and blind edits here could
#      fight its ordering).
#
# Never fails the install: every branch below is diagnostic. Read the
# Calamares log for the actual outcome.

import os

import libcalamares

SECURE_BOOT_EFIVAR = "/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"


def pretty_name():
    return "Checking disk encryption setup"


def _target_is_luks_encrypted(gs):
    partitions = gs.value("partitions") or []
    return any(p.get("luksMapperName") for p in partitions if isinstance(p, dict))


def _is_j1900_class(sl_detect_report):
    if not sl_detect_report:
        return False
    storage = sl_detect_report.get("storage")
    ram_mb = sl_detect_report.get("ram_mb", 4096)
    cpu_year = sl_detect_report.get("cpu", {}).get("approx_year", 2020)
    return storage == "hdd" or ram_mb < 2048 or (cpu_year and cpu_year < 2015)


def _secure_boot_enabled_on_live_system():
    try:
        with open(SECURE_BOOT_EFIVAR, "rb") as fh:
            data = fh.read()
        # efivar value: 4-byte attribute header + 1-byte payload (0/1)
        return len(data) >= 5 and data[4] == 1
    except OSError:
        return None  # not UEFI, no SB efivar, or unreadable — inconclusive


def _hooks_look_right(root):
    conf = os.path.join(root, "etc/mkinitcpio.conf")
    try:
        with open(conf, encoding="utf-8") as fh:
            for line in fh:
                if line.strip().startswith("HOOKS="):
                    hooks = line.split("=", 1)[1].strip().strip('()"\'').split()
                    if "encrypt" not in hooks:
                        return False
                    if "filesystems" in hooks and hooks.index("encrypt") > hooks.index("filesystems"):
                        return False
                    return True
    except OSError:
        return None  # can't read it — inconclusive, don't warn
    return None  # no HOOKS line found — inconclusive


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root:
        return ("No target", "rootMountPoint is not set")

    if not _target_is_luks_encrypted(gs):
        libcalamares.utils.debug("luks: no LUKS partitions detected, nothing to do")
        return None

    if _is_j1900_class(gs.value("slDetect")):
        libcalamares.utils.warning(
            "luks: LUKS2 elegido en hardware de clase J1900 (HDD/RAM baja/CPU "
            "antigua). docs/PROYECTO.md recomienda EXT4 sin cifrar aquí por rendimiento. "
            "No se bloquea la instalación."
        )

    sb = _secure_boot_enabled_on_live_system()
    if sb:
        libcalamares.utils.warning(
            "luks: Secure Boot está ACTIVADO en el firmware y Static Linux no lo "
            "soporta (GRUB sin firmar). Desactívalo en la BIOS/UEFI antes de "
            "arrancar el sistema instalado."
        )

    hooks_ok = _hooks_look_right(root)
    if hooks_ok is False:
        libcalamares.utils.warning(
            "luks: /etc/mkinitcpio.conf en el target no tiene 'encrypt' antes de "
            "'filesystems' en HOOKS. Revisa initcpiocfg, el arranque puede fallar."
        )

    gs.insert("slLuksChecked", True)
    return None
