#!/usr/bin/env python3
"""
sl-ctl — Static Linux post-install management tool.

Phase 8 target. This is the working skeleton: `detect`, `info`, `privacy` and
the `tweaks` backup/restore machinery are functional; `update`, `snapshot`,
`flavor` and `mirror` are wired to their real commands but marked EXPERIMENTAL.

CRITICAL RULE: every tweak has automatic backup/restore. No irreversible
changes — ever.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

__version__ = "0.1.0"

STATE_DIR = Path("/var/lib/static-linux")
BACKUP_DIR = Path("/var/backups/static-linux/tweaks")
SL_DETECT = "/usr/lib/static-linux/sl-detect/detect.py"
PRIVACY_DIR = Path("/usr/lib/static-linux/privacidad")
ACCENT_DIR = Path("/usr/lib/static-linux/accents")

GREEN = "\033[1;38;5;43m"   # Signal Green-ish for a 256-color terminal
DIM = "\033[2m"
RESET = "\033[0m"


def _sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, **kw)


def _need_root() -> None:
    if os.geteuid() != 0:
        sys.exit("sl-ctl: this command must be run as root")


def _sl_detect_path() -> str:
    if os.path.exists(SL_DETECT):
        return SL_DETECT
    local = Path(__file__).resolve().parents[1] / "sl-detect" / "detect.py"
    return str(local)


# ---------------------------------------------------------------------------
# detect / info
# ---------------------------------------------------------------------------
def cmd_detect(args) -> int:
    return _sh(["python3", _sl_detect_path(), "--all"]).returncode


def cmd_info(args) -> int:
    try:
        report = json.loads(
            _sh(["python3", _sl_detect_path(), "--json"],
                capture_output=True).stdout
        )
    except (ValueError, subprocess.SubprocessError):
        report = {}

    profile = "unknown"
    pf = STATE_DIR / "privacy-profile"
    if pf.exists():
        profile = pf.read_text().strip()

    rec = report.get("recommend", {})
    gpu = report.get("gpu", {})
    print(f"""{GREEN}  ▞▚  Static Linux{RESET}  {DIM}by Static Forge — fast. private. yours.{RESET}

  {GREEN}Kernel{RESET}    {os.uname().release}
  {GREEN}CPU{RESET}       {report.get('cpu', {}).get('model', 'n/a')}
  {GREEN}RAM{RESET}       {report.get('ram_mb', 0)} MB
  {GREEN}GPU{RESET}       {gpu.get('model', 'n/a')} ({gpu.get('driver', '?')})
  {GREEN}Arch{RESET}      {report.get('arch', 'n/a')} / {report.get('firmware', 'n/a')}
  {GREEN}Storage{RESET}   {report.get('storage', 'n/a')}
  {GREEN}Wayland{RESET}   {report.get('wayland', 'n/a')}
  {GREEN}Env (rec){RESET} {rec.get('env', 'n/a')}
  {GREEN}Privacy{RESET}   {profile}
