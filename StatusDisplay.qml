import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: statusDisplay
    color: "#111111" // Black background inside the widget panel
    border.color: "#333333"
    border.width: 1
    radius: 4
    height: 40

    property string displayText: ""
    property color displayColor: "#000000"

    Label{
        anchors.centerIn: parent
        text: statusDisplay.displayText
        color: statusDisplay.displayColor
        font.bold: true
        font.family: "Courier"
        font.pixelSize: 20
    }
}
