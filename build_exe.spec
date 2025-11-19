# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Container Geometry Analyzer
This creates a standalone .exe for Windows that can run in air-gapped environments.

Build with: pyinstaller build_exe.spec
"""

import sys
import os

# Get the directory where this spec file is located
spec_dir = os.path.dirname(os.path.abspath(__file__))

block_cipher = None

a = Analysis(
    [os.path.join(spec_dir, 'src/container_geometry_analyzer_gui_v3_11_8.py')],
    pathex=[spec_dir],
    binaries=[],
    datas=[
        (os.path.join(spec_dir, 'data'), 'data'),
        (os.path.join(spec_dir, 'requirements.txt'), '.'),
    ],
    hiddenimports=[
        'scipy.special._ufuncs_cxx',
        'scipy.signal.windows',
        'scipy.optimize',
        'scipy.interpolate',
        'scipy.signal',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ContainerGeometryAnalyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

# Optional: Create a Windows directory distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ContainerGeometryAnalyzer',
)
