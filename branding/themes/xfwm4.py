"""Generate the "StaticLinux" xfwm4 window decoration from a theme palette.

Three styles (theme.conf `style=`), all solid, all from the same palette:

  minimal   DESIGN.md §5: 2 px border (accent on the active window, `line`
            otherwise), 8 px corners, buttons as three 10 px dots in text_dim;
            on hover close turns `danger`, the others `accent`.
  aero      Frutiger Aero: glossy title bar (a light upper half over a tinted
            lower half), a 4 px frame in the title's colour, glossy capsule
            buttons with glyphs, the close one red.
  ventanas  Close to Windows 11: flat title bar, 1 px border, 46 px wide
            buttons with thin glyphs (minimise, maximise, close); close turns
            red on hover.
  estante   A shelf-and-launcher desktop (ChromeOS-like, no Google assets):
            tall flat title bar in the surface colour, 1 px border, 12 px
            corners, thin glyphs; hover draws a neutral circle and close is
            never red.

xfwm4 themes are XPM images. Corners are shaped with the XPM "None" colour
(xfwm4 uses it as the window mask); everything else is antialiased by
blending against the title bar, which is opaque, so no alpha is needed.
"""

from __future__ import annotations

from dataclasses import dataclass

SS = 4  # supersampling for anything round or diagonal


@dataclass(frozen=True)
class Style:
    title_h: int
    border: int
    radius: int
    button_w: int
    button_offset: int
    title_align: str


STYLES = {
    "minimal": Style(title_h=30, border=2, radius=8, button_w=20, button_offset=6, title_align="center"),
    "aero": Style(title_h=30, border=4, radius=8, button_w=30, button_offset=6, title_align="left"),
    "ventanas": Style(title_h=32, border=1, radius=8, button_w=46, button_offset=0, title_align="left"),
    "estante": Style(title_h=34, border=1, radius=12, button_w=34, button_offset=4, title_align="left"),
}


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(c) -> str:
    return "%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in c)


def _mix(a: str, b: str, t: float) -> str:
    """a -> b by t (0..1); hex in, hex out, no '#'."""
    ca, cb = _rgb(a), _rgb(b)
    return _hex(tuple(ca[i] + (cb[i] - ca[i]) * t for i in range(3)))


