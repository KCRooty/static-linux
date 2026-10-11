#!/bin/bash
# Static Linux — apply an accent colour across the whole look.
#
#   apply.sh --list                 show the accents
#   apply.sh --current              print the active accent
#   apply.sh purple                 apply to the invoking user + /etc (sudo for /etc)
#   apply.sh blue --user core       apply to another user's home
#   sudo apply.sh green --skel      render into /etc/skel + /etc (ISO build)
#
# Touches: fastfetch, GTK (3/4), xfwm4 border, xfce4-terminal, LightDM greeter,
# wallpaper. Every change is backed up to /var/backups/static-linux/accent/
# first — nothing here is irreversible.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PALETTE="$HERE/palette.conf"
TPL="$HERE/templates"

# Wallpapers: installed path first (/usr/share/static-linux/wallpapers, from
# the staticlinux-base package), else the repo-relative dev checkout layout
# (branding/wallpapers/, two levels above branding/accents/apply.sh) — same
# "installed, else repo-relative" pattern sl-ctl.py and sl-welcome use.
WP_DIR_INSTALLED="/usr/share/static-linux/wallpapers"
if [[ -d "$WP_DIR_INSTALLED" ]]; then
  WP_DIR="$WP_DIR_INSTALLED"
else
  WP_DIR="$(cd "$HERE/../../branding/wallpapers" 2>/dev/null && pwd)"
fi
WP_GEN="$WP_DIR/gen-wallpaper.py"
BACKUP="/var/backups/static-linux/accent/$(date +%Y%m%d-%H%M%S)"
STATE_SYS="/etc/static-linux/accent"
STATE_VAR="/var/lib/static-linux/accent"

MODE="home"
USER_NAME="${SUDO_USER:-${USER:-root}}"
ACCENT=""

log()  { printf '\033[1;35m[accent]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[accent]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[accent]\033[0m %s\n' "$*" >&2; exit 1; }

# ---- args -----------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --list)    grep -vE '^\s*#|^\s*$' "$PALETTE" | awk -F'|' '{printf "  %-10s %s\n",$1,$7}'; exit 0 ;;
    --current) cat "$STATE_SYS" 2>/dev/null || cat "$STATE_VAR" 2>/dev/null || echo "purple"; exit 0 ;;
    --skel)    MODE="skel" ;;
    --user)    USER_NAME="$2"; shift ;;
    -*)        die "unknown option: $1" ;;
    *)         ACCENT="$1" ;;
  esac
  shift
done
[[ -n "$ACCENT" ]] || die "pick an accent (apply.sh --list)"

# ---- look up the accent row --------------------------------------------
ROW="$(grep -vE '^\s*#|^\s*$' "$PALETTE" | awk -F'|' -v n="$ACCENT" '$1 ~ "^ *"n" *$"{print; exit}')"
[[ -n "$ROW" ]] || die "unknown accent '$ACCENT' (apply.sh --list)"
IFS='|' read -r _ ACCENT_HEX DIM_HEX DETAIL_HEX TEXT_HEX BG_HEX LABEL <<<"$ROW"
ACCENT_HEX="$(echo "$ACCENT_HEX" | tr -d ' ')"; DIM_HEX="$(echo "$DIM_HEX" | tr -d ' ')"
DETAIL_HEX="$(echo "$DETAIL_HEX" | tr -d ' ')"; TEXT_HEX="$(echo "$TEXT_HEX" | tr -d ' ')"
BG_HEX="$(echo "$BG_HEX" | tr -d ' ')"; LABEL="$(echo "$LABEL" | sed 's/^ *//;s/ *$//')"

ansi() { printf '38;2;%d;%d;%d' "0x${1:0:2}" "0x${1:2:2}" "0x${1:4:2}"; }
ACCENT_ANSI="$(ansi "$ACCENT_HEX")"; DIM_ANSI="$(ansi "$DIM_HEX")"
DETAIL_ANSI="$(ansi "$DETAIL_HEX")"; TEXT_ANSI="$(ansi "$TEXT_HEX")"

