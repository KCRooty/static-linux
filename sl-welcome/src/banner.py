"""Overview header: the 70s "groovy" stripes in the active accent's tones.

Same five tones as branding/wallpapers/gen-wallpaper.py, so the banner
matches the wallpaper. Painted with cairo only when the widget is resized
or while the one-off entrance animation runs (Adw.TimedAnimation, which
also honours the desktop's "reduce animations" setting).
"""

from __future__ import annotations

import math

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_foreign("cairo")  # ImportError without python-cairo; overview falls back
from gi.repository import Adw, Gtk  # noqa: E402


def _rgb(hexstr: str) -> tuple[float, float, float]:
    h = hexstr.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def stripe_colors(acc: dict) -> list[tuple[float, float, float]]:
    bg, dim = _rgb(acc["bg"]), _rgb(acc["dim"])
    accent, detail = _rgb(acc["accent"]), _rgb(acc["detail"])
    return [_mix(dim, bg, 0.35), dim, accent, _mix(accent, (1, 1, 1), 0.35), detail]


class GroovyBanner(Gtk.Overlay):
    HEIGHT = 168

    def __init__(self, acc: dict) -> None:
        super().__init__()
        self._colors = stripe_colors(acc)
        self._bg = _mix(_rgb(acc["bg"]), (1, 1, 1), 0.04)
        self._t = 0.0

        area = Gtk.DrawingArea(content_height=self.HEIGHT, hexpand=True)
        area.set_draw_func(self._draw)
        self._area = area
        self.set_child(area)

        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2,
                       halign=Gtk.Align.START, valign=Gtk.Align.START,
                       margin_start=26, margin_top=22)
        text.append(Gtk.Label(label="Static Linux", xalign=0, css_classes=["sl-wordmark"]))
        text.append(Gtk.Label(label="fast · private · yours", xalign=0, css_classes=["sl-tagline"]))
        self.add_overlay(text)

        target = Adw.CallbackAnimationTarget.new(self._tick)
        self._anim = Adw.TimedAnimation.new(area, 0.0, 1.0, 900, target)
        self._anim.set_easing(Adw.Easing.EASE_OUT_CUBIC)
        area.connect("map", lambda *_: self._anim.play())

    def _tick(self, value: float) -> None:
        self._t = value
        self._area.queue_draw()

    def _draw(self, _area, cr, w: int, h: int) -> None:
        r_box = 16
        cr.new_sub_path()
        cr.arc(w - r_box, r_box, r_box, -math.pi / 2, 0)
        cr.arc(w - r_box, h - r_box, r_box, 0, math.pi / 2)
        cr.arc(r_box, h - r_box, r_box, math.pi / 2, math.pi)
        cr.arc(r_box, r_box, r_box, math.pi, 3 * math.pi / 2)
        cr.close_path()
        cr.set_source_rgb(*self._bg)
        cr.fill_preserve()
        cr.clip()

        t = self._t
        sw = h * 0.075
        gap = sw * 0.22
        # main band: in from the left, curving down out of the bottom edge
        cx = w * 0.74 - (1 - t) * w * 0.35
        cy = h * 1.0
        r0 = h * 0.50
        cr.set_line_width(sw)
        for i, col in enumerate(self._colors):
            r = r0 - i * (sw + gap) - sw / 2
            cr.set_source_rgba(*col, t)
            cr.move_to(-10, cy - r)
            cr.line_to(cx, cy - r)
            cr.arc(cx, cy, r, -math.pi / 2, 0)
            cr.stroke()
        # small rainbow tucked into the top-right corner
        c0 = h * 0.42
        cr.set_line_width(sw * 0.7)
        for i, col in enumerate(self._colors):
            r = c0 - i * (sw * 0.7 + gap) - sw * 0.35
            cr.set_source_rgba(*col, t)
            cr.arc(w, 0, r, math.pi / 2, math.pi)
            cr.stroke()
