#!/bin/bash
# Static Linux — ISO build wrapper around mkarchiso.
#
#   sudo ./build.sh online     build the ~1 GB online ISO (network at install time)
#   sudo ./build.sh offline    build the ~4 GB offline-shaped ISO (see README.md —
#                               packages are bundled, Calamares still needs
#                               network today; that wiring isn't done)
#   sudo ./build.sh online --dev-ssh-key ~/.ssh/id_ed25519.pub
#                               development build: also enables root SSH into
#                               the live session for that key (QEMU testing)
#
# What this does that a bare `mkarchiso profiledir/` wouldn't:
#
#   1. Neither profiledir-*/ carries efiboot/, syslinux/, grub/ or
#      pacman.conf — those are upstream archiso's own boot-chain
#      boilerplate (from its releng profile), not something Static Linux
#      should hand-maintain and let drift from whatever archiso version is
#      actually on the build host. Copied in fresh on every build, gitignored.
#   2. Neither profiledir-*/ carries an airootfs/ either. It's assembled
#      fresh each build from two sources, also gitignored:
#        - iso/airootfs-common/         hand-authored (autologin, motd, the
#                                        .xinitrc that starts Calamares)
#        - installer/calamares/ -> airootfs/etc/calamares/, so Calamares
#          finds settings.conf/modules/branding when it launches live.
#   3. Wires the local package repo (packages/aur-cache/, built by
#      packages/local-repo.sh) into the profile's pacman.conf. mkarchiso's
#      pacstrap step only pulls from pacman repos, and two packages the
#      live image needs aren't in any official one:
#        - calamares        AUR-only, and the AUR build lacks the Python
#                           job support this installer depends on — see
#                           packages/calamares/PKGBUILD
#        - staticlinux-base /usr/lib/static-linux, sl-detect/sl-ctl, and
#                           the os-release identity (its install script
#                           repoints /etc/os-release, which a plain file
#                           copy into airootfs/ can't do)
#      The repo is only added to the ISO profile — the build host's own
#      /etc/pacman.conf is never touched.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
FLAVOR="${1:-}"
DEV_SSH_KEY=""
if [[ "${2:-}" == "--dev-ssh-key" ]]; then
    DEV_SSH_KEY="${3:-}"
    [[ -f "$DEV_SSH_KEY" ]] || { echo "--dev-ssh-key: no such file '$DEV_SSH_KEY'" >&2; exit 1; }
fi
RELENG="/usr/share/archiso/configs/releng"

