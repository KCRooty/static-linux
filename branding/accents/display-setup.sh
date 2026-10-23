#!/bin/bash
# Static Linux — HiDPI for the X11 desktops (XFCE, Openbox), at login.
#
# Scale: /etc/static-linux/display-scale (measured by the installer on this
# machine's screen), else measured now with sl-display-scale. XFCE gets it
# once through xsettings — after that the user's own Settings > Appearance
# choice is kept. Openbox has no settings daemon, so Xft.dpi is loaded on
# every login (cheap, and it follows a monitor change).

set -uo pipefail

scale="$(cat /etc/static-linux/display-scale 2>/dev/null || sl-display-scale 2>/dev/null || echo 1)"
case "$scale" in 1.25) dpi=120 ;; 1.5) dpi=144 ;; 2) dpi=192 ;; *) dpi=96; scale=1 ;; esac

if [[ "${XDG_CURRENT_DESKTOP:-}" == *XFCE* ]] && command -v xfconf-query >/dev/null; then
    state="$HOME/.local/state/static-linux/display-setup-done"
    [[ -e "$state" ]] && exit 0
    if [[ "$scale" == 2 ]]; then
        # whole-UI 2x (GTK widgets, icons, panel); fonts stay at 96 dpi on top
        xfconf-query -c xsettings -p /Gdk/WindowScalingFactor -n -t int -s 2 2>/dev/null \
            || xfconf-query -c xsettings -p /Gdk/WindowScalingFactor -s 2
    elif [[ "$scale" != 1 ]]; then
        # fractional: XFCE scales text through the font DPI
        xfconf-query -c xsettings -p /Xft/DPI -n -t int -s "$dpi" 2>/dev/null \
            || xfconf-query -c xsettings -p /Xft/DPI -s "$dpi"
    fi
    mkdir -p "$(dirname "$state")"
    touch "$state"
else
    [[ "$scale" == 1 ]] && exit 0
    printf 'Xft.dpi: %s\nXcursor.size: %s\n' "$dpi" "$(( 24 * dpi / 96 ))" | xrdb -merge
fi
