#!/bin/bash
# Static Linux — first Plasma login: wallpaper + accent colour.
#
# Run once per user from ~/.config/autostart/dev.staticforge.kde-firstrun.desktop.
# Plasma keeps its wallpaper and colours in files it rewrites itself, so they
# are applied through Plasma's own tools instead of shipping those files.

set -uo pipefail

STATE="$HOME/.local/state/static-linux/kde-firstrun-done"
[[ -e "$STATE" ]] && exit 0

ACCENT="$(cat /etc/static-linux/accent 2>/dev/null || echo purple)"
PALETTE=/usr/lib/static-linux/accents/palette.conf
HEX="$(awk -F'|' -v n="$ACCENT" '$1 ~ "^ *"n" *$" {gsub(/ /,"",$2); print $2}' "$PALETTE" 2>/dev/null)"
WP_PREFIX="$(case "$(cat /etc/static-linux/style 2>/dev/null)" in cyberpunk) echo neon ;; liquid) echo liquid ;; *) echo void ;; esac)"
WP="/usr/share/backgrounds/static-linux/$WP_PREFIX-$ACCENT.png"
[[ -f "$WP" ]] || WP="/usr/share/static-linux/wallpapers/$ACCENT/$WP_PREFIX-$ACCENT.png"

# plasmashell has to be up for the wallpaper call
for _ in $(seq 1 30); do
    qdbus6 org.kde.plasmashell /PlasmaShell >/dev/null 2>&1 && break
    sleep 1
done

[[ -f "$WP" ]] && plasma-apply-wallpaperimage "$WP"
if [[ -n "$HEX" ]]; then
    plasma-apply-colorscheme --accent-color "#$HEX" BreezeDark
else
    plasma-apply-colorscheme BreezeDark
fi

mkdir -p "$(dirname "$STATE")"
touch "$STATE"
