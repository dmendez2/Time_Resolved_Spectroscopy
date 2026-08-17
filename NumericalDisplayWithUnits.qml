import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: numericalDisplayWithUnits

    color: "#111111" // Darker background to distinguish from input
    border.color: "#333333"
    border.width: 1
    radius: 4

    property string displayValue: ""
    property string displayUnit: ""
    property color displayColor: "#000000"

    RowLayout{
        spacing: 1
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter

        Label {
            // Link this text property to your actual C++ or backend backend property
            // e.g., text: spectrometer.currentWavelength.toFixed(1)
            text: numericalDisplayWithUnits.displayValue
            color: numericalDisplayWithUnits.displayColor
            font.pixelSize: 16
            font.bold: true
            font.family: "Courier"
        }

        Label{
            text: numericalDisplayWithUnits.displayUnit
            color: numericalDisplayWithUnits.displayColor
            font.pixelSize: 16
            font.bold: true
            font.family: "Courier"
            opacity: 0.6 // Make the text for the unit (nm) be slightly darker than the value to aid readability
        }
    }
}
