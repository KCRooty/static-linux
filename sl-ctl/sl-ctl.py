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
import pwd
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "i18n"))
try:
    from sl_i18n import _  # noqa: E402
except ImportError:  # running without the i18n folder
    def _(text: str) -> str:
        return text

__version__ = "0.2.0"

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
        sys.exit("sl-ctl: " + _("este comando necesita root (usa sudo)"))


def _invoking_user() -> str | None:
    """The non-root user who launched sl-ctl, or None if there isn't one.

    SUDO_USER alone is not enough: it is unset under pkexec (sl-welcome), doas,
    `su`, or a plain root shell. Try every hint, in order of reliability, and
    never fall back to a made-up account.
    """
    candidates: list[str | int] = []
    for var in ("SUDO_USER", "DOAS_USER"):
        if os.environ.get(var):
            candidates.append(os.environ[var])
    for var in ("PKEXEC_UID", "SUDO_UID"):
        if os.environ.get(var, "").isdigit():
            candidates.append(int(os.environ[var]))
    try:
        # Set by pam_loginuid at login and inherited across su/sudo/pkexec.
        loginuid = int(Path("/proc/self/loginuid").read_text().strip())
        if loginuid != 0xFFFFFFFF:
            candidates.append(loginuid)
    except (OSError, ValueError):
        pass

    for cand in candidates:
        try:
            entry = pwd.getpwuid(cand) if isinstance(cand, int) else pwd.getpwnam(cand)
        except KeyError:
            continue
        if entry.pw_uid != 0:
            return entry.pw_name
    return None


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


def _row(label: str, value) -> str:
    return f"  {GREEN}{label:<24}{RESET}{value}"


