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
USER_NAME="${SUDO_USER:-${USER:-root}}"
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
# shared by both Hyprland tiers: the Astal bar (ags/)
copy_tree "$HERE/../hyprland-common/skel"
copy_tree "$HERE/skel"

# --- accent colour layer (fastfetch / GTK / greeter / wallpaper file) ---
ACCENT_SH_INSTALLED="/usr/lib/static-linux/accents/apply.sh"
if [[ -x "$ACCENT_SH_INSTALLED" ]]; then
    ACCENT_SH="$ACCENT_SH_INSTALLED"
else
    ACCENT_SH="$HERE/../../branding/accents/apply.sh"
fi
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
# app.tsx also loads ~/.config/gtk-4.0/gtk.css itself at shell startup, so the
# Astal bar (bar.css) picks up @accent_color live too — no separate step.

# --- wallpaper: hyprpaper needs its own config, not xfconf --------------
WP_DIR_INSTALLED="/usr/share/static-linux/wallpapers"
if [[ -d "$WP_DIR_INSTALLED" ]]; then
    WP_DIR="$WP_DIR_INSTALLED"
else
    WP_DIR="$HERE/../../branding/wallpapers"
fi
WP="$WP_DIR/$ACCENT/void-$ACCENT.png"
if [[ -f "$WP" ]]; then
    HYPR="$TARGET/.config/hypr"
    mkdir -p "$HYPR"
    # hyprpaper >= 0.8: one anonymous `wallpaper {}` block per monitor; an
    # empty monitor is the fallback for all of them
    cat > "$HYPR/hyprpaper.conf" <<WPEOF
wallpaper {
    monitor =
    path = $WP
    fit_mode = cover
}
splash = false
WPEOF
    # lock screen in the same accent
    PALETTE="/usr/lib/static-linux/accents/palette.conf"
    [[ -f "$PALETTE" ]] || PALETTE="$HERE/../../branding/accents/palette.conf"
    ACC_HEX="$(awk -F'|' -v n="$ACCENT" '$1 ~ "^ *"n" *$" {gsub(/ /,"",$2); print $2}' "$PALETTE")"
    ACC_HEX="${ACC_HEX:-C0A0F0}"
    cat > "$HYPR/hyprlock.conf" <<LOCKEOF
# Static Linux — lock screen (written by install.sh for the "$ACCENT" accent)
general {
    hide_cursor = true
}

background {
    path = $WP
    blur_passes = 2
    brightness = 0.7
}

label {
    text = \$TIME
    font_family = Outfit
    font_size = 96
    color = rgba(E6E8EEFF)
    position = 0, 160
    halign = center
    valign = center
}

label {
    text = cmd[update:60000] date '+%A %d %B'
    font_family = Space Grotesk
    font_size = 20
    color = rgba(${ACC_HEX}FF)
    position = 0, 70
    halign = center
    valign = center
}

input-field {
    size = 320, 56
    outline_thickness = 3
    outer_color = rgba(${ACC_HEX}FF)
    inner_color = rgba(12141AE6)
    font_color = rgba(E6E8EEFF)
    font_family = Space Grotesk
    placeholder_text = <i>Contraseña</i>
    fail_text = <i>Contraseña incorrecta</i>
    check_color = rgba(F2B33DFF)
    fail_color = rgba(C2452DFF)
    rounding = 14
    position = 0, -40
    halign = center
    valign = center
}
LOCKEOF
    log "hyprpaper + hyprlock -> $WP"
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
command -v ags >/dev/null || warn "ags (astal CLI) missing — staticlinux-local repo: aylurs-gtk-shell"
[[ -d /usr/share/icons/Papirus-Dark ]] || warn "Papirus-Dark missing — install papirus-icon-theme"
fc-list : family 2>/dev/null | grep -qi "space grotesk" || warn "font 'Space Grotesk' missing (staticlinux-fonts)"
fc-list : family 2>/dev/null | grep -qi "jetbrains mono" || warn "font 'JetBrains Mono' missing (pacman: ttf-jetbrains-mono)"

log "done. Backup of replaced files (if any): $BACKUP"
[[ "$MODE" == "home" ]] && log "log out and pick the Hyprland session (SDDM), or run: start-hyprland"
exit 0
