import json

from PySide6.QtCore import QObject, Property, QProcess, QTimer, Signal, Slot
from PySide6.QtSerialPort import QSerialPortInfo

class SerialManager(QObject):

    boardsChanged = Signal()
    selectedPortChanged = Signal()
    statusChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._boards = []
        self._selected_port = ""
        self._status = "Looking for boards…"
        self._ports = None
        self._rescan_pending = False

        self._process = QProcess(self)
        self._process.finished.connect(self._scan_finished)
        self._process.errorOccurred.connect(self._scan_error)

        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.setInterval(15000)
        self._timeout.timeout.connect(self._process.kill)

        self._watcher = QTimer(self)
        self._watcher.setInterval(1000)
        self._watcher.timeout.connect(self._check_ports)
        self._watcher.start()
        QTimer.singleShot(0, self._check_ports)

    @Property("QVariantList", notify=boardsChanged)
    def boards(self):
        return self._boards

    @Property(str, notify=selectedPortChanged)
    def selectedPort(self):
        return self._selected_port

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    def _set_status(self, text):
        if self._status != text:
            self._status = text
            self.statusChanged.emit()

    def _check_ports(self):
        ports = sorted(
            (p.systemLocation(), p.serialNumber(), p.vendorIdentifier(),
             p.productIdentifier())
            for p in QSerialPortInfo.availablePorts()
        )
        if ports != self._ports:
            self._ports = ports
            self.rescan()

    @Slot()
    def rescan(self):
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._rescan_pending = True
            return
        self._set_status("Looking for boards…")
        self._process.start("arduino-cli", ["board", "list", "--json"])
        self._timeout.start()

    def _scan_error(self, error):
        self._timeout.stop()
        if error == QProcess.ProcessError.FailedToStart:
            self._set_status("Cannot start arduino-cli. Install it and add it to PATH.")
        else:
            self._set_status("Board scan failed: " + self._process.errorString())

    def _scan_finished(self, exit_code, exit_status):
        self._timeout.stop()
        if exit_code != 0 or exit_status != QProcess.ExitStatus.NormalExit:
            detail = bytes(self._process.readAllStandardError()).decode(errors="replace").strip()
            self._set_status(detail or "Board scan failed or timed out.")
        else:
            try:
                result = json.loads(bytes(self._process.readAllStandardOutput()))
                # Older CLI releases returned the ports directly as an array.
                ports = result if isinstance(result, list) else result.get("detected_ports", [])
                boards = []
                for item in ports:
                    port = item["port"]
                    if port.get("protocol") != "serial":
                        continue
                    # Unidentified serial devices may also be Arduino clones.
                    for board in item.get("matching_boards") or [{"name": "Unknown board"}]:
                        boards.append({
                            "label": f"{board['name']} ({port['address']})",
                            "port": port["address"],
                            "fqbn": board.get("fqbn", ""),
                        })
                self._boards = boards
                self.boardsChanged.emit()
                if self._selected_port not in [b["port"] for b in boards]:
                    self._selected_port = ""
                    self.selectedPortChanged.emit()
                self._set_status(f"{len(boards)} board option(s) found." if boards else "No serial boards found.")
            except (ValueError, KeyError, TypeError, AttributeError):
                self._set_status("Could not read the arduino-cli board list.")
        if self._rescan_pending:
            self._rescan_pending = False
            self.rescan()

    @Slot(int)
    def selectBoard(self, index):
        if 0 <= index < len(self._boards):
            self._selected_port = self._boards[index]["port"]
            self.selectedPortChanged.emit()

    @Slot()
    def stop(self):
        self._watcher.stop()
        self._timeout.stop()
        self._rescan_pending = False
        self._process.blockSignals(True)
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(1000)

