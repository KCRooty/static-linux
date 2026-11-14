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

__version__ = "0.3.0"

STATE_DIR = Path("/var/lib/static-linux")
BACKUP_DIR = Path("/var/backups/static-linux/tweaks")
SL_DETECT = "/usr/lib/static-linux/sl-detect/detect.py"
PRIVACY_DIR = Path("/usr/lib/static-linux/privacidad")
ACCENT_DIR = Path("/usr/lib/static-linux/accents")

GREEN = "\033[1;38;5;43m"   # Signal Green-ish for a 256-color terminal
DIM = "\033[2m"
AMBER = "\033[38;5;214m"  # warnings, the offline ISO color
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
    # the profile's tools (firejail, usbguard, tor…) — not its kernel, which
    # stays whatever the machine boots now
    lst = {"perfil-basico": "privacy-basic", "perfil-mejorado": "privacy-enhanced",
           "perfil-maximo": "privacy-max"}[folder]
    lst_path = _flavor_lists_dir() / f"{lst}.list"
    if lst_path.exists():
        pkgs = [x.strip() for x in lst_path.read_text().splitlines()
                if x.strip() and not x.lstrip().startswith("#") and not x.strip().startswith("linux")]
        if pkgs:
            rc = _sh(["pacman", "-S", "--needed", "--noconfirm", *pkgs]).returncode
            if rc != 0:
                return rc
    return _sh(["bash", str(apply_sh)]).returncode


# ---------------------------------------------------------------------------
# audit  (what talks to the network, right now)
# ---------------------------------------------------------------------------
def _sockets(listening: bool) -> list[tuple[str, str, str]]:
    """(local, peer, process) from ss, loopback and link-local left out."""
    cmd = ["ss", "-Htunp"] + (["-l"] if listening else ["state", "established"])
    col = 4 if listening else 3  # a state filter drops ss's State column
    rows = []
    for line in _out(cmd).splitlines():
        parts = line.split()
        if len(parts) <= col + 1:
            continue
        local, peer = parts[col], parts[col + 1]
        host = (local if listening else peer).rsplit(":", 1)[0].strip("[]").split("%")[0]
        if host.startswith(("127.", "::1", "fe80:")) or host == "::ffff:127.0.0.1":
            continue
        proc = line.split('users:(("', 1)[1].split('"', 1)[0] if 'users:(("' in line else "?"
        rows.append((local, peer, proc))
    return rows


def cmd_audit(args) -> int:
    print(f"{GREEN}sl-ctl audit{RESET}")
    if os.geteuid() != 0:
        print(DIM + _("Sin sudo no se ven los procesos de otros usuarios ni de root.") + RESET)
    listen = _sockets(True)
    print(_row(_("Escuchando fuera"), ", ".join(f"{l} ({p})" for l, _x, p in listen) or _("nada")))
    out = _sockets(False)
    print(_row(_("Conexiones"), str(len(out))))
    for local, peer, proc in out:
        print(f"    {peer:<44} {proc}")
    resolv = _read("/etc/resolv.conf")
    servers = [ln.split()[1] for ln in resolv.splitlines() if ln.startswith("nameserver")]
    dns_ok = servers and all(x.startswith("127.") or x == "::1" for x in servers)
    print(_row("DNS", (", ".join(servers) or "?") + "  " +
               (_("(cifrado, dnscrypt-proxy)") if dns_ok and _active("dnscrypt-proxy.service")
                else _("(sin cifrar)"))))
    print(_row(_("Cortafuegos"), "ufw " + (_("activo") if _ufw_active() else _("desactivado"))))
    timers = [t for t in _out(["systemctl", "list-timers", "--no-legend", "--plain"]).split()
              if t.endswith(".timer")]
    print(_row(_("Temporizadores"), ", ".join(timers) or _("ninguno")))
    print()
    print(DIM + _("Static Linux no envía telemetría. Las conexiones de arriba son tuyas: navegador, actualizaciones que lances, sincronización de hora (NTP).") + RESET)
    return 0


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
# server  (Server/Homelab flavor: nothing listens until it is turned on here)
# ---------------------------------------------------------------------------
SERVER_SERVICES = {
    # name: (unit, package, firewall ports)
    "ssh": ("sshd.service", "openssh", ["22/tcp"]),
    "cockpit": ("cockpit.socket", "cockpit", ["9090/tcp"]),
    "docker": ("docker.socket", "docker", []),
    "nginx": ("nginx.service", "nginx", ["80/tcp", "443/tcp"]),
    "mariadb": ("mariadb.service", "mariadb", []),
    "fail2ban": ("fail2ban.service", "fail2ban", []),
    "wireguard": ("wg-quick@wg0.service", "wireguard-tools", ["51820/udp"]),
}


