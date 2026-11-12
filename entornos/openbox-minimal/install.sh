#!/bin/bash
# Static Linux — deploy the Openbox minimal environment (512 MB tier).
#
#   ./install.sh --home            deploy into $HOME (test on a live machine)
#   ./install.sh --home --user X   deploy into /home/X
#   sudo ./install.sh --skel       deploy into /etc/skel (ISO build)
#   sudo ./install.sh --skel --system-config   also drop etc/ files into /
#
# Idempotent. Existing dotfiles are backed up to <target>/.sl-openbox-backup/
# before being overwritten. Nothing here is irreversible.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE=""
TARGET=""
USER_NAME="${SUDO_USER:-${USER:-root}}"
SYSTEM_CONFIG=0

log()  { printf '\033[1;38;5;43m[openbox-minimal]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[openbox-minimal]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[openbox-minimal]\033[0m %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --home)          MODE="home" ;;
        --skel)          MODE="skel" ;;
        --user)          USER_NAME="$2"; shift ;;
        --system-config) SYSTEM_CONFIG=1 ;;
        *)               die "unknown option: $1" ;;
    esac
    shift
done

[[ -n "$MODE" ]] || die "pick a mode: --home or --skel"

if [[ "$MODE" == "skel" ]]; then
    TARGET="/etc/skel"
    [[ $EUID -eq 0 ]] || die "--skel needs root"
else
    TARGET="$(getent passwd "$USER_NAME" | cut -d: -f6)"
    [[ -n "$TARGET" && -d "$TARGET" ]] || die "no home dir for user '$USER_NAME'"
fi

log "target: $TARGET"

# --- backup + copy dotfiles ---------------------------------------------
BACKUP="$TARGET/.sl-openbox-backup/$(date +%Y%m%d-%H%M%S)"
copy_tree() {
    local src="$1" rel
    while IFS= read -r -d '' f; do
        rel="${f#"$src"/}"
        local dst="$TARGET/$rel"
        if [[ -e "$dst" && ! -e "$BACKUP/$rel" ]]; then
            mkdir -p "$(dirname "$BACKUP/$rel")"
            cp -a "$dst" "$BACKUP/$rel"
        fi
        mkdir -p "$(dirname "$dst")"
        cp -a "$f" "$dst"
    done < <(find "$src" -type f -print0)
}

log "deploying dotfiles"
copy_tree "$HERE/skel"
chmod +x "$TARGET/.config/openbox/autostart"

# --- theme: wallpaper + palette for this environment (sl-theme) ----------
# sl-theme writes only the pieces whose programs are installed (MANIFEST),
# so the same call themes XFCE, KDE, Hyprland or Openbox.
SL_THEME="/usr/share/static-linux/themes/sl-theme"
[[ -f "$SL_THEME" ]] || SL_THEME="$HERE/../../branding/themes/sl-theme"
THEME="$(cat /etc/static-linux/theme 2>/dev/null || echo ambar)"
log "applying theme: $THEME"
if [[ "$MODE" == "skel" ]]; then
    python3 "$SL_THEME" "$THEME" --skel || warn "theme apply failed"
else
    python3 "$SL_THEME" "$THEME" --user "$USER_NAME" || warn "theme apply failed"
fi

# --- optional system config (lightdm) -------------------------------
if [[ $SYSTEM_CONFIG -eq 1 ]]; then
    [[ $EUID -eq 0 ]] || die "--system-config needs root"
    log "installing etc/ config"
    [[ -d "$HERE/etc" ]] && cp -rv "$HERE/etc/." /etc/
fi

# --- ownership -------------------------------------------------------
if [[ "$MODE" == "home" && $EUID -eq 0 ]]; then
    chown -R "$USER_NAME": "$TARGET/.config" 2>/dev/null || true
fi

# --- sanity checks -------------------------------------------------
command -v openbox >/dev/null || warn "openbox not installed yet"
command -v tint2 >/dev/null || warn "tint2 not installed yet"
command -v jgmenu_run >/dev/null || warn "jgmenu not installed yet"
[[ -d /usr/share/icons/Papirus-Dark ]] || warn "Papirus-Dark missing — install papirus-icon-theme"
fc-list : family 2>/dev/null | grep -qi "space grotesk" || warn "font 'Space Grotesk' missing (AUR: otf-space-grotesk)"
fc-list : family 2>/dev/null | grep -qi "jetbrains mono" || warn "font 'JetBrains Mono' missing (pacman: ttf-jetbrains-mono)"

log "done. Backup of replaced files (if any): $BACKUP"
[[ "$MODE" == "home" ]] && log "log out and pick the Openbox session, or run: openbox-session"
exit 0
