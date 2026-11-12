#!/bin/sh
# Static Linux — live session: the XFCE desktop in the default theme (Ámbar,
# rendered into /root when the ISO was built), with the installer opening on
# its own. Closing it leaves a working desktop; "Instalar Static Linux" in the
# menu brings it back.
# native mode of whatever screen this is (VMs and some GPUs start smaller)
xrandr --auto 2>/dev/null
# HiDPI: Xft.dpi for the desktop, the factor for the installer
/usr/lib/static-linux/accents/display-setup.sh 2>/dev/null
scale="$(sl-display-scale 2>/dev/null || echo 1)"
echo "$scale" > /run/sl-display-scale
exec startxfce4
