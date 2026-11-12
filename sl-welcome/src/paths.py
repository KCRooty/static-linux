"""
Path resolution shared by sl-welcome's pages.

Same "installed path, else repo-relative" pattern sl-ctl.py uses — sl-welcome
has to work both from a pacman install (/usr/lib/static-linux/...) and from a
git checkout during development.
"""

from __future__ import annotations

from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
MODULE_DIR = SRC_DIR.parent  # .../sl-welcome

SL_DETECT_INSTALLED = Path("/usr/lib/static-linux/sl-detect/detect.py")
ACCENT_APPLY_INSTALLED = Path("/usr/lib/static-linux/accents/apply.sh")
ACCENT_PALETTE_INSTALLED = Path("/usr/lib/static-linux/accents/palette.conf")
PRIVACY_DIR_INSTALLED = Path("/usr/lib/static-linux/privacidad")
APPLY_PROFILE_WRAPPER_INSTALLED = Path("/usr/lib/static-linux/sl-welcome/apply-profile")
SF_PKGBUILDS_INSTALLED = Path("/usr/lib/static-linux/packages/sf")
THEMES_INSTALLED = Path("/usr/share/static-linux/themes")


def _repo_root() -> Path | None:
    root = MODULE_DIR.parent
    return root if (root / "sl-detect").is_dir() else None


def sl_detect_path() -> Path:
    if SL_DETECT_INSTALLED.exists():
        return SL_DETECT_INSTALLED
    root = _repo_root()
    if root:
        return root / "sl-detect" / "detect.py"
    return SL_DETECT_INSTALLED


def accent_apply_path() -> Path:
    if ACCENT_APPLY_INSTALLED.exists():
        return ACCENT_APPLY_INSTALLED
    root = _repo_root()
    if root:
        return root / "branding" / "accents" / "apply.sh"
    return ACCENT_APPLY_INSTALLED


def accent_palette_path() -> Path:
    if ACCENT_PALETTE_INSTALLED.exists():
        return ACCENT_PALETTE_INSTALLED
    root = _repo_root()
    if root:
        return root / "branding" / "accents" / "palette.conf"
    return ACCENT_PALETTE_INSTALLED


def privacy_profile_apply_path(folder: str) -> Path:
    installed = PRIVACY_DIR_INSTALLED / folder / "apply.sh"
    if installed.exists():
        return installed
    root = _repo_root()
    if root:
        return root / "privacidad" / folder / "apply.sh"
    return installed


def apply_profile_wrapper_path() -> Path | None:
    """The polkit-registered wrapper (see data/apply-profile). None in a dev
    checkout — the caller falls back to invoking the profile's apply.sh
    directly, just without the nicer pkexec dialog."""
    return APPLY_PROFILE_WRAPPER_INSTALLED if APPLY_PROFILE_WRAPPER_INSTALLED.exists() else None


def catalog_dir() -> Path:
    return MODULE_DIR / "catalog"


def sf_pkgbuild_dir(name: str) -> Path:
    """Folder holding the PKGBUILD of a Static Forge app (packages/sf/<name>)."""
    installed = SF_PKGBUILDS_INSTALLED / name
    if installed.is_dir():
        return installed
    root = _repo_root()
    if root:
        return root / "packages" / "sf" / name
    return installed


def themes_dir() -> Path:
    """branding/themes (sl-theme + one folder per theme)."""
    if (THEMES_INSTALLED / "sl-theme").is_file():
        return THEMES_INSTALLED
    root = _repo_root()
    if root:
        return root / "branding" / "themes"
    return THEMES_INSTALLED
