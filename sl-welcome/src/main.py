#!/usr/bin/env python3
"""
sl-welcome — Static Linux first-boot app (Fase 7).

    sl-welcome              always opens (menu launch, `sl-ctl welcome`)
    sl-welcome --autostart  opens once per user, then no-ops on later logins
                            (used by the XDG autostart .desktop entry)

GTK4 + libadwaita so it follows the active accent automatically: the accent
system (branding/accents/apply.sh) already writes libadwaita's own named
colours (accent_color, accent_bg_color, ...) into ~/.config/gtk-4.0/gtk.css.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
# i18n/sl_i18n.py: ../../i18n in the repo and in /usr/lib/static-linux
sys.path.insert(0, str(SRC_DIR.parent.parent / "i18n"))

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402

from window import WelcomeWindow  # noqa: E402

APP_ID = "dev.staticforge.welcome"
STATE_FILE = Path.home() / ".local" / "state" / "static-linux" / "welcome-shown"


class WelcomeApp(Adw.Application):
    def __init__(self, autostart: bool) -> None:
        super().__init__(application_id=APP_ID,
                          flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.autostart = autostart
        self.connect("activate", self.on_activate)

    def on_activate(self, app: Adw.Application) -> None:
        if self.autostart and STATE_FILE.exists():
            self.quit()
            return

        # libadwaita ignores the GTK theme, and a fresh XFCE session sets no
        # color-scheme preference, so it fell back to light
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(str(SRC_DIR / "style.css"))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.touch(exist_ok=True)

        win = WelcomeWindow(self)
        win.present()


def main() -> int:
    autostart = "--autostart" in sys.argv[1:]
    app = WelcomeApp(autostart)
    return app.run([sys.argv[0]])


if __name__ == "__main__":
    sys.exit(main())
