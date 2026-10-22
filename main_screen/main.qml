import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    width: 300
    height: 200
    visible: true
    title: "Rover Control"

    ColumnLayout {
        anchors.fill:  parent

        Button {
            text: serialManager.selectedPort || "Select Arduino board"
            Layout.alignment: Qt.AlignHCenter
            onClicked: boardMenu.open()

            Menu {
                id: boardMenu
                y: parent.height

                Instantiator {
                    model: serialManager.boards
                    delegate: MenuItem {
                        required property var modelData
                        required property int index
                        text: modelData.label
                        onTriggered: serialManager.selectBoard(index)
                    }
                    onObjectAdded: (index, object) => boardMenu.insertItem(index, object)
                    onObjectRemoved: (index, object) => boardMenu.removeItem(object)
                }

                MenuItem {
                    text: "No boards found"
                    visible: serialManager.boards.length === 0
                    height: visible ? implicitHeight : 0
                    enabled: false
                }
                MenuSeparator {}
                MenuItem {
                    text: "Rescan"
                    onTriggered: serialManager.rescan()
                }
            }
        }
        Label {
            text: serialManager.status
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
    }
}

