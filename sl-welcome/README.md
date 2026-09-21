# sl-welcome

First-boot app for Static Linux. GTK4 + libadwaita (Python/PyGObject).

## Why libadwaita

`branding/accents/apply.sh` already writes libadwaita's own semantic colours
(`accent_color`, `accent_bg_color`, `theme_selected_bg_color`, ...) into
`~/.config/gtk-4.0/gtk.css` for every accent in the palette. A libadwaita app
picks those up for free — no per-accent code in sl-welcome itself, one
theming path for the whole system (fastfetch/GTK/xfwm4/terminal/greeter/
wallpaper/sl-welcome).

## Pages

- **General** — branded header + a live `sl-detect --json` readout (CPU,
  RAM, GPU, driver, Wayland, firmware, storage, arch) + the recommended
  env/fs/kernel for this machine. Read-only, no privileges needed.
- **Apariencia** — the 10-accent grid from `branding/accents/palette.conf`.
  Runs `accents/apply.sh <name>` as the logged-in user — no root needed for
  a per-user apply.
- **Privacidad** — the 3 privacy profiles. "Aplicar" goes through `pkexec`
  and `data/apply-profile` (see below) since it touches `/etc`. Every
  profile backs itself up (`privacidad/scripts/lib.sh`), so this is never
  irreversible.
- **Catálogo** — curated extra apps from `catalog/*.yaml`, beyond what the
  chosen environment/flavor already installs. Checkable items install via
  `pkexec pacman -S --needed`. AUR-tagged apps are listed but not checkable
  — pacman can't build AUR packages as root; the row tells you the
  `paru -S <pkg>` command instead.

## Why a dedicated pkexec wrapper for the privacy page

`data/apply-profile` is a tiny, argument-validating script installed to
`/usr/lib/static-linux/sl-welcome/apply-profile`. `data/dev.staticforge.welcome.policy`
points polkit's `org.freedesktop.policykit.exec.path` at that exact file —
not at `/usr/bin/bash` — so sl-welcome's "aplicar perfil de privacidad"
policy only ever fires for this one action, not for every `pkexec bash`
call on the system. The catalog install goes straight through
`pkexec pacman`, which is precise enough on its own (pacman is the actual
action being authorized).

## Running from a checkout (no install)

```bash
python3 -m venv .venv && source .venv/bin/activate  # optional
python3 src/main.py
```

Needs `python-gobject`, `gtk4` and `libadwaita` on the system (they're
system packages, not pip-installable — this is why sl-welcome isn't
built/tested inside a Python venv on CI, only unit-testable pieces like
`catalog_loader.py` and `paths.py` are).

**Not testable in this dev environment**: no display server, and the `gi`
bindings here don't have a working GTK4/libadwaita backend. Per
CONTRIBUTING.md, sl-welcome needs a real run on the iMedia S2883 or a VM
before merging — same as any other GTK4 app in this repo.

## Layout

```
sl-welcome/
├── sl-welcome              launcher on PATH (what sl-ctl.py's `welcome`
│                            subcommand execs via shutil.which)
├── src/
│   ├── main.py              Adw.Application entry point
│   ├── window.py             Adw.ApplicationWindow + Adw.ViewSwitcher
│   ├── paths.py               installed-path / repo-relative resolution
│   ├── system_info.py          wraps `sl-detect --json`
│   ├── catalog_loader.py        parses catalog/*.yaml
│   ├── privileged.py            pkexec wrappers (privacy profile, pacman)
│   ├── style.css                  Outfit/Space Grotesk/JetBrains Mono hooks
│   └── pages/{overview,appearance,privacy,catalog}.py
├── catalog/*.yaml            the extra-apps catalog (8 categories, 56 apps)
└── data/
    ├── dev.staticforge.welcome.desktop   app-menu launcher
    ├── dev.staticforge.welcome.policy    polkit actions
    └── apply-profile                     pkexec target for Privacidad
```

Autostart (`sl-welcome --autostart`, only shown once per user via
`~/.local/state/static-linux/welcome-shown`) is wired per environment, since
each session type starts things differently:

- `xfce-themed`: `~/.config/autostart/dev.staticforge.welcome.desktop`
  (XDG autostart, read by xfce4-session).
- `openbox-minimal`: a line in `~/.config/openbox/autostart` (plain
  `openbox-session` doesn't read XDG autostart `.desktop` files).
- `hyprland-astal-full` / `hyprland-astal-lite`: `exec-once =` line in
  `hyprland.conf`.

## Adding a catalog entry

```yaml
# catalog/<category>.yaml
category: "Nombre visible"
apps:
  - id: unique-id
    name: Nombre mostrado
    desc: Una frase, en español.
    pkg: nombre-del-paquete
    aur: true   # solo si viene del AUR (omitir si no)
```
