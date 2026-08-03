from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH).parent
webview_datas, webview_binaries, webview_hiddenimports = collect_all("webview")

a = Analysis(
    [str(project_root / "desktop.py")],
    pathex=[str(project_root)],
    binaries=webview_binaries,
    datas=[
        (str(project_root / "app" / "static"), "app/static"),
        (str(project_root / "data" / "processed"), "data/processed"),
        (str(project_root / "prompts"), "prompts"),
        (str(project_root / "packaging" / "WinAssist.ico"), "."),
        *webview_datas,
    ],
    hiddenimports=webview_hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WinAssist",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project_root / "packaging" / "WinAssist.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="WinAssist",
)
