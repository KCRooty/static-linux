#!/bin/bash
# Static Linux — deploy Hyprland + Astal (lite tier, 2-4 GB RAM + Wayland GPU).
#
#   ./install.sh --home            deploy into $HOME (test on a live machine)
#   ./install.sh --home --user X   deploy into /home/X
#   sudo ./install.sh --skel       deploy into /etc/skel (ISO build)
#   sudo ./install.sh --skel --system-config   also drop etc/ files into /
#
# Idempotent. Existing dotfiles are backed up to <target>/.sl-hypr-backup/
# before being overwritten. Nothing here is irreversible.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE=""
TARGET=""
USER_NAME="${SUDO_USER:-$USER}"
SYSTEM_CONFIG=0

log()  { printf '\033[1;38;5;43m[hyprland-astal-lite]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[hyprland-astal-lite]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[hyprland-astal-lite]\033[0m %s\n' "$*" >&2; exit 1; }

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
BACKUP="$TARGET/.sl-hypr-backup/$(date +%Y%m%d-%H%M%S)"
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
chmod +x "$TARGET/.config/ags/app.ts"

# --- accent colour layer (fastfetch / GTK / greeter / wallpaper file) ---
ACCENT_SH="$HERE/../../branding/accents/apply.sh"
ACCENT="purple"
if [[ -x "$ACCENT_SH" ]]; then
    ACCENT="$(cat /etc/static-linux/accent 2>/dev/null || echo purple)"
    log "applying accent: $ACCENT"
    if [[ "$MODE" == "skel" ]]; then
        "$ACCENT_SH" "$ACCENT" --skel || warn "accent apply failed"
    else
        "$ACCENT_SH" "$ACCENT" --user "$USER_NAME" || warn "accent apply failed"
    fi
else
    warn "branding/accents/apply.sh not found — skipping colour layer"
fi
# app.ts also loads ~/.config/gtk-4.0/gtk.css itself at shell startup, so the
# Astal bar (bar.css) picks up @accent_color live too — no separate step.

# --- wallpaper: hyprpaper needs its own config, not xfconf --------------
WP="$HERE/../../branding/wallpapers/$ACCENT/void-$ACCENT.png"
if [[ -f "$WP" ]]; then
    HYPRPAPER_CFG="$TARGET/.config/hypr/hyprpaper.conf"
    mkdir -p "$(dirname "$HYPRPAPER_CFG")"
    cat > "$HYPRPAPER_CFG" <<EOF
preload = $WP
wallpaper = ,$WP
splash = false
EOF
    log "hyprpaper wallpaper -> $WP"
else
    warn "no wallpaper found for accent '$ACCENT' at $WP"
fi

# --- optional system config (sddm) -----------------------------------
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
command -v Hyprland >/dev/null || warn "hyprland not installed yet"
command -v ags >/dev/null || warn "ags (astal CLI) not installed yet — AUR: aylurs-gtk-shell"
[[ -d /usr/share/icons/Papirus-Dark ]] || warn "Papirus-Dark missing — install papirus-icon-theme"
fc-list : family 2>/dev/null | grep -qi "space grotesk" || warn "font 'Space Grotesk' missing (AUR: otf-space-grotesk)"
fc-list : family 2>/dev/null | grep -qi "jetbrains mono" || warn "font 'JetBrains Mono' missing (pacman: ttf-jetbrains-mono)"

log "done. Backup of replaced files (if any): $BACKUP"
[[ "$MODE" == "home" ]] && log "log out and pick the Hyprland session (SDDM), or run: Hyprland"
exit 0
