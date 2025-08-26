// Includes relevant modules used by the QML
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Provides basic features needed for all kirigami applications
Kirigami.ApplicationWindow {
    // Unique identifier to reference this object
    id: root

    width: 800
    height: 600

    // Window title
    title: "System Update"
    
    // Handle close events - prevent closing while tasks are running
    onClosing: function(close) {
        if (backend && !backend.can_close_app()) {
            close.accepted = false
        }
    }

    // Connect to popup message signal
    Connections {
        target: backend
        function onShowPopupMessage(message) {
            messageDialog.text = message
            messageDialog.open()
        }
    }

    // Popup dialog for messages
    Controls.Dialog {
        id: messageDialog
        title: "System Updater"
        standardButtons: Controls.Dialog.Ok
        anchors.centerIn: parent
        width: Math.max(400, messageLabel.implicitWidth + 60)
        height: Math.max(150, messageLabel.implicitHeight + 100)
        
        property alias text: messageLabel.text
        
        Controls.Label {
            id: messageLabel
            wrapMode: Text.WordWrap
            width: parent.width - 20
            anchors.centerIn: parent
        }
    }

    // Set the first page that will be loaded when the app opens
    pageStack.initialPage: Kirigami.Page {
        globalToolBarStyle: Kirigami.ApplicationHeaderStyle.None
        padding: Kirigami.Units.smallSpacing
        topPadding: Kirigami.Units.smallSpacing
        bottomPadding: Kirigami.Units.smallSpacing
        leftPadding: Kirigami.Units.smallSpacing
        rightPadding: Kirigami.Units.smallSpacing
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing

            Controls.ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Controls.TextArea {
                    id: outputText
                    readOnly: true
                    wrapMode: Controls.TextArea.Wrap
                    text: backend ? backend.outputText : "Output will appear here..."
                    background: Rectangle {
                        color: Kirigami.Theme.backgroundColor
                        border.color: Kirigami.Theme.disabledTextColor
                        border.width: 1
                    }
                }
            }

            // Button row at the bottom
            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                Controls.Button {
                    text: "Change Logs"
                    Layout.fillWidth: true
                    enabled: backend ? !backend.isRunning : false
                    onClicked: {
                        if (backend) backend.open_logs()
                    }
                }

                Controls.Button {
                    text: "Update"
                    Layout.fillWidth: true
                    enabled: backend ? !backend.isRunning : false
                    onClicked: {
                        if (backend) backend.activate_update()
                    }
                }

                Controls.Button {
                    text: "Apply Update (Reboot)"
                    Layout.fillWidth: true
                    enabled: backend ? (!backend.isRunning && backend.updateCompleted) : false
                    onClicked: {
                        if (backend) backend.reboot_system()
                    }
                }

                Controls.Button {
                    text: "Exit"
                    Layout.fillWidth: true
                    enabled: backend ? !backend.isRunning : false
                    onClicked: {
                        if (backend) backend.exit_app()
                    }
                }
            }
        }
    }
}
