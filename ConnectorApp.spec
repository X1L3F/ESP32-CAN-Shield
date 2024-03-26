# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\einrichten\\FuE_2_esp_can\\ESP32-CAN-Shield\\Connector\\qt_application_frontend.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\einrichten\\FuE_2_esp_can\\ESP32-CAN-Shield\\Connector\\qt_application.ui', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ConnectorApp',
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
