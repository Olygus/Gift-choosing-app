# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all
import os
import streamlit


streamlit_datas, streamlit_binaries, streamlit_hiddenimports = collect_all("streamlit")
streamlit_static_path = os.path.join(os.path.dirname(streamlit.__file__), "static")

a = Analysis(
    ['dashboard.py'],
    pathex=[],
    binaries=streamlit_binaries,
    datas=streamlit_datas + [
        (streamlit_static_path, 'streamlit/static'),
        ('app.py', '.'),
        ('giftyfy.db', '.'),
        ('assets/logo.png', 'assets'),
        ('assets/style.css', 'assets'),
        ('assets/templates.py', 'assets'),
    ],
    hiddenimports=streamlit_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='dashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
