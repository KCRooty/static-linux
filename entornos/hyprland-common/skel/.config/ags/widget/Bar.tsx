// Static Linux — Astal top bar.
//   start:  launcher · workspaces
//   center: clock (calendar on click)
//   end:    tray · wifi · volume · battery · power menu
// Everything is event-driven (Astal bindings), nothing polls except the clock.

import app from "ags/gtk4/app"
import Astal from "gi://Astal?version=4.0"
import Gtk from "gi://Gtk?version=4.0"
import Gdk from "gi://Gdk?version=4.0"
import GLib from "gi://GLib"
import AstalHyprland from "gi://AstalHyprland"
import AstalTray from "gi://AstalTray"
import AstalWp from "gi://AstalWp"
import AstalNetwork from "gi://AstalNetwork"
import AstalBattery from "gi://AstalBattery"
import { For, With, createBinding, onCleanup } from "ags"
import { createPoll } from "ags/time"
import { execAsync } from "ags/process"

// Hyprland >= 0.56 takes Lua dispatchers over IPC
const dispatch = (lua: string) => execAsync(["hyprctl", "dispatch", lua]).catch(console.error)
const run = (cmd: string) => execAsync(["bash", "-c", cmd]).catch(console.error)

function Launcher() {
  return (
    <button
      cssClasses={["launcher"]}
      tooltipText="Aplicaciones (Super + Espacio)"
      onClicked={() => run("rofi -show drun -show-icons")}
    >
      <image iconName="view-app-grid-symbolic" />
    </button>
  )
}

function Workspaces() {
  const hypr = AstalHyprland.get_default()
  const workspaces = createBinding(hypr, "workspaces")((ws) =>
    ws.filter((w) => w.id > 0).sort((a, b) => a.id - b.id),
  )
  const focused = createBinding(hypr, "focusedWorkspace")

  return (
    <box cssClasses={["workspaces"]} spacing={4}>
      <For each={workspaces}>
        {(ws: AstalHyprland.Workspace) => (
          <button
            cssClasses={focused((f) => (f?.id === ws.id ? ["ws", "active"] : ["ws"]))}
            onClicked={() => dispatch(`hl.dsp.focus({ workspace = ${ws.id} })`)}
          >
            <label label={String(ws.id)} />
          </button>
        )}
      </For>
    </box>
  )
}

function Clock() {
  const time = createPoll("", 1000, () => GLib.DateTime.new_now_local().format("%H:%M")!)
  const date = createPoll("", 60000, () => GLib.DateTime.new_now_local().format("%a %d %b")!)
  return (
    <menubutton cssClasses={["clock"]}>
      <box spacing={8}>
        <label cssClasses={["clock-date"]} label={date} />
        <label cssClasses={["clock-time"]} label={time} />
      </box>
      <popover>
        <Gtk.Calendar />
      </popover>
    </menubutton>
  )
}

function Tray() {
  const tray = AstalTray.get_default()
  const items = createBinding(tray, "items")
  const init = (btn: Gtk.MenuButton, item: AstalTray.TrayItem) => {
    btn.menuModel = item.menuModel
    btn.insert_action_group("dbusmenu", item.actionGroup)
    item.connect("notify::action-group", () => btn.insert_action_group("dbusmenu", item.actionGroup))
  }
  return (
    <box cssClasses={["tray"]} spacing={2}>
      <For each={items}>
        {(item) => (
          <menubutton $={(self) => init(self, item)} tooltipMarkup={createBinding(item, "tooltipMarkup")}>
            <image gicon={createBinding(item, "gicon")} />
          </menubutton>
        )}
      </For>
    </box>
  )
}

