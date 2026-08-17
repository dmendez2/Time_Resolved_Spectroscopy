import QtQuick 2.15
import QtQuick.Controls 2.15

Button {
    id: styledButton

    property string displayText: ""
    property color buttonColor: "#000000"
    property color pressedColor: "#000000"

    contentItem: Text {
        text: styledButton.displayText
        color: styledButton.enabled ? (styledButton.down ? "#FFFFFF" : styledButton.buttonColor) : "#808080"
        font.pixelSize: 16
        font.bold: true
        font.family: "Courier"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        color: styledButton.pressed ? styledButton.pressedColor : (styledButton.hovered ? "#888888" : "#111111")
        border.color: styledButton.enabled ? styledButton.buttonColor : "#808080"
        border.width: 1
        radius: 12
    }
}
