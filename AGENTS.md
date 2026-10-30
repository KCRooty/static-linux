# AGENTS.md — Static Linux by Static Forge
> Documento de contexto del proyecto. Leerlo entero antes de tocar nada.
> Version 2.2 — fase 2 en curso.

---

## ✅ CURRENT PROJECT STATUS

```
Phase 1: Minimal bootable base    → COMPLETE ✅
Phase 2: XFCE + sl-detect         → IN PROGRESS 🔄
Phase 3-14: ...                   → Planned
```

### What exists right now
- **Dev/test machine is the PC Principal** (Ryzen 5 5600 + RTX 3070 Ti, Arch on
  a 128 GB SSD). The iMedia S2883 that Phase 1 was validated on is retired;
  the ThinkPad T480s never arrived. Repo lives at `~/static-linux`.
- **`sl-detect/detect.py`** — validated on both machines: iMedia →
  `xfce-themed / ext4 / linux-lts`, PC Principal →
  `hyprland-astal-full / btrfs / linux-zen`. Rules in `sl-detect/rules/*.rules`.
  Both results pinned as unit tests.
- **`sl-ctl/sl-ctl.py`** — `detect`, `info`, `privacy`, `accent`, `tweaks`
  work; `update`/`snapshot`/`mirror` are thin wrappers; `flavor` is a stub.
- **`sl-welcome/`** — GTK4 first-boot app with the YAML catalog.
- Calamares sequence complete: `settings.conf`, branding, and the sl-detect /
  basepkgs / entorno-pkgs / sabores / privacidad-apply / accent / luks jobs.
- Package lists for base + all 4 environments + 9 flavors + 3 privacy profiles
- 3 privacy profiles with reversible `apply.sh` + shared `scripts/lib.sh`
- All 4 environments under `entornos/` with idempotent `install.sh`
- `branding/accents/` — 10 accent themes (purple is the default) + wallpapers
- `iso/build.sh` + online/offline archiso profiles
- `packages/staticlinux-base/` PKGBUILD (installs the repo to `/usr/lib/static-linux`)
- MkDocs wiki under `docs/wiki/`, deployed by `.github/workflows/docs.yml`

### ISO status (2026-10-11)
First real build and install. `packages/local-repo.sh` + `sudo iso/build.sh online`
produce a 1.7 GB ISO that boots in QEMU/KVM (UEFI) straight into Calamares; a
default install (erase disk, ext4, XFCE, basic privacy) completes and the
installed system boots to LightDM → XFCE → `sl-welcome`. Details and what is
still untested: `iso/README.md`.

### What to do next
Bugs seen during the first install test, not fixed yet:
1. SSH into the live session dies near the end of the install — suspected:
   the privacy profile's `apply.sh` enables the firewall against the *live*
   kernel from inside the chroot. Unconfirmed.
2. Installed system shows the stock XFCE wallpaper: `branding/accents/apply.sh`
   only sets `monitor0`, real outputs are named (`monitorDP-2`, `monitorVirtual-1`).
3. `sl-welcome` opens in a light theme.
4. Calamares `entorno`/`privacidad` pages: no preselection, no description
   until an item is clicked, page title is the default "Package Selection".
5. Installer branding images are placeholders cut from the purple wallpaper
   (`installer/calamares/branding/staticlinux/icon.png`) — needs the SF monogram.
6. Installer defaults to English; live session has no desktop, only Calamares.

Then:
- Test the other environments (Hyprland ×2, Openbox), privacy profiles,
  btrfs, LUKS and BIOS boot in the VM; then real hardware.
- First real Hyprland run on the PC Principal (proprietary NVIDIA + Wayland).
- Brave Origin ships preinstalled: built from Brave's own AUR package into
  the ISO's local repo, pacstrapped with base.list, default via
  /etc/xdg/mimeapps.list.
- Release path: build without `--dev-ssh-key`, GPG-sign, upload to
  SourceForge (project `static-linux`).

---

