#!/bin/bash
# Static Linux — deploy the Themed XFCE environment.
#
#   ./install.sh --home            deploy into $HOME (test on a live machine)
#   ./install.sh --home --user X   deploy into /home/X
#   sudo ./install.sh --skel       deploy into /etc/skel (ISO build)
#   sudo ./install.sh --skel --system-config   also drop etc/ files into /
#
# Idempotent. Existing dotfiles are backed up to <target>/.sl-xfce-backup/
# before being overwritten. Nothing here is irreversible.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$(cd "$HERE/../shared" && pwd)"
MODE=""
TARGET=""
USER_NAME="${SUDO_USER:-$USER}"
SYSTEM_CONFIG=0

log()  { printf '\033[1;38;5;43m[xfce-themed]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[xfce-themed]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[xfce-themed]\033[0m %s\n' "$*" >&2; exit 1; }

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
BACKUP="$TARGET/.sl-xfce-backup/$(date +%Y%m%d-%H%M%S)"
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

# --- compose the Static-Void xfwm4 theme ------------------------------
THEME_DST="$TARGET/.local/share/xfwm4/themes/Static-Void"
DEFAULT_SRC=""
for cand in /usr/share/themes/Default/xfwm4 /usr/share/themes/Adwaita/xfwm4; do
    [[ -d "$cand" ]] && { DEFAULT_SRC="$cand"; break; }
done
if [[ -n "$DEFAULT_SRC" ]]; then
    log "building xfwm4 theme from $DEFAULT_SRC"
    mkdir -p "$THEME_DST"
    cp -a "$DEFAULT_SRC/." "$THEME_DST/"
    cp -f "$SHARED/themes/Static-Void-xfwm4/themerc" "$THEME_DST/themerc"
else
    warn "no base xfwm4 theme found (install xfwm4); window decorations fall back to Default"
    # keep xfwm4.xml working regardless
    sed -i 's/value="Static-Void"/value="Default"/' \
        "$TARGET/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml" || true
fi

# --- wallpaper --------------------------------------------------------
WP_SRC="$SHARED/../../branding/wallpapers/dark/void-dark.png"
WP_SRC="$(readlink -f "$WP_SRC" 2>/dev/null || echo "$WP_SRC")"
if [[ -f "$WP_SRC" ]]; then
    if [[ $EUID -eq 0 ]]; then
        WP_DST="/usr/share/backgrounds/static-linux/void-dark.png"
        mkdir -p "$(dirname "$WP_DST")"
        install -m 0644 "$WP_SRC" "$WP_DST"
    else
        WP_DST="$TARGET/.local/share/backgrounds/static-linux/void-dark.png"
        mkdir -p "$(dirname "$WP_DST")"
        install -m 0644 "$WP_SRC" "$WP_DST"
    fi
    log "wallpaper -> $WP_DST"
    # point the xfconf key at the real path (skel XML uses the system path)
    sed -i "s#/usr/share/backgrounds/static-linux/void-dark.png#$WP_DST#" \
        "$TARGET/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
    # apply live if a session is running as this user
    if [[ "$MODE" == "home" ]] && pgrep -u "$USER_NAME" xfdesktop >/dev/null 2>&1; then
        run_as() { [[ $EUID -eq 0 ]] && sudo -u "$USER_NAME" "$@" || "$@"; }
        UID_N="$(id -u "$USER_NAME")"
        for prop in $(DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$UID_N/bus" \
                      run_as xfconf-query -c xfce4-desktop -l 2>/dev/null | grep 'last-image$'); do
            DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$UID_N/bus" \
                run_as xfconf-query -c xfce4-desktop -p "$prop" -s "$WP_DST" 2>/dev/null || true
        done
    fi
else
    warn "wallpaper not found ($WP_SRC) - run branding/wallpapers/gen-wallpaper.py"
fi

# --- optional system config (lightdm) -------------------------------
if [[ $SYSTEM_CONFIG -eq 1 ]]; then
    [[ $EUID -eq 0 ]] || die "--system-config needs root"
    log "installing etc/ config"
    cp -rv "$HERE/etc/." /etc/
fi

# --- ownership -------------------------------------------------------
if [[ "$MODE" == "home" && $EUID -eq 0 ]]; then
    chown -R "$USER_NAME": "$TARGET/.config" "$TARGET/.local" 2>/dev/null || true
fi

# --- sanity checks -------------------------------------------------
command -v xfce4-session >/dev/null || warn "xfce4 not installed yet"
[[ -d /usr/share/themes/Adwaita-dark || -d /usr/share/themes/Adwaita ]] || \
    warn "Adwaita-dark missing — install gnome-themes-extra"
[[ -d /usr/share/icons/Papirus-Dark ]] || warn "Papirus-Dark missing — install papirus-icon-theme"
fc-list : family 2>/dev/null | grep -qi "space grotesk" || warn "font 'Space Grotesk' missing (AUR: otf-space-grotesk)"
fc-list : family 2>/dev/null | grep -qi "jetbrains mono" || warn "font 'JetBrains Mono' missing (pacman: ttf-jetbrains-mono)"

log "done. Backup of replaced files (if any): $BACKUP"
[[ "$MODE" == "home" ]] && log "log out and pick the Xfce session, or run: startxfce4"
exit 0
