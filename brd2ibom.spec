# PyInstaller build specification for the personal Windows executable.
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


root = Path(SPECPATH)
hiddenimports = [
    *collect_submodules("brd2ibom"),
    *collect_submodules("InteractiveHtmlBom"),
    "jsonschema",
    "jsonschema_specifications",
    "referencing",
    "rpds",
    "attrs",
]
datas = [
    (str(root / "vendor" / "InteractiveHtmlBom"), "vendor/InteractiveHtmlBom"),
    (str(root / "vendor" / "exportJson"), "vendor/exportJson"),
    (str(root / "config"), "config"),
    (str(root / "skill"), "skill"),
]

a = Analysis(
    [str(root / "entrypoint.py")],
    pathex=[str(root / "src"), str(root / "vendor" / "InteractiveHtmlBom")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="brdibom",
    icon=str(root / "assets" / "brdibom.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