function Wifi() {
  const network = AstalNetwork.get_default()
  const wifi = createBinding(network, "wifi")
  const wired = createBinding(network, "wired")
  return (
    <box>
      <With value={wifi}>
        {(w) =>
          w ? (
            <button
              cssClasses={["chip"]}
              tooltipText={createBinding(w, "ssid")((s) => s || "Sin conexión")}
              onClicked={() => run("nm-connection-editor")}
            >
              <image iconName={createBinding(w, "iconName")} />
            </button>
          ) : (
            <With value={wired}>
              {(e) => e && (
                <button cssClasses={["chip"]} tooltipText="Cable" onClicked={() => run("nm-connection-editor")}>
                  <image iconName={createBinding(e, "iconName")} />
                </button>
              )}
            </With>
          )
        }
      </With>
    </box>
  )
}

function Volume() {
  const wp = AstalWp.get_default()
  if (!wp) return <box />
  const speaker = wp.defaultSpeaker
  return (
    <menubutton cssClasses={["chip"]}>
      <image iconName={createBinding(speaker, "volumeIcon")} />
      <popover>
        <box spacing={8} cssClasses={["volume-pop"]}>
          <button onClicked={() => speaker.set_mute(!speaker.mute)}>
            <image iconName={createBinding(speaker, "volumeIcon")} />
          </button>
          <slider
            widthRequest={220}
            onChangeValue={({ value }) => speaker.set_volume(value)}
            value={createBinding(speaker, "volume")}
          />
          <button tooltipText="Más ajustes de sonido" onClicked={() => run("pavucontrol")}>
            <image iconName="emblem-system-symbolic" />
          </button>
        </box>
      </popover>
    </menubutton>
  )
}

function Battery() {
  const bat = AstalBattery.get_default()
  const percent = createBinding(bat, "percentage")((p) => `${Math.round(p * 100)}%`)
  return (
    <box cssClasses={["chip"]} spacing={4} visible={createBinding(bat, "isPresent")}>
      <image iconName={createBinding(bat, "batteryIconName")} />
      <label label={percent} />
    </box>
  )
}

function Power() {
  const entry = (label: string, icon: string, cmd: string) => (
    <button onClicked={() => run(cmd)}>
      <box spacing={10}>
        <image iconName={icon} />
        <label label={label} xalign={0} />
      </box>
    </button>
  )
  return (
    <menubutton cssClasses={["power"]}>
      <image iconName="system-shutdown-symbolic" />
      <popover>
        <box orientation={Gtk.Orientation.VERTICAL} cssClasses={["power-pop"]}>
          {entry("Bloquear", "system-lock-screen-symbolic", "loginctl lock-session")}
          {entry("Suspender", "weather-clear-night-symbolic", "systemctl suspend")}
          {entry("Cerrar sesión", "system-log-out-symbolic",
            "command -v hyprshutdown >/dev/null && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'")}
          {entry("Reiniciar", "system-reboot-symbolic", "systemctl reboot")}
          {entry("Apagar", "system-shutdown-symbolic", "systemctl poweroff")}
        </box>
      </popover>
    </menubutton>
  )
}

export default function Bar({ gdkmonitor }: { gdkmonitor: Gdk.Monitor }) {
  let win: Astal.Window
  const { TOP, LEFT, RIGHT } = Astal.WindowAnchor
  onCleanup(() => win.destroy())

  return (
    <window
      $={(self) => (win = self)}
      visible
      namespace="sl-bar"
      name={`sl-bar-${gdkmonitor.connector}`}
      cssClasses={["sl-bar"]}
      gdkmonitor={gdkmonitor}
      exclusivity={Astal.Exclusivity.EXCLUSIVE}
      anchor={TOP | LEFT | RIGHT}
      application={app}
    >
      <centerbox cssClasses={["bar-inner"]}>
        <box $type="start" spacing={8}>
          <Launcher />
          <Workspaces />
        </box>
        <box $type="center">
          <Clock />
        </box>
        <box $type="end" spacing={4}>
          <Tray />
          <Wifi />
          <Volume />
          <Battery />
          <Power />
        </box>
      </centerbox>
    </window>
  )
}
