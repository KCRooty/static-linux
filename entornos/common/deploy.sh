#!/bin/bash
# Static Linux — shared deploy for the simpler environments (GNOME, Cinnamon,
# i3, bspwm, sway). Each entornos/<env>/install.sh sources this after setting
# ENV_NAME and HERE, then calls `deploy "$@"`.
#
#   ./install.sh --home [--user X]   into a user's home
#   sudo ./install.sh --skel         into /etc/skel (ISO / installer)
#
# Copies skel/ (backing up what it replaces into <target>/.sl-<env>-backup/)
# and applies the active theme with sl-theme, which writes only the pieces
# whose programs are installed.

log()  { printf '\033[1;38;5;43m[%s]\033[0m %s\n' "$ENV_NAME" "$*"; }
warn() { printf '\033[1;33m[%s]\033[0m %s\n' "$ENV_NAME" "$*" >&2; }
die()  { printf '\033[1;31m[%s]\033[0m %s\n' "$ENV_NAME" "$*" >&2; exit 1; }

deploy() {
    local mode="" user_name="${SUDO_USER:-${USER:-root}}" target
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --home) mode=home ;;
            --skel) mode=skel ;;
            --user) user_name="$2"; shift ;;
            *) die "unknown option: $1" ;;
        esac
        shift
    done
    [[ -n "$mode" ]] || die "pick a mode: --home or --skel"
    if [[ "$mode" == skel ]]; then
        [[ $EUID -eq 0 ]] || die "--skel needs root"
        target=/etc/skel
    else
        target="$(getent passwd "$user_name" | cut -d: -f6)"
        [[ -n "$target" && -d "$target" ]] || die "no home dir for user '$user_name'"
    fi
    log "target: $target"

    local backup="$target/.sl-$ENV_NAME-backup/$(date +%Y%m%d-%H%M%S)" f rel dst
    if [[ -d "$HERE/skel" ]]; then
        while IFS= read -r -d '' f; do
            rel="${f#"$HERE/skel/"}"; dst="$target/$rel"
            if [[ -e "$dst" && ! -e "$backup/$rel" ]]; then
                mkdir -p "$(dirname "$backup/$rel")"; cp -a "$dst" "$backup/$rel"
            fi
            mkdir -p "$(dirname "$dst")"; cp -a "$f" "$dst"
        done < <(find "$HERE/skel" -type f -print0)
        # scripts in skel keep their exec bit only if the package gave it back
        for f in .config/bspwm/bspwmrc .config/polybar/launch.sh; do
            [[ -f "$target/$f" ]] && chmod 755 "$target/$f"
        done
    fi

    local sl_theme=/usr/share/static-linux/themes/sl-theme theme
    [[ -f "$sl_theme" ]] || sl_theme="$HERE/../../branding/themes/sl-theme"
    theme="$(cat /etc/static-linux/theme 2>/dev/null || echo ambar)"
    log "applying theme: $theme"
    if [[ "$mode" == skel ]]; then
        python3 "$sl_theme" "$theme" --skel || warn "theme apply failed"
    else
        python3 "$sl_theme" "$theme" --user "$user_name" || warn "theme apply failed"
        [[ $EUID -eq 0 ]] && chown -R "$user_name": "$target/.config" "$target/.local" 2>/dev/null
    fi
    log "done. Backup of replaced files (if any): $backup"
}
