# hyprland-astal-lite

Tier: **Standard (2 GB)** — docs/PROYECTO.md requirements table. Same Astal shell
as `hyprland-astal-full` (`~/.config/ags/` is a straight copy — Astal itself
isn't the RAM-heavy part), `hyprland.conf` just strips blur, shadows and
most animation, and swaps Nautilus for Thunar / drops the dock.

Only ever recommended by sl-detect for a Wayland-capable GPU with
2-4 GB RAM (`hyprland-astal-full` takes over at >=4 GB, `xfce-themed` below
2 GB or when Wayland isn't viable — see `rules/entorno.rules`).

See `hyprland-astal-full/README.md` for the Astal shell's architecture and
its known simplifications (`createPoll` instead of native Hyprland event
signals, `app.get_monitors()` unconfirmed against a live runtime) — they
apply here unchanged since the shell files are identical.

## What's different from `hyprland-astal-full`

| | full | lite |
|---|---|---|
| Blur | on | off |
| Shadows | on | off |
| Animations | windows/border/fade/workspaces | fade only |
| Border width | 2px, gradient | 1px, flat |
| Files | Nautilus | Thunar |
| Dock | nwg-dock-hyprland | none |
| Brightness keys | bound | not bound (desktop-oriented package list) |

## Deploy

```bash
./install.sh --home                 # test on a live machine
sudo ./install.sh --skel            # ISO build (/etc/skel)
sudo ./install.sh --skel --system-config   # + /etc (SDDM etc.)
```
