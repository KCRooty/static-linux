"""Translations for Static Linux's own tools (gettext domain `static-linux`).

The source strings are Spanish. A Spanish locale gets them as they are; any
other locale gets its catalogue if there is one and English if there isn't.

    from sl_i18n import _, N_

Catalogues live in /usr/share/locale/<lang>/LC_MESSAGES/static-linux.mo
(staticlinux-base builds them from i18n/po/) or, in a repo checkout, in
i18n/build/locale after `i18n/build.sh`.
"""

from __future__ import annotations

import gettext
import os
from pathlib import Path

DOMAIN = "static-linux"
_DIRS = [Path(__file__).resolve().parent / "build" / "locale", Path("/usr/share/locale")]


def ui_language() -> str:
    """The language the session asked for, e.g. `pt_BR`, `ca`, `en`."""
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val:
            code = val.split(":")[0].split(".")[0].split("@")[0]
            return "en" if code in ("C", "POSIX") else code
    return "en"


def _load() -> gettext.NullTranslations:
    code = ui_language()
    base = code.split("_")[0]
    if base == "es":
        return gettext.NullTranslations()
    for d in _DIRS:
        for lang in (code, base, "en"):
            mo = d / lang / "LC_MESSAGES" / f"{DOMAIN}.mo"
            if mo.is_file():
                with mo.open("rb") as f:
                    return gettext.GNUTranslations(f)
    return gettext.NullTranslations()


_T = _load()


def _(text: str) -> str:
    return _T.gettext(text) if text else text


def ngettext(singular: str, plural: str, n: int) -> str:
    return _T.ngettext(singular, plural, n)


def N_(text: str) -> str:
    """Marks a string for extraction without translating it yet."""
    return text
