"""
Loads the extra-apps catalog (sl-welcome/catalog/*.yaml) for the Catálogo page.

Each file is one category:

    category: "Internet"
    apps:
      - id: brave-browser
        name: Brave
        desc: Navegador ya instalado por defecto — no aparece aquí.
        pkg: brave-bin
        aur: true
"""

from __future__ import annotations

import yaml

from paths import catalog_dir


def load_categories() -> list[dict]:
    cats = []
    d = catalog_dir()
    if not d.is_dir():
        return cats
    for f in sorted(d.glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text()) or {}
        except yaml.YAMLError:
            continue
        if "category" in data and "apps" in data:
            cats.append(data)
    return cats
