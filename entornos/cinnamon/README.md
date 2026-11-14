# Cinnamon

`install.sh` copies `skel/` into a home (or `/etc/skel`) and applies the theme.

## Idle RAM (rule: 650 MB)

Stock Cinnamon idles at ~780 MB (VM with virgl, Mejorado profile). What
`skel/` turns off, and how to get each back:

| What | ~MB | Back |
|---|---|---|
| Evolution alarm notifier (and the evolution-data-server it wakes) | 65 | delete `~/.config/autostart/org.gnome.Evolution-alarm-notify.desktop` |
| Desktop icons (`nemo-desktop`) | 25 | System Settings → Desktop, or `gsettings set org.nemo.desktop show-desktop-icons true` |
| `cinnamon-launcher` (crash fallback) | 37 | delete `~/.local/share/applications/cinnamon.desktop` |
| `cinnamon-killer-daemon` (Ctrl+Alt+Esc) | 29 | delete `~/.local/share/applications/cinnamon-killer-daemon.desktop` |
| csd wacom, color, smartcard, housekeeping, clipboard | 50 | delete the matching `~/.config/autostart/cinnamon-settings-daemon-*.desktop` |

Result: ~630 MB. The desktop-icons default comes from
`branding/cinnamon/90_static-linux-cinnamon.gschema.override` (staticlinux-base).
