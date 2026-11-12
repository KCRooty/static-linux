#!/bin/sh
# Static Linux — ISO build step, run once inside the live root filesystem by
# etc/pacman.d/hooks/50-sl-live-setup.hook while mkarchiso installs packages.
# Spanish locale for the live desktop and the installer, and the default
# theme rendered into /root so the live session starts already themed.
set -u
grep -q '^es_ES.UTF-8' /etc/locale.gen 2>/dev/null || echo 'es_ES.UTF-8 UTF-8' >> /etc/locale.gen
locale-gen >/dev/null
[ -x /usr/share/static-linux/themes/sl-theme ] && \
    HOME=/root python3 /usr/share/static-linux/themes/sl-theme ambar --user root >/dev/null
# the welcome app is for installed systems
rm -f /root/.config/autostart/dev.staticforge.welcome.desktop
exit 0
