#!/bin/bash
# Static Linux — build the local pacman repo the ISO build pulls from.
#
#   packages/local-repo.sh            build every package below, refresh the repo
#   packages/local-repo.sh calamares  build just that one
#   (calamares, staticlinux-base, staticlinux-fonts: PKGBUILDs under packages/)
#
# Run as your normal user (makepkg refuses root). Build dependencies must
# already be installed. Only the Astal chain (CHROOT_AUR_PKGS) uses sudo, for
# the devtools build chroot; everything else is plain makepkg:
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
# Astal (the Hyprland shell): AUR-only, -git packages that build against each
# other, so they're built in dependency order inside a clean devtools chroot
# whose pacman.conf includes this local repo — nothing gets installed on the build host.
# Needs `devtools` and sudo (makechrootpkg mounts the chroot).
CHROOT_AUR_PKGS=(paru-bin appmenu-glib-translator-git libastal-io-git libastal-git libastal-4-git
                 libastal-hyprland-git libastal-tray-git libastal-wireplumber-git
                 libastal-network-git libastal-battery-git aylurs-gtk-shell)
PKGS=("$@")
[[ ${#PKGS[@]} -gt 0 ]] || PKGS=(calamares staticlinux-base staticlinux-fonts staticlinux-keyring "${AUR_PKGS[@]}"
                                  "${CHROOT_AUR_PKGS[@]}")

log() { printf '\033[1;38;5;43m[local-repo]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[local-repo]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -ne 0 ]] || die "run as a normal user — makepkg refuses root"
mkdir -p "$REPO_DIR"

refresh_db() {
    rm -f "$REPO_DIR/$REPO_NAME".{db,files}*
    repo-add --quiet "$REPO_DIR/$REPO_NAME.db.tar.zst" "$REPO_DIR"/*.pkg.tar.zst
}

CHROOT="$REPO_DIR/.chroot"
make_chroot() {
    [[ -d "$CHROOT/root" ]] && return 0
    command -v mkarchroot >/dev/null || die "install devtools for the Astal packages"
    log "creating the clean build chroot"
    mkdir -p "$CHROOT"
    cp /usr/share/devtools/pacman.conf.d/extra.conf "$CHROOT/pacman.conf"
    sudo mkarchroot -C "$CHROOT/pacman.conf" \
        -M /usr/share/devtools/makepkg.conf.d/x86_64.conf "$CHROOT/root" base-devel
    # arch-nspawn bind-mounts every file:// Server it finds in the chroot's
    # pacman.conf from the host, so the local repo is visible at its real path
    printf '\n[%s]\nSigLevel = Optional TrustAll\nServer = file://%s\n' \
        "$REPO_NAME" "$REPO_DIR" | sudo tee -a "$CHROOT/root/etc/pacman.conf" >/dev/null
}

build_in_chroot() {  # <aur pkg>: clone, build against the local repo, add it
    local pkg="$1" src="$REPO_DIR/.aur/$1"
    make_chroot
    log "fetching $pkg from the AUR"
    rm -rf "$src"
    git clone --quiet --depth 1 "https://aur.archlinux.org/$pkg.git" "$src"
    log "building $pkg (clean chroot)"
    # The old build is only replaced once the new one exists: these are -git
    # packages and upstream breaks now and then (libastal-tray, 2026-11-14) —
    # a failed build must leave the last good package in the repo.
    if ! (
        cd "$src"
        makechrootpkg -c -u -r "$CHROOT" -- --noconfirm
    ); then
        if ls "$REPO_DIR/$pkg"-[0-9r]*.pkg.tar.zst >/dev/null 2>&1; then
            log "$pkg failed to build — keeping the previous package"
            return 0
        fi
        die "$pkg failed to build and there is no previous package"
    fi
    rm -f "$src"/*-debug-*.pkg.tar.zst   # devtools builds debug splits by default
    rm -f "$REPO_DIR/$pkg"-[0-9r]*.pkg.tar.zst
    mv "$src"/*.pkg.tar.zst "$REPO_DIR/"
    refresh_db   # the next package in the chain resolves this one from the repo
}

for pkg in "${PKGS[@]}"; do
    if [[ " ${CHROOT_AUR_PKGS[*]} " == *" $pkg "* ]]; then
        build_in_chroot "$pkg"
        continue
    fi
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
refresh_db
log "done -> $REPO_DIR"