class Canvas:
    """A tiny pixel grid that serialises to XPM. None = transparent."""

    def __init__(self, w: int, h: int, fill: str | None) -> None:
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def set(self, x: int, y: int, colour: str | None) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = colour

    def get(self, x: int, y: int) -> str | None:
        return self.px[y][x]

    def xpm(self, name: str) -> str:
        colours = sorted({c for row in self.px for c in row if c is not None})
        chars = "+.@#$%&*=-;:>,<1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        cpp = 1 if len(colours) < len(chars) else 2

        def code(i: int) -> str:
            return chars[i] if cpp == 1 else chars[i // len(chars)] + chars[i % len(chars)]
        table = {c: code(i + 1) for i, c in enumerate(colours)}
        none = " " * cpp
        lines = [f'"{self.w} {self.h} {len(colours) + 1} {cpp}",', f'"{none} c None",']
        lines += [f'"{table[c]} c #{c}",' for c in colours]
        rows = ['"' + "".join(table[c] if c else none for c in row) + '"' for row in self.px]
        return "/* XPM */\nstatic char * " + name + "[] = {\n" + "\n".join(lines) + "\n" + ",\n".join(rows) + "};\n"


# ---------------------------------------------------------------- geometry

def _cover(x: int, y: int, inside) -> float:
    """Fraction of pixel (x, y) for which inside(px, py) holds."""
    hits = sum(inside(x + (i + 0.5) / SS, y + (j + 0.5) / SS) for i in range(SS) for j in range(SS))
    return hits / (SS * SS)


def _round_rect(x0: float, y0: float, x1: float, y1: float, r: float):
    def inside(px: float, py: float) -> bool:
        if not (x0 <= px <= x1 and y0 <= py <= y1):
            return False
        cx = min(max(px, x0 + r), x1 - r)
        cy = min(max(py, y0 + r), y1 - r)
        return (px - cx) ** 2 + (py - cy) ** 2 <= r * r
    return inside


def _segment(ax: float, ay: float, bx: float, by: float, width: float):
    def inside(px: float, py: float) -> bool:
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        qx, qy = ax + t * dx, ay + t * dy
        return (px - qx) ** 2 + (py - qy) ** 2 <= (width / 2) ** 2
    return inside


def _paint(c: Canvas, inside, colour, box=None) -> None:
    """Blend `colour` (hex, or f(y) -> hex) over the canvas wherever inside() covers."""
    x0, y0, x1, y1 = box or (0, 0, c.w, c.h)
    for y in range(max(0, y0), min(c.h, y1)):
        col = colour(y) if callable(colour) else colour
        for x in range(max(0, x0), min(c.w, x1)):
            a = _cover(x, y, inside)
            if a and c.get(x, y) is not None:
                c.set(x, y, _mix(c.get(x, y), col, a))


# ---------------------------------------------------------------- palettes per style

def _rows(theme: dict[str, str], style: str, active: bool) -> tuple[list[str], str]:
    """(title bar colour per row, frame colour) for one window state."""
    s = STYLES[style]
    bg, line, accent = theme["bg"], theme["line"], theme["accent"]
    if style == "aero":
        tint = _mix(bg, accent, 0.30 if active else 0.10)
        deep = _mix(bg, accent, 0.45 if active else 0.16)
        half = s.title_h // 2
        rows = [_mix("FFFFFF", tint, 0.25 + 0.5 * y / half) for y in range(half)]
        rows += [_mix(deep, tint, (y - half) / (s.title_h - half)) for y in range(half, s.title_h)]
        return rows, rows[-1]
    if style == "ventanas":
        return [bg] * s.title_h, line
    if style == "estante":
        return [theme["surface"] if active else bg] * s.title_h, line
    return [bg] * s.title_h, accent if active else line


def _frame_colour(theme, style, active) -> tuple[str, str]:
    """(outer line, inner fill) of the side and bottom frame."""
    rows, frame = _rows(theme, style, active)
    if style == "aero":
        outer = _mix(theme["accent"], "000000", 0.25) if active else theme["line"]
        return outer, frame
    return frame, frame


# ---------------------------------------------------------------- pieces

def _title_column(rows: list[str], outer: str, s: Style) -> Canvas:
    c = Canvas(1, s.title_h, None)
    for y, col in enumerate(rows):
        c.set(0, y, outer if y < (1 if s.border > 2 else s.border) else col)
    return c


def _corner_top(rows, outer, inner, s: Style, flip: bool) -> Canvas:
    r, b = s.radius, s.border
    line_w = 1 if b > 2 else b  # aero: 1 px outer line, the rest is frame fill
    c = Canvas(r, s.title_h, None)
    for y in range(s.title_h):
        for x in range(r):
            px, py = x + 0.5, y + 0.5
            outside = y < r and (px - r) ** 2 + (py - r) ** 2 > r * r
            if outside:
                col = None
            elif x < line_w or y < line_w or (y < r and (px - r) ** 2 + (py - r) ** 2 > (r - line_w) ** 2):
                col = outer
            elif x < b:
                col = inner
            else:
                col = rows[y]
            c.set(r - 1 - x if flip else x, y, col)
    return c


def _corner_bottom(outer, inner, s: Style, flip: bool) -> Canvas:
    r = s.radius
    b = s.border
    line_w = 1 if b > 2 else b
    c = Canvas(r, r, None)
    for y in range(r):
        for x in range(r):
            px, py = x + 0.5, (r - 1 - y) + 0.5
            if (px - r) ** 2 + (py - r) ** 2 > r * r and x < r and (r - 1 - y) < r:
                col = None
            elif x < line_w or (r - 1 - y) < line_w or (px - r) ** 2 + (py - r) ** 2 > (r - line_w) ** 2:
                col = outer
            else:
                col = inner
            c.set(r - 1 - x if flip else x, y, col)
    return c


def _side(outer, inner, s: Style, vertical: bool, flip: bool) -> Canvas:
    line_w = 1 if s.border > 2 else s.border
    cols = [outer] * line_w + [inner] * (s.border - line_w)
    if flip:
        cols = cols[::-1]
    if vertical:  # left / right strip: border wide, 1 tall
        c = Canvas(s.border, 1, None)
        for x, col in enumerate(cols):
            c.set(x, 0, col)
    else:         # bottom strip: 1 wide, border tall (outer line at the bottom)
        c = Canvas(1, s.border, None)
        for y, col in enumerate(cols[::-1]):
            c.set(0, y, col)
    return c


GLYPHS = {
    "close": lambda cx, cy, k, w: [_segment(cx - k, cy - k, cx + k, cy + k, w),
                                   _segment(cx - k, cy + k, cx + k, cy - k, w)],
    "hide": lambda cx, cy, k, w: [_segment(cx - k, cy, cx + k, cy, w)],
    "maximize": lambda cx, cy, k, w: [_segment(cx - k, cy - k, cx + k, cy - k, w), _segment(cx + k, cy - k, cx + k, cy + k, w),
                                      _segment(cx + k, cy + k, cx - k, cy + k, w), _segment(cx - k, cy + k, cx - k, cy - k, w)],
    "maximize-toggled": lambda cx, cy, k, w: [
        _segment(cx - k, cy - k + 2, cx + k - 2, cy - k + 2, w), _segment(cx + k - 2, cy - k + 2, cx + k - 2, cy + k, w),
        _segment(cx + k - 2, cy + k, cx - k, cy + k, w), _segment(cx - k, cy + k, cx - k, cy - k + 2, w),
        _segment(cx - k + 2, cy - k, cx + k, cy - k, w), _segment(cx + k, cy - k, cx + k, cy + k - 2, w)],
}


def _button(theme, style: str, active: bool, button: str, state: str) -> Canvas:
    """state: normal | prelight | pressed."""
    s = STYLES[style]
    rows, _ = _rows(theme, style, active)
    outer, _ = _frame_colour(theme, style, active)
    c = Canvas(s.button_w, s.title_h, None)
    col = _title_column(rows, outer, s)
    for y in range(s.title_h):
        for x in range(s.button_w):
            c.set(x, y, col.get(0, y))
    top = 1 if s.border > 2 else s.border
    cx, cy = s.button_w / 2, top + (s.title_h - top) / 2

    if style == "minimal":
        dot = theme["danger"] if button == "close" else theme["accent"]
        normal = theme["text_dim"] if active else theme["line"]
        colour = {"normal": normal, "prelight": dot, "pressed": _mix(dot, theme["bg"], 0.35)}[state]
        _paint(c, lambda px, py: (px - cx) ** 2 + (py - cy) ** 2 <= 25, colour)
        return c

    if style == "aero":
        # glossy capsule: close is red, the others take the title tint
        base = "C8352B" if button == "close" else _mix(theme["bg"], theme["accent"], 0.35 if active else 0.12)
        if state == "prelight":
            base = "E0453A" if button == "close" else _mix(base, theme["accent"], 0.45)
        elif state == "pressed":
            base = _mix(base, "000000", 0.25)
        if not active and state == "normal" and button == "close":
            base = _mix(theme["bg"], "C8352B", 0.35)
        x0, x1, y0, y1 = 2.0, s.button_w - 2.0, top + 5.0, s.title_h - 5.0
        mid = (y0 + y1) / 2
        def capsule_colour(y: int) -> str:
            if y < mid:
                return _mix("FFFFFF", base, 0.35 + 0.4 * (y - y0) / (mid - y0))
            return _mix(_mix(base, "000000", 0.12), base, (y - mid) / (y1 - mid))
        _paint(c, _round_rect(x0, y0, x1, y1, 4.0), _mix(base, "000000", 0.35))          # rim
        _paint(c, _round_rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, 3.0), capsule_colour)     # body
        glyph = "FFFFFF" if button == "close" or theme["mode"] == "dark" else _mix(theme["text"], base, 0.15)
        for shape in GLYPHS[button](cx, mid, 3.5, 1.8):
            _paint(c, shape, glyph)
        return c

    if style == "estante":
        # neutral circle on hover/press, the same for every button
        if state != "normal":
            ring = _mix(rows[0], theme["text"], 0.12 if state == "prelight" else 0.20)
            r = min(s.button_w, s.title_h - top) / 2 - 3
            _paint(c, lambda px, py: (px - cx) ** 2 + (py - cy) ** 2 <= r * r, ring)
        glyph = theme["text"] if active else theme["text_dim"]
        for shape in GLYPHS[button](cx, cy, 4.5, 1.4):
            _paint(c, shape, glyph)
        return c

    # ventanas: flat cell, hover tint; close turns red
    if state != "normal":
        hover = "C42B1C" if button == "close" else _mix(theme["bg"], theme["text"], 0.10 if state == "prelight" else 0.06)
        if button == "close" and state == "pressed":
            hover = "B22A1C"
        for y in range(top, s.title_h):
            for x in range(s.button_w):
                c.set(x, y, hover)
    glyph = "FFFFFF" if (button == "close" and state != "normal") else (theme["text"] if active else theme["text_dim"])
    for shape in GLYPHS[button](cx, cy, 5.0, 1.0):
        _paint(c, shape, glyph)
    return c


