# iso/

Builds Static Linux's live/install medium with [archiso](https://gitlab.archlinux.org/archlinux/archiso).

```bash
sudo pacman -S archiso
packages/local-repo.sh      # as your normal user: builds calamares, staticlinux-base, brave-origin-bin
sudo iso/build.sh universal # ~4.5 GB, installs with or without a network (the public one)
sudo iso/build.sh online    # ~2 GB, downloads everything at install time
```

`packages/local-repo.sh` lists the build dependencies it needs in its
header. Output lands in `iso/out/`.

For a development build that can be driven over SSH from the build host
(QEMU with `hostfwd=tcp:127.0.0.1:2222-:22`):

```bash
sudo iso/build.sh universal --dev-ssh-key ~/.ssh/id_ed25519.pub   # never distribute this ISO
```

## What `build.sh` assembles

`profiledir-*/` only hold `profiledef.sh` + `packages.x86_64`. Everything
else a real archiso profile needs is put together fresh on every run and is
gitignored:

- **`efiboot/`, `syslinux/`, `grub/`, `pacman.conf`** — copied from archiso's
  own `releng` profile on the build host, so the boot chain never drifts
  from the installed archiso version.
- **`airootfs/`**, from four sources:
  1. a handful of live-system files from `releng`'s airootfs (the initramfs
     hooks that find and mount the ISO, the pacman keyring bootstrap, the
     mirrorlist hooks);
  2. `entornos/xfce-themed/skel/` copied into `/root`: the live session is
     the XFCE desktop;
  3. `iso/airootfs-common/` — root account, autologin on tty1, Spanish
     locale and keyboard, the `.xinitrc`/`.bash_profile` that start XFCE,
     and `sl-live-install`, which opens Calamares at login and from the menu
     ("Instalar Static Linux"). A build-only pacman hook
     (`etc/pacman.d/hooks/50-sl-live-setup.hook`) runs `locale-gen` and
     renders the default theme (Ámbar) into `/root` while mkarchiso installs
     the packages, so the live desktop starts already themed;
  4. `installer/calamares/` copied to `airootfs/etc/calamares/`.
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

Since then (VM): every environment, the three privacy profiles, btrfs with
Snapper, the Server and Gaming setups, and on 2026-11-14 the universal ISO
installing with no network at all. Not tested yet: BIOS boot, LUKS, real
hardware. How the universal ISO works: `docs/wiki/iso.md`.

## Known gaps

- **The 10 AUR-only packages** across `packages/lists/*.list` (`paru`,
  `ttf-outfit`, `otf-space-grotesk`, `nwg-dock-hyprland`, `davinci-resolve`,
  `thonny`, `heroic-games-launcher-bin`, `proton-ge-custom-bin`,
  `joplin-desktop`, `bridge-utils`) are skipped by the installer and left
  for `paru` after first boot. They'd need building into the local repo to
  be installable from the ISO.
- Flavors are not on the universal ISO: with no network at install time
  they are left for `sudo sl-ctl flavor add pending`.
