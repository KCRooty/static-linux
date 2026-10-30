# Contributing to Static Linux

Static Linux is a Static Forge project. Thanks for helping.

## Ground rules

- All contributions must be **GPL-3.0** compatible.
- Open an issue **before** starting large changes — discuss the approach first.
- Follow the existing file structure and code style.
- Test on real hardware or a VM before opening a PR.
- Every `sl-ctl` tweak and every privacy action **must** have automatic
  backup/restore. No irreversible changes. Ever.

## Development machines

| Machine | Role | Command tag |
|---|---|---|
| Main PC — Arch (Ryzen 5 5600, RTX 3070 Ti) | main dev, ISO builds, VMs, bare-metal test | `[BUILD · bash]` |
| Main PC — Windows 11 (same box, dual boot) | branding, docs, design | `[PROD · PowerShell]` |
| Packard Bell iMedia S2883 (J1900) | first target — retired, kept as `sl-detect` regression reference | — |

Never mix command environments. `pacman` / `paru` on Linux — never `apt`,
never `brew`.

## Repo layout

```
sl-detect/      hardware detection (Python, stdlib only) — current priority
sl-ctl/         post-install management CLI
sl-welcome/     first-boot GTK4 app
entornos/       desktop environment configs (xfce-themed is the current focus)
sabores/        flavor presets (gaming, dev, cybersecurity, ...)
privacidad/     3 privacy profiles + shared apply lib
installer/      Calamares modules + branding
packages/       package lists per environment / profile
iso/            archiso profiles (online + offline) + build.sh
branding/       GRUB, SDDM, Plymouth, wallpapers, logos
docs/wiki/      MkDocs Material sources
```

## sl-detect

- Standard library only. It must run on the minimal live ISO.
- Add hardware knowledge to `sl-detect/rules/*.rules`, not to `detect.py`.
- Run the tests: `python3 -m unittest discover -s sl-detect/tests -v`
- If you tested on a new machine, add its `sl-detect --all` output to the PR.

## Areas where help is needed

- sl-detect: GPU rules for edge-case hardware and ARM boards.
- Calamares modules: flavor and privacy profile integration.
- sl-welcome: GTK4 app development.
- Branding: wallpapers, SDDM theme, Plymouth animation.
- Documentation: wiki pages in any supported language.
- Testing: ISO testing on varied hardware — especially old machines.
- ARM64: porting and testing on RPi 4/5, Pinebook Pro, RK3588.

## Reporting bugs

Use GitHub Issues with the bug report template. Include:

- `sl-detect --all` output
- relevant `journalctl` logs
- hardware model
- which ISO (online / offline) and its build date

## Commit messages

Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
Scope when useful: `feat(sl-detect): add RK3588 GPU rule`.

## Releases

All public ISOs are GPG-signed with the Static Forge Release Key and shipped
with a SHA256 checksum. Naming: `static-linux-YYYY.MM-ARCH.iso`.