log()  { printf '\033[1;38;5;43m[iso-build]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[iso-build]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[iso-build]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$FLAVOR" == "online" || "$FLAVOR" == "offline" ]] || die "usage: $0 online|offline [--dev-ssh-key PUBKEY]"
[[ $EUID -eq 0 ]] || die "mkarchiso needs root (pacstrap/mount namespaces)"
command -v mkarchiso >/dev/null || die "mkarchiso not found — pacman -S archiso"
[[ -d "$RELENG" ]] || die "$RELENG not found — archiso package looks incomplete"

PROFILE="$HERE/profiledir-$FLAVOR"
WORK="$HERE/work-$FLAVOR"
OUT="$HERE/out"

[[ -f "$PROFILE/profiledef.sh" ]] || die "$PROFILE/profiledef.sh missing"
[[ -f "$PROFILE/packages.x86_64" ]] || die "$PROFILE/packages.x86_64 missing"

LOCAL_REPO="$REPO/packages/aur-cache"
LOCAL_REPO_NAME="staticlinux-local"

# ---- 0. the local repo must hold what pacstrap can't get elsewhere -----
[[ -f "$LOCAL_REPO/$LOCAL_REPO_NAME.db" ]] || die "local repo missing at $LOCAL_REPO — \
run packages/local-repo.sh as your normal user first"
for pkg in calamares staticlinux-base staticlinux-fonts brave-origin-bin; do
    compgen -G "$LOCAL_REPO/$pkg-[0-9]*.pkg.tar.zst" >/dev/null || die "$pkg isn't in \
the local repo — run packages/local-repo.sh $pkg as your normal user"
done

# ---- 1. boot chain, fresh from archiso's own releng profile ------------
for d in efiboot syslinux grub; do
    rm -rf "${PROFILE:?}/$d"
    if [[ -d "$RELENG/$d" ]]; then
        log "boot chain: $d/ <- releng"
        cp -a "$RELENG/$d" "$PROFILE/$d"
    fi
done
rm -f "$PROFILE/pacman.conf"
log "boot chain: pacman.conf <- releng (+ $LOCAL_REPO_NAME)"
cp -a "$RELENG/pacman.conf" "$PROFILE/pacman.conf"
# Unsigned on purpose: these are packages built on this machine from this
# checkout. Release ISOs get a signed Static Forge repo instead.
printf '\n[%s]\nSigLevel = Optional TrustAll\nServer = file://%s\n' \
    "$LOCAL_REPO_NAME" "$LOCAL_REPO" >> "$PROFILE/pacman.conf"

# releng's menus are Arch's: "Arch Linux install medium", the Arch splash.
# Rebrand the copies rather than forking the files, so the boot entries
# themselves still track upstream.
log "boot chain: rebranding menus as Static Linux"
# The speech entries need espeakup, which this image doesn't ship.
rm -f "$PROFILE/efiboot/loader/entries/02-archiso-speech-linux.conf"
sed -i '/with speakup screen reader/,/^}/d' "$PROFILE"/grub/*.cfg
sed -i '/^# Accessibility boot option$/,$d' "$PROFILE/syslinux/archiso_sys-linux.cfg"
sed -i 's/^beep on$/beep off/' "$PROFILE/efiboot/loader/loader.conf"
grep -rlZ 'Arch Linux' "$PROFILE/efiboot" "$PROFILE/syslinux" "$PROFILE/grub" | xargs -0 -r sed -i \
    -e 's/Arch Linux \(install\|live\) medium/Static Linux installer/g' \
    -e 's/install Arch Linux/install Static Linux/g' \
    -e 's/MENU TITLE Arch Linux/MENU TITLE Static Linux/'
if grep -rq 'Arch Linux' "$PROFILE/efiboot" "$PROFILE/syslinux" "$PROFILE/grub"; then
    warn "boot menus still mention Arch Linux — releng changed, update the rebrand step"
fi
install -m644 "$HERE/boot/splash.png" "$PROFILE/syslinux/splash.png"

# ---- 2. airootfs, assembled fresh every build ---------------------------
AIROOTFS="$PROFILE/airootfs"
rm -rf "$AIROOTFS"
mkdir -p "$AIROOTFS"

# The parts of a live system that are archiso's business, not Static
# Linux's: the initramfs hooks that find and mount the ISO, the pacman
# keyring bootstrap, the build-time mirrorlist hooks. Same reasoning as the
# boot chain above — taken from the installed archiso, never hand-copied.
log "airootfs: live-system plumbing <- releng"
for f in \
    etc/mkinitcpio.conf.d/archiso.conf \
    etc/pacman.d/hooks \
    etc/systemd/system/pacman-init.service \
    etc/systemd/system/etc-pacman.d-gnupg.mount \
    etc/systemd/journald.conf.d \
    etc/systemd/logind.conf.d \
    etc/locale.conf \
    etc/localtime
do
    [[ -e "$RELENG/airootfs/$f" || -L "$RELENG/airootfs/$f" ]] \
        || die "releng no longer ships airootfs/$f — update iso/build.sh"
    mkdir -p "$AIROOTFS/$(dirname "$f")"
    cp -a "$RELENG/airootfs/$f" "$AIROOTFS/$f"
done

log "airootfs: hand-authored bits <- iso/airootfs-common"
cp -a "$REPO/iso/airootfs-common/." "$AIROOTFS/"

# Calamares installs live with pacman, so the session needs a network and an
# initialised keyring before the installer window appears.
WANTS="$AIROOTFS/etc/systemd/system/multi-user.target.wants"
mkdir -p "$WANTS"
ln -sf /usr/lib/systemd/system/NetworkManager.service "$WANTS/NetworkManager.service"
ln -sf ../pacman-init.service "$WANTS/pacman-init.service"

# Development builds only: key-based root SSH into the live session, so the
# installer can be driven and debugged from the build host (QEMU port
# forward). Never pass this for an ISO that leaves the machine.
if [[ -n "$DEV_SSH_KEY" ]]; then
    warn "DEV BUILD: root SSH enabled for $(basename "$DEV_SSH_KEY") — do not distribute this ISO"
    install -Dm600 "$DEV_SSH_KEY" "$AIROOTFS/root/.ssh/authorized_keys"
    chmod 700 "$AIROOTFS/root/.ssh"
    ln -sf /usr/lib/systemd/system/sshd.service "$WANTS/sshd.service"
fi

log "airootfs: installer/calamares/ -> etc/calamares/"
mkdir -p "$AIROOTFS/etc/calamares"
cp -a "$REPO/installer/calamares/." "$AIROOTFS/etc/calamares/"

# The installer pacstraps the target from inside the live session, and
# staticlinux-base has to be installable there too — so the live image
# carries the same local repo, and a pacman.conf that knows about it.
LIVE_REPO_DIR="/opt/staticlinux-repo"
log "airootfs: local repo -> ${LIVE_REPO_DIR#/} (for the installer's pacstrap)"
install -d "$AIROOTFS$LIVE_REPO_DIR"
cp -L "$LOCAL_REPO"/*.pkg.tar.zst \
      "$LOCAL_REPO/$LOCAL_REPO_NAME.db" "$LOCAL_REPO/$LOCAL_REPO_NAME.files" \
      "$AIROOTFS$LIVE_REPO_DIR/"
cp "$RELENG/pacman.conf" "$AIROOTFS/etc/pacman.conf"
printf '\n[%s]\nSigLevel = Optional TrustAll\nServer = file://%s\n' \
    "$LOCAL_REPO_NAME" "$LIVE_REPO_DIR" >> "$AIROOTFS/etc/pacman.conf"

# ---- 3. build ------------------------------------------------------------
# mkarchiso skips every stage it already finished in an existing work dir,
# so a rebuild after changing the repo silently produced nothing new.
if [[ -d "$WORK" ]]; then
    log "removing previous work dir $WORK"
    rm -rf --one-file-system "$WORK"
fi
log "building $FLAVOR ISO from $PROFILE"
mkdir -p "$OUT"
mkarchiso -v -w "$WORK" -o "$OUT" "$PROFILE"

log "done -> $OUT"
