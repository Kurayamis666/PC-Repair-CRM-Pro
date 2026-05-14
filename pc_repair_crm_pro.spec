# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


ROOT = Path(SPECPATH)

hiddenimports = []
for package_name in (
    "core",
    "database",
    "models",
    "services",
    "translations",
    "ui",
    "utils",
):
    hiddenimports += collect_submodules(package_name)
hiddenimports += collect_submodules("customtkinter")

datas = collect_data_files("customtkinter")

for path in [
    ROOT / ".env.example",
    ROOT / "database" / "schema.sql",
]:
    if path.exists():
        datas.append((str(path), str(path.parent.relative_to(ROOT))))

for package_name in (
    "core",
    "database",
    "models",
    "services",
    "translations",
    "ui",
    "utils",
):
    package_path = ROOT / package_name
    if package_path.exists():
        datas.append((str(package_path), package_name))

icon_path = ROOT / "ui" / "assets" / "app_icon.ico"
icon_arg = str(icon_path) if icon_path.exists() else None


a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(ROOT / "hooks")],
    hooksconfig={},
    runtime_hooks=[str(ROOT / "hooks" / "rthook_pc_repair_paths.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="PC Repair CRM Pro",
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
    exclude_binaries=True,
    icon=icon_arg,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PC Repair CRM Pro",
)