def _installed(pkg: str) -> bool:
    return _sh(["pacman", "-Q", pkg], capture_output=True).returncode == 0


def _ufw_active() -> bool:
    # `ufw status` needs root; without it, read the config ufw itself reads at boot.
    if os.geteuid() == 0:
        return "Status: active" in _out(["ufw", "status"])
    try:
        with open("/etc/ufw/ufw.conf") as f:
            enabled = any(l.strip() == "ENABLED=yes" for l in f)
    except OSError:
        return False
    return enabled and _active("ufw.service")


def _server_status() -> int:
    print(f"{GREEN}sl-ctl server{RESET}")
    for name, (unit, pkg, ports) in SERVER_SERVICES.items():
        if not _installed(pkg):
            state = DIM + _("no instalado") + RESET
        elif _active(unit):
            state = _("activo")
        else:
            state = _("parado")
        extra = f"  {DIM}{', '.join(ports)}{RESET}" if ports else ""
        print(_row(name, state + extra))
    listening = _out(["ss", "-tulnH"])
    public = [l.split()[4] for l in listening.splitlines()
              if len(l.split()) > 4 and not l.split()[4].startswith(("127.", "[::1]", "::1", "[fe80"))]
    print(_row(_("Escuchando"), ", ".join(sorted(set(public))) or _("nada")))
    print(_row(_("Cortafuegos"), "ufw " + (_("activo") if _ufw_active() else _("desactivado"))))
    print()
    print(DIM + _("Activar: sudo sl-ctl server on <servicio> · apagar: sudo sl-ctl server off <servicio>") + RESET)
    return 0


def _server_on(name: str) -> int:
    unit, pkg, ports = SERVER_SERVICES[name]
    if not _installed(pkg):
        print(_("{pkg} no está instalado: sudo pacman -S {pkg}").format(pkg=pkg))
        return 1
    if name == "mariadb" and not any(Path("/var/lib/mysql").glob("mysql")):
        _sh(["mariadb-install-db", "--user=mysql", "--basedir=/usr", "--datadir=/var/lib/mysql"],
            capture_output=True)
    if name == "wireguard" and not Path("/etc/wireguard/wg0.conf").exists():
        print(_("Falta /etc/wireguard/wg0.conf: créalo primero (wiki: Servidor)."))
        return 1
    if _sh(["systemctl", "enable", "--now", unit]).returncode != 0:
        return 1
    if name == "docker":
        user = _invoking_user()
        if user:
            _sh(["usermod", "-aG", "docker", user])
            print(_("{user} está en el grupo docker (vale desde el próximo inicio de sesión).").format(user=user))
    for port in ports:
        if _ufw_active():
            _sh(["ufw", "allow", port, "comment", f"sl-ctl server {name}"], capture_output=True)
            print(_("Cortafuegos: {port} abierto.").format(port=port))
        else:
            print(_("Cortafuegos desactivado: {port} queda accesible desde la red.").format(port=port))
    print(_("{name}: activo.").format(name=name))
    return 0


def _server_off(name: str) -> int:
    unit, _pkg, ports = SERVER_SERVICES[name]
    _sh(["systemctl", "disable", "--now", unit], capture_output=True)
    if unit.endswith(".socket"):  # the socket can leave its service running
        _sh(["systemctl", "stop", unit.replace(".socket", ".service")], capture_output=True)
    for port in ports:
        if shutil.which("ufw"):
            _sh(["ufw", "delete", "allow", port], capture_output=True)
    print(_("{name}: parado y sin puertos abiertos.").format(name=name))
    return 0


