import sys
import os
import subprocess

# import time, sorry bro, but i replaced you with QTimer
import socket
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

PORT = 8501


def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


class StreamlitWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.resize(1200, 800)

        self.browser = QWebEngineView()
        self.browser.setContextMenuPolicy(
            sys.modules["PyQt6.QtCore"].Qt.ContextMenuPolicy.NoContextMenu
        )

        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # PyInstaller path resolution for app.py
        if getattr(sys, "frozen", False):
            script_path = os.path.join(sys._MEIPASS, "app.py")
        else:
            script_path = os.path.abspath("app.py")

        self.server_process = subprocess.Popen(
            [
                "streamlit",
                "run",
                script_path,
                f"--server.port={PORT}",
                "--server.headless=true",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.check_timer = QTimer()  # replacement for time.time(), who tf names these
        self.check_timer.timeout.connect(self.check_server_ready)
        self.check_timer.start(100)

    def check_server_ready(self):
        if is_port_open(PORT):
            self.check_timer.stop()
            self.browser.setUrl(QUrl(f"http://127.0.0.1:{PORT}"))

    def closeEvent(self, event):
        if hasattr(self, "server_process"):
            self.server_process.terminate()
        event.accept()


# def not_gonna_Kill_myself(python): removed as i finished the fkn python

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StreamlitWindow()
    window.show()
    sys.exit(app.exec())
