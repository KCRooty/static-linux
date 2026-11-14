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

# sl_apparmor_cmdline on|off : AppArmor only runs if the kernel loads it as an
# LSM, and Arch kernels leave it out of the default list. Add (or remove) it in
# GRUB_CMDLINE_LINUX_DEFAULT. In the installer this runs before the grubcfg
# job, which keeps the parameters already on that line; on a running system
# grub.cfg is regenerated here. Takes effect on the next boot.
SL_LSM="lsm=landlock,lockdown,yama,integrity,apparmor,bpf"
sl_apparmor_cmdline() {
    local want="$1" f=/etc/default/grub
    [[ -f "$f" ]] || { sl_warn "no $f, AppArmor not added to the kernel command line"; return 0; }
    local line cur new
    line="$(grep -m1 '^GRUB_CMDLINE_LINUX_DEFAULT=' "$f" || true)"
    cur="${line#GRUB_CMDLINE_LINUX_DEFAULT=}"; cur="${cur#[\"\']}"; cur="${cur%[\"\']}"
    new="$(printf '%s\n' $cur | { grep -v -e '^lsm=' -e '^$' || true; } | tr '\n' ' ')"
    [[ "$want" == on ]] && new="$new$SL_LSM"
    new="${new% }"
    [[ "$new" == "$cur" ]] && return 0
    sl_backup_file "$f"
    if [[ -n "$line" ]]; then
        sed -i "s|^GRUB_CMDLINE_LINUX_DEFAULT=.*|GRUB_CMDLINE_LINUX_DEFAULT=\"$new\"|" "$f"
    else
        echo "GRUB_CMDLINE_LINUX_DEFAULT=\"$new\"" >> "$f"
    fi
    sl_log "kernel command line: AppArmor $want"
    if ! systemd-detect-virt --chroot -q 2>/dev/null && [[ -f /boot/grub/grub.cfg ]] \
       && command -v grub-mkconfig >/dev/null; then
        sl_backup_file /boot/grub/grub.cfg
        grub-mkconfig -o /boot/grub/grub.cfg >/dev/null 2>&1 \
            && sl_log "grub.cfg regenerated" || sl_warn "grub-mkconfig failed; see /etc/default/grub"
    fi
}

# Non-profit or no-log, uncensored, in Europe and worldwide anycast
SL_DNS_SERVERS="['quad9-dnscrypt-ip4-nofilter-pri', 'quad9-doh-ip4-port443-nofilter-pri', 'mullvad-doh', 'dnscry.pt-madrid-ipv4', 'dnscry.pt-paris-ipv4', 'dnscry.pt-frankfurt-ipv4', 'dnscry.pt-amsterdam-ipv4']"

sl_dns_servers() {
    local toml="$1"
    [[ -f "$toml" ]] || return 0
    if grep -q '^server_names' "$toml"; then
        sed -i "s/^server_names.*/server_names = $SL_DNS_SERVERS/" "$toml"
    elif grep -q '^# server_names' "$toml"; then
        sed -i "0,/^# server_names.*/s//server_names = $SL_DNS_SERVERS/" "$toml"
    else
        sed -i "1i server_names = $SL_DNS_SERVERS" "$toml"
    fi
}

# Applied by every profile: the "day 0" defaults from the Master Document §9.1
sl_apply_baseline() {
    sl_log "applying baseline privacy defaults"

    # Encrypted DNS via dnscrypt-proxy. The packaged config listens on
    # 127.0.0.1:53 itself, so run the service (the .socket unit binds the
    # same port and needs listen_addresses = [] to work).
    sl_backup_file /etc/dnscrypt-proxy/dnscrypt-proxy.toml
    # A short, known list instead of "every no-log server in the public
    # list": left alone, dnscrypt-proxy measures ~170 resolvers at every
    # start (hobby servers included) and then picks any of them.
    sl_dns_servers /etc/dnscrypt-proxy/dnscrypt-proxy.toml
    sl_enable dnscrypt-proxy.service
    # Without this NetworkManager keeps writing the DHCP servers into
    # resolv.conf and dnscrypt-proxy is never asked. Global DNS makes NM
    # write 127.0.0.1 there itself, on every connection.
    sl_write /etc/NetworkManager/conf.d/10-static-linux-dns.conf <<'EOF'
[global-dns-domain-*]
servers=127.0.0.1
EOF
    # On a running system (sl-welcome, sl-ctl) switch now: resolver first,
    # then NM, so there is never a moment with 127.0.0.1 and nobody there.
    if ! systemd-detect-virt --chroot -q 2>/dev/null; then
        systemctl start dnscrypt-proxy.service \
            && nmcli general reload conf 2>/dev/null \
            && sl_log "DNS now goes through dnscrypt-proxy" \
            || sl_warn "dnscrypt-proxy did not start; DNS left as it was until reboot"
    fi

    # NetworkManager asks http://ping.archlinux.org every 5 minutes whether
    # there is internet (plain HTTP: your IP, and that you run Arch). Off; the
    # only loss is the automatic captive-portal page on hotel/café wifi.
    sl_write /etc/NetworkManager/conf.d/20-connectivity.conf <<'EOF'
[connectivity]
enabled=false
EOF

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
