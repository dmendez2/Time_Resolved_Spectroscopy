import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 1200
    height: 700
    color: "#000000"
    title: "Time-Resolved Spectroscopy Suite"
    Component.onCompleted: trs_controller.refresh_gpib_addresses()

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        MenuBar {

            background: Rectangle {
                color: "#222222"
            }

            delegate: MenuBarItem {
                contentItem: Text {
                    text: parent.text
                    color: "white"
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 10
                    rightPadding: 10
                }

                background: Rectangle {
                    color: highlighted ? "#444444" : "transparent"
                }
            }

            Menu {
                title: "Settings"

                delegate: MenuItem {
                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        rightPadding: 10
                    }

                    background: Rectangle {
                        color: highlighted ? "#444444" : "#transparent"
                    }
                }

                Action {
                    text: "View Instrument Log"

                    onTriggered: {
                        logWindow.show()
                        logWindow.raise()
                        logWindow.requestActivate()
                    }
                }
            }
        }

        // Master Layout: Splits screen into Left Sidebar and Right Main Content
        RowLayout {
            id: root
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            TapHandler {
                onTapped: root.forceActiveFocus()
            }

            // ==========================================
            // LEFT SIDEBAR: Device Hardware Controls
            // ==========================================
            ScrollView {
                id: sleekScrollView
                Layout.fillHeight: true
                Layout.preferredWidth: 320
                clip: true
                height: 200

                // Force the horizontal scroll bar off, keep vertical active
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                // CUSTOM VERTICAL SCROLLBAR OVERRIDE
                ScrollBar.vertical: ScrollBar {
                    id: customScrollBar
                    parent: sleekScrollView
                    x: sleekScrollView.width - width - 4 // Tiny offset from the right boundary
                    y: sleekScrollView.topPadding
                    height: sleekScrollView.availableHeight
                    width: 10 // Super narrow track profile

                    // The Moving Indicator Bar (The Thumb)
                    contentItem: Rectangle {
                        implicitWidth: 6
                        implicitHeight: 100
                        radius: 5
                        // Dim gray normally, highlights to electric purple on active interaction
                        color: customScrollBar.pressed ? "#888888" : (customScrollBar.hovered ? "#888888" : "#444444")

                        // Clean fade animation when appearing/disappearing
                        Behavior on color { ColorAnimation { duration: 150 } }
                    }

                    // The Track Behind the Thumb
                    background: Rectangle {
                        implicitWidth: 10
                        color: "transparent" // Fully transparent keep the layout clean
                    }
                }

                ColumnLayout {
                    width: parent.width - 10
                    spacing: 15

                    TapHandler {
                        onTapped: root.forceActiveFocus()
                    }

                    // MODULE 1: Current Spectrometer Controls
                    Rectangle {
                        id: spectrometerControlBox
                        Layout.fillWidth: true
                        Layout.preferredHeight: 500
                        color: "#000000"
                        border.color: "#2D2D2D"
                        border.width: 1
                        radius: 4

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 10

                            Label {
                                text: "Spectrometer Control"
                                color: "#2CFF05" // Neon Green Theme
                                font.bold: true
                                font.pointSize: 16
                                font.letterSpacing: 1.4
                                font.capitalization: Font.AllUppercase
                                font.family: "Courier"

                                Layout.fillWidth: true
                            }

                            // GPIB ADDRESS SELECTOR
                            ColumnLayout {
                                spacing: 4
                                Layout.fillWidth: true

                                Label {
                                    text: "GPIB ADDRESS:"
                                    color: "#888888"
                                    font.pixelSize: 10
                                    font.bold: true
                                }

                                ComboBox {
                                    id: gpibSelector
                                    Layout.fillWidth: true
                                    height: 40

                                    // Defines the available GPIB addresses (Standard instruments use 1 to 30)
                                    model: trs_controller.gpibAddresses
                                    currentIndex: 1 // Defaults to address 9 (common for Horiba setups)

                                    // Custom text rendering inside the ComboBox
                                    contentItem: Text {
                                        text: gpibSelector.displayText
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
                                        x: gpibSelector.width - width - 12
                                        y: (gpibSelector.height - height) / 2
                                        width: 12
                                        height: 8
                                        contextType: "2d"
                                        onPaint: {
                                            context.reset();
                                            context.moveTo(0, 0);
                                            context.lineTo(width, 0);
                                            context.lineTo(width / 2, height);
                                            context.closePath();
                                            context.fillStyle = gpibSelector.pressed ? "#BF00FF" : "#888888";
                                            context.fill();
                                        }
                                    }

                                    // Custom Background Box
                                    background: Rectangle {
                                        color: "#2D2D2D"
                                        border.color: gpibSelector.popup.visible ? "#BF00FF" : "#111111"
                                        border.width: 1
                                        radius: 4
                                    }

                                    // Custom Popup Menu Layout (The scrolling dropdown list)
                                    popup: Popup {
                                        y: gpibSelector.height + 2
                                        width: gpibSelector.width
                                        implicitHeight: contentItem.implicitHeight
                                        padding: 1

                                        contentItem: ListView {
                                            clip: true
                                            implicitHeight: contentHeight
                                            model: gpibSelector.popup.visible ? gpibSelector.delegateModel : null
                                            currentIndex: gpibSelector.highlightedIndex

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
                                        width: gpibSelector.width
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
                            }

                            // Button to connect the HR320 Spectrometer
                            Button {
                                id: spectrometerConnectButton
                                Layout.fillWidth: true
                                Layout.preferredHeight: 25
                                contentItem: Text {
                                    text: "Connect Spectrometer"
                                    color: spectrometerConnectButton.down ? "#FFFFFF" : "#2CFF05" // Neon Green
                                    font.pixelSize: 16
                                    font.bold: true
                                    font.family: "Courier"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                background: Rectangle {
                                    color: spectrometerConnectButton.pressed ? "#339152" : (spectrometerConnectButton.hovered ? "#888888" : "#111111")
                                    border.color: "#2CFF05"
                                    border.width: 1
                                    radius: 12
                                }

                                onPressed: {
                                    trs_controller.initialize_HR320(gpibSelector.currentText)
                                }
                            }

                            ColumnLayout{

                                Label {
                                    text: "CALIBRATE WAVELENGTH:"
                                    color: "#888888"
                                    font.pixelSize: 10
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }

                                // Validated Input Field
                                TextField {
                                    id: calibrationInput
                                    Layout.fillWidth: true //Layout.preferred
                                    height: 40
                                    text: "650.0" // Default startupvalue
                                    color: "#FFFFFF" // Neon Purple Accent of Theme
                                    font.pixelSize: 16
                                    font.bold: true
                                    font.family: "Courier" // Monospace looks great for hardware UIs
                                    selectByMouse: true
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: TextInput.AlignVCenter

                                    // Restricts input strictly to decimals between 0.0 and 1300.0 nm --> These are limits of HR-320 According to Horiba Documentation
                                    validator: DoubleValidator {
                                        bottom: 0.0
                                        top: 1300.0
                                        decimals: 1
                                        notation: DoubleValidator.StandardNotation
                                    }

                                    background: Rectangle {
                                        color: "#2D2D2D" // Black background inside the widget panel
                                        border.color: calibrationInput.activeFocus ? "#BF00FF" : "#111111"
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
                                        x: (parent.width / 2) + (calibrationInput.contentWidth / 2) + 6

                                        anchors.verticalCenter: parent.verticalCenter

                                        // Optional: Hides the unit badge completely if the field is empty
                                        visible: calibrationInput.text.length > 0
                                    }
                                }
                            }

                            // Button to Calibrate Wavelength
                            Button {
                                id: spectrometerCalibrateButton
                                enabled: trs_controller.isHR320Connected
                                hoverEnabled: trs_controller.isHR320Connected
                                Layout.fillWidth: true
                                Layout.preferredHeight: 25
                                contentItem: Text {
                                    text: "Calibrate Spectrometer"
                                    color: spectrometerCalibrateButton.enabled ? (spectrometerCalibrateButton.down ? "#FFFFFF" : "#0096FF") : "#808080" // Neon Blue
                                    font.pixelSize: 16
                                    font.bold: true
                                    font.family: "Courier"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                background: Rectangle {
                                    color: spectrometerCalibrateButton.pressed ? "#0077CC" : (spectrometerCalibrateButton.hovered ? "#888888" : "#111111")
                                    border.color: spectrometerCalibrateButton.enabled ? "#0096FF" : "#808080"
                                    border.width: 1
                                    radius: 12
                                }

                                onPressed: {
                                    trs_controller.calibrate_HR320(calibrationInput.text)
                                }
                            }


                            ColumnLayout{
                                spacing: 2

                                Label {
                                    text: "TARGET WAVELENGTH:"
                                    color: "#888888"
                                    font.pixelSize: 10
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }

                                // Validated Input Field
                                TextField {
                                    id: wavelengthInput
                                    Layout.fillWidth: true //Layout.preferred
                                    height: 40
                                    text: "650.0" // Default startupvalue
                                    color: "#FFFFFF" // Neon Purple Accent of Theme
                                    font.pixelSize: 16
                                    font.bold: true
                                    font.family: "Courier" // Monospace looks great for hardware UIs
                                    selectByMouse: true
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: TextInput.AlignVCenter

                                    // Restricts input strictly to decimals between 0.0 and 1300.0 nm --> These are limits of HR-320 According to Horiba Documentation
                                    validator: DoubleValidator {
                                        bottom: 0.0
                                        top: 1300.0
                                        decimals: 1
                                        notation: DoubleValidator.StandardNotation
                                    }

                                    background: Rectangle {
                                        color: "#2D2D2D" // Black background inside the widget panel
                                        border.color: wavelengthInput.activeFocus ? "#BF00FF" : "#111111"
                                        border.width: 1
                                        radius: 4
                                    }

                                    Label {
                                        id: unitLabel
                                        text: "nm"
                                        color: "#AAAAAA"
                                        font.pixelSize: 14
                                        font.family: "Courier"
                                        font.bold: true

                                        // X position calculation:
                                        // Starts at the left padding, adds the real width of the text, plus spacing
                                        x: (parent.width / 2) + (wavelengthInput.contentWidth / 2) + 6

                                        anchors.verticalCenter: parent.verticalCenter

                                        // Optional: Hides the unit badge completely if the field is empty
                                        visible: wavelengthInput.text.length > 0
                                    }
                                }
                            }

                            // Button to Move to Target Wavelength
                            Button {
                                id: spectrometerMoveButton
                                enabled: trs_controller.isHR320Calibrated && !trs_controller.isHR320Busy
                                hoverEnabled: trs_controller.isHR320Calibrated && !trs_controller.isHR320Busy
                                Layout.fillWidth: true
                                Layout.preferredHeight: 25
                                contentItem: Text {
                                    text: "Move Spectrometer"
                                    color: spectrometerMoveButton.enabled ? (spectrometerMoveButton.down ? "#FFFFFF" : "#2CFF05") : "#808080" // Neon Green
                                    font.pixelSize: 16
                                    font.bold: true
                                    font.family: "Courier"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                background: Rectangle {
                                    color: spectrometerMoveButton.pressed ? "#339152" : (spectrometerMoveButton.hovered ? "#888888" : "#111111")
                                    border.color: spectrometerMoveButton.enabled ? "#2CFF05" : "#808080"
                                    border.width: 1
                                    radius: 12
                                }

                                onPressed:{
                                    trs_controller.move_HR320_motor(wavelengthInput.text)
                                }
                            }

                            // Button to Stop Spectrometer
                            Button {
                                id: spectrometerStopButton
                                enabled: trs_controller.isHR320Calibrated && trs_controller.isHR320Busy
                                hoverEnabled: trs_controller.isHR320Calibrated && trs_controller.isHR320Busy
                                Layout.fillWidth: true
                                Layout.preferredHeight: 25
                                contentItem: Text {
                                    text: "Stop Spectrometer"
                                    color: spectrometerStopButton.enabled ? (spectrometerStopButton.down ? "#FFFFFF" : "#FF2C2C") : "#808080" // Neon Red
                                    font.pixelSize: 16
                                    font.bold: true
                                    font.family: "Courier"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                background: Rectangle {
                                    color: spectrometerStopButton.pressed ? "#B20000" : (spectrometerStopButton.hovered ? "#888888" : "#111111")
                                    border.color: spectrometerStopButton.pressed ? "#FF2C2C" : "#808080"
                                    border.width: 1
                                    radius: 12
                                }

                                onPressed:{
                                    trs_controller.stop_HR320_motor()
                                }
                            }

                            // CURRENT WAVELENGTH DISPLAY (Read-Only Status)
                            ColumnLayout {
                                spacing: 2

                                Label {
                                    text: "CURRENT WAVELENGTH:"
                                    color: "#888888"
                                    font.pixelSize: 10
                                    font.bold: true
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 40
                                    color: "#111111" // Darker background to distinguish from input
                                    border.color: "#333333"
                                    border.width: 1
                                    radius: 4

                                    RowLayout{
                                        spacing: 1
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        anchors.verticalCenter: parent.verticalCenter

                                        Label {
                                            id: currentWavelengthDisplay
                                            // Link this text property to your actual C++ or backend backend property
                                            // e.g., text: spectrometer.currentWavelength.toFixed(1)
                                            text: trs_controller.currentWavelength
                                            color: "#B6B0FF" // Readable bright purple which is the accent for our black/green theme
                                            font.pixelSize: 16
                                            font.bold: true
                                            font.family: "Courier"
                                        }

                                        Label{
                                            text: " nm"
                                            color: "#B6B0FF" // Classic matrix green for telemetry data
                                            font.pixelSize: 16
                                            font.bold: true
                                            font.family: "Courier"
                                            opacity: 0.6 // Make the text for the unit (nm) be slightly darker than the value to aid readability
                                        }
                                    }
                                }
                            }

                            ColumnLayout{
                                spacing: 2

                                Label {
                                    text: "MOTOR STATUS:"
                                    color: "#888888"
                                    font.pixelSize: 10
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }

                                Rectangle {
                                    color: "#111111" // Black background inside the widget panel
                                    border.color: "#333333"
                                    border.width: 1
                                    radius: 4
                                    Layout.fillWidth: true
                                    height: 40

                                    Label{
                                        anchors.centerIn: parent
                                        text: trs_controller.isHR320Busy ? "Motor Busy" : "Motor Free"
                                        color: trs_controller.isHR320Busy ?  "#FF2C2C" : "#2CFF05"
                                        font.bold: true
                                        font.family: "Courier"
                                        font.pixelSize: 20
                                        Layout.alignment: Qt.AlignVCenter
                                    }
                                }
                            }
                        }
                    }

                    // MODULE 2: PLACEHOLDER FOR PICOHARP 300
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 140
                        color: "#2D2D2D"
                        opacity: 0.5 // Dimmed to show it is a future expansion
                        radius: 4

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 15

                            Label {
                                text: "PicoHarp 300 (Future Work)"
                                color: "#FFFFFF"
                                font.bold: true
                                font.pixelSize: 16
                            }

                            Label {
                                text: "TCSPC modules will plug in here."
                                color: "#888888"
                                font.pixelSize: 12
                            }
                        }
                    }

                    // MODULE 3: PLACEHOLDER FOR SR400
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 140
                        color: "#2D2D2D"
                        opacity: 0.5
                        radius: 4

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 15

                            Label {
                                text: "SR400 Gated Counter (Future Work)"
                                color: "#FFFFFF"
                                font.bold: true
                                font.pixelSize: 16
                            }

                            Label {
                                text: "Photon counter parameters go here."
                                color: "#888888"
                                font.pixelSize: 12
                            }
                        }
                    }

                    // Pushes modules to the top of the sidebar
                    Item { Layout.fillHeight: true }
                }
            }

            // ==========================================
            // RIGHT CANVAS: Future Live Plotting Engine
            // ==========================================
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#000000" // Pure Black canvas for the scope trace
                border.color: "#2D2D2D"
                border.width: 1

                Label {
                    anchors.centerIn: parent
                    text: "Plot Canvas Placeholder\\n(Will implement QCustomPlot, QtCharts, or QNanoPainter here)"
                    color: "#444444"
                    font.pixelSize: 16
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        Window {
            id: logWindow

            width: 700
            height: 500
            title: "Instrument Communication Log"

            visible: false

            Rectangle {
                anchors.fill: parent
                color: "#202020"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#101010"

                        ListView {
                            id: logView

                            anchors.fill: parent
                            anchors.margins: 8

                            model: logger

                            delegate: RowLayout {
                                width: logView.width
                                spacing: 10

                                Label {
                                    text: model.timestamp
                                    color: "#888888"
                                    font.family: "monospace"
                                }

                                Label {
                                    text: model.instrument
                                    color: model.instrument === "TX"
                                           ? "#66ccff"
                                           : model.instrument === "RX"
                                             ? "#66ff99"
                                             : "white"

                                    font.family: "monospace"
                                    font.bold: true
                                }

                                Label {
                                    text: model.message
                                    color: "white"
                                    font.family: "monospace"
                                }
                            }

                            ScrollBar.vertical: ScrollBar {}
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        Item {
                            Layout.fillWidth: true
                        }

                        Button {
                            text: "Clear Log"

                            onClicked: {
                                logger.clear()
                            }
                        }

                        Button {
                            text: "Close"

                            onClicked: {
                                logWindow.hide()
                            }
                        }
                    }
                }
            }
        }
    }
}
