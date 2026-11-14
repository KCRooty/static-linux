#!/bin/bash
# Static Linux — sign an ISO and upload it to the mirrors.
#
#   iso/release.sh sign  iso/out/static-linux-VERSION-x86_64.iso
#       SHA256 sum (.sha256) and detached GPG signature with the Static Forge
#       release key (.sig, binary, and .asc, armored). The passphrase comes
#       from ~/.config/static-linux/gpg.env (SL_GPG_PASS), never this repo.
#
#   iso/release.sh sourceforge  iso/out/static-linux-VERSION-x86_64.iso
#       rsync the ISO and its three companions to
#       frs.sourceforge.net:/home/frs/project/static-linux/VERSION/
#       Needs SF_USER in ~/.config/static-linux/sourceforge.env and an SSH key
#       registered in the SourceForge account (SF_KEY, default
#       ~/.ssh/sourceforge_ed25519).
#
#   iso/release.sh drive  iso/out/static-linux-VERSION-x86_64.iso
#       rclone copy to the "sl-drive:" remote, folder "Static Linux/VERSION".
#
#   iso/release.sh archive  iso/out/static-linux-VERSION-x86_64.iso
#       Upload to the Internet Archive as item static-linux-VERSION (public,
#       GPL-3.0); archive.org then seeds a torrent of it by itself. Needs the
#       account's S3 keys (archive.org/account/s3.php) as IA_ACCESS/IA_SECRET
#       in ~/.config/static-linux/archive.env.
#
# Refuses an ISO built with --dev-ssh-key (it would let anyone with that key
# into the live session).

set -euo pipefail

KEY_FPR="3E617ED06C90C75735C9C45E51D58FA35045B8D0"
die() { printf '\033[1;31m[release]\033[0m %s\n' "$*" >&2; exit 1; }
log() { printf '\033[1;38;5;43m[release]\033[0m %s\n' "$*"; }

cmd="${1:-}"; iso="${2:-}"
[[ -f "$iso" ]] || die "usage: $0 sign|sourceforge|drive|archive ISO"
name="$(basename "$iso")"
ver="$(sed -E 's/^static-linux-([0-9.]+)-x86_64\.iso$/\1/' <<<"$name")"
[[ "$ver" != "$name" ]] || die "unexpected ISO name: $name"

not_dev() {
    # the dev build puts root's authorized_keys into the live image
    if command -v bsdtar >/dev/null && bsdtar -tf "$iso" 2>/dev/null | grep -q 'airootfs.sfs$'; then
        local tmp; tmp="$(mktemp -d)"
        bsdtar -xf "$iso" -C "$tmp" 'staticlinux/x86_64/airootfs.sfs' 2>/dev/null || true
        if [[ -f "$tmp/staticlinux/x86_64/airootfs.sfs" ]] &&
           unsquashfs -l "$tmp/staticlinux/x86_64/airootfs.sfs" 2>/dev/null | grep -q 'root/.ssh/authorized_keys'; then
            rm -rf "$tmp"; die "$name is a development build (root SSH key inside): never publish it"
        fi
        rm -rf "$tmp"
    fi
}

case "$cmd" in
sign)
    not_dev
    # shellcheck disable=SC1090
    source ~/.config/static-linux/gpg.env
    cd "$(dirname "$iso")"
    log "sha256 -> $name.sha256"
    sha256sum "$name" > "$name.sha256"
    for kind in sig asc; do
        rm -f "$name.$kind"
        armor=(); [[ $kind == asc ]] && armor=(--armor)
        gpg --batch --yes --pinentry-mode loopback --passphrase "$SL_GPG_PASS" \
            --local-user "$KEY_FPR" "${armor[@]}" --detach-sign --output "$name.$kind" "$name"
    done
    gpg --verify "$name.sig" "$name" 2>&1 | grep -E 'Good signature|Firma correcta' \
        || die "the signature does not verify"
    log "signed with $KEY_FPR"
    ;;
sourceforge)
    # shellcheck disable=SC1090
    source ~/.config/static-linux/sourceforge.env
    : "${SF_USER:?set SF_USER (your SourceForge username) in sourceforge.env}"
    key="${SF_KEY:-$HOME/.ssh/sourceforge_ed25519}"
    for f in "$iso" "$iso.sha256" "$iso.sig" "$iso.asc"; do [[ -f "$f" ]] || die "missing $f (run sign first)"; done
    log "uploading to SourceForge: static-linux/$ver/"
    rsync -av --progress --partial -e "ssh -i $key -o StrictHostKeyChecking=accept-new" \
        "$iso" "$iso.sha256" "$iso.sig" "$iso.asc" \
        "$SF_USER@frs.sourceforge.net:/home/frs/project/${SOURCEFORGE_PROJECT:-static-linux}/$ver/"
    log "https://sourceforge.net/projects/${SOURCEFORGE_PROJECT:-static-linux}/files/$ver/"
    ;;
drive)
    for f in "$iso" "$iso.sha256" "$iso.sig" "$iso.asc"; do [[ -f "$f" ]] || die "missing $f (run sign first)"; done
    log "uploading to Google Drive: Static Linux/$ver/"
    for f in "$iso" "$iso.sha256" "$iso.sig" "$iso.asc"; do
        rclone copy --progress --drive-chunk-size 64M "$f" "sl-drive:Static Linux/$ver/"
    done
    ;;
archive)
    # shellcheck disable=SC1090
    source ~/.config/static-linux/archive.env
    : "${IA_ACCESS:?set IA_ACCESS and IA_SECRET in archive.env}" "${IA_SECRET:?}"
    command -v ia >/dev/null || die "install python-internetarchive"
    for f in "$iso" "$iso.sha256" "$iso.sig" "$iso.asc"; do [[ -f "$f" ]] || die "missing $f (run sign first)"; done
    item="static-linux-$ver"
    log "uploading to archive.org: $item"
    cfg="$(mktemp)"; trap 'rm -f "$cfg"' EXIT
    printf '[s3]\naccess = %s\nsecret = %s\n' "$IA_ACCESS" "$IA_SECRET" > "$cfg"
    ia --config-file "$cfg" upload "$item" "$iso" "$iso.sha256" "$iso.sig" "$iso.asc" \
        --retries 10 --checksum \
        --metadata="title:Static Linux $ver" \
        --metadata="mediatype:software" \
        --metadata="collection:opensource_media" \
        --metadata="creator:Static Forge" \
        --metadata="date:$(date -I)" \
        --metadata="licenseurl:https://www.gnu.org/licenses/gpl-3.0.html" \
        --metadata="subject:linux;arch linux;distribution;static linux" \
        --metadata="description:Static Linux $ver, an Arch-based distribution by Static Forge (x86_64, UEFI). Test release. Signed with the Static Forge release key 3E617ED06C90C75735C9C45E51D58FA35045B8D0. https://staticforge.me/linux/"
    log "https://archive.org/details/$item (torrent: https://archive.org/download/$item/${item}_archive.torrent)"
    ;;
*) die "usage: $0 sign|sourceforge|drive|archive ISO" ;;
esac
