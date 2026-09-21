# Static Linux — live session autostart.
# Autologin (see etc/systemd/system/getty@tty1.service.d/autologin.conf)
# drops straight into a root shell on tty1; this brings up the graphical
# installer automatically without needing a display manager.
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec startx
fi
