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
                rightPadding: 10
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
                    width: sleekScrollView.availableWidth
                    spacing: 15

                    Layout.alignment: Layout.Center

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

                                StyledComboBox{
                                    id: gpibSelector
                                    Layout.fillWidth: true

                                    // Get the GPIB addresses found by the time resolved controller
                                    model: trs_controller.gpibAddresses
                                    currentIndex: 1
                                }

                            }

                            // Button to connect the HR320 Spectrometer
                            StyledButton{
                                id: spectrometerConnectButton
                                displayText: "Connect Spectrometer"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 25

                                buttonColor: "#2CFF05"
                                pressedColor: "#339152"

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


                                StyledTextFieldWithUnits{
                                    id: calibrationInput
                                    Layout.fillWidth: true

                                    displayText: "650.0" // Default startupvalue
                                    displayColor: "#FFFFFF"

                                    // Restricts input strictly to decimals between 0.0 and 1300.0 nm --> These are limits of HR-320 According to Horiba Documentation
                                    bottomAllowedVal: 0.0
                                    topAllowedVal: 1300.0
                                    allowedDecimalPlaces: 1

                                }

                            }

                            // Button to Calibrate Wavelength
                            StyledButton {
                                id: spectrometerCalibrateButton
                                displayText: "Calibrate Spectrometer"
                                enabled: trs_controller.isHR320Connected
                                hoverEnabled: trs_controller.isHR320Connected
                                Layout.fillWidth: true
                                Layout.preferredHeight: 25

                                buttonColor: "#0096FF"
                                pressedColor: "#0077CC"

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

                                StyledTextFieldWithUnits{
                                    id: wavelengthInput
                                    Layout.fillWidth: true

                                    displayText: "650.0" // Default startupvalue
                                    displayColor: "#FFFFFF"

                                    // Restricts input strictly to decimals between 0.0 and 1300.0 nm --> These are limits of HR-320 According to Horiba Documentation
                                    bottomAllowedVal: 0.0
                                    topAllowedVal: 1300.0
                                    allowedDecimalPlaces: 1

                                }
                            }

                            // Button to Move to Target Wavelength
                            StyledButton {
                                id: spectrometerMoveButton
                                displayText: "Move Spectrometer"
                                enabled: trs_controller.isHR320Calibrated && !trs_controller.isHR320Busy
                                hoverEnabled: trs_controller.isHR320Calibrated && !trs_controller.isHR320Busy
                                Layout.fillWidth: true
                                Layout.preferredHeight: 25

                                buttonColor: "#2CFF05"
                                pressedColor: "#339152"

                                onPressed:{
                                    trs_controller.move_HR320_motor(wavelengthInput.text)
                                }
                            }

                            // Button to Stop Spectrometer
                            StyledButton {
                                id: spectrometerStopButton
                                displayText: "Stop Spectrometer"

                                enabled: trs_controller.isHR320Calibrated && trs_controller.isHR320Busy
                                hoverEnabled: trs_controller.isHR320Calibrated && trs_controller.isHR320Busy
                                Layout.fillWidth: true
                                Layout.preferredHeight: 25

                                buttonColor: "#FF3131"
                                pressedColor: "#B20000"

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

                                NumericalDisplayWithUnits{
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 40

                                    displayValue: trs_controller.currentWavelength
                                    displayUnit: " nm"
                                    displayColor: "#B6B0FF" // Readable bright purple which is the accent for our black/green theme
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

                                StatusDisplay{
                                    Layout.fillWidth: true
                                    displayText: trs_controller.isHR320Busy ? "Motor Busy" : "Motor Free"
                                    displayColor: trs_controller.isHR320Busy ?  "#FF3131" : "#2CFF05"
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
