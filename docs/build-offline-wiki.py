#!/usr/bin/env python3
"""Static Linux — render docs/wiki into one self-contained offline HTML page.

Shipped by staticlinux-base at /usr/share/doc/static-linux/wiki/index.html so
sl-welcome's "Wiki" opens without a network connection. Follows the page
order of mkdocs.yml's `nav:`; every page becomes a section, shown one at a
time through the URL fragment (#instalacion, #herramientas-sl-ctl, ...).
No JavaScript, no web fonts: it uses the brand fonts installed on the system.

    python3 docs/build-offline-wiki.py OUT.html
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import markdown
import yaml

REPO = Path(__file__).resolve().parent.parent
WIKI = REPO / "docs" / "wiki"
ONLINE = "https://staticforge.me/static-linux/"


def flatten(nav, group=None):
    for entry in nav:
        (title, target), = entry.items()
        if isinstance(target, list):
            yield from flatten(target, title)
        else:
            yield group, title, target


def anchor(md_path: str) -> str:
    return "p-" + re.sub(r"[^a-z0-9]+", "-", md_path.lower().removesuffix(".md")).strip("-")


def main(out: Path) -> None:
    cfg = yaml.safe_load((REPO / "mkdocs.yml").read_text(encoding="utf-8"))
    pages = list(flatten(cfg["nav"]))
    md = markdown.Markdown(extensions=["admonition", "tables", "fenced_code", "toc", "sane_lists"])

    nav_html, sections = [], []
    last_group = None
    for group, title, path in pages:
        if group != last_group and group:
            nav_html.append(f'<p class="group">{html.escape(group)}</p>')
        last_group = group
        a = anchor(path)
        nav_html.append(f'<a href="#{a}" class="{"sub" if group else ""}">{html.escape(title)}</a>')

        body = md.reset().convert((WIKI / path).read_text(encoding="utf-8"))
        # links between wiki pages -> in-page anchors
        base = Path(path).parent

        def relink(m):
            target, frag = m.group(1), m.group(2) or ""
            if re.match(r"[a-z]+:", target):
                return m.group(0)
            resolved = (base / target).as_posix()
            resolved = re.sub(r"[^/]+/\.\./", "", resolved)
            return f'href="#{anchor(resolved)}"' if not frag else f'href="#{anchor(resolved)}"'
        body = re.sub(r'href="([^"#]+\.md)(#[^"]*)?"', relink, body)
        sections.append(f'<section id="{a}">{body}</section>')

    first = anchor(pages[0][2])
    page = TEMPLATE.format(nav="\n".join(nav_html), sections="\n".join(sections),
                           first=first, online=ONLINE)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({len(pages)} pages, {out.stat().st_size // 1024} KiB)")


TEMPLATE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wiki de Static Linux</title>
<style>
:root {{ --void:#0B0C10; --panel:#12141A; --line:#262A34; --text:#D6D8E0; --muted:#8A8F9C;
        --green:#00C8A0; --amber:#F2B33D; --orange:#E8792B; --red:#C2452D; --brown:#6B3A1F; --teal:#2A9D8F; }}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; background:var(--void); color:var(--text); font:16px/1.65 "Space Grotesk","Noto Sans",sans-serif; }}
header {{ position:relative; overflow:hidden; padding:28px 32px 24px; border-bottom:1px solid var(--line); }}
header h1 {{ margin:0; font:800 30px "Outfit","Space Grotesk",sans-serif; letter-spacing:.02em; }}
header p {{ margin:4px 0 0; color:var(--muted); }}
header svg {{ position:absolute; right:0; top:0; height:100%; }}
.wrap {{ display:flex; min-height:calc(100vh - 110px); }}
nav {{ width:270px; flex:none; padding:18px 12px; border-right:1px solid var(--line); background:var(--panel); }}
nav a {{ display:block; padding:6px 12px; border-radius:8px; color:var(--text); text-decoration:none; transition:background .15s; }}
nav a.sub {{ padding-left:24px; font-size:15px; }}
nav a:hover {{ background:#1C1F27; color:var(--green); }}
nav .group {{ margin:14px 12px 4px; font-size:12px; letter-spacing:.12em; text-transform:uppercase; color:var(--amber); }}
nav .online {{ margin-top:18px; border:1px solid var(--line); }}
main {{ flex:1; min-width:0; padding:8px 44px 60px; max-width:960px; }}
section {{ display:none; animation:fade .25s ease-out; }}
section:target, #{first}:not(:has(~ section:target)) {{ display:block; }}
@keyframes fade {{ from {{ opacity:0; transform:translateY(6px); }} to {{ opacity:1; }} }}
h1, h2, h3 {{ font-family:"Outfit","Space Grotesk",sans-serif; line-height:1.25; }}
h1 {{ font-size:30px; border-bottom:3px solid var(--green); padding-bottom:6px; display:inline-block; }}
h2 {{ margin-top:34px; color:#E6E8EE; }}
a {{ color:var(--green); }}
code, pre {{ font-family:"JetBrains Mono",monospace; font-size:14px; }}
code {{ background:#1A1D25; padding:2px 6px; border-radius:6px; }}
pre {{ background:#14161D; border:1px solid var(--line); border-radius:10px; padding:14px 16px; overflow:auto; }}
pre code {{ background:none; padding:0; }}
table {{ border-collapse:collapse; width:100%; margin:16px 0; font-size:15px; }}
th, td {{ border:1px solid var(--line); padding:8px 10px; text-align:left; vertical-align:top; }}
th {{ background:#1A1D25; color:var(--amber); }}
.admonition {{ border-left:4px solid var(--green); background:#14161D; border-radius:8px; padding:4px 16px; margin:16px 0; }}
.admonition.warning {{ border-color:var(--amber); }}
.admonition.danger {{ border-color:var(--red); }}
.admonition-title {{ font-weight:700; }}
@media (max-width: 760px) {{ .wrap {{ display:block; }} nav {{ width:auto; border-right:none; border-bottom:1px solid var(--line); }} main {{ padding:8px 18px 40px; }} }}
</style></head><body>
<header>
  <h1>Wiki de Static Linux</h1>
  <p>fast · private · yours — copia local, funciona sin conexión</p>
  <svg viewBox="0 0 160 110" aria-hidden="true">
    <g fill="none" stroke-width="9">
      <path d="M 50 -5 A 115 115 0 0 0 165 110" stroke="var(--brown)"/>
      <path d="M 62 -5 A 103 103 0 0 0 165 98" stroke="var(--red)"/>
      <path d="M 74 -5 A 91 91 0 0 0 165 86" stroke="var(--orange)"/>
      <path d="M 86 -5 A 79 79 0 0 0 165 74" stroke="var(--amber)"/>
      <path d="M 98 -5 A 67 67 0 0 0 165 62" stroke="var(--teal)"/>
    </g>
  </svg>
</header>
<div class="wrap">
<nav>
{nav}
<a class="online" href="{online}">Wiki online ↗</a>
</nav>
<main>
{sections}
</main>
</div>
</body></html>
"""

if __name__ == "__main__":
    main(Path(sys.argv[1]))