def cmd_server(args) -> int:
    if args.action in ("on", "off"):
        if args.service not in SERVER_SERVICES:
            print(_("Servicios: {names}").format(names=", ".join(SERVER_SERVICES)))
            return 2
        _need_root()
        return _server_on(args.service) if args.action == "on" else _server_off(args.service)
    return _server_status()


# ---------------------------------------------------------------------------
# thin wrappers  (EXPERIMENTAL — real logic lands in later phases)
# ---------------------------------------------------------------------------
def cmd_update(args) -> int:
    _need_root()
    if Path("/etc/snapper/configs/root").exists() and Path("/usr/share/libalpm/hooks/05-snap-pac-pre.hook").exists():
        print(DIM + _("Instantánea antes y después de actualizar (snap-pac): si algo sale mal, sl-ctl snapshot --rollback <n>") + RESET)
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
    if not Path("/etc/snapper/configs/root").exists():
        sys.exit("sl-ctl: " + _("no hay instantáneas: el sistema no está en BTRFS o Snapper no está configurado"))
    if args.create:
        _need_root()
        return _sh(["snapper", "create", "-c", "number", "-d", "sl-ctl manual",
                    "--userdata", "important=yes"]).returncode
    if args.rollback:
        # The installer mounts subvol=@ explicitly, so `snapper rollback`
        # (new default subvolume) would change nothing at the next boot.
        # undochange puts the files back as they were in that snapshot.
        _need_root()
        snap = args.rollback
        print(_("Se devolverán los archivos del sistema al estado de la instantánea {n}.").format(n=snap))
        print(_("Antes se crea otra instantánea, por si quieres volver a lo de ahora."))
        _sh(["snapper", "create", "-c", "number", "-d", f"sl-ctl antes de deshacer hasta {snap}"])
        rc = _sh(["snapper", "undochange", f"{snap}..0"]).returncode
        if rc == 0:
            print(_("Hecho. Reinicia para que todo cargue la versión restaurada."))
        return rc
    return _sh(["snapper", "list"]).returncode


def cmd_mirror(args) -> int:
    _need_root()
    if not shutil.which("reflector"):
        sys.exit("sl-ctl: " + _("reflector no está instalado"))
    return _sh(["reflector", "--latest", "20", "--sort", "rate",
                "--protocol", "https", "--save", "/etc/pacman.d/mirrorlist"]).returncode


# ---------------------------------------------------------------------------
# flavor  (same package lists the installer uses: packages/lists/sabor-*.list)
# ---------------------------------------------------------------------------
FLAVORS = ("gaming", "content-creation", "development", "cybersecurity",
           "office", "server", "vm", "education")
FLAVOR_LISTS = Path("/usr/lib/static-linux/packages/lists")
FLAVOR_STATE = Path("/etc/static-linux/flavors")
FLAVOR_GROUPS = {"gaming": ["gamemode"], "content-creation": ["realtime"],
                 "development": ["docker"], "vm": ["libvirt"]}
FLAVOR_SOCKETS = {"development": ["docker.socket"], "vm": ["libvirtd.socket"]}
NTSYNC = Path("/etc/modules-load.d/ntsync.conf")
FLATHUB = "https://dl.flathub.org/repo/flathub.flatpakrepo"


def _flavor_lists_dir() -> Path:
    if FLAVOR_LISTS.is_dir():
        return FLAVOR_LISTS
    return Path(__file__).resolve().parents[1] / "packages" / "lists"


def _flavor_parse(slug: str) -> tuple[list[str], list[str], list[str]]:
    """(official packages, Flathub ids, AUR packages) of one flavor."""
    pkgs, flatpaks, aur = [], [], []
    for raw in (_flavor_lists_dir() / f"sabor-{slug}.list").read_text().splitlines():
        line = raw.strip()
        if line.startswith("# flatpak:"):
            flatpaks.append(line.split(":", 1)[1].strip())
        elif line.startswith("#") and line.endswith("(AUR)"):
            aur.append(line[1:-5].strip())
        elif line and not line.startswith("#"):
            pkgs.append(line)
    return pkgs, flatpaks, aur


