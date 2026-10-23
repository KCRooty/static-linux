-- Static Linux — Hyprland base config (Hyprland >= 0.56, Lua).
--
-- Shipped by staticlinux-base at /usr/share/static-linux/hypr/static.lua and
-- loaded by ~/.config/hypr/hyprland.lua, which only sets SL_TIER ("full" or
-- "lite") and holds the user's own overrides — package updates improve this
-- file without touching the user's.
--
-- Every bind carries a `description`: the post-install keybinding guide
-- (sl-hypr-guide, Super+F1) reads them live from `hyprctl binds -j`.

local tier = SL_TIER or "full"
local full = tier == "full"

------------------------------------------------------------------------
-- helpers
------------------------------------------------------------------------
local function read_file(path)
    local f = io.open(path, "r")
    if not f then return nil end
    local s = f:read("*a")
    f:close()
    return s
end

-- the accent the user picked (installer / sl-ctl accent), for the borders
local function accent_colors()
    local name = (read_file("/etc/static-linux/accent") or "purple"):gsub("%s+", "")
    local palette = read_file("/usr/lib/static-linux/accents/palette.conf") or ""
    for line in palette:gmatch("[^\n]+") do
        local n, acc, dim, detail = line:match("^%s*([%w-]+)%s*|%s*(%x+)%s*|%s*(%x+)%s*|%s*(%x+)")
        if n == name then return acc, dim, detail end
    end
    return "C0A0F0", "8A78AA", "F2C94C"
end

-- keyboard layout chosen in the installer (Calamares writes it for X11)
local function keyboard()
    local conf = read_file("/etc/X11/xorg.conf.d/00-keyboard.conf") or ""
    local layout = conf:match('Option%s+"XkbLayout"%s+"([^"]+)"') or "es"
    local variant = conf:match('Option%s+"XkbVariant"%s+"([^"]*)"') or ""
    return layout, variant
end

local accent, dim, detail = accent_colors()
local kb_layout, kb_variant = keyboard()

local terminal    = "kitty"
local fileManager = full and "nautilus" or "thunar"
local browser     = "brave-origin"
local launcher    = "rofi -show drun -show-icons"

------------------------------------------------------------------------
-- monitors
------------------------------------------------------------------------
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })

------------------------------------------------------------------------
-- autostart
------------------------------------------------------------------------
hl.on("hyprland.start", function()
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("ags run ~/.config/ags/app.tsx")
    hl.exec_cmd("dunst")
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("nm-applet --indicator")
    hl.exec_cmd("wl-paste --watch cliphist store")
    hl.exec_cmd("sleep 3 && sl-hypr-guide --autostart")
    hl.exec_cmd("sl-welcome --autostart")
end)

------------------------------------------------------------------------
-- environment
------------------------------------------------------------------------
hl.env("XCURSOR_THEME", "Adwaita")
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
if io.open("/usr/bin/kvantummanager") then hl.env("QT_STYLE_OVERRIDE", "kvantum") end
hl.env("GDK_BACKEND", "wayland,x11")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")

------------------------------------------------------------------------
-- look and feel (full: blur/shadows/animations · lite: flat and light)
------------------------------------------------------------------------
hl.config({
    general = {
        gaps_in = full and 5 or 3,
        gaps_out = full and 12 or 6,
        border_size = 2,
        col = {
            active_border   = { colors = { "rgba(" .. accent .. "ff)", "rgba(" .. detail .. "ff)" }, angle = 45 },
            inactive_border = "rgba(" .. dim .. "55)",
        },
        resize_on_border = true,
        allow_tearing = false,
        layout = "dwindle",
    },

    decoration = {
        rounding = full and 12 or 8,
        rounding_power = 2,
        active_opacity = 1.0,
        inactive_opacity = full and 0.95 or 1.0,
        shadow = {
            enabled = full,
            range = 14,
            render_power = 3,
            color = 0xaa0b0c10,
        },
        blur = {
            enabled = full,
            size = 6,
            passes = 2,
            vibrancy = 0.17,
        },
    },

    animations = { enabled = true },

    dwindle = { preserve_split = true },
    master  = { new_status = "master" },

    misc = {
        force_default_wallpaper = 0,
        disable_hyprland_logo = true,
        disable_splash_rendering = true,
        vfr = true,
    },

    input = {
        kb_layout = kb_layout,
        kb_variant = kb_variant,
        follow_mouse = 1,
        sensitivity = 0,
        touchpad = { natural_scroll = true },
    },
})

