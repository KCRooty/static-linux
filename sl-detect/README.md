# sl-detect

Hardware detection for Static Linux. Runs silently before the Calamares
installer UI and decides the optimal **environment**, **filesystem** and
**kernel** for the detected machine. Also usable standalone after install
(`sl-ctl detect`).

- Standard library only (Python 3.9+). Runs on the minimal live ISO as root.
- Never crashes: every probe degrades to a safe fallback (XFCE / ext4 / lts).
- Hardware knowledge lives in [`rules/`](rules/), not in code — edit the rule
  files to add a GPU or retune a threshold without touching `detect.py`.

## Usage

```bash
sl-detect --all               # full human-readable report
sl-detect --json              # machine-readable, consumed by Calamares
sl-detect --recommend-env     # -> hyprland-astal-full | ...-lite | xfce-themed | openbox-minimal
sl-detect --recommend-fs      # -> btrfs | ext4 | f2fs
sl-detect --recommend-kernel  # -> linux-lts | linux-zen
sl-detect --gpu               # GPU model, driver, Wayland support
```

## What it detects

| Function | Returns |
|---|---|
| `detect_arch()` | `x86_64` / `arm64` / `arm32` |
| `detect_firmware()` | `uefi` / `bios` |
| `detect_ram_mb()` | total usable RAM in MB |
| `detect_gpu()` | model, driver, family, `wayland_ok` |
| `detect_wayland_support()` | `True` / `False` (family known-good **and** a DRM node exists) |
| `detect_storage_type()` | `ssd` / `hdd` / `emmc` |
| `detect_cpu_year()` | approximate CPU release year (hint, from `rules/kernel.rules`) |

## Recommendation logic

```
environment:
  arch == arm32                      -> openbox-minimal
  ram_mb < XFCE_RAM_MB (1024)        -> openbox-minimal
  not wayland                        -> xfce-themed        (forced)
  wayland and ram_mb >= 4096         -> hyprland-astal-full
  wayland and ram_mb >= 2048         -> hyprland-astal-lite
  wayland and ram_mb <  2048         -> xfce-themed

filesystem:
  storage == emmc                    -> f2fs
  storage == ssd and ram_mb >= 4096  -> btrfs
  otherwise                          -> ext4

kernel:
  storage == hdd                     -> linux-lts
  cpu_year < LTS_CPU_YEAR (2015)     -> linux-lts
  otherwise                          -> linux-zen
```

## Reference result — Packard Bell iMedia S2883

The first real Static Linux machine (Celeron J1900, Bay Trail, 3.64 GB usable,
250 GB HDD, UEFI):

```
→ environment : xfce-themed      (Bay Trail = no Wayland, forced)
→ filesystem  : ext4             (HDD)
→ kernel      : linux-lts        (HDD + 2013 CPU)
→ I/O sched   : bfq
swapfile 2G   : True             (RAM < 4 GB — needed for paru/Rust builds)
EFI fallback  : True             (limited UEFI — stage BOOTX64.EFI)
force XFCE    : True
```

## Reference result — PC Principal (Ryzen 5 5600 + RTX 3070 Ti)

The current dev/test machine, replacing the iMedia (32 GB, SATA SSD, UEFI,
proprietary NVIDIA driver):

```
→ environment : hyprland-astal-full   (Turing+ GPU = Wayland OK, RAM >= 4 GB)
→ filesystem  : btrfs                 (SSD + RAM >= 4 GB)
→ kernel      : linux-zen             (SSD + 2022 CPU)
→ I/O sched   : none
swapfile 2G   : False
EFI fallback  : True
force XFCE    : False
```

## Rule files

| File | Purpose |
|---|---|
| `rules/gpu.rules` | `regex \| family \| driver \| wayland` — GPU classification |
| `rules/wayland.rules` | hard veto list: families forced to `wayland = false` |
| `rules/entorno.rules` | RAM thresholds for each environment tier |
| `rules/kernel.rules` | `LTS_CPU_YEAR` + CPU-model → release-year hints |

## Tests

```bash
python3 -m unittest discover -s tests -v
```

No third-party dependencies — `unittest` only, so it runs on the live ISO.
