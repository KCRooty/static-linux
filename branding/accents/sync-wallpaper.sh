#!/bin/bash
# Static Linux — put the Static Linux wallpaper on every XFCE monitor.
#
# The skel xfce4-desktop.xml can only name `monitor0`, but xfdesktop keys its
# backdrops by output name (monitorDP-2, monitorVirtual-1, ...), so a fresh
# user got the stock XFCE wallpaper. Runs at every login from
# ~/.config/autostart/dev.staticforge.wallpaper.desktop: for each connected
# output and workspace, it sets the image only when none is set or the one set
# is a stock XFCE background — a wallpaper the user picked is never touched.
# A monitor plugged in later gets the wallpaper on the next login.

set -uo pipefail

ACCENT="$(cat /etc/static-linux/accent 2>/dev/null || echo purple)"
WP="$(xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/last-image 2>/dev/null)"
for cand in "$WP" \
            "$HOME/.local/share/backgrounds/static-linux/void-$ACCENT.png" \
            "/usr/share/backgrounds/static-linux/void-$ACCENT.png" \
            "/usr/share/backgrounds/static-linux/void-purple.png"; do
  [[ -n "$cand" && -f "$cand" ]] && { WP="$cand"; break; }
done
[[ -f "$WP" ]] || exit 0

# xrandr is not always there; xfdesktop's own keys are the fallback
OUTPUTS="$(xrandr --listmonitors 2>/dev/null | awk 'NR>1 {print $NF}')"
[[ -n "$OUTPUTS" ]] || OUTPUTS="$(xfconf-query -c xfce4-desktop -l 2>/dev/null \
  | sed -nE 's#^/backdrop/screen0/monitor([^/]+)/.*#\1#p' | sort -u)"
WS="$(xfconf-query -c xfwm4 -p /general/workspace_count 2>/dev/null || echo 4)"

set_if_stock() {  # <property>
  local cur
  cur="$(xfconf-query -c xfce4-desktop -p "$1" 2>/dev/null)"
  [[ -z "$cur" || "$cur" == /usr/share/backgrounds/xfce/* ]] || return 0
  xfconf-query -c xfce4-desktop -p "$1" -n -t string -s "$WP" 2>/dev/null \
    || xfconf-query -c xfce4-desktop -p "$1" -s "$WP"
  local style="${1%/last-image}/image-style"
  xfconf-query -c xfce4-desktop -p "$style" -n -t int -s 5 2>/dev/null \
    || xfconf-query -c xfce4-desktop -p "$style" -s 5
}

for out in $OUTPUTS; do
  for ((i = 0; i < WS; i++)); do
    set_if_stock "/backdrop/screen0/monitor$out/workspace$i/last-image"
  done
done
exit 0
