"""Static Linux — shared helpers for the installer's Python jobs.

Lives in /etc/calamares/lib on the live ISO; each job adds that folder to
sys.path. One place for "install packages into the target", so basepkgs,
entorno-pkgs, privacidad-apply and sabores all see the same repositories:

  /opt/staticlinux-repo     our own packages (staticlinux-base, Brave, Astal…),
                            on every ISO
  /opt/staticlinux-offline  universal ISO only: base system, every desktop,
                            the kernels and the privacy tools, downloaded when
                            the ISO was built

When the offline repository is there, the base system and the desktop come
from it and nothing else — same snapshot, no network needed, and no mixing
with newer packages from the mirrors halfway through. With a network, the
target is brought up to date (`pacman -Syu`) before the flavors are added.
"""

import os
import socket
import subprocess

import libcalamares

LIVE_REPO = "/opt/staticlinux-repo"
LIVE_REPO_NAME = "staticlinux-local"
OFFLINE_REPO = "/opt/staticlinux-offline"
OFFLINE_REPO_NAME = "staticlinux-offline"
HOST_CONF = "/tmp/sl-install-pacman.conf"     # for pacstrap, run from the live system
TARGET_CONF = "/tmp/sl-target-pacman.conf"    # inside the target, for chrooted pacman


def offline_repo() -> bool:
    return os.path.isfile(os.path.join(OFFLINE_REPO, f"{OFFLINE_REPO_NAME}.db"))


def _reachable(timeout: float) -> bool:
    for host in ("geo.mirror.pkgbuild.com", "mirrors.kernel.org"):
        try:
            with socket.create_connection((host, 443), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def online(timeout: float = 6.0) -> bool:
    """Can we reach the Arch mirrors? Cached in globalStorage after the first ask.

    In a thread with a deadline: with no network the DNS lookup ignores the
    socket timeout and can hang for a minute or two per host.
    """
    gs = libcalamares.globalstorage
    if gs.contains("slOnline"):
        return bool(gs.value("slOnline"))
    import threading
    result = []
    t = threading.Thread(target=lambda: result.append(_reachable(timeout / 2)), daemon=True)
    t.start()
    t.join(timeout)
    ok = bool(result and result[0])
    gs.insert("slOnline", ok)
    libcalamares.utils.debug(f"slinstall: network {'up' if ok else 'down'}, "
                             f"offline repo {'present' if offline_repo() else 'absent'}")
    return ok


def _options(conf_path: str) -> str:
    """The [options] section of a pacman.conf, without any repository."""
    out = []
    with open(conf_path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip().startswith("[") and line.strip() != "[options]":
                break
            out.append(line)
    return "".join(out)


def _repo(name: str, path: str) -> str:
    return f"\n[{name}]\nSigLevel = Optional TrustAll\nServer = file://{path}\n"


def host_conf() -> str | None:
    """pacman.conf for pacstrap when installing from the ISO's own packages."""
    if not offline_repo():
        return None
    text = _options("/etc/pacman.conf") + _repo(OFFLINE_REPO_NAME, OFFLINE_REPO)
    if os.path.isdir(LIVE_REPO):
        text += _repo(LIVE_REPO_NAME, LIVE_REPO)
    with open(HOST_CONF, "w", encoding="utf-8") as fh:
        fh.write(text)
    return HOST_CONF


def target_pacman(root: str, pkgs: list[str], use_mirrors: bool = False) -> int:
    """pacman -S --needed in the target, with the ISO's repositories bind-mounted in.

    use_mirrors=False (base, desktop, privacy tools): from the ISO when it
    carries the offline repo, otherwise from the mirrors as before.
    use_mirrors=True (flavors): the target's own repos plus our local one.
    """
    root = root.rstrip("/")
    mounts = []
    for src in (LIVE_REPO, OFFLINE_REPO):
        if not os.path.isdir(src):
            continue
        dst = root + src
        os.makedirs(dst, exist_ok=True)
        if subprocess.run(["mount", "--bind", "-o", "ro", src, dst]).returncode == 0:
            mounts.append(dst)
    target_conf = os.path.join(root, "etc/pacman.conf")
    if offline_repo() and not use_mirrors:
        text = _options(target_conf) + _repo(OFFLINE_REPO_NAME, OFFLINE_REPO)
    else:
        with open(target_conf, encoding="utf-8") as fh:
            text = fh.read()
    if os.path.isdir(LIVE_REPO):
        text += _repo(LIVE_REPO_NAME, LIVE_REPO)
    with open(root + TARGET_CONF, "w", encoding="utf-8") as fh:
        fh.write(text)
    try:
        return libcalamares.utils.target_env_call(
            ["pacman", "--config", TARGET_CONF, "-Sy", "--needed", "--noconfirm", *pkgs])
    finally:
        drop_cached_copies(root)
        for dst in mounts:
            subprocess.run(["umount", dst])
            try:
                os.rmdir(dst)   # /opt itself belongs to the filesystem package
            except OSError:
                pass
        try:
            os.remove(root + TARGET_CONF)
        except OSError:
            pass


def drop_cached_copies(root: str) -> None:
    """pacman copies every package it installs into the target's cache; the
    ones that came off the ISO would just sit there (~1.5 GB)."""
    if not offline_repo():
        return
    cache = os.path.join(root, "var/cache/pacman/pkg")
    try:
        names = os.listdir(cache)
    except OSError:
        return
    for name in names:
        base = name[:-4] if name.endswith(".sig") else name
        if os.path.exists(os.path.join(OFFLINE_REPO, base)) or \
           os.path.exists(os.path.join(LIVE_REPO, base)):
            try:
                os.remove(os.path.join(cache, name))
            except OSError:
                pass


def target_upgrade(root: str) -> int:
    """Bring a target installed from the ISO snapshot up to the mirrors' current state."""
    return libcalamares.utils.target_env_call(["pacman", "-Syu", "--noconfirm"])