def cmd_info(args) -> int:
    try:
        report = json.loads(
            _sh(["python3", _sl_detect_path(), "--json"],
                capture_output=True).stdout
        )
    except (ValueError, subprocess.SubprocessError):
        report = {}

    profile = _("desconocido")
    pf = STATE_DIR / "privacy-profile"
    if pf.exists():
        profile = pf.read_text().strip()

    rec = report.get("recommend", {})
    gpu = report.get("gpu", {})
    print(f"""{GREEN}  ▞▚  Static Linux{RESET}  {DIM}by Static Forge · fast. private. yours.{RESET}

{_row(_("Kernel"), os.uname().release)}
{_row("CPU", report.get('cpu', {}).get('model', 'n/a'))}
{_row("RAM", f"{report.get('ram_mb', 0)} MB")}
{_row("GPU", f"{gpu.get('model', 'n/a')} ({gpu.get('driver', '?')})")}
{_row(_("Arquitectura"), f"{report.get('arch', 'n/a')} / {report.get('firmware', 'n/a')}")}
{_row(_("Disco"), report.get('storage', 'n/a'))}
{_row("Wayland", report.get('wayland', 'n/a'))}
{_row(_("Escritorio recomendado"), rec.get('env', 'n/a'))}
{_row(_("Privacidad"), profile)}
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
        print(pf.read_text().strip() if pf.exists() else _("desconocido"))
        return 0
    folder = mapping.get(args.profile.lower())
    if not folder:
        sys.exit("sl-ctl: " + _("perfil de privacidad desconocido: {name}").format(name=args.profile))
    apply_sh = PRIVACY_DIR / folder / "apply.sh"
    if not apply_sh.exists():
        local = Path(__file__).resolve().parents[1] / "privacidad" / folder / "apply.sh"
        apply_sh = local
    if not apply_sh.exists():
        sys.exit("sl-ctl: " + _("no se encuentra {path}").format(path=apply_sh))
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
        sys.exit("sl-ctl: " + _("no se encuentra la herramienta de acentos"))
    if args.list:
        return _sh(["bash", str(apply), "--list"]).returncode
    if not args.name:
        return _sh(["bash", str(apply), "--current"]).returncode
    if os.geteuid() != 0:
        sys.exit("sl-ctl: " + _("'accent <nombre>' necesita root (cambia /etc)"))
    return _sh(["bash", str(apply), args.name]).returncode


def _theme_tool() -> Path | None:
    for p in (Path("/usr/share/static-linux/themes/sl-theme"),
              Path(__file__).resolve().parents[1] / "branding" / "themes" / "sl-theme"):
        if p.exists():
            return p
    return None


def cmd_theme(args) -> int:
    """Wallpaper + palette + style for the whole look (DESIGN.md), via sl-theme."""
    tool = _theme_tool()
    if tool is None:
        sys.exit("sl-ctl: " + _("no se encuentra sl-theme"))
    if args.list or not args.name:
        return _sh(["python3", str(tool), "--list"]).returncode
    if os.geteuid() != 0:
        rc = _sh(["python3", str(tool), args.name]).returncode
        print("sl-ctl: " + _("con sudo también cambian la pantalla de inicio de sesión, GRUB y el arranque"))
        return rc
    # as root: the invoking user's desktop, then the machine-wide pieces
    rc = 0
    if os.environ.get("SUDO_USER"):
        rc = _sh(["python3", str(tool), args.name, "--user", os.environ["SUDO_USER"]]).returncode
    return rc or _sh(["python3", str(tool), args.name, "--system"]).returncode


# ---------------------------------------------------------------------------
# tweaks  (generic reversible file tweaks)
# ---------------------------------------------------------------------------
def _tweaks_registry() -> dict:
    """name -> {'desc', 'files': [...], 'apply': [...], 'check': cmd}."""
    # swappiness-10 and hdd-bfq are gone (2026-11-13): with zram as swap a
    # high swappiness is the right value, and every disk type already gets
    # its I/O scheduler from rendimiento/ (see `sl-ctl perf`).
    return {
        "trim-timer": {
            "desc": _("fstrim.timer semanal (solo SSD)"),
            "unit": "fstrim.timer",
        },
        "split-lock": {
            "desc": _("Volver a frenar los split locks (desactivado por rendimiento)"),
            "file": "/etc/sysctl.d/99-sl-split-lock.conf",
            "content": "kernel.split_lock_mitigate=1\n",
            "post": ["sysctl", "--system"],
        },
        "watchdog": {
            "desc": _("Volver a cargar los watchdogs de hardware (quitados por defecto)"),
            # same name in /etc shadows the vendor file (and its blacklist)
            "file": "/etc/modprobe.d/static-linux.conf",
            "content": "# sl-ctl tweak 'watchdog': shadows /usr/lib/modprobe.d/static-linux.conf,\n"
                       "# so iTCO_wdt / sp5100_tco load again (next boot).\n",
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
            mark = f"{GREEN}{_('aplicado')}{RESET}" if state.get(name) else "-"
            print(f"  {name:18} [{mark}]  {meta['desc']}")
        return 0

    _need_root()
    name = args.apply or args.revert
    if name not in reg:
        sys.exit("sl-ctl: " + _("ajuste desconocido: {name}").format(name=name))
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
        print(f"{GREEN}{_('aplicado')}{RESET} {name}")
        return 0

    # revert
    if name not in state:
        sys.exit("sl-ctl: " + _("el ajuste {name} no está aplicado").format(name=name))
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
    print(_("revertido: {name}").format(name=name))
    return 0


# ---------------------------------------------------------------------------
# perf  (rendimiento/: what the system is doing, and the two knobs)
# ---------------------------------------------------------------------------
SCX_CONF = Path("/etc/scx_loader/config.toml")
SCX_TEMPLATE = Path("/usr/share/static-linux/rendimiento/scx/config.toml")
SCHEDULERS = ("lavd", "bpfland", "cosmos", "flash", "rusty")
PROFILES = ("power-saver", "balanced", "performance")


def _read(path: str, default: str = "") -> str:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return default


def _out(cmd: list[str]) -> str:
    if not shutil.which(cmd[0]):
        return ""
    try:
        return _sh(cmd, capture_output=True, timeout=5).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def _active(unit: str) -> bool:
    return _out(["systemctl", "is-active", unit]) == "active"


def _perf_status() -> int:
    ext = Path("/sys/kernel/sched_ext")
    if not ext.exists():
        sched = _("el del kernel (este kernel no tiene sched_ext)")
    elif _read(str(ext / "state")) == "enabled":
        ops = _read(str(ext / "root/ops"), "sched_ext").split("_")  # lavd_1.1.4_x86_64_…
        sched = f"scx_{ops[0]} {ops[1]}" if len(ops) > 1 else f"scx_{ops[0]}"
    else:
        sched = _("el del kernel (EEVDF)")

    profile = _out(["powerprofilesctl", "get"]) or _("sin power-profiles-daemon")

    zram = []
    for line in _read("/proc/swaps").splitlines()[1:]:
        f = line.split()
        if len(f) >= 3:
            zram.append(f"{Path(f[0]).name} {int(f[2]) // 1024} MB")
    swap = ", ".join(zram) or _("ninguna")

    disks = []
    for q in sorted(Path("/sys/block").glob("*/queue/scheduler")):
        dev = q.parent.parent.name
        if dev.startswith(("loop", "zram", "ram", "dm-", "sr", "nbd", "md")):
            continue
        cur = next((w.strip("[]") for w in _read(str(q)).split() if w.startswith("[")), "?")
        disks.append(f"{dev} {cur}")

    print(f"{GREEN}  ▞▚  Static Linux{RESET}  {DIM}{_('rendimiento')}{RESET}\n")
    print(_row(_("Kernel"), os.uname().release))
    print(_row(_("Planificador de CPU"), sched))
    print(_row(_("Perfil de energía"), profile))
    print(_row("swap", swap))
    print(_row("swappiness", _read("/proc/sys/vm/swappiness", "?")))
    print(_row(_("Planificador de disco"), ", ".join(disks) or "-"))
    print(_row("earlyoom", _("activo") if _active("earlyoom.service") else _("parado")))
    print()
    # xgettext:no-python-format
    print(f"  {DIM}" + _("Juegos: en Steam pon  sl-game %command%  en las opciones de lanzamiento.") + RESET)
    return 0


def _perf_profile(name: str | None) -> int:
    if not shutil.which("powerprofilesctl"):
        sys.exit("sl-ctl: " + _("power-profiles-daemon no está instalado"))
    if not name:
        return _sh(["powerprofilesctl", "list"]).returncode
    if name not in PROFILES:
        sys.exit("sl-ctl: " + _("perfil desconocido: {name}").format(name=name)
                 + f" ({', '.join(PROFILES)})")
    return _sh(["powerprofilesctl", "set", name]).returncode


def _perf_scheduler(name: str | None) -> int:
    if not name:
        print(_("Planificadores: {list}, off").format(list=", ".join(SCHEDULERS)))
        print(_("lavd es el recomendado: sigue la carga solo y prioriza juegos, audio y escritorio."))
        return 0
    name = name.removeprefix("scx_")
    if name not in SCHEDULERS + ("off",):
        sys.exit("sl-ctl: " + _("planificador desconocido: {name}").format(name=name))
    _need_root()
    if name == "off":
        _sh(["systemctl", "disable", "--now", "scx_loader.service"])
        print(_("Vuelve el planificador del kernel."))
        return 0
    if not Path("/sys/kernel/sched_ext").exists():
        sys.exit("sl-ctl: " + _("este kernel no tiene sched_ext; usa linux-zen o linux"))
    if not shutil.which("scx_loader") or not shutil.which("scx_lavd"):
        rc = _sh(["pacman", "-S", "--needed", "--noconfirm", "scx-scheds", "scx-tools"]).returncode
        if rc != 0:
            return rc
    # backup like any tweak, then write the default the loader starts at boot
    if SCX_CONF.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = BACKUP_DIR / "scx" / f"config.toml.{stamp}"
        bak.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SCX_CONF, bak)
    text = SCX_TEMPLATE.read_text() if SCX_TEMPLATE.exists() else \
        'default_sched = "scx_lavd"\ndefault_mode = "Auto"\n'
    lines = [f'default_sched = "scx_{name}"' if ln.startswith("default_sched") else ln
             for ln in text.splitlines()]
    SCX_CONF.parent.mkdir(parents=True, exist_ok=True)
    SCX_CONF.write_text("\n".join(lines) + "\n")
    _sh(["systemctl", "enable", "scx_loader.service"])
    _sh(["systemctl", "restart", "scx_loader.service"])
    # the BPF program takes a few seconds to verify and attach
    import time
    for _i in range(30):
        if _read("/sys/kernel/sched_ext/state") == "enabled":
            break
        time.sleep(0.5)
    else:
        print("sl-ctl: " + _("el planificador no ha arrancado; mira  journalctl -u scx_loader"),
              file=sys.stderr)
        return 1
    print(_("Planificador: scx_{name} (también en el próximo arranque).").format(name=name))
    return 0


def cmd_perf(args) -> int:
    if args.what == "profile":
        return _perf_profile(args.value)
    if args.what == "scheduler":
        return _perf_scheduler(args.value)
    return _perf_status()


# ---------------------------------------------------------------------------
# thin wrappers  (EXPERIMENTAL — real logic lands in later phases)
# ---------------------------------------------------------------------------
def cmd_update(args) -> int:
    _need_root()
    rc = _sh(["pacman", "-Syu"]).returncode
    if shutil.which("paru"):
        user = _invoking_user()
        if user:
            _sh(["sudo", "-u", user, "paru", "-Syu"])
        else:
            # paru refuses to build as root, and there is no user to drop to.
            print("sl-ctl: " + _("AUR sin actualizar: no hay un usuario normal al que pasar. "
                  "Ejecuta `paru -Sua` con tu usuario."), file=sys.stderr)
    if shutil.which("flatpak"):
        _sh(["flatpak", "update"])
    return rc


def cmd_snapshot(args) -> int:
    if not shutil.which("snapper"):
        sys.exit("sl-ctl: " + _("snapper no está instalado (solo BTRFS)"))
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
        sys.exit("sl-ctl: " + _("reflector no está instalado"))
    return _sh(["reflector", "--latest", "20", "--sort", "rate",
                "--protocol", "https", "--save", "/etc/pacman.d/mirrorlist"]).returncode


def cmd_flavor(args) -> int:
    print("sl-ctl flavor: " + _("aún no está hecho; los sabores se añaden desde el catálogo de sl-welcome."))
    return 1


def cmd_welcome(args) -> int:
    if shutil.which("sl-welcome"):
        return _sh(["sl-welcome"]).returncode
    print("sl-ctl welcome: " + _("sl-welcome no está instalado."))
    return 1


# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sl-ctl", description=_("Gestión de Static Linux"))
    p.add_argument("--version", action="version", version=f"sl-ctl {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("detect", help=_("ejecuta sl-detect y muestra el resultado")).set_defaults(fn=cmd_detect)
    sub.add_parser("info", help=_("información del sistema")).set_defaults(fn=cmd_info)
    sub.add_parser("update", help=_("actualiza todo el sistema (pacman + AUR + Flatpak)")).set_defaults(fn=cmd_update)
    sub.add_parser("mirror", help=_("renueva los mirrors con reflector")).set_defaults(fn=cmd_mirror)
    sub.add_parser("welcome", help=_("abre otra vez sl-welcome")).set_defaults(fn=cmd_welcome)

    t = sub.add_parser("tweaks", help=_("ajustes del sistema reversibles"))
    t.add_argument("--list", action="store_true")
    t.add_argument("--apply", metavar="NAME")
    t.add_argument("--revert", metavar="NAME")
    t.set_defaults(fn=cmd_tweaks)

    s = sub.add_parser("snapshot", help=_("instantáneas de Snapper"))
    s.add_argument("--create", action="store_true")
    s.add_argument("--list", action="store_true")
    s.add_argument("--rollback", metavar="ID")
    s.set_defaults(fn=cmd_snapshot)

    f = sub.add_parser("flavor", help=_("añade o quita sabores"))
    f.add_argument("--add", metavar="FLAVOR")
    f.add_argument("--remove", metavar="FLAVOR")
    f.set_defaults(fn=cmd_flavor)

    pr = sub.add_parser("privacy", help=_("muestra o cambia el perfil de privacidad"))
    pr.add_argument("--profile", metavar="basic|improved|maximum")
    pr.set_defaults(fn=cmd_privacy)

    ac = sub.add_parser("accent", help=_("muestra o cambia el color de acento"))
    ac.add_argument("name", nargs="?", metavar="purple|blue|green|...")
    ac.add_argument("--list", action="store_true", help=_("lista los acentos"))
    ac.set_defaults(fn=cmd_accent)

    th = sub.add_parser("theme", help=_("muestra o cambia el tema (fondo + paleta + estilo)"))
    th.add_argument("name", nargs="?", metavar="ambar|papel|aero|ventanas|...")
    th.add_argument("--list", action="store_true", help=_("lista los temas"))
    th.set_defaults(fn=cmd_theme)

    pf = sub.add_parser("perf", help=_("rendimiento: estado, perfil de energía y planificador de CPU"))
    pf.add_argument("what", nargs="?", choices=("status", "profile", "scheduler"), default="status")
    pf.add_argument("value", nargs="?", metavar="performance|lavd|off|...")
    pf.set_defaults(fn=cmd_perf)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
