# staticlinux-base

The distribution's base meta-package — everything `installer/calamares/modules/*`,
`sl-ctl` and `sl-welcome` assume lives at `/usr/lib/static-linux/...` comes
from here. See the `PKGBUILD`'s own header comment for the full layout; the
short version:

| Where | What |
|---|---|
| `/usr/lib/static-linux/` | sl-detect, sl-ctl, sl-welcome, accents, privacidad, packages/lists/*.list, entornos/*/{install.sh,skel/} |
| `/usr/share/static-linux/` | fastfetch logos, per-accent wallpapers + the generator |
| `/usr/bin/{sl-detect,sl-ctl,sl-welcome}` | symlinks into the above |
| `/etc/os-release`, `/etc/lsb-release` | identity files (see below) |
| `/etc/fastfetch/config.jsonc`, `/etc/static-linux/accent` | defaults — `sl-welcome`/`sl-ctl accent` overwrite these later |

## Build

```bash
cd packages/staticlinux-base
makepkg -si
```

No `source=()` to fetch — this packages the monorepo in place. Run it from
inside a checkout.

## `/etc/os-release` and `filesystem`

On a plain Arch box `/etc/os-release` is a symlink to `/usr/lib/os-release`,
owned by the `filesystem` package. This package never touches
`/usr/lib/os-release` — it ships `/etc/os-release` and `/etc/lsb-release` as
plain files at those exact paths instead, replacing the symlink. Nothing
else owns that literal path, so there's no `conflicts=()`/`provides=()`
fight with `filesystem`, and since most `/etc/os-release` readers check
`/etc/` before falling back to `/usr/lib/`, this is enough to make
fastfetch, `neofetch`-alikes, GNOME/KDE "About" panels, `lsb_release`, and
`ID_LIKE=arch`-aware tooling all report Static Linux correctly. Both files
are in `backup=()`, so a future package upgrade drops a `.pacnew` instead of
silently overwriting a hand edit.

## Future contents

- `/etc/issue`, `/etc/motd` with the SF banner
- pacman.conf drop-ins (Static Forge repo, once it exists)
- `/etc/os-release` `LOGO=static-linux` → ship `static-linux.svg` in
  `/usr/share/pixmaps/` and the hicolor icon dirs (no logo asset exists yet
  — Core does the graphic design himself)
- default `makepkg.conf` tuning, `zram-generator` config, sysctl drop-ins
- splitting `sl-welcome` into its own package once the project has an actual
  repo to publish multiple packages from — for now, one package is simpler
