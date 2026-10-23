-- Static Linux — Hyprland (full tier). Your config: edit freely.
--
-- The Static Linux defaults (binds, look, autostart, rules) live in
-- /usr/share/static-linux/hypr/static.lua and update with the system.
-- Anything you set below the dofile() line overrides them.
-- Keybinding guide: Super+F1.

SL_TIER = "full"
dofile("/usr/share/static-linux/hypr/static.lua")

-- ---- your changes go here ------------------------------------------------
-- hl.config({ general = { gaps_out = 20 } })
-- hl.bind("SUPER + T", hl.dsp.exec_cmd("kitty"), { description = "Mi terminal" })
