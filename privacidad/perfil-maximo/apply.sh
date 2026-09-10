#!/bin/bash
# Static Linux — Privacy profile: Maximum / Máximo
# Improved + system Tor proxy + kloak keystroke-timing obfuscation +
# aggressive MAC randomization + encrypted swap. Kernel: linux-hardened.
#
# NOT recommended for very old / slow hardware (e.g. J1900): Tor + hardened
# kernel + encrypted swap add real overhead. sl-detect flags this.

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../scripts/lib.sh
source "$HERE/../scripts/lib.sh"

sl_require_root
sl_log "=== Applying privacy profile: Maximum ==="

sl_apply_baseline

# --- Improved layer -----------------------------------------------------
sl_enable apparmor
command -v firecfg >/dev/null && { sl_backup_file /usr/local/bin; firecfg >/dev/null; }
if command -v usbguard >/dev/null; then
    sl_backup_file /etc/usbguard/rules.conf
    mkdir -p /etc/usbguard
    usbguard generate-policy > /etc/usbguard/rules.conf
    chmod 0600 /etc/usbguard/rules.conf
    sl_enable usbguard
fi

# --- Aggressive MAC randomization (also on ethernet, new MAC per scan) --
sl_write /etc/NetworkManager/conf.d/00-static-linux-privacy.conf <<'EOF'
[device-mac-randomization]
wifi.scan-rand-mac-address=yes

[connection-mac-randomization]
wifi.cloned-mac-address=random
ethernet.cloned-mac-address=random
EOF

# --- System Tor proxy -------------------------------------------------
if command -v tor >/dev/null; then
    sl_write /etc/tor/torrc <<'EOF'
SocksPort 9050
ControlPort 9051
CookieAuthentication 1
DataDirectory /var/lib/tor
EOF
    sl_enable tor
    sl_log "Tor SOCKS proxy on 127.0.0.1:9050 (use torsocks / proxychains)"
fi

# --- kloak: keystroke timing obfuscation (AUR package provides the unit) -
if systemctl list-unit-files 2>/dev/null | grep -q '^kloak'; then
    sl_enable kloak
else
    sl_warn "kloak not installed — install from AUR for keystroke obfuscation"
fi

# --- Encrypted swap ---------------------------------------------------
# If swap is a plain partition, switch it to a per-boot random-key crypt
# device. Swapfiles inside a LUKS2 root are already encrypted — skip then.
root_src="$(findmnt -n -o SOURCE / || true)"
if [[ "$root_src" != /dev/mapper/* ]]; then
    swap_part="$(awk '$3=="swap" && $1 ~ /^\/dev\// {print $1; exit}' /proc/swaps 2>/dev/null || true)"
    if [[ -n "${swap_part:-}" ]]; then
        sl_backup_file /etc/crypttab
        sl_backup_file /etc/fstab
        swapoff "$swap_part" || true
        grep -q '^swap ' /etc/crypttab 2>/dev/null || \
            echo "swap $swap_part /dev/urandom swap,cipher=aes-xts-plain64,size=256" >> /etc/crypttab
        sed -i "s|^$swap_part .*swap.*|/dev/mapper/swap none swap defaults 0 0|" /etc/fstab
        sl_log "swap partition $swap_part converted to encrypted swap"
    fi
fi

sl_record_profile "maximum"
sl_log "Maximum profile applied. Reboot REQUIRED (linux-hardened, crypttab)."
