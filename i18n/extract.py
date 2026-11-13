#!/usr/bin/env python3
"""Collects every visible string of Static Linux into i18n/static-linux.pot
and merges it into i18n/po/*.po.

    python3 i18n/extract.py

Code goes through xgettext (Python: _ N_ _tr ngettext; shell: t; TSX: _).
Data files have no gettext calls, so they are read here: the sl-welcome
catalog, theme names, Hyprland bind descriptions, the installer pages and
slideshow, `{{_ "…"}}` in sl-theme templates, .desktop files and the polkit
policy. The source language is Spanish.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
POT = I18N / "static-linux.pot"

PY = (sorted(ROOT.glob("sl-welcome/src/**/*.py"))
      + [ROOT / "sl-ctl" / n for n in ("sl-ctl.py", "sl-quick", "sl-hypr-guide")]
      + sorted(ROOT.glob("installer/calamares/modules/*/main.py")))
SH = [ROOT / "sl-ctl" / "sl-screenshot"] + sorted(ROOT.glob("sl-ctl/sl-*.sh"))
JS = [ROOT / "entornos/hyprland-common/skel/.config/ags/widget/Bar.tsx"]


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def theme_comment(conf: str) -> str | None:
    """Same rule as sl-welcome's appearance page."""
    for line in conf.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("# ").split(":", 1)[-1].strip().split(". ")[0].rstrip(".")
    return None


def yaml_block(lines: list[str], i: int) -> tuple[str, int]:
    """Value of a `key: >-` folded block or a one-line `key: "value"` at lines[i]."""
    head = lines[i].split(":", 1)[1].strip()
    if head in (">-", ">", "|", "|-"):
        indent = None
        parts = []
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if ln.strip() == "":
                break
            lead = len(ln) - len(ln.lstrip())
            if indent is None:
                indent = lead
            if lead < indent:
                break
            parts.append(ln.strip())
            j += 1
        return " ".join(parts), j
    return head.strip().strip('"').strip("'"), i + 1


def data_strings() -> list[tuple[str, str, str | None]]:
    """(msgid, location, translator comment)."""
    out: list[tuple[str, str, str | None]] = []
    add = lambda s, where, note=None: s and out.append((s, where, note))  # noqa: E731

    for f in sorted(ROOT.glob("sl-welcome/catalog/*.yaml")):
        for n, line in enumerate(f.read_text().splitlines(), 1):
            m = re.match(r'\s*(category|desc):\s*"?(.*?)"?\s*$', line)
            if m:
                add(m.group(2), f"{rel(f)}:{n}",
                    "app category in the sl-welcome catalog" if m.group(1) == "category"
                    else "one-line app description in the sl-welcome catalog")

    for f in sorted(ROOT.glob("branding/themes/*/theme.conf")):
        text = f.read_text()
        m = re.search(r"^name=(.+)$", text, re.M)
        if m:
            add(m.group(1).strip(), rel(f), "theme name")
        c = theme_comment(text)
        add(c, rel(f), "short description of a theme")

    lua = ROOT / "entornos/hyprland-common/static.lua"
    for n, line in enumerate(lua.read_text().splitlines(), 1):
        m = re.match(r'\s*bind\(.*,\s*"([^"]+)"\s*(,.*)?\)\s*$', line)
        if m:
            cat, _, text = m.group(1).partition(": ")
            if text:
                add(cat, f"{rel(lua)}:{n}", "group of keyboard shortcuts in the Hyprland guide")
                add(text, f"{rel(lua)}:{n}", "what a keyboard shortcut does (Hyprland guide)")

    for f in sorted(ROOT.glob("installer/calamares/modules/*/module.conf")):
        lines = f.read_text().splitlines()
        i = 0
        while i < len(lines):
            m = re.match(r"\s*(step|name|description):", lines[i])
            if m:
                val, j = yaml_block(lines, i)
                add(val, f"{rel(f)}:{i + 1}", f"installer page ({m.group(1)})")
                i = j
            else:
                i += 1

    qml = ROOT / "installer/calamares/branding/staticlinux/show.qml"
    for n, line in enumerate(qml.read_text().splitlines(), 1):
        for key, val in re.findall(r'\b(title|body):\s*"((?:[^"\\]|\\.)*)"', line):
            if val != "Static Linux":
                add(val.replace("\\n", "\n"), f"{rel(qml)}:{n}", "installer slideshow")

    for f in sorted(ROOT.glob("branding/themes/templates/**/*.in")):
        for n, line in enumerate(f.read_text().splitlines(), 1):
            for val in re.findall(r'\{\{_\s*"([^"]+)"\s*\}\}', line):
                add(val, f"{rel(f)}:{n}")

    for f in DESKTOP_FILES():
        for n, line in enumerate(f.read_text().splitlines(), 1):
            m = re.match(r"(Name|GenericName|Comment)=(.+)$", line)
            if m:
                add(m.group(2), f"{rel(f)}:{n}", "menu entry")

    for f in sorted(ROOT.glob("sl-welcome/data/*.policy")):
        for n, line in enumerate(f.read_text().splitlines(), 1):
            m = re.search(r"<(description|message)>(.+)</\1>", line)
            if m:
                add(m.group(2), f"{rel(f)}:{n}", "password prompt")
    return out


