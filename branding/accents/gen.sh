#!/bin/bash
# Static Linux — pre-bake every accent (wallpapers + rendered theme fragments).
# Run from a repo checkout; commit the results so the offline ISO ships them
# without needing to render at install time.
#
#   ./gen.sh                 all accents, 3840x2160 wallpapers
#   ./gen.sh 2560x1440       all accents at a custom size

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
SIZE="${1:-3840x2160}"

echo "==> wallpapers ($SIZE)"
python3 "$REPO/branding/wallpapers/gen-wallpaper.py" --accent all --size "$SIZE"

echo "==> theme fragments"
ansi() { printf '38;2;%d;%d;%d' "0x${1:0:2}" "0x${1:2:2}" "0x${1:4:2}"; }
grep -vE '^\s*#|^\s*$' "$HERE/palette.conf" | while IFS='|' read -r name a d det t bg label; do
  name="$(echo "$name" | tr -d ' ')"
  a="$(echo "$a" | tr -d ' ')"; d="$(echo "$d" | tr -d ' ')"; det="$(echo "$det" | tr -d ' ')"
  t="$(echo "$t" | tr -d ' ')"; bg="$(echo "$bg" | tr -d ' ')"
  label="$(echo "$label" | sed 's/^ *//;s/ *$//')"
  out="$HERE/themes/$name"; mkdir -p "$out"
  for tpl in "$HERE"/templates/*.in; do
    base="$(basename "${tpl%.in}")"
    sed -e "s/@ACCENT_HEX@/$a/g" -e "s/@DIM_HEX@/$d/g" -e "s/@DETAIL_HEX@/$det/g" \
        -e "s/@TEXT_HEX@/$t/g" -e "s/@BG_HEX@/$bg/g" \
        -e "s/@ACCENT_ANSI@/$(ansi "$a")/g" -e "s/@DIM_ANSI@/$(ansi "$d")/g" \
        -e "s/@DETAIL_ANSI@/$(ansi "$det")/g" -e "s/@TEXT_ANSI@/$(ansi "$t")/g" \
        -e "s/@LABEL@/$label/g" -e "s/@ACCENT@/$name/g" "$tpl" > "$out/$base"
  done
  echo "  $name -> themes/$name/"
done

echo "==> done"
