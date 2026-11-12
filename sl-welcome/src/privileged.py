"""
Runs the two things in sl-welcome that need root, via pkexec so the GTK app
never has to ask for a password itself.

CRITICAL RULE (docs/PROYECTO.md): no irreversible changes. Both actions here just
call scripts that already do their own backup — privacidad/*/apply.sh backs
up to /var/backups/static-linux/privacy/, pacman itself is the reversible
part for package installs (`pacman -R` undoes it).
"""

from __future__ import annotations

import shutil
import subprocess

from paths import apply_profile_wrapper_path, privacy_profile_apply_path

PROFILE_FOLDERS = {
    "basico": "perfil-basico",
    "mejorado": "perfil-mejorado",
    "maximo": "perfil-maximo",
}


class PrivilegedActionError(RuntimeError):
    pass


def _pkexec_run(cmd: list[str]) -> subprocess.CompletedProcess:
    if not shutil.which("pkexec"):
        raise PrivilegedActionError(
            "pkexec no está instalado. Instala 'polkit' para aplicar cambios de sistema."
        )
    return subprocess.run(["pkexec", *cmd], capture_output=True, text=True)


def apply_privacy_profile(profile: str) -> subprocess.CompletedProcess:
    folder = PROFILE_FOLDERS.get(profile)
    if not folder:
        raise PrivilegedActionError(f"perfil de privacidad desconocido: {profile}")

    wrapper = apply_profile_wrapper_path()
    if wrapper:
        return _pkexec_run([str(wrapper), profile])

    script = privacy_profile_apply_path(folder)
    if not script.exists():
        raise PrivilegedActionError(f"no encuentro {script}")
    return _pkexec_run(["bash", str(script)])


def install_packages(pkgs: list[str]) -> subprocess.CompletedProcess:
    if not pkgs:
        raise PrivilegedActionError("no hay paquetes seleccionados")
    return _pkexec_run(["pacman", "-S", "--needed", "--noconfirm", *pkgs])
