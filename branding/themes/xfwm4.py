"""Generate the "StaticLinux" xfwm4 window decoration from a theme palette.

DESIGN.md §5: solid frame, 2 px border (accent on the active window, `line`
otherwise), 8 px corners, no title text decoration, buttons as three 10 px
dots in text_dim; on hover close turns `danger`, the others `accent`.

xfwm4 themes are XPM images. Corners are shaped with the XPM "None" colour
(xfwm4 uses it as the window mask); the dots are antialiased by blending
against the title bar colour, which is opaque, so no alpha is needed.
"""

from __future__ import annotations

TITLE_H = 30      # title bar height, border included
BORDER = 2
RADIUS = 8
DOT = 10          # button dot diameter
BUTTON_W = 20     # each button cell: dot centred in 20 x TITLE_H
SS = 4            # supersampling for the dots


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(c: tuple[float, float, float]) -> str:
    return "#%02X%02X%02X" % tuple(round(v) for v in c)


def _mix(a: str, b: str, t: float) -> str:
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

    def xpm(self, name: str) -> str:
        colours = sorted({c for row in self.px for c in row if c is not None})
        chars = "+.@#$%&*=-;:>,<1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        cpp = 1 if len(colours) < len(chars) else 2
        def code(i: int) -> str:
            return chars[i] if cpp == 1 else chars[i // len(chars)] + chars[i % len(chars)]
        table = {c: code(i + 1) for i, c in enumerate(colours)}
        none = " " * cpp
        lines = [f'"{self.w} {self.h} {len(colours) + 1} {cpp}",', f'"{none} c None",']
        lines += [f'"{table[c]} c {c}",' for c in colours]
        rows = ['"' + "".join(table[c] if c else none for c in row) + '"' for row in self.px]
        body = ",\n".join(rows)
        return "/* XPM */\nstatic char * " + name + "[] = {\n" + "\n".join(lines) + "\n" + body + "};\n"


def _inside_round(x: float, y: float, r: float) -> bool:
    """Is pixel centre (x, y) inside a quarter circle of radius r at (r, r)?"""
    return (x - r) ** 2 + (y - r) ** 2 <= r * r


def _corner_top(border: str, bg: str, flip: bool) -> Canvas:
    c = Canvas(RADIUS, TITLE_H, bg)
    for y in range(TITLE_H):
        for x in range(RADIUS):
            px, py = x + 0.5, y + 0.5
            if y < RADIUS and not _inside_round(px, py, RADIUS):
                colour = None
            elif x < BORDER or y < BORDER or (y < RADIUS and not _inside_round(px, py, RADIUS - BORDER)):
                colour = "#" + border
            else:
                colour = "#" + bg
            c.set(RADIUS - 1 - x if flip else x, y, colour)
    return c


def _corner_bottom(border: str, bg: str, flip: bool) -> Canvas:
    c = Canvas(RADIUS, RADIUS, None)
    for y in range(RADIUS):
        for x in range(RADIUS):
            # mirror vertically: measure from the bottom edge
            px, py = x + 0.5, (RADIUS - 1 - y) + 0.5
            if not _inside_round(px, py, RADIUS):
                colour = None
            elif x < BORDER or (RADIUS - 1 - y) < BORDER or not _inside_round(px, py, RADIUS - BORDER):
                colour = "#" + border
            else:
                colour = "#" + bg
            c.set(RADIUS - 1 - x if flip else x, y, colour)
    return c


def _strip(w: int, h: int, colour: str) -> Canvas:
    return Canvas(w, h, "#" + colour)


def _title(border: str, bg: str) -> Canvas:
    c = Canvas(1, TITLE_H, "#" + bg)
    for y in range(BORDER):
        c.set(0, y, "#" + border)
    return c


def _button(border: str, bg: str, dot: str) -> Canvas:
    c = _title(border, bg)
    c.w, c.px = BUTTON_W, [[px[0]] * BUTTON_W for px in c.px]
    cx, cy, r = BUTTON_W / 2, BORDER + (TITLE_H - BORDER) / 2, DOT / 2
    for y in range(BORDER, TITLE_H):
        for x in range(BUTTON_W):
            hits = sum((x + (i + 0.5) / SS - cx) ** 2 + (y + (j + 0.5) / SS - cy) ** 2 <= r * r
                       for i in range(SS) for j in range(SS))
            if hits:
                c.set(x, y, _mix(bg, dot, hits / (SS * SS)))
    return c


def generate(theme: dict[str, str]) -> dict[str, str]:
    bg, line, accent = theme["bg"], theme["line"], theme["accent"]
    dim, danger = theme["text_dim"], theme["danger"]
    files: dict[str, str] = {}
    for state, border in (("active", accent), ("inactive", line)):
        parts = {
            f"top-left-{state}": _corner_top(border, bg, flip=False),
            f"top-right-{state}": _corner_top(border, bg, flip=True),
            f"bottom-left-{state}": _corner_bottom(border, bg, flip=False),
            f"bottom-right-{state}": _corner_bottom(border, bg, flip=True),
            f"left-{state}": _strip(BORDER, 1, border),
            f"right-{state}": _strip(BORDER, 1, border),
            f"bottom-{state}": _strip(1, BORDER, border),
        }
        for i in range(1, 6):
            parts[f"title-{i}-{state}"] = _title(border, bg)
        for button in ("close", "hide", "maximize", "maximize-toggled"):
            hover = danger if button == "close" else accent
            normal = dim if state == "active" else line
            parts[f"{button}-{state}"] = _button(border, bg, normal)
            if state == "active":
                parts[f"{button}-prelight"] = _button(border, bg, hover)
                parts[f"{button}-pressed"] = _button(border, bg, _mix(hover, bg, 0.35))
        for name, canvas in parts.items():
            files[f"{name}.xpm"] = canvas.xpm(name.replace("-", "_"))
    files["themerc"] = "\n".join([
        f"# Static Linux · {theme['name']} (generated by sl-theme, edits are overwritten)",
        "title_alignment=center",
        "full_width_title=true",
        "title_shadow_active=false",
        "title_shadow_inactive=false",
        f"active_text_color=#{theme['text']}",
        f"inactive_text_color=#{theme['text_dim']}",
        "button_offset=6",
        "button_spacing=0",
        f"title_vertical_offset_active={BORDER // 2}",
        f"title_vertical_offset_inactive={BORDER // 2}",
        "show_app_icon=false",
        "",
    ])
    return files
