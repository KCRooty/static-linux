/* Static Linux — install-time slideshow (Calamares slideshowAPI 2).
 * Void ground, 70s groovy stripes, five slides that rotate while the
 * install runs. Cheap on purpose: the stripes are painted once into a
 * Canvas and every animation only moves or fades already-drawn items. */
import QtQuick 2.15

Rectangle {
    id: root
    color: "#0B0C10"
    clip: true

    property bool activatedInCalamares: false
    property int current: 0
    readonly property var groovy: ["#6B3A1F", "#C2452D", "#E8792B", "#F2B33D", "#2A9D8F"]

    readonly property var slides: [
        { title: "Static Linux",
          body: "fast · private · yours\nTu sistema se está instalando. Esto tarda unos minutos.",
          tone: 4 },
        { title: "Tu escritorio, tu color",
          body: "Diez acentos para todo el sistema: fondo, ventanas, terminal y login.\nCámbialo cuando quieras desde la bienvenida o con  sl-ctl accent.",
          tone: 3 },
        { title: "Privado de serie",
          body: "Cero telemetría. DNS cifrado y cortafuegos activos desde el primer arranque.\nSube el nivel con  sl-ctl privacy.",
          tone: 2 },
        { title: "Todo a mano",
          body: "sl-welcome: catálogo de apps y primeros pasos.\nsl-ctl: actualizar, snapshots, ajustes y más.",
          tone: 1 },
        { title: "Hecho para tu equipo",
          body: "sl-detect ha elegido entorno, kernel y sistema de archivos\nsegún tu hardware, de un Celeron a una RTX.",
          tone: 4 }
    ]

    function onActivate() { activatedInCalamares = true; current = 0; play(); timer.restart() }
    function onLeave()    { activatedInCalamares = false; timer.stop() }

    function play() { enter.restart() }

    Timer {
        id: timer
        interval: 7000
        repeat: true
        running: false
        onTriggered: leave.restart()
    }

    /* ---- groovy band: in from the left, curving down to the bottom ---- */
    Item {
        id: band
        width: root.width
        height: root.height
        Canvas {
            id: stripes
            anchors.fill: parent
            renderStrategy: Canvas.Cooperative
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                var sw = Math.max(10, height * 0.045), gap = sw * 0.18
                var cx = width * 0.70, cy = height, r0 = height * 0.42
                for (var i = 0; i < root.groovy.length; i++) {
                    var r = r0 - i * (sw + gap) - sw / 2
                    ctx.beginPath()
                    ctx.lineWidth = sw
                    ctx.strokeStyle = root.groovy[i]
                    ctx.moveTo(-10, cy - r)
                    ctx.lineTo(cx, cy - r)
                    ctx.arc(cx, cy, r, -Math.PI / 2, 0, false)
                    ctx.stroke()
                }
            }
        }
    }

    /* ---- small rainbow, top-right corner (static) ---- */
    Canvas {
        anchors.fill: parent
        renderStrategy: Canvas.Cooperative
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var sw = Math.max(10, height * 0.045), gap = sw * 0.18
            var c0 = height * 0.22
            for (var j = 0; j < root.groovy.length; j++) {
                var rc = c0 - j * (sw * 0.7 + gap) - sw * 0.35
                ctx.beginPath()
                ctx.lineWidth = sw * 0.7
                ctx.strokeStyle = root.groovy[j]
                ctx.arc(width, 0, rc, Math.PI / 2, Math.PI, false)
                ctx.stroke()
            }
        }
    }

    /* ---- slide text ---- */
    Column {
        id: text
        x: root.width * 0.08
        y: root.height * 0.16
        width: root.width * 0.80
        spacing: 14

        Rectangle {
            width: 56; height: 6; radius: 3
            color: root.groovy[root.slides[root.current].tone]
            Behavior on color { ColorAnimation { duration: 400 } }
        }
        Text {
            text: root.slides[root.current].title
            color: "#E6E8EE"
            font.family: "JetBrains Mono"
            font.weight: Font.ExtraBold
            font.pixelSize: Math.max(22, root.height * 0.085)
        }
        Text {
            width: parent.width
            text: root.slides[root.current].body
            color: "#A9AEBB"
            font.family: "Space Grotesk"
            font.pixelSize: Math.max(13, root.height * 0.036)
            lineHeight: 1.25
            wrapMode: Text.WordWrap
        }

        Row {
            topPadding: 6
            spacing: 8
            Repeater {
                model: root.slides.length
                Rectangle {
                    required property int index
                    height: 8; radius: 4
                    width: index === root.current ? 28 : 8
                    color: index === root.current ? "#00C8A0" : "#2C303C"
                    Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
                    Behavior on color { ColorAnimation { duration: 300 } }
                }
            }
        }
    }

    /* ---- transitions ---- */
    SequentialAnimation {
        id: enter
        ParallelAnimation {
            NumberAnimation { target: text; property: "opacity"; from: 0; to: 1; duration: 450 }
            NumberAnimation { target: text; property: "y"; from: root.height * 0.20; to: root.height * 0.16
                              duration: 550; easing.type: Easing.OutCubic }
            NumberAnimation { target: band; property: "x"; from: -root.width * 0.25; to: 0
                              duration: 900; easing.type: Easing.OutCubic }
        }
    }
    SequentialAnimation {
        id: leave
        ParallelAnimation {
            NumberAnimation { target: text; property: "opacity"; to: 0; duration: 300 }
            NumberAnimation { target: band; property: "x"; to: root.width * 0.06; duration: 300; easing.type: Easing.InCubic }
        }
        ScriptAction { script: { root.current = (root.current + 1) % root.slides.length; root.play() } }
    }

    // also animate when previewed outside Calamares (qmlscene / qml)
    Component.onCompleted: if (!activatedInCalamares) play()
}
