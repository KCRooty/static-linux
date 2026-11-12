"""
Loads the extra-apps catalog (sl-welcome/catalog/*.yaml) for the Catálogo page.

Each file is one category (files sort by name, hence the NN- prefixes):

    category: "Juegos"
    apps:
      - id: heroic
        name: Heroic Games Launcher
        desc: Epic, GOG y Amazon.
        flatpak: com.heroicgameslauncher.hgl   # sources: pkg / flatpak / aur
        aur: heroic-games-launcher-bin         # (pkg may list several, space-separated)
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