render() {  # render <template> -> stdout
  sed -e "s/@ACCENT_HEX@/$ACCENT_HEX/g"   -e "s/@DIM_HEX@/$DIM_HEX/g" \
      -e "s/@DETAIL_HEX@/$DETAIL_HEX/g"   -e "s/@TEXT_HEX@/$TEXT_HEX/g" \
      -e "s/@BG_HEX@/$BG_HEX/g" \
      -e "s/@ACCENT_ANSI@/$ACCENT_ANSI/g" -e "s/@DIM_ANSI@/$DIM_ANSI/g" \
      -e "s/@DETAIL_ANSI@/$DETAIL_ANSI/g" -e "s/@TEXT_ANSI@/$TEXT_ANSI/g" \
      -e "s/@LABEL@/$LABEL/g" "$1"
}
bk() { local f="$1"; [[ -e "$f" && ! -e "$BACKUP$f" ]] && { mkdir -p "$(dirname "$BACKUP$f")"; cp -a "$f" "$BACKUP$f"; }; return 0; }

# ---- resolve target home ---------------------------------------------
if [[ "$MODE" == "skel" ]]; then
  [[ $EUID -eq 0 ]] || die "--skel needs root"
  HOMEDIR="/etc/skel"
else
  HOMEDIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
  [[ -d "$HOMEDIR" ]] || die "no home for '$USER_NAME'"
fi
IS_ROOT=$([[ $EUID -eq 0 ]] && echo 1 || echo 0)

log "accent: $ACCENT ($LABEL)  ·  #$ACCENT_HEX  ·  target $HOMEDIR"

# ---- 1. fastfetch (system) -----------------------------------------
if [[ $IS_ROOT -eq 1 ]]; then
  bk /etc/fastfetch/config.jsonc
  mkdir -p /etc/fastfetch
  render "$TPL/fastfetch.jsonc.in" > /etc/fastfetch/config.jsonc
  log "fastfetch -> /etc/fastfetch/config.jsonc"
else
  warn "not root: skipping /etc/fastfetch (run with sudo for the system fetch)"
fi

# ---- 2. GTK 3 / 4 --------------------------------------------------
for gv in gtk-3.0 gtk-4.0; do
  dst="$HOMEDIR/.config/$gv/gtk.css"
  bk "$dst"; mkdir -p "$(dirname "$dst")"
  render "$TPL/gtk.css.in" > "$dst"
done
log "GTK 3/4 accent -> $HOMEDIR/.config/gtk-*/gtk.css"

# ---- 3. xfwm4 "Static-Void" theme -------------------------------
THEME_DST="$HOMEDIR/.local/share/xfwm4/themes/Static-Void"
DEFAULT_SRC=""
for c in /usr/share/themes/Default/xfwm4 /usr/share/themes/Adwaita/xfwm4; do
  [[ -d "$c" ]] && { DEFAULT_SRC="$c"; break; }
done
if [[ -n "$DEFAULT_SRC" ]]; then
  bk "$THEME_DST/themerc"
  mkdir -p "$THEME_DST"; cp -an "$DEFAULT_SRC/." "$THEME_DST/" 2>/dev/null || true
  render "$TPL/xfwm4-themerc.in" > "$THEME_DST/themerc"
  log "xfwm4 border -> $THEME_DST/themerc"
fi

# ---- 4. xfce4-terminal colours ---------------------------------
TRC="$HOMEDIR/.config/xfce4/terminal/terminalrc"
if [[ -f "$TRC" ]]; then
  bk "$TRC"
  # drop any previous accent block, then append the new one
  sed -i '/^# --- accent colours ---/,/^ColorSelectionForeground=/d' "$TRC"
  { echo "# --- accent colours ---"; render "$TPL/terminalrc-colors.in" | grep -E '^Color'; } >> "$TRC"
  log "terminal colours -> $TRC"
fi

