import sys
import os
import subprocess

# import time, sorry bro, but i replaced you with QTimer
import socket
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

IS_FROZEN = getattr(sys, "_MEIPASS", None) is not None
PORT = 8501


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
    # the broken white screen happened when execution has no Click context, so initialize Streamlit through bootstrap directly.
    flag_options = {
        "global.developmentMode": False,
        "server.address": "127.0.0.1",
        "server.port": port,
        "server.headless": True,
    }
    config._main_script_path = os.path.abspath(script_path)
    bootstrap.load_config_options(flag_options=flag_options)
    bootstrap.run(script_path, False, [], flag_options)


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

        self.network_manager = QNetworkAccessManager(self)
        self.readiness_request_pending = False
        self.check_timer = QTimer()  # replacement for time.time(), who tf names these
        self.check_timer.timeout.connect(self.check_server_ready)
        self.check_timer.start(100)

    def check_server_ready(self):
        if self.readiness_request_pending:
            return
        self.readiness_request_pending = True
        request = QNetworkRequest(
            QUrl(f"http://127.0.0.1:{self.port}/_stcore/health")
        )
        reply = self.network_manager.get(request)
        reply.finished.connect(self.check_root_route)

    def check_root_route(self):
        reply = self.sender()
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        reply.deleteLater()
        if status != 200:
            self.readiness_request_pending = False
            return

        request = QNetworkRequest(QUrl(f"http://127.0.0.1:{self.port}/"))
        root_reply = self.network_manager.get(request)
        root_reply.finished.connect(self.load_dashboard)

    def load_dashboard(self):
        reply = self.sender()
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        reply.deleteLater()
        self.readiness_request_pending = False
        if status == 200:
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
    window = StreamlitWindow(PORT)
    window.show()
    sys.exit(app.exec())
