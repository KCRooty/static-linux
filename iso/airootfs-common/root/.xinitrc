#!/bin/sh
# Static Linux — live session X setup: bare Openbox just to host Calamares'
# window, no theming/panel/autostart from entornos/ (this is the installer
# session, not an installed desktop).
xsetroot -solid "#0B0C10" &
openbox &
sleep 1
exec calamares