""")
    return 0


# ---------------------------------------------------------------------------
# privacy
# ---------------------------------------------------------------------------
def cmd_privacy(args) -> int:
    _need_root()
    mapping = {
        "basic": "perfil-basico", "basico": "perfil-basico",
        "improved": "perfil-mejorado", "mejorado": "perfil-mejorado",
        "maximum": "perfil-maximo", "maximo": "perfil-maximo",
    }
    if not args.profile:
        pf = STATE_DIR / "privacy-profile"
        print(pf.read_text().strip() if pf.exists() else "unknown")
        return 0
    folder = mapping.get(args.profile.lower())
    if not folder:
        sys.exit(f"sl-ctl: unknown privacy profile '{args.profile}'")
    apply_sh = PRIVACY_DIR / folder / "apply.sh"
    if not apply_sh.exists():
        local = Path(__file__).resolve().parents[1] / "privacidad" / folder / "apply.sh"
        apply_sh = local
    if not apply_sh.exists():
        sys.exit(f"sl-ctl: {apply_sh} not found")
    return _sh(["bash", str(apply_sh)]).returncode


# ---------------------------------------------------------------------------
# accent  (whole-look colour)
# ---------------------------------------------------------------------------
def _accent_apply() -> Path | None:
    for p in (ACCENT_DIR / "apply.sh",
              Path(__file__).resolve().parents[1] / "branding" / "accents" / "apply.sh"):
        if p.exists():
            return p
    return None


def cmd_accent(args) -> int:
    apply = _accent_apply()
    if apply is None:
        sys.exit("sl-ctl: accent tool not found")
    if args.list:
        return _sh(["bash", str(apply), "--list"]).returncode
    if not args.name:
        return _sh(["bash", str(apply), "--current"]).returncode
    if os.geteuid() != 0:
        sys.exit("sl-ctl: 'accent <name>' must be run as root (touches /etc)")
    return _sh(["bash", str(apply), args.name]).returncode


# ---------------------------------------------------------------------------
# tweaks  (generic reversible file tweaks)
# ---------------------------------------------------------------------------
def _tweaks_registry() -> dict:
    """name -> {'desc', 'files': [...], 'apply': [...], 'check': cmd}."""
    return {
        "swappiness-10": {
            "desc": "Lower vm.swappiness to 10 (favor RAM over swap)",
            "file": "/etc/sysctl.d/99-sl-swappiness.conf",
            "content": "vm.swappiness=10\n",
            "post": ["sysctl", "--system"],
        },
        "trim-timer": {
            "desc": "Enable weekly fstrim.timer (SSD only)",
            "unit": "fstrim.timer",
        },
        "hdd-bfq": {
            "desc": "Set the bfq I/O scheduler for rotational disks",
            "file": "/etc/udev/rules.d/60-sl-ioschedulers.rules",
            "content": 'ACTION=="add|change", KERNEL=="sd[a-z]", '
                       'ATTR{queue/rotational}=="1", '
                       'ATTR{queue/scheduler}="bfq"\n',
            "post": ["udevadm", "control", "--reload"],
        },
    }


def _state() -> dict:
    f = STATE_DIR / "tweaks.json"
    if f.exists():
        try:
            return json.loads(f.read_text())
        except ValueError:
            return {}
    return {}


def _save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "tweaks.json").write_text(json.dumps(state, indent=2))


def cmd_tweaks(args) -> int:
    reg = _tweaks_registry()
    state = _state()

    if args.list or not (args.apply or args.revert):
        for name, meta in reg.items():
            mark = f"{GREEN}applied{RESET}" if state.get(name) else "—"
            print(f"  {name:18} [{mark}]  {meta['desc']}")
        return 0

    _need_root()
    name = args.apply or args.revert
    if name not in reg:
        sys.exit(f"sl-ctl: unknown tweak '{name}'")
    meta = reg[name]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    if args.apply:
        if "file" in meta:
            target = Path(meta["file"])
            if target.exists():
                bak = BACKUP_DIR / name / f"{target.name}.{stamp}"
                bak.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, bak)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                (BACKUP_DIR / name).mkdir(parents=True, exist_ok=True)
                (BACKUP_DIR / name / f"{target.name}.{stamp}.ABSENT").write_text("")
            target.write_text(meta["content"])
        if "unit" in meta:
            _sh(["systemctl", "enable", "--now", meta["unit"]])
        if "post" in meta:
            _sh(meta["post"])
        state[name] = {"applied": stamp}
        _save_state(state)
        print(f"{GREEN}applied{RESET} {name}")
        return 0

    # revert
    if name not in state:
        sys.exit(f"sl-ctl: tweak '{name}' is not applied")
    if "file" in meta:
        target = Path(meta["file"])
        backups = sorted((BACKUP_DIR / name).glob(f"{target.name}.*"))
        if backups and backups[-1].name.endswith(".ABSENT"):
            target.unlink(missing_ok=True)
        elif backups:
            shutil.copy2(backups[-1], target)
    if "unit" in meta:
        _sh(["systemctl", "disable", "--now", meta["unit"]])
    if "post" in meta:
        _sh(meta["post"])
    del state[name]
    _save_state(state)
    print(f"reverted {name}")
    return 0


# ---------------------------------------------------------------------------
# thin wrappers  (EXPERIMENTAL — real logic lands in later phases)
# ---------------------------------------------------------------------------
def cmd_update(args) -> int:
    _need_root()
    rc = _sh(["pacman", "-Syu"]).returncode
    if shutil.which("paru"):
        _sh(["sudo", "-u", os.environ.get("SUDO_USER", "nobody"), "paru", "-Syu"])
    if shutil.which("flatpak"):
        _sh(["flatpak", "update"])
    return rc


def cmd_snapshot(args) -> int:
    if not shutil.which("snapper"):
        sys.exit("sl-ctl: snapper not installed (BTRFS only)")
    if args.create:
        return _sh(["snapper", "create", "-d", "sl-ctl manual"]).returncode
    if args.list:
        return _sh(["snapper", "list"]).returncode
    if args.rollback:
        _need_root()
        return _sh(["snapper", "rollback", args.rollback]).returncode
    return _sh(["snapper", "list"]).returncode


def cmd_mirror(args) -> int:
    _need_root()
    if not shutil.which("reflector"):
        sys.exit("sl-ctl: reflector not installed")
    return _sh(["reflector", "--latest", "20", "--sort", "rate",
                "--protocol", "https", "--save", "/etc/pacman.d/mirrorlist"]).returncode


def cmd_flavor(args) -> int:
    print("sl-ctl flavor: not yet implemented (Phase 6). "
          "Flavor package lists live in sabores/.")
    return 1


def cmd_welcome(args) -> int:
    if shutil.which("sl-welcome"):
        return _sh(["sl-welcome"]).returncode
    print("sl-ctl welcome: sl-welcome not installed (Phase 7).")
    return 1


# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sl-ctl", description="Static Linux management")
    p.add_argument("--version", action="version", version=f"sl-ctl {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("detect", help="run sl-detect and show the result").set_defaults(fn=cmd_detect)
    sub.add_parser("info", help="branded system info").set_defaults(fn=cmd_info)
    sub.add_parser("update", help="full system update (pacman + AUR + Flatpak)").set_defaults(fn=cmd_update)
    sub.add_parser("mirror", help="refresh mirrorlist with reflector").set_defaults(fn=cmd_mirror)
    sub.add_parser("welcome", help="relaunch sl-welcome").set_defaults(fn=cmd_welcome)

    t = sub.add_parser("tweaks", help="reversible system tweaks")
    t.add_argument("--list", action="store_true")
    t.add_argument("--apply", metavar="NAME")
    t.add_argument("--revert", metavar="NAME")
    t.set_defaults(fn=cmd_tweaks)

    s = sub.add_parser("snapshot", help="Snapper snapshots")
    s.add_argument("--create", action="store_true")
    s.add_argument("--list", action="store_true")
    s.add_argument("--rollback", metavar="ID")
    s.set_defaults(fn=cmd_snapshot)

    f = sub.add_parser("flavor", help="add/remove flavors post-install")
    f.add_argument("--add", metavar="FLAVOR")
    f.add_argument("--remove", metavar="FLAVOR")
    f.set_defaults(fn=cmd_flavor)

    pr = sub.add_parser("privacy", help="show or change the privacy profile")
    pr.add_argument("--profile", metavar="basic|improved|maximum")
    pr.set_defaults(fn=cmd_privacy)

    ac = sub.add_parser("accent", help="show or change the accent colour")
    ac.add_argument("name", nargs="?", metavar="purple|blue|green|...")
    ac.add_argument("--list", action="store_true", help="list available accents")
    ac.set_defaults(fn=cmd_accent)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
