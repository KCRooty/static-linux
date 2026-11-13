# Static Linux — translations for shell scripts (source it, then use `t "texto"`).
# Same rules as sl_i18n.py: Spanish source strings; Spanish locales get them
# as they are, others their catalogue or English. Catalogues: i18n/build/locale
# in a repo checkout, /usr/share/locale once installed.
_sl_here="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
export TEXTDOMAIN=static-linux
if [[ -d "$_sl_here/build/locale" ]]; then export TEXTDOMAINDIR="$_sl_here/build/locale"; fi
_sl_code="${LANGUAGE:-${LC_ALL:-${LC_MESSAGES:-${LANG:-en}}}}"
_sl_code="${_sl_code%%:*}"; _sl_code="${_sl_code%%.*}"; _sl_code="${_sl_code%%@*}"
if [[ "${_sl_code%%_*}" == es ]] || ! command -v gettext >/dev/null; then
    t() { printf '%s' "$1"; }
else
    export LANGUAGE="$_sl_code:${_sl_code%%_*}:en"
    t() { gettext "$1"; }
fi
