#!/bin/bash
# Static Linux — build the local pacman repo the ISO build pulls from.
#
#   packages/local-repo.sh            build every package below, refresh the repo
#   packages/local-repo.sh calamares  build just that one
#
# Run as your normal user (makepkg refuses root). Build dependencies must
# already be installed — this never calls sudo:
#
#   sudo pacman -S --needed base-devel cmake extra-cmake-modules ninja pybind11 \
#       qt6-tools qt6-translations libglvnd kcoreaddons kpmcore libpwquality \
#       qt6-declarative qt6-svg yaml-cpp
#
# Output: packages/aur-cache/ (gitignored) — the built packages plus the
# `staticlinux-local` repo database. iso/build.sh adds that directory to the
# ISO profile's pacman.conf, which is how packages that aren't in the
# official repos (calamares, staticlinux-base) become pacstrap-able.
#
# Packages with a PKGBUILD under packages/ are built from this checkout.
# The ones in AUR_PKGS are built from the AUR instead, cloned fresh so the
# ISO always carries the current release:
#   brave-origin-bin  the default browser. This is Brave's own AUR package
#                     (maintainer "brave") — the same thing Brave's official
#                     install.sh installs on Arch through an AUR helper.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$HERE/aur-cache"
REPO_NAME="staticlinux-local"
AUR_PKGS=(brave-origin-bin)
PKGS=("$@")
[[ ${#PKGS[@]} -gt 0 ]] || PKGS=(calamares staticlinux-base "${AUR_PKGS[@]}")

log() { printf '\033[1;38;5;43m[local-repo]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[local-repo]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -ne 0 ]] || die "run as a normal user — makepkg refuses root"
mkdir -p "$REPO_DIR"

for pkg in "${PKGS[@]}"; do
    src="$HERE/$pkg"
    if [[ ! -f "$src/PKGBUILD" ]]; then
        [[ " ${AUR_PKGS[*]} " == *" $pkg "* ]] \
            || die "no PKGBUILD for '$pkg' in packages/, and it isn't in AUR_PKGS"
        src="$REPO_DIR/.aur/$pkg"
        log "fetching $pkg from the AUR"
        rm -rf "$src"
        git clone --quiet --depth 1 "https://aur.archlinux.org/$pkg.git" "$src"
    fi
    log "building $pkg"
    # Keep src/ and pkg/ out of the checkout; drop older builds of this
    # package so the repo holds exactly one version of each.
    rm -f "$REPO_DIR/$pkg"-[0-9]*.pkg.tar.zst
    (
        cd "$src"
        saved="$(mktemp)"; cp PKGBUILD "$saved"
        # makepkg rewrites pkgver= in place when a pkgver() function exists
        trap 'cp "$saved" PKGBUILD; rm -f "$saved"' EXIT
        BUILDDIR="${BUILDDIR:-$REPO_DIR/.build}" PKGDEST="$REPO_DIR" \
            makepkg --force --clean
    )
done

log "refreshing $REPO_NAME database"
rm -f "$REPO_DIR/$REPO_NAME".{db,files}*
repo-add --quiet "$REPO_DIR/$REPO_NAME.db.tar.zst" "$REPO_DIR"/*.pkg.tar.zst
log "done -> $REPO_DIR"