hl.curve("slOut",  { type = "bezier", points = { { 0.16, 1 }, { 0.3, 1 } } })
hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
hl.curve("snappy", { type = "spring", mass = 1, stiffness = 238, dampening = 24 })
if full then
    hl.animation({ leaf = "windowsIn",  enabled = true, speed = 4,   spring = "snappy", style = "popin 85%" })
    hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.6, bezier = "linear", style = "popin 85%" })
    hl.animation({ leaf = "windowsMove", enabled = true, speed = 4,  spring = "snappy" })
    hl.animation({ leaf = "fade",       enabled = true, speed = 3,   bezier = "slOut" })
    hl.animation({ leaf = "layers",     enabled = true, speed = 3.5, bezier = "slOut", style = "fade" })
    hl.animation({ leaf = "border",     enabled = true, speed = 5,   bezier = "slOut" })
    hl.animation({ leaf = "workspaces", enabled = true, speed = 3,   bezier = "slOut", style = "slide" })
else
    -- lite: a couple of quick fades, nothing that costs GPU time
    hl.animation({ leaf = "global",     enabled = false })
    hl.animation({ leaf = "fade",       enabled = true, speed = 2.5, bezier = "slOut" })
    hl.animation({ leaf = "workspaces", enabled = true, speed = 2.5, bezier = "slOut", style = "fade" })
end

hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

------------------------------------------------------------------------
-- keybindings (each one documented for sl-hypr-guide)
------------------------------------------------------------------------
local M = "SUPER"
local function bind(keys, action, desc, flags)
    flags = flags or {}
    flags.description = desc
    hl.bind(keys, action, flags)
end

-- apps
bind(M .. " + Return",      hl.dsp.exec_cmd(terminal),    "Apps: abrir la terminal")
bind(M .. " + E",           hl.dsp.exec_cmd(fileManager), "Apps: abrir el gestor de archivos")
bind(M .. " + B",           hl.dsp.exec_cmd(browser),     "Apps: abrir el navegador (Brave Origin)")
bind(M .. " + Space",       hl.dsp.exec_cmd(launcher),    "Apps: lanzador de aplicaciones")
bind(M .. " + D",           hl.dsp.exec_cmd(launcher),    "Apps: lanzador de aplicaciones")
bind(M .. " + SHIFT + V",   hl.dsp.exec_cmd("cliphist list | rofi -dmenu -p Portapapeles | cliphist decode | wl-copy"),
                                                          "Apps: historial del portapapeles")
bind(M .. " + F1",          hl.dsp.exec_cmd("sl-hypr-guide"), "Ayuda: esta guía de atajos")

-- capture
bind(M .. " + SHIFT + S",   hl.dsp.exec_cmd("sl-screenshot"), "Captura: zona de pantalla (archivo + portapapeles)")
bind("Print",               hl.dsp.exec_cmd("sl-screenshot"), "Captura: zona de pantalla (archivo + portapapeles)")

-- windows
bind(M .. " + Q",           hl.dsp.window.close(),                     "Ventanas: cerrar la ventana")
bind(M .. " + F",           hl.dsp.window.fullscreen({ action = "toggle" }), "Ventanas: pantalla completa")
bind(M .. " + V",           hl.dsp.window.float({ action = "toggle" }), "Ventanas: flotante / en mosaico")
bind(M .. " + P",           hl.dsp.window.pseudo(),                    "Ventanas: pseudo-mosaico")
bind(M .. " + J",           hl.dsp.layout("togglesplit"),              "Ventanas: cambiar división horizontal/vertical")
bind("ALT + Tab",           hl.dsp.window.cycle_next(),                "Ventanas: pasar a la siguiente")
for key, dir in pairs({ left = "left", right = "right", up = "up", down = "down" }) do
    bind(M .. " + " .. key,             hl.dsp.focus({ direction = dir }),       "Ventanas: mover el foco")
    bind(M .. " + SHIFT + " .. key,     hl.dsp.window.move({ direction = dir }), "Ventanas: mover la ventana")
