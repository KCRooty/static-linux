#!/usr/bin/env bash
# Static Linux — rebuild the translations.
#   i18n/build.sh            .mo files into i18n/build/locale (for running from the repo)
#                            + translations into installer pages, slideshow, .desktop, polkit
#   i18n/build.sh <destdir>  only the .mo files, into <destdir>/<lang>/LC_MESSAGES (PKGBUILD)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
out="${1:-$here/build/locale}"
for po in "$here"/po/*.po; do
    lang="$(basename "$po" .po)"
    mkdir -p "$out/$lang/LC_MESSAGES"
    msgfmt --check-format -o "$out/$lang/LC_MESSAGES/static-linux.mo" "$po"
done
[[ $# -eq 0 ]] && python3 "$here/apply.py"
exit 0
