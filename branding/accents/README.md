# Accent colours

One knob recolours the whole Static Linux look — fastfetch, GTK 3/4, the
xfwm4 window border, xfce4-terminal, the LightDM greeter and the wallpaper.
The installer offers the list; **purple is the default**.

```
purple    Morado                    ← default
yellow    Amarillo
red       Rojo
green     Verde                     (the original Signal Green)
blue      Azul
pink      Rosa
grey      Gris
mono      Monocromo                 (no chroma)
hc-dark   Alto contraste oscuro     (#000 ground, #FFF text)
hc-light  Alto contraste claro      (#FFF ground, #000 text)
```

Each accent: a **dominant** colour, a **dim** variant (rules, inactive
borders), a small **detail** colour (purple → a touch of yellow) and the
text / background pair. All defined in [`palette.conf`](palette.conf).

## Use

```bash
sl-ctl accent --list          # the table above
sl-ctl accent                 # current accent
sudo sl-ctl accent blue       # switch (reversible — backs up first)

# or directly:
branding/accents/apply.sh --list
sudo branding/accents/apply.sh green
sudo branding/accents/apply.sh green --user core
sudo branding/accents/apply.sh green --skel      # ISO build → /etc/skel + /etc
```

`apply.sh` backs every file up to `/var/backups/static-linux/accent/<ts>/`
before touching it and records the choice in `/etc/static-linux/accent`.
Switching accent again fully replaces the previous one.

## How it works

```
palette.conf ── row ──▶ apply.sh ──renders──▶ templates/*.in ──▶ deployed files
                                                                  ├─ /etc/fastfetch/config.jsonc
                                                                  ├─ ~/.config/gtk-3.0|4.0/gtk.css
                                                                  ├─ ~/.local/share/xfwm4/themes/Static-Void/themerc
                                                                  ├─ ~/.config/xfce4/terminal/terminalrc  (colour block)
                                                                  ├─ /etc/lightdm/lightdm-gtk-greeter.conf.d/50-static-linux.conf
                                                                  └─ wallpaper (branding/wallpapers/<accent>/void-<accent>.png)
```

`gen.sh` pre-renders `themes/<accent>/` and all wallpapers so the **offline
ISO** ships them without rendering at install time:

```bash
branding/accents/gen.sh            # commit the results
```

## Installer

`installer/calamares/modules/accent/` — a Python job that reads
`globalStorage["slAccent"]` (set by the accent selection page) and runs
`apply.sh --skel` + `--user <login>` inside the target. The swatch-grid
selection page itself is a Phase 6 QML deliverable; until then the ISO can
pin a default via an automated/OEM config.

## Adding an accent

Add a row to `palette.conf`, run `gen.sh`, done — every component picks it up.
