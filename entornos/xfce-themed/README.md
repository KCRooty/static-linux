# Themed XFCE

Static Linux's compatibility environment. Tier: **Minimum functional (1 GB)**,
Xorg. `sl-detect` selects it automatically when Wayland is unavailable
(Bay Trail, Kepler, pre-GCN) or RAM is between 1–2 GB. Validated on the
Packard Bell iMedia S2883 (J1900).

Same Static Linux palette and fonts as the Hyprland environments, predictable
XFCE behaviour underneath.

## What's in here

```
skel/.config/
  xfce4/xfconf/xfce-perchannel-xml/
    xsettings.xml                Adwaita-dark + Papirus-Dark, Space Grotesk / JetBrains Mono
    xfwm4.xml                    Static-Void WM theme, compositor on, Super+arrows tiling
    xfce4-panel.xml              single top panel (Void 96%): Whisker · tasklist · tray · audio · power · clock
    xfce4-desktop.xml            Void background, home/trash icons
    xfce4-keyboard-shortcuts.xml Super+Return term, Super+E files, Super+B Brave Origin, PrtSc screenshot
  gtk-3.0/gtk.css               Signal Green accent overlay (accents only, not a full theme)
  gtk-4.0/gtk.css               same for the few GTK4 apps
  xfce4/terminal/terminalrc     JetBrains Mono, Void bg, green cursor

etc/lightdm/                    greeter: Void background, Signal Green, brand clock

../shared/themes/Static-Void-xfwm4/themerc   xfwm4 palette overlay
```

## Deploy

```bash
# test on this machine (live)
./install.sh --home

# during ISO build
sudo ./install.sh --skel --system-config
```

`install.sh` is idempotent and backs up any file it replaces to
`<target>/.sl-xfce-backup/<timestamp>/`.

## Packages

See [`packages/lists/xfce.list`](../../packages/lists/xfce.list). Key deps:
`xfce4`, `xfce4-goodies`, `lightdm` + `lightdm-gtk-greeter`, `gnome-themes-extra`
(Adwaita-dark), `papirus-icon-theme`, `network-manager-applet`, `xfce4-terminal`.

## Still to do (branding pass)

- Real pixmap-based `Static-Void` xfwm4 theme (currently composed from the
  system Default theme + our `themerc` at install time).
- `void-dark.png` wallpaper and the SF monogram assets referenced by the
  greeter (`branding/`).
- `ttf-outfit` / `otf-space-grotesk` AUR packages so the brand fonts ship.
