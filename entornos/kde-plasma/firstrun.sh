#!/bin/bash
# Static Linux — first Plasma login: theme colours + wallpaper.
#
# Run once per user from ~/.config/autostart/dev.staticforge.kde-firstrun.desktop.
# sl-theme already merged the colours into kdeglobals and wrote the
# StaticLinux scheme; Plasma keeps its wallpaper in a file it rewrites itself,
# so that part goes through Plasma's own tools once plasmashell is up.

set -uo pipefail

STATE="$HOME/.local/state/static-linux/kde-firstrun-done"
[[ -e "$STATE" ]] && exit 0

THEME="$(cat "$HOME/.config/static-linux/theme" 2>/dev/null || cat /etc/static-linux/theme 2>/dev/null || echo ambar)"
WP="/usr/share/static-linux/themes/$THEME/wallpaper.jpg"

# plasmashell has to be up for the wallpaper call
for _ in $(seq 1 30); do
    qdbus6 org.kde.plasmashell /PlasmaShell >/dev/null 2>&1 && break
    sleep 1
done

[[ -f "$WP" ]] && plasma-apply-wallpaperimage "$WP"
[[ -f "$HOME/.local/share/color-schemes/StaticLinux.colors" ]] && plasma-apply-colorscheme StaticLinux

mkdir -p "$(dirname "$STATE")"
touch "$STATE"