def DESKTOP_FILES() -> list[Path]:
    return [ROOT / "sl-welcome/data/dev.staticforge.welcome.desktop",
            ROOT / "packages/staticlinux-base/sl-screenshot.desktop",
            ROOT / "iso/airootfs-common/usr/share/applications/sl-live-install.desktop"]


def po_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        common = ["xgettext", "--from-code=UTF-8", "--add-comments=TRANSLATORS",
                  "--package-name=static-linux", "--msgid-bugs-address=staticforge@staticforge.me",
                  "--no-wrap", "--sort-by-file"]
        subprocess.run([*common, "-L", "Python", "-k_", "-kN_", "-k_tr", "-kngettext:1,2",
                        "-o", str(tmp / "py.pot"), *map(rel, PY)], cwd=ROOT, check=True)
        subprocess.run([*common, "-L", "Shell", "-kt", "-o", str(tmp / "sh.pot"),
                        *map(rel, SH)], cwd=ROOT, check=True)
        subprocess.run([*common, "-L", "JavaScript", "-k_", "-o", str(tmp / "js.pot"),
                        *map(rel, JS)], cwd=ROOT, check=True)
        seen: dict[str, list] = {}
        for msgid, where, note in data_strings():
            seen.setdefault(msgid, [[], set()])
            seen[msgid][0].append(where)
            if note:
                seen[msgid][1].add(note)
        lines = ['msgid ""', 'msgstr ""', '"Content-Type: text/plain; charset=UTF-8\\n"', ""]
        for msgid, (where, notes) in seen.items():
            lines += [f"#. {n}" for n in sorted(notes)]
            lines.append("#: " + " ".join(where))
            lines += [f'msgid "{po_escape(msgid)}"', 'msgstr ""', ""]
        (tmp / "data.pot").write_text("\n".join(lines))
        pots = [str(tmp / f"{n}.pot") for n in ("py", "sh", "js", "data") if (tmp / f"{n}.pot").exists()]
        subprocess.run(["msgcat", "--use-first", "--no-wrap", "-o", str(POT), *pots], check=True)
    # msgcat drops the header fields xgettext wrote; put the essentials back
    pot = POT.read_text()
    if "Project-Id-Version" not in pot:
        pot = pot.replace('"Content-Type: text/plain; charset=UTF-8\\n"',
                          '"Project-Id-Version: static-linux\\n"\n"Language: \\n"\n'
                          '"MIME-Version: 1.0\\n"\n"Content-Type: text/plain; charset=UTF-8\\n"\n'
                          '"Content-Transfer-Encoding: 8bit\\n"', 1)
        POT.write_text(pot)
    n = pot.count("\nmsgid ") - 1
    print(f"{rel(POT)}: {n} cadenas")
    for po in sorted((I18N / "po").glob("*.po")):
        subprocess.run(["msgmerge", "--quiet", "--update", "--backup=none", "--no-wrap",
                        "--no-fuzzy-matching", str(po), str(POT)], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