## 🖥️ RETIRED REFERENCE — Packard Bell iMedia S2883

**The first real Static Linux machine. No longer available, but all sl-detect
logic must keep handling this hardware correctly — it is the low-end
regression reference.**

```
Model:   Packard Bell iMedia S2883
CPU:     Intel Celeron J1900 (Bay Trail, 2013, 4 cores)
GPU:     Intel Atom Processor Z36xxx/Z37xxx (i915 driver)
RAM:     8GB DDR3 installed / 3.64GB usable (shared VRAM)
Storage: 250GB HDD (partitioned: sda1=512MB EFI, sda2=232GB EXT4)
Network: Integrated LAN enp3s0 (ethernet)
Display: MAG 272F 1920x1080
Kernel:  linux-lts 6.18.50-2-lts
```

### Expected sl-detect output for the iMedia
```
gpu:        intel_bay_trail
driver:     i915
wayland:    False  ← Bay Trail has poor Wayland support
ram_mb:     3727
arch:       x86_64
firmware:   uefi
storage:    hdd
recommend:  xfce-themed
fs:         ext4
kernel:     linux-lts
```

---

## 🔧 LESSONS LEARNED FROM PHASE 1 INSTALLATION

These are now part of the installer design. Do not forget them.

| Problem | What happened | Static Linux solution |
|---|---|---|
| UEFI limited firmware | efibootmgr I/O error on J1900 UEFI | Always copy grubx64.efi to /EFI/BOOT/BOOTX64.EFI |
| Rust compilation OOM | paru SIGKILL during compilation | Auto-create 2GB swapfile when RAM < 4GB |
| EXT4 over BTRFS | J1900 + HDD → BTRFS overhead bad | sl-detect: HDD → EXT4, SSD+4GB → BTRFS |
| Bay Trail → no Wayland | Z36xxx GPU = no Wayland | sl-detect: Z36xxx → force XFCE fallback |
| Swapfile persistence | Swap gone after reboot | Installer adds /swapfile to /etc/fstab |

---

## 📋 PROJECT IDENTITY

```
Name:     Static Linux
Brand:    by Static Forge
Tagline:  fast. private. yours.
Base:     Arch Linux
Init:     systemd
Repo:     github.com/KCRooty/static-linux
```

---

## ❌ DO NOT RE-SUGGEST THESE (final decisions)

```
Base distro     → Arch (not Artix, not Debian, not Ubuntu)
Init system     → systemd (not OpenRC, not runit, not dinit)
Default browser → Brave Origin, Release channel (not Firefox, not Chromium, not full Brave)
Default shell   → bash (fish/zsh in catalog only)
AUR helper      → paru CLI only
Secure Boot     → not supported
Telemetry       → ABSOLUTE ZERO
RAM ceiling     → 4 GB recommended max
GPU shell accel → not a thing. Kitty is the GPU terminal.
```

---

## 🏗️ ARCHITECTURE

```
BASE         → Arch Linux (pacstrap minimal)
KERNEL       → linux-lts (old HW/HDD) · linux-zen (modern) · linux-hardened (privacy)
FIRMWARE     → linux-firmware + linux-firmware-whence
INIT         → systemd
NETWORK      → NetworkManager
REPOS        → pacman + paru (AUR) + Flatpak/Flathub + Distrobox
HW DETECT    → sl-detect (Python)
ENVIRONMENTS → Hyprland+Astal / XFCE / Openbox / TTY
ENCRYPTION   → LUKS2 optional (not for J1900-class hardware)
PRIVACY      → ufw + AppArmor + Firejail + dnscrypt-proxy (3 profiles)
STABILITY    → BTRFS+Snapper or EXT4 (by sl-detect) + pacman hook
SWAP         → zram (zstd, 50% RAM) + swapfile if RAM < 4GB
INSTALLER    → Calamares + sl-detect + flavors
POST-INSTALL → sl-welcome + sl-ctl
```

---

## 🔍 sl-detect SPECIFICATION

