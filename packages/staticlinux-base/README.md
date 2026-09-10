# staticlinux-base

The distribution's base meta-package. Owns the files that make an Arch install
identify and behave as **Static Linux**.

| File | Target | Purpose |
|---|---|---|
| `os-release` | `/usr/lib/os-release` (and `/etc/os-release`) | `NAME`/`PRETTY_NAME` = "Static Linux", `ID=static-linux`, `ID_LIKE=arch`, `ANSI_COLOR` = Signal Green. Makes fastfetch, GNOME/KDE about screens, `/etc/issue` generators etc. say Static Linux. |
| `lsb-release` | `/etc/lsb-release` | `DISTRIB_ID=StaticLinux` for `lsb_release` consumers. |

On a plain Arch box `/etc/os-release` is a symlink to `/usr/lib/os-release`
(owned by the `filesystem` package). The eventual `staticlinux-base` PKGBUILD
must either `provides`/`conflicts` a replacement or install to
`/usr/lib/os-release` with an overwrite entry. For now (Phase 2) the files are
copied into place by hand / by the ISO build.

## Future contents

- `/etc/issue`, `/etc/motd` with the SF banner
- pacman.conf drop-ins (Static Forge repo, once it exists)
- `/etc/os-release` `LOGO=static-linux` → ship `static-linux.svg` in
  `/usr/share/pixmaps/` and the hicolor icon dirs
- default `makepkg.conf` tuning, `zram-generator` config, sysctl drop-ins
