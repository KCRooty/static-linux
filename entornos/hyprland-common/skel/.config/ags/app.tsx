// Static Linux — Astal shell entry point (Hyprland full and lite).
// Started by /usr/share/static-linux/hypr/static.lua: `ags run ~/.config/ags/app.tsx`.

import app from "ags/gtk4/app"
import GLib from "gi://GLib"
import { createBinding, For, This } from "ags"
import Bar from "./widget/Bar"

const HOME = GLib.get_home_dir()

app.start({
  instanceName: "sl-shell",
  main() {
    // accent overlay first (branding/accents/apply.sh writes @accent_color,
    // @sl_bg, ... there), then the bar's own rules that use those colours
    app.apply_css(`${HOME}/.config/gtk-4.0/gtk.css`)
    app.apply_css(`${HOME}/.config/ags/bar.css`)

    const monitors = createBinding(app, "monitors")
    return (
      <For each={monitors}>
        {(monitor) => (
          <This this={app}>
            <Bar gdkmonitor={monitor} />
          </This>
        )}
      </For>
    )
  },
})