**Language:** Python 3
**Path:** `sl-detect/detect.py`
**Runs:** Silently before installer UI

### Detection functions
```python
detect_gpu()              # → gpu_id, driver, wayland_ok
detect_ram()              # → MB integer
detect_wayland_support()  # → True | False
detect_arch()             # → x86_64 | arm64 | arm32
detect_firmware()         # → uefi | bios
detect_storage_type()     # → ssd | hdd | emmc
```

### Recommendation logic
```python
# Environment
if wayland_support and ram_mb >= 4096:  → hyprland-astal-full
if wayland_support and ram_mb >= 2048:  → hyprland-astal-lite
if wayland_support and ram_mb >= 1024:  → xfce-themed
if not wayland_support:                 → xfce-themed (FORCED)
if ram_mb < 1024:                       → openbox-minimal
if arch == 'arm32':                     → openbox-minimal

# Filesystem
if storage == 'ssd' and ram_mb >= 4096: → btrfs
if storage == 'hdd' or ram_mb < 2048:  → ext4  ← iMedia S2883 case
if storage == 'emmc':                   → f2fs

# Kernel
if year_cpu < 2015 or storage == 'hdd': → linux-lts  ← iMedia S2883 case
else:                                   → linux-zen
```

### GPU → Wayland table
```
Intel Bay Trail Z36xxx/Z37xxx → Wayland: FALSE ← CONFIRMED on iMedia S2883
AMD GCN+ (HD 7000+)          → Wayland: TRUE
Intel Sandy Bridge+           → Wayland: TRUE
Nvidia RTX 20xx+              → Wayland: TRUE
Nvidia GTX 10xx Pascal        → Wayland: TRUE
Nvidia GTX 700 Kepler         → Wayland: FALSE → XFCE fallback
```

### CLI
```bash
sl-detect --all            # full output
sl-detect --recommend-env  # environment string only
sl-detect --recommend-fs   # filesystem string only
sl-detect --json           # for Calamares module
sl-detect --gpu            # GPU info only
```

---

## 📊 REQUIREMENTS

| Tier | RAM | Storage | Environment |
|---|---|---|---|
| Minimum (absolute) | 512 MB | 10 GB | Openbox minimal |
| Minimum (functional) | 1 GB | 15 GB | Themed XFCE |
| Standard | 2 GB | 20 GB | XFCE or Hyprland lite |
| Recommended (CEILING) | 4 GB | 30 GB | Hyprland + Astal full |

**Validated:** iMedia S2883 (J1900, 3.64GB, HDD) → XFCE themed ✅
**Detected, not yet run:** PC Principal (Ryzen 5 5600, RTX 3070 Ti) → Hyprland + Astal full

---

## 🎮 FLAVORS (9 presets)

```
🖥️  Daily Driver      → always included
🎮  Gaming            → Steam+Proton-GE, Lutris, Heroic, MangoHud, GameMode
🎨  Content Creation  → Krita, GIMP, Blender, DaVinci, OBS, LMMS, Ardour
💻  Development       → VS Code, Git, Docker, Python, Rust, Node, Java
🔒  Cybersecurity     → Nmap, Wireshark, Metasploit, Hashcat, Ghidra, Tor
📄  Office            → LibreOffice, Obsidian, Joplin, Bitwarden
🖥️  Server/Homelab   → Docker, Nginx, MariaDB, WireGuard, Fail2ban, Cockpit
🧪  Virtual Machines  → QEMU+KVM, virt-manager, VirtualBox
🎓  Education         → GeoGebra, Stellarium, Anki, Jupyter, Thonny, FreeCAD
```

---

## 🎨 BRANDING

```
Logo:         Static Forge SF monogram (bicolor B&W diagonal split)
Void:         #0B0C10  (main background)
Signal Green: #00C8A0  (primary accent)
Amber:        #F5A623  (offline ISO, warnings)
White:        #FFFFFF  (text on dark)

Fonts (all SIL OFL):
  Outfit 700        → display, headings, GRUB, SDDM
  Space Grotesk 400 → UI, body text
  JetBrains Mono    → terminal, code, sl-ctl
```

