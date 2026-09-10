#!/usr/bin/env python3
"""
sl-detect — Static Linux hardware detection tool.

Runs silently before the Calamares installer UI and determines the optimal
environment, filesystem and kernel for the detected hardware. Also usable as a
standalone tool after installation (see `sl-ctl detect`).

Design goals:
  * Standard library only. Must run on the minimal live ISO as root.
  * Never crash. Every probe degrades to a safe fallback (XFCE / ext4 / lts).
  * Hardware knowledge lives in rules/*.rules (data), not in code.

CLI:
  sl-detect --all               full human-readable report
  sl-detect --json              machine-readable, for the Calamares module
  sl-detect --recommend-env     environment string only
  sl-detect --recommend-fs      filesystem string only
  sl-detect --recommend-kernel  kernel string only
  sl-detect --gpu               GPU model + driver + Wayland support
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

__version__ = "0.1.0"

RULES_DIR = Path(__file__).resolve().parent / "rules"

# ---------------------------------------------------------------------------
# Defaults — overridable from rules/entorno.rules and rules/kernel.rules
# ---------------------------------------------------------------------------
DEFAULTS = {
    "FULL_RAM_MB": 4096,   # >= this + Wayland  -> hyprland-astal-full
    "LITE_RAM_MB": 2048,   # >= this + Wayland  -> hyprland-astal-lite
    "XFCE_RAM_MB": 1024,   # >= this            -> xfce-themed
    "LTS_CPU_YEAR": 2015,  # CPU older than this -> linux-lts
}

# Built-in GPU knowledge, used only when rules/gpu.rules is missing or has no
# match. Each entry: (regex, family, driver, wayland_ok).
BUILTIN_GPU_RULES = [
    (r"z3[67]xxx|bay trail|atom.*graphics", "intel_bay_trail", "i915", False),
    (r"iris xe|alder lake|tiger lake|ice lake", "intel_xe", "xe", True),
    (r"hd graphics|uhd graphics|intel.*(hd|iris)", "intel_gen", "i915", True),
    (r"navi|rdna|vega|polaris|radeon r[579]|rx \d", "amd_gcn", "amdgpu", True),
    (r"radeon hd [2-6]\d{3}|radeon hd [67]\d{2}\b", "amd_pre_gcn", "radeon", False),
    (r"geforce (rtx|gtx 16)", "nvidia_turing_plus", "nvidia", True),
    (r"geforce gtx (10|9)\d{2}", "nvidia_pascal_maxwell", "nvidia", True),
    (r"geforce gt[x]? [2-7]\d{2}\b|kepler|fermi", "nvidia_kepler", "nouveau", False),
    (r"nvidia|geforce", "nvidia_unknown", "nvidia", True),
    (r"amd|radeon", "amd_unknown", "amdgpu", True),
    (r"intel", "intel_unknown", "i915", True),
]


# ---------------------------------------------------------------------------
# Rules loading
# ---------------------------------------------------------------------------
def _read_rules_file(name: str) -> list[str]:
    """Return non-empty, non-comment lines from rules/<name>, or []."""
    path = RULES_DIR / name
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def load_thresholds() -> dict:
    """Merge DEFAULTS with `key = value` overrides from entorno/kernel rules."""
    values = dict(DEFAULTS)
    for fname in ("entorno.rules", "kernel.rules"):
        for line in _read_rules_file(fname):
            if "=" not in line:
                continue
            key, _, raw = line.partition("=")
            key, raw = key.strip(), raw.strip()
            if key in values and raw.lstrip("-").isdigit():
                values[key] = int(raw)
    return values


def load_gpu_rules() -> list[tuple]:
    """rules/gpu.rules lines: `regex | family | driver | wayland`."""
    rules = []
    for line in _read_rules_file("gpu.rules"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 4:
            continue
        pattern, family, driver, wl = parts
        rules.append((pattern, family, driver, wl.lower() in ("1", "true", "yes")))
    return rules or BUILTIN_GPU_RULES


def load_kernel_year_map() -> list[tuple[str, int]]:
    """rules/kernel.rules lines: `cpu model substring = year`."""
    out = []
    for line in _read_rules_file("kernel.rules"):
        if "=" not in line:
            continue
        sub, _, year = line.partition("=")
        sub, year = sub.strip(), year.strip()
        if year.isdigit() and not sub.replace(" ", "").isupper():
            out.append((sub.lower(), int(year)))
    return out


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
def detect_arch() -> str:
    """Return 'x86_64', 'arm64' or 'arm32'."""
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    if machine in ("aarch64", "arm64"):
        return "arm64"
    if machine.startswith("arm") or machine.startswith("armv"):
        return "arm32"
    return machine or "unknown"


def detect_firmware() -> str:
    """Return 'uefi' or 'bios'."""
    return "uefi" if os.path.isdir("/sys/firmware/efi") else "bios"


def detect_ram_mb() -> int:
    """Total usable RAM in MB, from /proc/meminfo (kB)."""
    match = re.search(r"^MemTotal:\s+(\d+)\s+kB", _read("/proc/meminfo"), re.M)
    if match:
        return int(match.group(1)) // 1024
    try:
        return (os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")) // (1024 * 1024)
    except (ValueError, OSError):
        return 0


def _cpu_model() -> str:
    match = re.search(r"^model name\s*:\s*(.+)$", _read("/proc/cpuinfo"), re.M)
    if match:
        return match.group(1).strip()
    match = re.search(r"^Model\s*:\s*(.+)$", _read("/proc/cpuinfo"), re.M)
    return match.group(1).strip() if match else ""


def detect_cpu_year() -> int | None:
    """Best-effort CPU release year from rules/kernel.rules substring map."""
    model = _cpu_model().lower()
    if not model:
        return None
    for substring, year in load_kernel_year_map():
        if substring in model:
            return year
    return None


def _pci_display_devices() -> list[str]:
    """Return description strings of VGA/3D/Display controllers."""
    devices = []
    if shutil.which("lspci"):
        for line in _run(["lspci", "-mm"]).splitlines():
            # -mm quotes fields: slot "class" "vendor" "device" ...
            fields = re.findall(r'"([^"]*)"', line)
            if len(fields) >= 3 and re.search(
                r"VGA|3D|Display", fields[0], re.I
            ):
                devices.append(f"{fields[1]} {fields[2]}".strip())
    if devices:
        return devices

    # /sys fallback: PCI class 0x03xxxx = display controller
    for dev in sorted(Path("/sys/bus/pci/devices").glob("*")):
        cls = _read(str(dev / "class")).strip()
        if not cls.startswith("0x03"):
            continue
        vendor = _read(str(dev / "vendor")).strip().lower()
        name = {
            "0x8086": "Intel",
            "0x1002": "AMD",
            "0x1022": "AMD",
            "0x10de": "NVIDIA",
        }.get(vendor, f"PCI {vendor}")
        devices.append(name)
    return devices


def detect_gpu() -> dict:
    """Return {model, driver, family, wayland_ok, all_gpus}."""
    gpus = _pci_display_devices()
    rules = load_gpu_rules()

    def classify(description: str) -> tuple[str, str, bool]:
        for pattern, family, driver, wl in rules:
            if re.search(pattern, description, re.I):
                return family, driver, wl
        return "unknown", "modesetting", False  # safe: no Wayland

    if not gpus:
        return {
            "model": "unknown",
            "driver": "modesetting",
            "family": "unknown",
            "wayland_ok": False,
            "all_gpus": [],
        }

    # If several GPUs, prefer the one that supports Wayland (dGPU on a laptop).
    classified = [(g, *classify(g)) for g in gpus]
    classified.sort(key=lambda c: c[3], reverse=True)  # wayland_ok True first
    model, family, driver, wayland_ok = classified[0]
    return {
        "model": model,
        "driver": driver,
        "family": family,
        "wayland_ok": wayland_ok,
        "all_gpus": gpus,
    }


def detect_wayland_support(gpu: dict | None = None, arch: str | None = None) -> bool:
    """True only if the GPU family is known-good AND a DRM render node exists."""
    gpu = gpu or detect_gpu()
    arch = arch or detect_arch()
    if not gpu["wayland_ok"]:
        return False
    # Families explicitly force-disabled in rules/wayland.rules.
    blocked = {line.split(":")[0].strip().lower()
               for line in _read_rules_file("wayland.rules") if ":" in line}
    if gpu["family"].lower() in blocked:
        return False
    # Need a usable DRM node (kernel modesetting driver bound).
    has_drm = any(Path("/dev/dri").glob("card*")) if Path("/dev/dri").exists() else False
    if not has_drm and Path("/sys/class/drm").exists():
        has_drm = any(p.name.startswith("card") for p in Path("/sys/class/drm").iterdir())
    return has_drm


def _root_disk() -> str | None:
    """Base block device backing '/', e.g. 'sda' from '/dev/sda2'."""
    src = _run(["findmnt", "-n", "-o", "SOURCE", "/"]).strip()
    match = re.match(r"/dev/([a-z]+|nvme\d+n\d+|mmcblk\d+)", src)
    if match:
        return match.group(1)
    return None


def _largest_fixed_disk() -> str | None:
    best, best_size = None, -1
    for dev in sorted(Path("/sys/block").glob("*")):
        name = dev.name
        if name.startswith(("loop", "ram", "zram", "sr", "fd")):
            continue
        if _read(str(dev / "removable")).strip() == "1":
            continue
        try:
            size = int(_read(str(dev / "size")).strip() or 0)
        except ValueError:
            size = 0
        if size > best_size:
            best, best_size = name, size
    return best


def detect_storage_type(device: str | None = None) -> str:
    """Return 'ssd', 'hdd' or 'emmc' for the install target disk."""
    dev = device or _root_disk() or _largest_fixed_disk()
    if not dev:
        return "hdd"  # conservative default -> ext4 + bfq
    dev = dev.removeprefix("/dev/")
    if dev.startswith("mmcblk"):
        return "emmc"
    if dev.startswith("nvme"):
        return "ssd"
    rotational = _read(f"/sys/block/{dev}/queue/rotational").strip()
    return "hdd" if rotational == "1" else "ssd"


# ---------------------------------------------------------------------------
# Recommendation logic  (Master Document v4, section 5.2)
# ---------------------------------------------------------------------------
def recommend_env(wayland: bool, ram_mb: int, arch: str, thresholds: dict) -> str:
    if arch == "arm32":
        return "openbox-minimal"
    if ram_mb and ram_mb < thresholds["XFCE_RAM_MB"]:
        return "openbox-minimal"
    if not wayland:
        return "xfce-themed"  # forced fallback
    if ram_mb >= thresholds["FULL_RAM_MB"]:
        return "hyprland-astal-full"
    if ram_mb >= thresholds["LITE_RAM_MB"]:
        return "hyprland-astal-lite"
    return "xfce-themed"


def recommend_fs(storage: str, ram_mb: int, thresholds: dict) -> str:
    if storage == "emmc":
        return "f2fs"
    if storage == "ssd" and ram_mb >= thresholds["FULL_RAM_MB"]:
        return "btrfs"
    if storage == "hdd" or ram_mb < thresholds["LITE_RAM_MB"]:
        return "ext4"
    return "ext4"


def recommend_kernel(storage: str, cpu_year: int | None, thresholds: dict) -> str:
    if storage == "hdd":
        return "linux-lts"
    if cpu_year is not None and cpu_year < thresholds["LTS_CPU_YEAR"]:
        return "linux-lts"
    return "linux-zen"


def recommend_io_scheduler(storage: str) -> str:
    return "bfq" if storage == "hdd" else "none"


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------
def build_report() -> dict:
    thresholds = load_thresholds()
    arch = detect_arch()
    firmware = detect_firmware()
    ram_mb = detect_ram_mb()
    gpu = detect_gpu()
    wayland = detect_wayland_support(gpu, arch)
    storage = detect_storage_type()
    cpu_model = _cpu_model()
    cpu_year = detect_cpu_year()

    env = recommend_env(wayland, ram_mb, arch, thresholds)
    fs = recommend_fs(storage, ram_mb, thresholds)
    kernel = recommend_kernel(storage, cpu_year, thresholds)

    needs_swapfile = ram_mb > 0 and ram_mb < thresholds["FULL_RAM_MB"]
    uefi_fallback = firmware == "uefi"  # always stage BOOTX64.EFI on limited UEFI

    return {
        "sl_detect_version": __version__,
        "cpu": {"model": cpu_model, "approx_year": cpu_year},
        "arch": arch,
        "firmware": firmware,
        "ram_mb": ram_mb,
        "gpu": gpu,
        "wayland": wayland,
        "storage": storage,
        "recommend": {
            "env": env,
            "fs": fs,
            "kernel": kernel,
            "io_scheduler": recommend_io_scheduler(storage),
        },
        "installer_actions": {
            "create_swapfile_2g": needs_swapfile,
            "efi_bootx64_fallback": uefi_fallback,
            "force_xfce": not wayland,
        },
    }


def format_report(report: dict) -> str:
    gpu = report["gpu"]
    rec = report["recommend"]
    act = report["installer_actions"]
    lines = [
        "Static Linux — sl-detect",
        "─" * 40,
        f"CPU        : {report['cpu']['model'] or 'unknown'}"
        + (f"  (~{report['cpu']['approx_year']})" if report['cpu']['approx_year'] else ""),
        f"Arch       : {report['arch']}",
        f"Firmware   : {report['firmware']}",
        f"RAM        : {report['ram_mb']} MB",
        f"GPU        : {gpu['model']}",
        f"  family   : {gpu['family']}",
        f"  driver   : {gpu['driver']}",
        f"Wayland    : {report['wayland']}",
        f"Storage    : {report['storage']}",
        "─" * 40,
        f"→ environment : {rec['env']}",
        f"→ filesystem  : {rec['fs']}",
        f"→ kernel      : {rec['kernel']}",
        f"→ I/O sched   : {rec['io_scheduler']}",
        "─" * 40,
        f"swapfile 2G  : {act['create_swapfile_2g']}",
        f"EFI fallback : {act['efi_bootx64_fallback']}",
        f"force XFCE   : {act['force_xfce']}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sl-detect", description="Static Linux hardware detection"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="full human-readable report")
    group.add_argument("--json", action="store_true", help="machine-readable JSON")
    group.add_argument("--recommend-env", action="store_true")
    group.add_argument("--recommend-fs", action="store_true")
    group.add_argument("--recommend-kernel", action="store_true")
    group.add_argument("--gpu", action="store_true", help="GPU model, driver, Wayland")
    parser.add_argument("--version", action="version", version=f"sl-detect {__version__}")
    args = parser.parse_args(argv)

    report = build_report()

    if args.json:
        print(json.dumps(report, indent=2))
    elif args.recommend_env:
        print(report["recommend"]["env"])
    elif args.recommend_fs:
        print(report["recommend"]["fs"])
    elif args.recommend_kernel:
        print(report["recommend"]["kernel"])
    elif args.gpu:
        gpu = report["gpu"]
        print(f"{gpu['model']}\ndriver: {gpu['driver']}\nwayland: {report['wayland']}")
    else:  # default and --all behave the same
        print(format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
