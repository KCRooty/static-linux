// Static Linux — Astal top bar. Workspaces (left) · focused window title
// (center) · clock (right). Void/Signal-Green palette via bar.css.
//
// Values are read with createPoll instead of native Hyprland signals — see
// app.ts's header comment for why. 500ms is frequent enough to feel live
// without noticeable CPU cost.

import app from "ags/gtk4/app"
import { Astal, Gdk } from "ags/gtk4"
import { createPoll } from "ags/time"
import Hyprland from "gi://AstalHyprland"

const { TOP, LEFT, RIGHT } = Astal.WindowAnchor

function Workspaces() {
  const hypr = Hyprland.get_default()
  const ids = createPoll<number[]>([], 500, () =>
    hypr.get_workspaces().map((w) => w.id).sort((a, b) => a - b)
  )
  const activeId = createPoll<number>(1, 500, () =>
    hypr.get_focused_workspace()?.id ?? 1
  )

  return (
    <box cssClasses={["workspaces"]}>
      {ids.as((list) =>
        list.map((id) => (
          <button
            cssClasses={activeId.as((active) =>
              active === id ? ["workspace", "active"] : ["workspace"]
            )}
            onClicked={() => hypr.dispatch("workspace", String(id))}
          >
            <label label={String(id)} />
          </button>
        ))
      )}
    </box>
  )
}

function FocusedTitle() {
  const hypr = Hyprland.get_default()
  const title = createPoll<string>("Escritorio", 500, () =>
    hypr.get_focused_client()?.title ?? "Escritorio"
  )
  return <label cssClasses={["window-title"]} label={title} maxWidthChars={60} ellipsize={3} />
}

function Clock() {
  const time = createPoll<string>("", 1000, "date '+%H:%M'")
  const date = createPoll<string>("", 60000, "date '+%A %d %B'")
  return (
    <box cssClasses={["clock"]} spacing={6}>
      <label label={date} cssClasses={["clock-date"]} />
      <label label={time} cssClasses={["clock-time"]} />
    </box>
  )
}

export default function Bar(monitor: Gdk.Monitor) {
  return (
    <window
      visible
      monitor={monitor}
      cssClasses={["bar"]}
      anchor={TOP | LEFT | RIGHT}
      exclusivity={Astal.Exclusivity.EXCLUSIVE}
      application={app}
    >
      <centerbox cssClasses={["bar-inner"]}>
        <Workspaces $type="start" />
        <FocusedTitle $type="center" />
        <Clock $type="end" />
      </centerbox>
    </window>
  )
}
