#!/bin/sh
# Static Linux: load XFCE panel plugins inside xfce4-panel instead of one
# wrapper-2.0 process each (~10 MB of GTK per plugin, ~30 MB idle on the
# default panel). The plugin packages ship them as external; the pacman hook
# sl-xfce-panel-internal.hook runs this after every update. Plugins that are
# not installed are skipped. Undo: reinstall the plugin packages and remove
# /usr/share/libalpm/hooks/sl-xfce-panel-internal.hook.
d=/usr/share/xfce4/panel/plugins
for p in whiskermenu systray pulseaudio docklike genmon; do
    [ -f "$d/$p.desktop" ] && sed -i -E 's/^X-XFCE-Internal=(false|FALSE)$/X-XFCE-Internal=true/' "$d/$p.desktop"
done
exit 0
