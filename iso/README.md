# iso/

Builds Static Linux's live/install medium with [archiso](https://gitlab.archlinux.org/archlinux/archiso).

```bash
sudo pacman -S archiso
cd iso
sudo ./build.sh online     # ~1 GB, needs network at install time
sudo ./build.sh offline    # ~4 GB, packages bundled (see caveat below)
```

Output lands in `iso/out/`.

## Why `profiledir-online/` and `profiledir-offline/` only hold `profiledef.sh` + `packages.x86_64`

A real archiso profile also needs `airootfs/` (the live root filesystem
overlay), `efiboot/`, `syslinux/`, `grub/` (the boot chain) and
`pacman.conf`. None of that is checked in here — `build.sh` assembles it
fresh on every run, gitignored:

- **`efiboot/`, `syslinux/`, `grub/`, `pacman.conf`** are copied straight
  from `archiso`'s own `releng` profile (`/usr/share/archiso/configs/releng`
  on the build host). This is upstream's boot-chain boilerplate — Static
  Linux hand-maintaining a copy would just drift from whatever archiso
  version is actually installed. Pulled in fresh, never committed.
- **`airootfs/`** is assembled from three sources:
  1. `iso/airootfs-common/` — the small hand-authored part (autologin on
     tty1, `/etc/motd`, `/etc/hostname`, and `.xinitrc`/`.bash_profile` that
     auto-start Openbox + Calamares so the live session boots straight into
     the installer).
  2. `packages/staticlinux-base/PKGBUILD`'s own `package()` function, run
     with `pkgdir` pointed at the profile's `airootfs/` instead of a real
     package. The live session ends up with the exact same
     `/usr/lib/static-linux` tree a real `pacman -S staticlinux-base` would
     produce — `sl-detect`/`sl-ctl` need to be there for Calamares' own
     `sl-detect`/`accent`/`sabores`/etc. jobs to find them, and this way
     there's no second copy of that packaging logic to keep in sync.
  3. `installer/calamares/` copied to `airootfs/etc/calamares/`, so
     Calamares actually finds `settings.conf` when it launches.

## Known gaps — read before building

**`calamares` is AUR-only.** Checked directly:
`archlinux.org/packages/search/json/?name=calamares` returns zero results;
the AUR has it. `mkarchiso`'s `pacstrap` step only pulls from the pacman
repos configured on the *build host* — it can't reach the AUR. `build.sh`
checks `pacman -Si calamares` up front and refuses to start rather than
fail confusingly mid-build, but it can't fix this for you: you need a local
pacman repo with a prebuilt `calamares` package added to your own
`/etc/pacman.conf` before building (the same thing EndeavourOS, Manjaro
etc. do — Static Linux doesn't have its own repo yet, see
`packages/staticlinux-base/README.md`). The 10 AUR-only packages spread
across `packages/lists/*.list` (`paru`, `ttf-outfit`,
`otf-space-grotesk`, `nwg-dock-hyprland`, `davinci-resolve`, `thonny`,
`heroic-games-launcher-bin`, `proton-ge-custom-bin`, `joplin-desktop`,
`bridge-utils`) have the exact same problem for the *offline* ISO's
bundling story specifically — they can't be pacstrapped in either.

**The offline ISO is offline-*shaped*, not offline-*functional* yet.**
`profiledir-offline/packages.x86_64` gets every official-repo package
`packages/lists/*.list` references pacstrapped into the live image's own
pacman cache at build time. That's not the same as Calamares' live
`pacman -S` calls (`basepkgs`, `entorno-pkgs`, `sabores`,
`privacidad-apply` — see `installer/calamares/modules/`) actually reading
from that cache instead of hitting the network during install. Making that
work needs either a bind-mounted cache directory + a `CacheDir` override in
the target's `pacman.conf`, or a local repo added to it before `basepkgs`
runs — neither is wired up. Until it is, both ISOs need network at install
time; `offline` is only ahead in that its live image already carries the
packages, ready for whoever finishes that wiring.

**Nothing here has been build-tested.** No Arch machine was available this
session (see `docs/PROYECTO.md`'s hardware status) — `archiso`/`mkarchiso` aren't
installable in this sandbox either. Every path was verified with what
*was* available: `bash -n` on `build.sh`, the airootfs assembly steps
run end-to-end against a scratch directory (confirms `iso/airootfs-common/`
+ the `staticlinux-base` `package()` call + the `installer/calamares/` copy
all land where expected), and every package name in both
`packages.x86_64` files checked against `archlinux.org/packages/search/json`.
A real `sudo ./build.sh online` run, on real Arch, is the next step —
per `CONTRIBUTING.md`, test before merge.