# ---- 5. LightDM greeter (system) ------------------------------
if [[ $IS_ROOT -eq 1 ]]; then
  dst=/etc/lightdm/lightdm-gtk-greeter.conf.d/50-static-linux.conf
  bk "$dst"; mkdir -p "$(dirname "$dst")"
  render "$TPL/lightdm-greeter.conf.in" > "$dst"
  log "greeter -> $dst"
fi

# ---- 6. wallpaper ------------------------------------------------
WP="$WP_DIR/$ACCENT/void-$ACCENT.png"
[[ -f "$WP" ]] || { log "generating wallpaper"; python3 "$WP_GEN" --accent "$ACCENT" >/dev/null; }
if [[ $IS_ROOT -eq 1 ]]; then
  WP_DST="/usr/share/backgrounds/static-linux/void-$ACCENT.png"
  install -Dm0644 "$WP" "$WP_DST"
else
  WP_DST="$HOMEDIR/.local/share/backgrounds/static-linux/void-$ACCENT.png"
  install -Dm0644 "$WP" "$WP_DST"
fi
# update the desktop XML (skel + live)
DXML="$HOMEDIR/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
[[ -f "$DXML" ]] && { bk "$DXML"; sed -i -E "s#(void-)[a-z-]+(\.png)#\\1$ACCENT\\2#; s#/backgrounds/static-linux/void-[a-z-]+\.png#$(dirname "$WP_DST" | sed 's#/[^/]*$##')/void-$ACCENT.png#" "$DXML" 2>/dev/null || true; }
log "wallpaper -> $WP_DST"

# ---- 7. record + live apply -----------------------------------
if [[ $IS_ROOT -eq 1 ]]; then mkdir -p "$(dirname "$STATE_SYS")"; echo "$ACCENT" > "$STATE_SYS"; fi
mkdir -p "$(dirname "$STATE_VAR")" 2>/dev/null && echo "$ACCENT" > "$STATE_VAR" 2>/dev/null || true

if [[ "$MODE" == "home" ]] && pgrep -u "$USER_NAME" xfce4-session >/dev/null 2>&1; then
  UID_N="$(id -u "$USER_NAME")"
  DBUS="unix:path=/run/user/$UID_N/bus"
  as() { [[ $IS_ROOT -eq 1 ]] && sudo -u "$USER_NAME" env DBUS_SESSION_BUS_ADDRESS="$DBUS" "$@" \
                              || env DBUS_SESSION_BUS_ADDRESS="$DBUS" "$@"; }
  # wallpaper on every monitor path + restart xfdesktop
  for base in $(as xfconf-query -c xfce4-desktop -l 2>/dev/null | grep -oE '/backdrop/screen[0-9]+/monitor[^/]+' | sort -u); do
    for p in "$base/workspace0/last-image" "$base/last-image"; do
      as xfconf-query -c xfce4-desktop -p "$p" -n -t string -s "$WP_DST" 2>/dev/null \
        || as xfconf-query -c xfce4-desktop -p "$p" -s "$WP_DST" 2>/dev/null || true
    done
    for p in "$base/workspace0/image-style" "$base/image-style"; do
      as xfconf-query -c xfce4-desktop -p "$p" -n -t int -s 5 2>/dev/null \
        || as xfconf-query -c xfce4-desktop -p "$p" -s 5 2>/dev/null || true
    done
  done
  as bash -c 'kill "$(pgrep -x xfdesktop)" 2>/dev/null; sleep 1; setsid xfdesktop >/dev/null 2>&1 &' || true
  # nudge xfsettingsd so GTK apps reload gtk.css, and reload xfwm4
  as xfconf-query -c xsettings -p /Gtk/ThemeName -s Adwaita-dark 2>/dev/null || true
  as xfwm4 --replace >/dev/null 2>&1 &
  log "applied live — open a new terminal to see the fetch"
fi

log "done.  Backup: $BACKUP   ·   revert: sl-ctl accent <other>  or restore from that dir"
