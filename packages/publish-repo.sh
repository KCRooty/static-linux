#!/bin/bash
# Static Linux — publish the [staticlinux] pacman repository.
#
#   packages/publish-repo.sh            sign + upload everything in aur-cache/
#   packages/publish-repo.sh --dry-run  build the signed repo in a folder, upload nothing
#
# Takes the packages packages/local-repo.sh built (packages/aur-cache/), signs
# each one and the database with the Static Forge release key, and uploads
# them as assets of the GitHub release tagged `repo` in KCRooty/static-linux.
# Installed systems use it as:
#
#   [staticlinux]
#   Server = https://github.com/KCRooty/static-linux/releases/download/repo
#
# so a fix to staticlinux-base (or a new Brave Origin) reaches every
# installed machine with a normal `pacman -Syu`, no new ISO needed.
#
# The key's passphrase comes from ~/.config/static-linux/gpg.env (SL_GPG_PASS,
# never in the repo). GitHub asset names can't hold ':' — packages with an
# epoch (brave-origin-bin 1:…) are renamed before repo-add, which records the
# file name pacman will ask for.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/aur-cache"
OUT="$HERE/aur-cache/.publish"
REPO=staticlinux
GH_REPO=KCRooty/static-linux
TAG=repo
KEY=3E617ED06C90C75735C9C45E51D58FA35045B8D0
# calamares only matters on the ISO; nothing installed needs it from here
SKIP=(calamares)
DRY=0; [[ "${1:-}" == "--dry-run" ]] && DRY=1

log() { printf '\033[1;38;5;43m[publish-repo]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[publish-repo]\033[0m %s\n' "$*" >&2; exit 1; }

ENV_FILE="$HOME/.config/static-linux/gpg.env"
[[ -f "$ENV_FILE" ]] || die "no $ENV_FILE (SL_GPG_PASS=…)"
# shellcheck disable=SC1090
source "$ENV_FILE"
sign() { gpg --batch --yes --pinentry-mode loopback --passphrase "$SL_GPG_PASS" \
             --local-user "$KEY" --detach-sign --no-armor --output "$1.sig" "$1"; }

rm -rf "$OUT"; mkdir -p "$OUT"
for f in "$SRC"/*.pkg.tar.zst; do
    name="$(basename "$f")"
    pkgname="$(bsdtar -xOf "$f" .PKGINFO | awk -F' = ' '$1=="pkgname"{print $2; exit}')"
    [[ " ${SKIP[*]} " == *" $pkgname "* ]] && continue
    cp "$f" "$OUT/${name//:/.}"
done
cd "$OUT"
for f in *.pkg.tar.zst; do sign "$f"; done
repo-add --quiet "$REPO.db.tar.zst" *.pkg.tar.zst
# pacman asks for $REPO.db / $REPO.files: real files, not symlinks, for upload
for x in db files; do
    rm -f "$REPO.$x"; cp "$REPO.$x.tar.zst" "$REPO.$x"
    sign "$REPO.$x"; cp "$REPO.$x.sig" "$REPO.$x.tar.zst.sig"
done
gpg --verify "$REPO.db.sig" "$REPO.db" 2>/dev/null || die "the database signature does not verify"
log "$(ls *.pkg.tar.zst | wc -l) packages signed in $OUT"
[[ $DRY -eq 1 ]] && exit 0

command -v gh >/dev/null || die "gh (GitHub CLI) is needed to upload"
if ! gh release view "$TAG" -R "$GH_REPO" >/dev/null 2>&1; then
    gh release create "$TAG" -R "$GH_REPO" --prerelease --title "Repositorio [staticlinux]" \
        --notes "Paquetes de Static Linux para pacman, firmados con la clave de Static Forge (3E61 7ED0 6C90 C757 35C9  C45E 51D5 8FA3 5045 B8D0). No es una versión: no descargues nada de aquí a mano." \
        >/dev/null
fi
log "uploading"
gh release upload "$TAG" -R "$GH_REPO" --clobber ./*.pkg.tar.zst ./*.pkg.tar.zst.sig \
    "$REPO".db "$REPO".db.sig "$REPO".files "$REPO".files.sig \
    "$REPO".db.tar.zst "$REPO".db.tar.zst.sig "$REPO".files.tar.zst "$REPO".files.tar.zst.sig
# old versions of a package stay behind as assets; drop what the db no longer lists
keep="$(ls)"
gh release view "$TAG" -R "$GH_REPO" --json assets -q '.assets[].name' | while read -r a; do
    grep -qxF "$a" <<<"$keep" || { gh release delete-asset "$TAG" "$a" -R "$GH_REPO" -y >/dev/null; log "removed old $a"; }
done
log "done: https://github.com/$GH_REPO/releases/tag/$TAG"
