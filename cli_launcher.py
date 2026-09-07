import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
executable = bundle_root / ("giftyfy.exe" if sys.platform == "win32" else "giftyfy")
arguments = [str(executable), *sys.argv[1:]]

if sys.platform == "win32" or (sys.stdin.isatty() and sys.stdout.isatty()):
	os.execv(str(executable), arguments)

terminal_commands = [
	("x-terminal-emulator", ["-e", *arguments]),
	("gnome-terminal", ["--wait", "--", *arguments]),
	("konsole", ["--hold", "-e", *arguments]),
	("xfce4-terminal", ["--hold", "--command", shlex.join(arguments)]),
	("xterm", ["-hold", "-e", *arguments]),
]

for terminal_name, terminal_arguments in terminal_commands:
	terminal_path = shutil.which(terminal_name)
	if terminal_path:
		subprocess.run([terminal_path, *terminal_arguments], check=False)
		break
else:
	raise RuntimeError("No supported terminal emulator was found")