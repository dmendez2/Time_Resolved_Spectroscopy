import QtQuick 2.15
import QtQuick.Controls 2.15


// Validated Input Field
TextField {
    id: styledTextField

    property string displayText: ""
    property color displayColor: "#000000"
    property double bottomAllowedVal: 0.0
    property double topAllowedVal: 0.0
    property int allowedDecimalPlaces: 1

    text: styledTextField.displayText
    color: styledTextField.displayColor

    height: 40
    font.pixelSize: 16
    font.bold: true
    font.family: "Courier" // Monospace looks great for hardware UIs
    selectByMouse: true
    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: TextInput.AlignVCenter

    validator: DoubleValidator {
        bottom: styledTextField.bottomAllowedVal
        top: styledTextField.topAllowedValp
        decimals: styledTextField.allowedDecimalPlaces
        notation: DoubleValidator.StandardNotation
    }

    background: Rectangle {
        color: "#2D2D2D" // Black background inside the widget panel
        border.color: styledTextField.activeFocus ? "#BF00FF" : "#111111"
        border.width: 1
        radius: 4
    }

    Label {
        text: "nm"
        color: "#AAAAAA"
        font.pixelSize: 14
        font.family: "Courier"
        font.bold: true

        // X position calculation:
        // Starts at the left padding, adds the real width of the text, plus spacing
        x: (parent.width / 2) + (styledTextField.contentWidth / 2) + 6

        anchors.verticalCenter: parent.verticalCenter

        // Optional: Hides the unit badge completely if the field is empty
        visible: styledTextField.text.length > 0
    }
}
