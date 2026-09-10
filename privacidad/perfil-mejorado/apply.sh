#!/bin/bash
# Static Linux — Privacy profile: Improved / Mejorado
# Basic + Firejail sandboxing + AppArmor + BleachBit + USBGuard.
# Kernel: linux-zen.

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../scripts/lib.sh
source "$HERE/../scripts/lib.sh"

sl_require_root
sl_log "=== Applying privacy profile: Improved ==="

sl_apply_baseline

# AppArmor (kernel param apparmor=1 security=apparmor is set by the installer
# in the GRUB cmdline for this profile).
sl_enable apparmor

# Firejail: sandbox common risk apps by symlinking them through firejail.
if command -v firecfg >/dev/null; then
    sl_backup_file /usr/local/bin
    firecfg >/dev/null
    sl_log "firejail default profiles linked (firecfg)"
fi

# USBGuard: generate an allow-list from currently connected devices, then
# enforce. New/unknown USB devices are blocked until the user approves them.
if command -v usbguard >/dev/null; then
    sl_backup_file /etc/usbguard/rules.conf
    mkdir -p /etc/usbguard
    usbguard generate-policy > /etc/usbguard/rules.conf
    chmod 0600 /etc/usbguard/rules.conf
    sl_enable usbguard
fi

sl_record_profile "improved"
sl_log "Improved profile applied. Reboot required (AppArmor, linux-zen)."
