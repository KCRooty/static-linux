"""Every graphical environment list must bring exactly one display manager.

2026-11-14: Cinnamon, i3, bspwm and sway shipped without one and booted to a
console login; Calamares only enables the display managers that exist.
Run: python3 -m unittest discover -s packages/tests
"""
import re
import unittest
from pathlib import Path

LISTS = Path(__file__).resolve().parent.parent / "lists"
DMS = {"gdm", "lightdm", "sddm"}
# environment -> package list, from the entorno-pkgs Calamares job
ENV_LISTS = {"xfce", "openbox", "hyprland-lite", "hyprland-full", "kde", "gnome",
             "cinnamon", "i3", "bspwm", "sway"}


def packages(name: str) -> set[str]:
    text = (LISTS / f"{name}.list").read_text()
    return {ln.split()[0] for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")}


class DisplayManagers(unittest.TestCase):
    def test_each_environment_has_one_display_manager(self):
        for env in sorted(ENV_LISTS):
            with self.subTest(env=env):
                self.assertEqual(len(packages(env) & DMS), 1, f"{env}.list: {sorted(packages(env) & DMS)}")

    def test_env_lists_match_the_installer(self):
        job = (LISTS.parent.parent / "installer/calamares/modules/entorno-pkgs/main.py").read_text()
        used = set(re.findall(r'"packages/lists/([a-z0-9-]+)\.list"', job))
        used -= {"sin-escritorio"}
        self.assertEqual(used, ENV_LISTS)


# 2026-11-14 (real install): sl-welcome's installs failed with "Error creating textual
# authentication agent" on XFCE; only Hyprland shipped a polkit agent. GNOME and
# Cinnamon have one built into the shell.
AGENTS = {"polkit-gnome", "polkit-kde-agent", "hyprpolkitagent", "gnome-shell", "cinnamon"}


class PolkitAgents(unittest.TestCase):
    def test_each_environment_can_ask_for_a_password(self):
        for env in sorted(ENV_LISTS):
            with self.subTest(env=env):
                self.assertTrue(packages(env) & AGENTS, f"{env}.list has no polkit agent")


class OneNamePerLine(unittest.TestCase):
    """2026-11-14: "hyprpaper swaybg" on one line reached pacman as a single name and
    Hyprland lite/full failed to install (iso/build.sh splits words, the installer
    did not). The installer now splits too; keep the lists one name per line anyway."""

    def test_every_list_line_is_one_package(self):
        for path in sorted(LISTS.glob("*.list")):
            for n, ln in enumerate(path.read_text().splitlines(), 1):
                body = ln.split("#", 1)[0].split()
                with self.subTest(list=path.name, line=n):
                    self.assertLessEqual(len(body), 1, ln)


if __name__ == "__main__":
    unittest.main()
