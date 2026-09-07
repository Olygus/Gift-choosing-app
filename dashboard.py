import sys
import os
import subprocess

# import time, sorry bro, but i replaced you with QTimer
import socket
import urllib.request
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

IS_FROZEN = getattr(sys, "_MEIPASS", None) is not None


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def run_bundled_streamlit(port):
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    from streamlit import config
    from streamlit.web import bootstrap

    if len(sys.argv) < 3:
        raise SystemExit(
            "Missing Streamlit script path (expected: --run-streamlit <script> [args...])"
        )

    script_path = sys.argv[2]
    config.set_option("server.address", "127.0.0.1")
    config.set_option("server.port", port)
    config.set_option("server.headless", True)
    bootstrap.run(
        script_path,
        False,
        sys.argv[3:],
        {
            "server.address": "127.0.0.1",
            "server.port": port,
            "server.headless": True,
        },
    )


def is_server_ready(port):
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/_stcore/health", timeout=1
        ) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


class StreamlitWindow(QMainWindow):
    def __init__(self, port):
        super().__init__()
        self.port = port
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
        if IS_FROZEN:
            script_path = os.path.join(sys._MEIPASS, "app.py")
        else:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

        streamlit_command = [
            sys.executable,
            "--run-streamlit",
            script_path,
            f"--server.port={port}",
            "--server.address=127.0.0.1",
            "--server.headless=true",
        ] if IS_FROZEN else [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            script_path,
            f"--server.port={port}",
            "--server.address=127.0.0.1",
            "--server.headless=true",
        ]
        self.server_process = subprocess.Popen(
            streamlit_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.check_timer = QTimer()  # replacement for time.time(), who tf names these
        self.check_timer.timeout.connect(self.check_server_ready)
        self.check_timer.start(100)

    def check_server_ready(self):
        if is_server_ready(self.port):
            self.check_timer.stop()
            self.browser.setUrl(QUrl(f"http://127.0.0.1:{self.port}"))

    def closeEvent(self, event):
        if hasattr(self, "server_process"):
            self.server_process.terminate()
        event.accept()


# failed to implement an iteration where the app runs on a headless server with self.server_process to avoid having to install streamlit on every machine

# def not_gonna_Kill_myself(python): removed as i finished the fkn python

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run-streamlit":
        port_argument = next(
            argument for argument in sys.argv[3:] if argument.startswith("--server.port=")
        )
        run_bundled_streamlit(int(port_argument.split("=", 1)[1]))
        raise SystemExit

    app = QApplication(sys.argv)
    window = StreamlitWindow(find_free_port())
    window.show()
    sys.exit(app.exec())