---

## 💿 DISTRIBUTION

```
Online ISO  (~1GB, monthly):   GitHub Releases + SourceForge
Offline ISO (~4GB, quarterly): MEGA + MediaFire + Torrent
GPG:   Static Forge Release Key — sign all ISOs
SHA256: published alongside every ISO
Wiki:  GitHub Pages + MkDocs Material
```

---

## 📁 REPOSITORY STRUCTURE

```
static-linux/
├── iso/
│   ├── profiledir-online/
│   ├── profiledir-offline/
│   └── build.sh
├── installer/calamares/modules/
│   ├── sl-detect/
│   ├── entorno/
│   ├── sabores/
│   ├── privacidad/
│   └── luks/
├── sl-detect/
│   ├── detect.py
│   ├── rules/
│   └── tests/
├── sl-welcome/
│   ├── src/main.py
│   └── catalog/
├── sl-ctl/
│   ├── sl-ctl.py
│   └── tweaks/
├── entornos/
│   ├── hyprland-astal-full/
│   ├── hyprland-astal-lite/
│   ├── xfce-themed/
│   ├── openbox-minimal/
│   └── shared/
├── sabores/
├── privacidad/
├── branding/
├── packages/
├── docs/wiki/
├── README.md
├── CONTRIBUTING.md
└── AGENTS.md
```

---

## ⚙️ sl-ctl COMMANDS

```bash
sl-ctl update                    # pacman + AUR + Flatpak
sl-ctl tweaks --list             # all tweaks and state
sl-ctl tweaks --apply <name>     # apply with auto-backup
sl-ctl tweaks --revert <name>    # revert to original
sl-ctl snapshot --create         # manual snapshot
sl-ctl snapshot --list           # list snapshots
sl-ctl snapshot --rollback <id>  # rollback
sl-ctl flavor --add <flavor>     # add flavor post-install
sl-ctl flavor --remove <flavor>  # remove flavor
sl-ctl privacy --profile <p>     # change privacy profile
sl-ctl info                      # system info branded
sl-ctl detect                    # run sl-detect
sl-ctl welcome                   # relaunch sl-welcome
sl-ctl mirror                    # update mirrors
```

**ALL tweaks must have backup/restore. No irreversible changes. Ever.**

---

## 🔑 GPG SIGNING

```bash
# Generate key (one time)
gpg --full-generate-key
# RSA 4096 · Name: Static Forge · Email: releases@staticforge.dev

# Sign ISO
gpg --armor --detach-sign static-linux-2025.06-x86_64.iso

# User verification
gpg --verify static-linux-2025.06-x86_64.iso.sig \
              static-linux-2025.06-x86_64.iso
```

---

## ⚠️ CRITICAL RULES

1. ALL sl-ctl tweaks MUST have backup/restore.
2. Never suggest formatting storage without explicit confirmation.
3. sl-detect must work BEFORE the installer shows recommendations.
4. Offline ISO is as important as online ISO.
5. StaticOS (from-scratch) is future. Static Linux is now. Keep separate.
6. Before any USB operation → verify target is not critical storage.
7. All ISOs must be GPG signed before public distribution.
8. > 500 MB idle RAM = design bug, fix it.
9. Bay Trail (Z36xxx) → always XFCE, never Wayland. CONFIRMED.
10. J1900 class hardware → always linux-lts, always EXT4 on HDD.

---

## 🔗 NAMESPACE

| Name | What | Status |
|---|---|---|
| Static Linux | Arch-based distro by Static Forge | 🟢 Active |
| StaticOS | From-scratch OS (own kernel) | 🔵 Reserved |
| sl-detect | HW detection tool | 🟢 Working, validated on 2 machines |
| sl-ctl | Post-install management | 🟢 In development |
| sl-welcome | First-boot app | 🟢 In development |

---

*AGENTS.md v2.2 · Static Linux · Static Forge · Phase 2 in progress*
