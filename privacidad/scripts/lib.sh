#!/bin/bash
# Static Linux — shared helpers for privacy profile apply scripts.
# Sourced by privacidad/perfil-*/apply.sh. Every change is backed up first;
# nothing here is irreversible (Static Linux critical rule #1).

set -euo pipefail

SL_BACKUP_DIR="/var/backups/static-linux/privacy"
SL_STATE_DIR="/var/lib/static-linux"

sl_log()  { printf '\033[1;36m[privacy]\033[0m %s\n' "$*"; }
sl_warn() { printf '\033[1;33m[privacy]\033[0m %s\n' "$*" >&2; }

sl_require_root() {
    if [[ $EUID -ne 0 ]]; then
        sl_warn "must run as root"
        exit 1
    fi
}

# sl_backup_file <path> : copy a file into the backup tree once, keeping the
# first (pristine) copy. Safe to call repeatedly.
sl_backup_file() {
    local src="$1"
    [[ -e "$src" ]] || return 0
    local dest="${SL_BACKUP_DIR}${src}"
    if [[ ! -e "$dest" ]]; then
        mkdir -p "$(dirname "$dest")"
        cp -a "$src" "$dest"
        sl_log "backed up $src"
    fi
}

# sl_write <path> : write stdin to a file, backing up any previous version.
sl_write() {
    local path="$1"
    sl_backup_file "$path"
    mkdir -p "$(dirname "$path")"
    cat > "$path"
    sl_log "wrote $path"
}

# sl_enable <unit...> : enable (and start if running system) systemd units.
sl_enable() {
    for unit in "$@"; do
        systemctl enable "$unit" 2>/dev/null && sl_log "enabled $unit" \
            || sl_warn "could not enable $unit"
    done
}

sl_record_profile() {
    mkdir -p "$SL_STATE_DIR"
    echo "$1" > "$SL_STATE_DIR/privacy-profile"
    sl_log "active privacy profile: $1"
}

# Applied by every profile: the "day 0" defaults from the Master Document §9.1
sl_apply_baseline() {
    sl_log "applying baseline privacy defaults"

    # DNS over HTTPS via dnscrypt-proxy (default resolver: Quad9)
    sl_backup_file /etc/dnscrypt-proxy/dnscrypt-proxy.toml
    sl_enable dnscrypt-proxy.socket

    # NetworkManager: randomize MAC on wifi + stable-per-connection on ethernet
    sl_write /etc/NetworkManager/conf.d/00-static-linux-privacy.conf <<'EOF'
[device-mac-randomization]
wifi.scan-rand-mac-address=yes

[connection-mac-randomization]
wifi.cloned-mac-address=random
ethernet.cloned-mac-address=stable
EOF

    # journald: volatile logs by default (no persistence across reboots)
    sl_write /etc/systemd/journald.conf.d/00-static-linux-privacy.conf <<'EOF'
[Journal]
Storage=volatile
EOF

    # UFW: deny incoming, allow outgoing
    if command -v ufw >/dev/null; then
        ufw --force reset >/dev/null
        ufw default deny incoming
        ufw default allow outgoing
        # Inside the installer's chroot, `ufw enable` loads the rules into the
        # kernel the chroot shares with the live session and cuts its
        # incoming connections. There, only flip ENABLED so ufw.service
        # loads them on the installed system's first boot.
        if systemd-detect-virt --chroot -q 2>/dev/null; then
            sl_backup_file /etc/ufw/ufw.conf
            sed -i 's/^ENABLED=.*/ENABLED=yes/' /etc/ufw/ufw.conf
            sl_log "ufw enabled for next boot (running in a chroot)"
        else
            ufw --force enable
        fi
        sl_enable ufw
    fi

    sl_enable systemd-oomd
}
