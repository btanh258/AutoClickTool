# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['AutoClickTool.pyw'],
    pathex=[],
    binaries=[],
    datas=[('icon_AutoClickTool.ico', '.')],
    hiddenimports=['pynput.keyboard._win32', 'pynput.mouse._win32',
                   'pystray._win32'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# 1.1.6: onedir (khong onefile nua) - python311.dll + cac DLL nam canh
# exe trong thu muc app, khong con buoc giai nen ra %TEMP%\_MEI* moi lan
# mo app, nen Defender khong chan duoc LoadLibrary sau khi cap nhat.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AutoClickTool',
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
    icon=['icon_AutoClickTool.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoClickTool',
)
