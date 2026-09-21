# hyprland-astal-full

Tier: **Recommended / RAM ceiling (4 GB)** — docs/PROYECTO.md requirements table.
Wayland, blur + shadows + animations on. Only ever recommended by sl-detect
when `wayland_ok` is true (see `sl-detect/rules/wayland.rules`), so this
config doesn't need to defend against a GPU that can't handle it.

## Stack

| Role | Tool |
|---|---|
| Compositor | Hyprland |
| Shell (bar) | Astal / AGS (`~/.config/ags/`, TypeScript) |
| Wallpaper | hyprpaper |
| Lock / idle | hyprlock / hypridle |
| Launcher | rofi (`$mod+D`) |
| Terminal | kitty (`$mod+Return`) |
| Files | Nautilus |
| Notifications | dunst |
| Screenshot | grim + slurp (`Print`, region select) |

## The Astal shell (`~/.config/ags/`)

`app.ts` is the entry point (`exec-once = ags run ~/.config/ags/app.ts` in
`hyprland.conf`), `widget/Bar.tsx` is a single top bar: workspaces (left),
focused window title (center), clock (right). Styled by `bar.css`, which
reads the **same `@accent_color` / `@sl_bg` named colours** that
`branding/accents/apply.sh` writes to `~/.config/gtk-4.0/gtk.css` for every
other themed app — `app.ts` loads that file before `bar.css`, so the bar
follows the active accent automatically, no extra plumbing.

**Known simplification — verify before shipping**: this was written against
the AGS quick-start guide (`aylur.github.io/ags`) without a live Hyprland +
Astal runtime to test against (no hardware for this session — see
docs/PROYECTO.md's hardware status). Two things to check on real hardware:

- `Bar.tsx` reads workspace/window state with `createPoll` (a 500 ms
  interval) instead of Astal's native Hyprland event signals
  (`AstalHyprland`'s `workspace-added`/`focused-client` signals). Polling is
  simpler to get right blind; swapping to real event bindings would make it
  instant instead of ≤500 ms stale, at the same idle-CPU cost.
  - `app.get_monitors()` in `app.ts` for the multi-monitor loop — plausible
  per Astal's `App` API shape, not confirmed against a running instance.
- No notification popup widget in the shell — dunst handles that
  separately, same as the other two environments. A native `AstalNotifd`
  popup is a reasonable follow-up once this is confirmed working.

## Deploy

```bash
./install.sh --home                 # test on a live machine
sudo ./install.sh --skel            # ISO build (/etc/skel)
sudo ./install.sh --skel --system-config   # + /etc (SDDM etc.)
```
