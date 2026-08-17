import QtQuick 2.15
import QtQuick.Controls 2.15

ComboBox {
    id: styledComboBox
    height: 40

    // Custom text rendering inside the ComboBox
    contentItem: Text {
        text: styledComboBox.displayText
        font.pixelSize: 15
        font.bold: true
        font.family: "Courier"
        color: "#FFFFFF" // White text matches your Target Input style
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        leftPadding: 12
    }

    // Custom Dropdown Arrow Button
    indicator: Canvas {
        id: canvas
        x: styledComboBox.width - width - 12
        y: (styledComboBox.height - height) / 2
        width: 12
        height: 8
        contextType: "2d"
        onPaint: {
            context.reset();
            context.moveTo(0, 0);
            context.lineTo(width, 0);
            context.lineTo(width / 2, height);
            context.closePath();
            context.fillStyle = styledComboBox.pressed ? "#BF00FF" : "#888888";
            context.fill();
        }
    }

    // Custom Background Box
    background: Rectangle {
        color: "#2D2D2D"
        border.color: styledComboBox.popup.visible ? "#BF00FF" : "#111111"
        border.width: 1
        radius: 4
    }

    // Custom Popup Menu Layout (The scrolling dropdown list)
    popup: Popup {
        y: styledComboBox.height + 2
        width: styledComboBox.width
        implicitHeight: contentItem.implicitHeight
        padding: 1

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: styledComboBox.popup.visible ? styledComboBox.delegateModel : null
            currentIndex: styledComboBox.highlightedIndex

            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            color: "#111111" // Dark popover menu background
            border.color: "#333333"
            radius: 4
        }
    }

    // Custom Styling for Individual Rows inside the Dropdown list
    delegate: ItemDelegate {
        id: itemDelegate
        width: styledComboBox.width
        height: 35

        contentItem: Text {
            text: modelData
            color: itemDelegate.highlighted ? "#00FF66" : "#FFFFFF" // Turns green on hover/highlight
            font.pixelSize: 14
            font.family: "Courier"
            font.bold: itemDelegate.highlighted
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            leftPadding: 12
        }

        background: Rectangle {
            color: itemDelegate.highlighted ? "#2D2D2D" : "transparent"
        }
    }
}
