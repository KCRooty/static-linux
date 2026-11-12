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

# --- accent: GTK overlay, fastfetch, wallpaper file (the shared layer) ---
ACCENT_SH="/usr/lib/static-linux/accents/apply.sh"
[[ -x "$ACCENT_SH" ]] || ACCENT_SH="$HERE/../../branding/accents/apply.sh"
ACCENT="$(cat /etc/static-linux/accent 2>/dev/null || echo purple)"
if [[ -x "$ACCENT_SH" ]]; then
    log "applying accent: $ACCENT"
    if [[ "$MODE" == "skel" ]]; then
        "$ACCENT_SH" "$ACCENT" --skel || warn "accent apply failed"
    else
        "$ACCENT_SH" "$ACCENT" --user "$USER_NAME" || warn "accent apply failed"
    fi
fi

# Plasma's own accent: kdeglobals AccentColor (r,g,b). firstrun.sh applies
# it again through plasma-apply-colorscheme on the first login.
PALETTE="/usr/lib/static-linux/accents/palette.conf"
[[ -f "$PALETTE" ]] || PALETTE="$HERE/../../branding/accents/palette.conf"
HEX="$(awk -F'|' -v n="$ACCENT" '$1 ~ "^ *"n" *$" {gsub(/ /,"",$2); print $2}' "$PALETTE")"
if [[ -n "$HEX" ]]; then
    RGB="$((16#${HEX:0:2})),$((16#${HEX:2:2})),$((16#${HEX:4:2}))"
    sed -i "/^AccentColor=/d; s/^\[General\]$/[General]\nAccentColor=$RGB/" "$TARGET/.config/kdeglobals"
    log "Plasma accent -> #$HEX"
fi

# --- system bits (installer / ISO only) -------------------------------
if [[ "$MODE" == "skel" ]]; then
    # SDDM: Breeze theme on the accent wallpaper, Wayland greeter
    WP_PREFIX="$(case "$(cat /etc/static-linux/style 2>/dev/null)" in cyberpunk) echo neon ;; liquid) echo liquid ;; *) echo void ;; esac)"
    WP="/usr/share/backgrounds/static-linux/$WP_PREFIX-$ACCENT.png"
    install -d /etc/sddm.conf.d
    cat > /etc/sddm.conf.d/10-static-linux.conf <<EOF
[General]
DisplayServer=wayland
GreeterEnvironment=QT_WAYLAND_SHELL_INTEGRATION=layer-shell

[Theme]
Current=breeze
CursorTheme=breeze_cursors
EOF
    if [[ -d /usr/share/sddm/themes/breeze && -f "$WP" ]]; then
        printf '[General]\nbackground=%s\ntype=image\n' "$WP" \
            > /usr/share/sddm/themes/breeze/theme.conf.user
    fi
    log "sddm -> breeze, background $WP"
fi

# --- ownership ---------------------------------------------------------
if [[ "$MODE" == "home" && $EUID -eq 0 ]]; then
    chown -R "$USER_NAME": "$TARGET/.config" 2>/dev/null || true
fi

command -v plasmashell >/dev/null || warn "plasma not installed yet (packages/lists/kde.list)"
log "done. Backup of replaced files (if any): $BACKUP"
exit 0