end
bind(M .. " + mouse:272",   hl.dsp.window.drag(),   "Ventanas: arrastrar con Super + clic izquierdo", { mouse = true })
bind(M .. " + mouse:273",   hl.dsp.window.resize(), "Ventanas: redimensionar con Super + clic derecho", { mouse = true })

-- workspaces
for i = 1, 9 do
    bind(M .. " + " .. i,           hl.dsp.focus({ workspace = i }),       "Escritorios: ir a un escritorio")
    bind(M .. " + SHIFT + " .. i,   hl.dsp.window.move({ workspace = i }), "Escritorios: mover la ventana a otro escritorio")
end
bind(M .. " + mouse_down",  hl.dsp.focus({ workspace = "e+1" }), "Escritorios: siguiente (rueda del ratón)")
bind(M .. " + mouse_up",    hl.dsp.focus({ workspace = "e-1" }), "Escritorios: anterior (rueda del ratón)")
bind(M .. " + S",           hl.dsp.workspace.toggle_special("scratch"), "Escritorios: mostrar/ocultar el escritorio rápido")
bind(M .. " + ALT + S",     hl.dsp.window.move({ workspace = "special:scratch" }), "Escritorios: mandar la ventana al escritorio rápido")

-- session
bind(M .. " + L",           hl.dsp.exec_cmd("loginctl lock-session"), "Sesión: bloquear la pantalla")
bind(M .. " + N",           hl.dsp.exec_cmd("dunstctl history-pop"), "Sesión: ver la última notificación")
bind(M .. " + SHIFT + Q",   hl.dsp.exec_cmd("command -v hyprshutdown >/dev/null && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"),
                                                                   "Sesión: cerrar sesión")

-- media keys (also work on the lock screen)
local media = { locked = true, repeating = true }
bind("XF86AudioRaiseVolume",  hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), "Multimedia: subir volumen", media)
bind("XF86AudioLowerVolume",  hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),      "Multimedia: bajar volumen", media)
bind("XF86AudioMute",         hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),     "Multimedia: silenciar", { locked = true })
bind("XF86AudioMicMute",      hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),   "Multimedia: silenciar el micrófono", { locked = true })
bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("brightnessctl set 5%+"), "Multimedia: subir brillo", media)
bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl set 5%-"), "Multimedia: bajar brillo", media)
bind("XF86AudioPlay",         hl.dsp.exec_cmd("playerctl play-pause"), "Multimedia: reproducir/pausar", { locked = true })
bind("XF86AudioNext",         hl.dsp.exec_cmd("playerctl next"),       "Multimedia: siguiente pista", { locked = true })
bind("XF86AudioPrev",         hl.dsp.exec_cmd("playerctl previous"),   "Multimedia: pista anterior", { locked = true })

------------------------------------------------------------------------
-- rules
------------------------------------------------------------------------
hl.window_rule({ name = "sl-suppress-maximize", match = { class = ".*" }, suppress_event = "maximize" })
hl.window_rule({
    name = "sl-fix-xwayland-drags",
    match = { class = "^$", title = "^$", xwayland = true, float = true, fullscreen = false, pin = false },
    no_focus = true,
})
hl.window_rule({ name = "sl-guide",   match = { class = "^dev\\.staticforge\\.hyprguide$" }, float = true, center = true })
hl.window_rule({ name = "sl-welcome", match = { class = "^dev\\.staticforge\\.welcome$" },   float = true, center = true })
hl.window_rule({ name = "sl-pavucontrol", match = { class = "^(org\\.pulseaudio\\.pavucontrol|nm-connection-editor|blueman-manager)$" },
                 float = true, center = true })
if full then
    hl.window_rule({ name = "sl-kitty-glass", match = { class = "^kitty$" }, opacity = "0.95 0.90" })
    hl.layer_rule({ match = { namespace = "^(sl-bar|rofi|notifications)$" }, blur = true, ignore_alpha = 0.3 })
end
