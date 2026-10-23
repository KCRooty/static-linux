"""sl-welcome's single window: a ToolbarView with a ViewSwitcher over 4 pages."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from pages import appearance, catalog, overview, privacy  # noqa: E402


class WelcomeWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app, title="Bienvenido a Static Linux",
                          default_width=760, default_height=620)

        self.toast_overlay = Adw.ToastOverlay()

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        switcher = Adw.ViewSwitcher(policy=Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)
        toolbar_view.add_top_bar(header)

        stack = Adw.ViewStack()
        stack.add_titled_with_icon(overview.build(), "overview", "General",
                                    "go-home-symbolic")
        stack.add_titled_with_icon(appearance.build(self.toast_overlay),
                                    "appearance", "Apariencia",
                                    "applications-graphics-symbolic")
        stack.add_titled_with_icon(privacy.build(self.toast_overlay), "privacy",
                                    "Privacidad", "channel-secure-symbolic")
        stack.add_titled_with_icon(catalog.build(self.toast_overlay), "catalog",
                                    "Catálogo", "system-software-install-symbolic")

        switcher.set_stack(stack)
        # short fade-in of the page being switched to
        stack.connect("notify::visible-child", self._fade_in)
        toolbar_view.set_content(stack)
        self.toast_overlay.set_child(toolbar_view)
        self.set_content(self.toast_overlay)

    def _fade_in(self, stack: Adw.ViewStack, _pspec) -> None:
        child = stack.get_visible_child()
        if child is None:
            return
        target = Adw.PropertyAnimationTarget.new(child, "opacity")
        self._page_anim = Adw.TimedAnimation.new(child, 0.0, 1.0, 220, target)
        self._page_anim.play()
