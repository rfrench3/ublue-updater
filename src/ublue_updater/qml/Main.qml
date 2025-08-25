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
    title: i18nc("@title:window", "System Update")

    // Set the first page that will be loaded when the app opens
    pageStack.initialPage: Kirigami.Page {
        ColumnLayout {
            anchors.fill: parent

            Controls.ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Controls.TextArea {
                    id: outputText
                    readOnly: true
                    wrapMode: TextArea.Wrap
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
                    onClicked: {
                        if (backend) backend.open_logs()
                    }
                }

                Controls.Button {
                    text: "Update"
                    Layout.fillWidth: true
                    onClicked: {
                        if (backend) backend.activate_update()
                    }
                }

                Controls.Button {
                    text: "Apply Update (Reboot)"
                    Layout.fillWidth: true
                    onClicked: {
                        if (backend) backend.reboot_system()
                    }
                }

                Controls.Button {
                    text: "Exit"
                    Layout.fillWidth: true
                    onClicked: {
                        if (backend) backend.exit_app()
                    }
                }
            }
        }
    }
}