# ---------------------------------------------------------------- theme

def generate(theme: dict[str, str]) -> dict[str, str]:
    style = theme.get("style", "minimal")
    if style not in STYLES:
        raise ValueError(f"unknown style '{style}' (one of {', '.join(STYLES)})")
    s = STYLES[style]
    files: dict[str, str] = {}
    for state in ("active", "inactive"):
        active = state == "active"
        rows, _ = _rows(theme, style, active)
        outer, inner = _frame_colour(theme, style, active)
        parts = {
            f"top-left-{state}": _corner_top(rows, outer, inner, s, flip=False),
            f"top-right-{state}": _corner_top(rows, outer, inner, s, flip=True),
            f"bottom-left-{state}": _corner_bottom(outer, inner, s, flip=False),
            f"bottom-right-{state}": _corner_bottom(outer, inner, s, flip=True),
            f"left-{state}": _side(outer, inner, s, vertical=True, flip=False),
            f"right-{state}": _side(outer, inner, s, vertical=True, flip=True),
            f"bottom-{state}": _side(outer, inner, s, vertical=False, flip=False),
        }
        for i in range(1, 6):
            parts[f"title-{i}-{state}"] = _title_column(rows, outer, s)
        for button in ("close", "hide", "maximize", "maximize-toggled"):
            parts[f"{button}-{state}"] = _button(theme, style, active, button, "normal")
            if active:
                parts[f"{button}-prelight"] = _button(theme, style, True, button, "prelight")
                parts[f"{button}-pressed"] = _button(theme, style, True, button, "pressed")
        for name, canvas in parts.items():
            files[f"{name}.xpm"] = canvas.xpm(name.replace("-", "_"))
    top = 1 if s.border > 2 else s.border
    files["themerc"] = "\n".join([
        f"# Static Linux · {theme['name']} · style {style} (generated by sl-theme, edits are overwritten)",
        f"title_alignment={s.title_align}",
        "full_width_title=true",
        "title_shadow_active=false",
        "title_shadow_inactive=false",
        f"active_text_color=#{theme['text']}",
        f"inactive_text_color=#{theme['text_dim']}",
        f"button_offset={s.button_offset}",
        "button_spacing=0",
        f"title_vertical_offset_active={top // 2}",
        f"title_vertical_offset_inactive={top // 2}",
        "show_app_icon=false",
        "",
    ])
    return files


BUTTON_LAYOUT = {"minimal": "|HMC", "aero": "|HMC", "ventanas": "|HMC", "estante": "|HMC"}
