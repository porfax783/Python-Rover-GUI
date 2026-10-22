import sys
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from serial_manager import SerialManager

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    serial_manager = SerialManager(app)
    app.aboutToQuit.connect(serial_manager.stop)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("serialManager", serial_manager)
    engine.addImportPath(sys.path[0])
    engine.loadFromModule("main_screen", "main")
    if not engine.rootObjects():
        sys.exit(-1)
    exit_code = app.exec()
    del engine
    sys.exit(exit_code)
