#!/bin/bash
# Static Linux — ISO build wrapper around mkarchiso.
#
#   sudo ./build.sh online     build the ~1 GB online ISO (network at install time)
#   sudo ./build.sh offline    build the ~4 GB offline-shaped ISO (see README.md —
#                               packages are bundled, Calamares still needs
#                               network today; that wiring isn't done)
#
# What this does that a bare `mkarchiso profiledir/` wouldn't:
#
#   1. Neither profiledir-*/ carries efiboot/, syslinux/, grub/ or
#      pacman.conf — those are upstream archiso's own boot-chain
#      boilerplate (from its releng profile), not something Static Linux
#      should hand-maintain and let drift from whatever archiso version is
#      actually on the build host. Copied in fresh on every build, gitignored.
#   2. Neither profiledir-*/ carries an airootfs/ either. It's assembled
#      fresh each build from three sources, also gitignored:
#        - iso/airootfs-common/         hand-authored (autologin, motd, the
#                                        .xinitrc that starts Calamares)
#        - packages/staticlinux-base/PKGBUILD's package() function, run
#          with pkgdir pointed at the profile's airootfs/ instead of a real
#          package — the live session gets the exact same
#          /usr/lib/static-linux tree a real `pacman -S staticlinux-base`
#          would produce, no duplicated packaging logic.
#        - installer/calamares/ -> airootfs/etc/calamares/, so Calamares
#          finds settings.conf/modules/branding when it launches live.
#   3. Checks that `calamares` actually resolves against the build host's
#      configured pacman repos before doing any of the above — it's AUR-only
#      (confirmed: https://archlinux.org/packages/search/json/?name=calamares
#      returns zero results, https://aur.archlinux.org has it). Static Linux
#      has no repo of its own yet (see packages/staticlinux-base/README.md),
#      so mkarchiso's pacstrap step can't get it unless the build host has
#      calamares available some other way — a local repo with a prebuilt
#      calamares package is the standard fix (same thing EndeavourOS/etc. do).
#      This script can't set that up for you; it just fails loudly instead
#      of letting pacstrap die deep into a build.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
FLAVOR="${1:-}"
RELENG="/usr/share/archiso/configs/releng"

log()  { printf '\033[1;38;5;43m[iso-build]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[iso-build]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[iso-build]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$FLAVOR" == "online" || "$FLAVOR" == "offline" ]] || die "usage: $0 online|offline"
[[ $EUID -eq 0 ]] || die "mkarchiso needs root (pacstrap/mount namespaces)"
command -v mkarchiso >/dev/null || die "mkarchiso not found — pacman -S archiso"
[[ -d "$RELENG" ]] || die "$RELENG not found — archiso package looks incomplete"

PROFILE="$HERE/profiledir-$FLAVOR"
WORK="$HERE/work-$FLAVOR"
OUT="$HERE/out"

[[ -f "$PROFILE/profiledef.sh" ]] || die "$PROFILE/profiledef.sh missing"
[[ -f "$PROFILE/packages.x86_64" ]] || die "$PROFILE/packages.x86_64 missing"

# ---- 0. calamares must be resolvable, or pacstrap dies mid-build -------
if ! pacman -Si calamares >/dev/null 2>&1; then
    die "calamares isn't in any pacman repo configured on this machine. \
It's AUR-only (see this script's header) — build it and add it to a local \
repo in /etc/pacman.conf before running this (paru -S calamares gets it \
into your own system, but won't make it pacstrap-able unless you also \
stand up a local repo with it in)."
fi

# ---- 1. boot chain, fresh from archiso's own releng profile ------------
for d in efiboot syslinux grub; do
    rm -rf "${PROFILE:?}/$d"
    if [[ -d "$RELENG/$d" ]]; then
        log "boot chain: $d/ <- releng"
        cp -a "$RELENG/$d" "$PROFILE/$d"
    fi
done
rm -f "$PROFILE/pacman.conf"
log "boot chain: pacman.conf <- releng"
cp -a "$RELENG/pacman.conf" "$PROFILE/pacman.conf"

# ---- 2. airootfs, assembled fresh every build ---------------------------
AIROOTFS="$PROFILE/airootfs"
rm -rf "$AIROOTFS"
mkdir -p "$AIROOTFS"

log "airootfs: hand-authored bits <- iso/airootfs-common"
cp -a "$REPO/iso/airootfs-common/." "$AIROOTFS/"

log "airootfs: staticlinux-base tree (running PKGBUILD's package() against it)"
(
    startdir="$REPO/packages/staticlinux-base"
    pkgdir="$AIROOTFS"
    pkgname="staticlinux-base"
    # shellcheck source=/dev/null
    source "$startdir/PKGBUILD"
    package
)

log "airootfs: installer/calamares/ -> etc/calamares/"
mkdir -p "$AIROOTFS/etc/calamares"
cp -a "$REPO/installer/calamares/." "$AIROOTFS/etc/calamares/"

# ---- 3. build ------------------------------------------------------------
log "building $FLAVOR ISO from $PROFILE"
mkdir -p "$OUT"
mkarchiso -v -w "$WORK" -o "$OUT" "$PROFILE"

log "done -> $OUT"
