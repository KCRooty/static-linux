#!/bin/bash
# Static Linux — deploy KDE Plasma 6 (4 GB tier).
#
#   ./install.sh --home            deploy into $HOME
#   ./install.sh --home --user X   deploy into /home/X
#   sudo ./install.sh --skel       deploy into /etc/skel + system bits (ISO / installer)
#
# Idempotent. Existing dotfiles are backed up to <target>/.sl-kde-backup/
# before being overwritten. Nothing here is irreversible.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE=""
TARGET=""
USER_NAME="${SUDO_USER:-${USER:-root}}"

log()  { printf '\033[1;38;5;43m[kde-plasma]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[kde-plasma]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[kde-plasma]\033[0m %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --home) MODE="home" ;;
        --skel) MODE="skel" ;;
        --user) USER_NAME="$2"; shift ;;
        *)      die "unknown option: $1" ;;
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

# --- dotfiles -------------------------------------------------------
BACKUP="$TARGET/.sl-kde-backup/$(date +%Y%m%d-%H%M%S)"
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

# --- system bits (installer / ISO only) -------------------------------
if [[ "$MODE" == "skel" ]]; then
    # SDDM: Breeze theme, Wayland greeter (sl-theme --system sets its
    # wallpaper from the theme)
    install -d /etc/sddm.conf.d
    cat > /etc/sddm.conf.d/10-static-linux.conf <<EOF
[General]
DisplayServer=wayland
GreeterEnvironment=QT_WAYLAND_SHELL_INTEGRATION=layer-shell

[Theme]
Current=breeze
CursorTheme=breeze_cursors
EOF
    log "sddm -> breeze"
fi

# --- ownership ---------------------------------------------------------
if [[ "$MODE" == "home" && $EUID -eq 0 ]]; then
    chown -R "$USER_NAME": "$TARGET/.config" 2>/dev/null || true
fi

command -v plasmashell >/dev/null || warn "plasma not installed yet (packages/lists/kde.list)"
log "done. Backup of replaced files (if any): $BACKUP"
exit 0