def _flavors_installed() -> list[str]:
    try:
        return [x for x in FLAVOR_STATE.read_text().split() if x in FLAVORS]
    except OSError:
        return []


def _flavors_save(slugs: list[str]) -> None:
    FLAVOR_STATE.parent.mkdir(parents=True, exist_ok=True)
    FLAVOR_STATE.write_text("".join(f"{x}\n" for x in slugs))


def _gpu_lib32() -> list[str]:
    """32-bit Vulkan driver for the GPU sl-detect finds (the installer does the same)."""
    out = _sh([sys.executable, _sl_detect_path(), "--json"], capture_output=True)
    try:
        driver = (json.loads(out.stdout).get("gpu") or {}).get("driver", "").lower()
    except (ValueError, AttributeError):
        return []
    if "nvidia" in driver and "nouveau" not in driver:
        return ["lib32-nvidia-utils"]
    if "amdgpu" in driver or "radeon" in driver:
        return ["lib32-vulkan-radeon"]
    if "i915" in driver or driver == "xe" or "intel" in driver:
        return ["lib32-vulkan-intel"]
    return []


FLAVOR_PENDING = Path("/etc/static-linux/pending-flavors")


def _flavors_pending() -> list[str]:
    """Flavors picked in an installer with no network (universal ISO, offline)."""
    try:
        return [x for x in FLAVOR_PENDING.read_text().split() if x in FLAVORS]
    except OSError:
        return []


def _flavor_pending_done(slug: str) -> None:
    left = [x for x in _flavors_pending() if x != slug]
    try:
        if left:
            FLAVOR_PENDING.write_text("\n".join(left) + "\n")
        elif FLAVOR_PENDING.exists():
            FLAVOR_PENDING.unlink()
    except OSError:
        pass


def _flavor_list() -> int:
    have, pending = _flavors_installed(), _flavors_pending()
    print(f"{GREEN}sl-ctl flavor{RESET}")
    for slug in FLAVORS:
        if slug in have:
            mark = _("instalado")
        elif slug in pending:
            mark = AMBER + _("pendiente (instalación sin red)") + RESET
        else:
            mark = DIM + "-" + RESET
        print(_row(slug, mark))
    print()
    if pending:
        print(AMBER + _("Con conexión: sudo sl-ctl flavor add pending") + RESET)
    print(DIM + _("Añadir: sudo sl-ctl flavor add <sabor> · quitar: sudo sl-ctl flavor remove <sabor>") + RESET)
    return 0


def _flavor_add(slug: str) -> int:
    _need_root()
    pkgs, flatpaks, aur = _flavor_parse(slug)
    if slug == "gaming":
        pkgs += [p for p in _gpu_lib32() if p not in pkgs]
    print(_("Instalando el sabor {name}: {n} paquetes").format(name=slug, n=len(pkgs)))
    # -Syu, never a bare -S: after an offline install the system is still at
    # the ISO's snapshot, and new packages from today's mirrors would be a
    # partial upgrade
    rc = _sh(["pacman", "-Syu", "--needed", "--noconfirm", *pkgs]).returncode
    if rc != 0:
        return rc
    _flavor_pending_done(slug)
    if flatpaks and shutil.which("flatpak"):
        _sh(["flatpak", "remote-add", "--if-not-exists", "--system", "flathub", FLATHUB])
        for app in flatpaks:
            if _sh(["flatpak", "install", "--system", "--noninteractive", "-y", "flathub", app]).returncode != 0:
                print("sl-ctl: " + _("no se pudo instalar {app} desde Flathub").format(app=app), file=sys.stderr)
    user = _invoking_user()
    for group in FLAVOR_GROUPS.get(slug, []):
        _sh(["groupadd", "-f", group])
        if user:
            _sh(["usermod", "-aG", group, user])
    for unit in FLAVOR_SOCKETS.get(slug, []):
        _sh(["systemctl", "enable", "--now", unit])
    if slug == "gaming":
        NTSYNC.parent.mkdir(parents=True, exist_ok=True)
        NTSYNC.write_text("# Static Linux gaming flavor: Wine/Proton NT sync primitives\nntsync\n")
        _sh(["modprobe", "ntsync"], stderr=subprocess.DEVNULL)
        if Path("/sys/kernel/sched_ext").exists():
            _perf_scheduler("lavd")
    if aur:
        if shutil.which("paru") and user:
            _sh(["sudo", "-u", user, "paru", "-S", "--needed", *aur])
        else:
            print(_("Del AUR, con tu usuario:") + f" paru -S {' '.join(aur)}")
    have = _flavors_installed()
    _flavors_save(have + [slug] if slug not in have else have)
    if FLAVOR_GROUPS.get(slug):
        print(_("Cierra la sesión y vuelve a entrar para usar los grupos nuevos."))
    print(_("Sabor {name} instalado.").format(name=slug))
    return 0


