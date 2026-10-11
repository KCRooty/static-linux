/* Static Linux — install-time slideshow (Calamares slideshowAPI 2).
 * A single static panel for now: a real slide deck needs the SF artwork. */
import QtQuick 2.15

Rectangle {
    color: "#0B0C10"

    Column {
        anchors.centerIn: parent
        spacing: 12

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Static Linux"
            color: "#D6D8E0"
            font.pixelSize: 34
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "fast. private. yours."
            color: "#C0A0F0"
            font.pixelSize: 16
        }
    }
}
