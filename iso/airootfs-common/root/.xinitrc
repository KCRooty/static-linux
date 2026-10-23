#!/bin/sh
# Static Linux — live session X setup: bare Openbox just to host Calamares'
# window, no theming/panel/autostart from entornos/ (this is the installer
# session, not an installed desktop).
xsetroot -solid "#0B0C10"
feh --no-fehbg --bg-fill /usr/share/static-linux/wallpapers/green/void-green.png 2>/dev/null &
openbox &
sleep 1
# preselect sl-detect's recommended environment on the "Entorno" page
env="$(sl-detect --recommend-env 2>/dev/null)"
case "$env" in
    xfce-themed|openbox-minimal|hyprland-astal-lite|hyprland-astal-full)
        sed -i "s/^default: .*/default: $env/" /etc/calamares/modules/entorno/module.conf ;;
esac
# Spanish installer UI by default (the live system itself stays C.UTF-8;
# Qt picks the translation from LANG, no compiled glibc locale needed)
export LANG=es_ES.UTF-8
exec calamares
