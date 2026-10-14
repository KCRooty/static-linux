# iso/

Builds Static Linux's live/install medium with [archiso](https://gitlab.archlinux.org/archlinux/archiso).

```bash
sudo pacman -S archiso
packages/local-repo.sh      # as your normal user: builds calamares, staticlinux-base, brave-origin-bin
sudo iso/build.sh online    # ~1.7 GB, needs network at install time
sudo iso/build.sh offline   # packages bundled (see caveat below)
```

`packages/local-repo.sh` lists the build dependencies it needs in its
header. Output lands in `iso/out/`.

For a development build that can be driven over SSH from the build host
(QEMU with `hostfwd=tcp:127.0.0.1:2222-:22`):

```bash
sudo iso/build.sh online --dev-ssh-key ~/.ssh/id_ed25519.pub   # never distribute this ISO
```

## What `build.sh` assembles

`profiledir-*/` only hold `profiledef.sh` + `packages.x86_64`. Everything
else a real archiso profile needs is put together fresh on every run and is
gitignored:

- **`efiboot/`, `syslinux/`, `grub/`, `pacman.conf`** — copied from archiso's
  own `releng` profile on the build host, so the boot chain never drifts
  from the installed archiso version.
- **`airootfs/`**, from three sources:
  1. a handful of live-system files from `releng`'s airootfs (the initramfs
     hooks that find and mount the ISO, the pacman keyring bootstrap, the
     mirrorlist hooks);
  2. `iso/airootfs-common/` — root account, autologin on tty1, and the
     `.xinitrc`/`.bash_profile` that start Openbox + Calamares;
  3. `installer/calamares/` copied to `airootfs/etc/calamares/`.
- **The local package repo** (`packages/aur-cache/`, built by
  `packages/local-repo.sh`). `calamares` and `staticlinux-base` aren't in any
  official repo, so the repo is added to the profile's `pacman.conf` for
  pacstrap, and also shipped inside the image at `/opt/staticlinux-repo` so
  the installer can pacstrap `staticlinux-base` into the target.

`calamares` is Static Linux's own build (`packages/calamares/`): the AUR
package has no Python job support and skips `packagechooser`, both of which
`installer/calamares/settings.conf` depends on.

## Status

Build-tested and install-tested on 2026-10-11 (archiso 91, QEMU/KVM, UEFI):
the online ISO boots into Calamares, a default install (erase disk, ext4,
XFCE, basic privacy profile) completes, and the installed system boots to
LightDM and the XFCE session with `sl-welcome`.

Not tested yet: BIOS boot, the other three environments, the improved and
maximum privacy profiles, LUKS, btrfs, real hardware, and the offline ISO.

## Known gaps

- **The 10 AUR-only packages** across `packages/lists/*.list` (`paru`,
  `ttf-outfit`, `otf-space-grotesk`, `nwg-dock-hyprland`, `davinci-resolve`,
  `thonny`, `heroic-games-launcher-bin`, `proton-ge-custom-bin`,
  `joplin-desktop`, `bridge-utils`) are skipped by the installer and left
  for `paru` after first boot. They'd need building into the local repo to
  be installable from the ISO.
- **The offline ISO is offline-*shaped*, not offline-*functional*.** Its
  live image carries the packages, but Calamares' pacstrap/pacman calls
  still download from the network. Wiring the bundled cache in is not done.
- **The installed system doesn't know the local repo**, so `staticlinux-base`
  is a foreign package there and never updates. Needs a real Static Forge
  repo.