def _flavor_remove(slug: str) -> int:
    _need_root()
    pkgs, flatpaks, _aur = _flavor_parse(slug)
    if slug == "gaming":
        pkgs += _gpu_lib32()
    keep: set[str] = set()
    for other in _flavors_installed():
        if other != slug:
            keep.update(_flavor_parse(other)[0])
    # never take away what the base system or the desktop installed
    for lst in _flavor_lists_dir().glob("*.list"):
        if not lst.name.startswith("sabor-"):
            keep.update(x.strip() for x in lst.read_text().splitlines()
                        if x.strip() and not x.lstrip().startswith("#"))
    installed = set(_sh(["pacman", "-Qq"], capture_output=True).stdout.split())
    targets = [p for p in pkgs if p in installed and p not in keep]
    for unit in FLAVOR_SOCKETS.get(slug, []):
        _sh(["systemctl", "disable", "--now", unit])
    if slug == "gaming":
        if shutil.which("scx_loader"):
            _perf_scheduler("off")
        NTSYNC.unlink(missing_ok=True)
    rc = 0
    if targets:
        # -u: whatever another package still needs stays; config files are kept (.pacsave)
        rc = _sh(["pacman", "-Rsu", "--noconfirm", *targets]).returncode
    if flatpaks and shutil.which("flatpak"):
        for app in flatpaks:
            _sh(["flatpak", "uninstall", "--system", "--noninteractive", "-y", app],
                stderr=subprocess.DEVNULL)
    _flavors_save([x for x in _flavors_installed() if x != slug])
    print(_("Sabor {name} quitado.").format(name=slug))
    return rc


def cmd_flavor(args) -> int:
    action, name = args.action, args.name
    if args.add:
        action, name = "add", args.add
    elif args.remove:
        action, name = "remove", args.remove
    if action in (None, "list"):
        return _flavor_list()
    if action == "add" and name == "pending":
        rc = 0
        for slug in _flavors_pending():
            rc = _flavor_add(slug) or rc
        return rc
    if action not in ("add", "remove") or not name:
        sys.exit("sl-ctl: " + _("uso: sl-ctl flavor [list | add <sabor> | remove <sabor>]"))
    if name not in FLAVORS:
        sys.exit("sl-ctl: " + _("sabor desconocido: {name}").format(name=name) + f" ({', '.join(FLAVORS)})")
    return _flavor_add(name) if action == "add" else _flavor_remove(name)


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
    s.add_argument("--rollback", metavar="ID", help=_("devuelve los archivos del sistema a esa instantánea"))
    s.set_defaults(fn=cmd_snapshot)

    f = sub.add_parser("flavor", help=_("añade o quita sabores"))
    f.add_argument("action", nargs="?", choices=["list", "add", "remove"])
    f.add_argument("name", nargs="?", metavar="FLAVOR")
    f.add_argument("--add", metavar="FLAVOR")
    f.add_argument("--remove", metavar="FLAVOR")
    f.set_defaults(fn=cmd_flavor)

    sub.add_parser("audit", help=_("qué se conecta a la red ahora mismo")).set_defaults(fn=cmd_audit)

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

    sv = sub.add_parser("server", help=_("servidor: estado de los servicios y activarlos o apagarlos"))
    sv.add_argument("action", nargs="?", choices=("status", "on", "off"), default="status")
    sv.add_argument("service", nargs="?", metavar="ssh|cockpit|docker|nginx|mariadb|fail2ban|wireguard")
    sv.set_defaults(fn=cmd_server)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
