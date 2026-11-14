# openbox-minimal

Tier: **512 MB absolute minimum** (docs/PROYECTO.md requirements table). Xorg, no
compositor by default, no XDG-autostart daemon (`lxsession`) — one less
resident process. `~/.config/openbox/autostart` starts everything explicitly.

## Stack

| Role | Tool |
|---|---|
| WM | Openbox |
| Panel | tint2 (taskbar + systray + clock — no launcher applet) |
| Menu | jgmenu (auto-discovers `.desktop` files, no menu.xml to maintain) |
| Files | PCManFM |
| Terminal | LXTerminal |
| Wallpaper | feh (`~/.fehbg`) |
| Notifications | dunst |
| Compositor | picom — shipped, **not autostarted** (`>600 MB idle RAM = design bug`) |

Right-click or middle-click the desktop, or `Super+D`, opens jgmenu.
`Super+Return` opens a terminal, `Super+E` opens the file manager.

## Theming

`install.sh` calls `branding/accents/apply.sh` for fastfetch, GTK 3/4 and the
LightDM greeter — same as `xfce-themed`. Two things it does **not** cover
here, both noted so they don't get mistaken for bugs:

- **Wallpaper**: feh doesn't read xfconf, so `install.sh` writes `~/.fehbg`
  (feh's own persistence convention — sourced from `autostart`) instead of
  going through `apply.sh`'s xfdesktop step. (Not nitrogen — dropped from
  the official Arch repos, unmaintained upstream.)
- **Window border**: Openbox's `rc.xml` theme isn't accent-reactive yet — it
  ships with a fixed dark theme. Making the border color follow the accent
  needs a proper Openbox theme (an `openbox-3/` theme directory with
  per-accent variants), which doesn't exist yet. Tracked as follow-up work,
  same spirit as `branding/accents/templates/xfwm4-themerc.in` for XFCE.

## Deploy

```bash
./install.sh --home                 # test on a live machine
sudo ./install.sh --skel            # ISO build (/etc/skel)
sudo ./install.sh --skel --system-config   # + /etc (LightDM etc.)
```
