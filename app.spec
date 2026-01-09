# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, copy_metadata


# Collect VPython internal files
vpython_datas = collect_data_files('vpython', include_py_files=True)
# Ensure metadata is copied for VPython
vpython_metadata = copy_metadata('vpython')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')] + vpython_datas + vpython_metadata,
    hiddenimports=['vpython.vpython', 'vpython.gs_version'],
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
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)
