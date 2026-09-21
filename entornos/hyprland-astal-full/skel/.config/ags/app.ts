#!/usr/bin/env -S ags run
// Static Linux — Astal shell entry point (Hyprland full, >=4 GB tier).
// Run by hyprland.conf's `exec-once = ags run ~/.config/ags/app.ts`.
//
// Confirmed against the AGS quick-start guide (aylur.github.io/ags):
// import from "ags/gtk4/app", app.start({ main() {...} }). The Hyprland
// widget bindings (workspaces/focused client) use createPoll rather than
// native Hyprland event signals — simpler to get right without a live
// Hyprland socket to test against. Swap for real event bindings
// (AstalHyprland's workspace/client-added signals) once this runs on
// real hardware — see README.md "Known simplification".

import app from "ags/gtk4/app"
import GLib from "gi://GLib"
import Bar from "./widget/Bar"

const HOME = GLib.get_home_dir()

app.start({
  instanceName: "sl-shell",
  main() {
    // Load the accent overlay first (branding/accents/apply.sh writes the
    // @accent_color / @sl_bg / ... named colours here) so bar.css's own
    // @accent_color references resolve — the shell follows the active
    // accent for free, same trick sl-welcome uses.
    app.apply_css(`${HOME}/.config/gtk-4.0/gtk.css`)
    app.apply_css(`${HOME}/.config/ags/bar.css`)

    for (const monitor of app.get_monitors()) {
      Bar(monitor)
    }
  },
})
