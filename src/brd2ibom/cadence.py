from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .errors import Brd2IbomError


@dataclass(frozen=True)
class CadenceInstallation:
    root: Path
    executable: Path

    @property
    def version(self) -> str | None:
        match = re.search(r"SPB[_-](\d+(?:\.\d+)*)", self.root.name, re.IGNORECASE)
        return match.group(1) if match else None


def _candidate_executables(root: Path) -> Iterable[Path]:
    yield root / "tools" / "bin" / "allegro.exe"
    yield root / "tools" / "pcb" / "bin" / "allegro.exe"
    yield root / "tools" / "pcb" / "bin" / "allegrox.exe"
    yield root / "tools" / "pcb" / "bin" / "allegro_x.exe"


def _infer_installation_root(executable: Path) -> Path:
    for parent in (executable.parent, *executable.parents):
        if parent.name.lower() == "tools":
            return parent.parent
    return executable.parents[2]


def _installation_from_root(root: Path) -> CadenceInstallation | None:
    root = root.expanduser().resolve()
    for executable in _candidate_executables(root):
        if executable.is_file():
            return CadenceInstallation(root=root, executable=executable)
    return None


def _roots_from_environment() -> list[Path]:
    roots: list[Path] = []
    for name in ("CDSROOT", "ALLEGRO_ROOT", "ALLEGRO_INSTALL_ROOT"):
        value = os.environ.get(name)
        if value:
            roots.append(Path(value))
    return roots


def _roots_from_registry() -> list[Path]:
    if os.name != "nt":
        return []

    try:
        import winreg
    except ImportError:
        return []

    locations = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Cadence Design Systems, Inc."),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Cadence Design Systems, Inc."),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Cadence Design Systems, Inc."),
    ]
    roots: list[Path] = []

    def visit(key, path: str) -> None:
        try:
            subkeys, values, _ = winreg.QueryInfoKey(key)
            for index in range(values):
                name, value, _ = winreg.EnumValue(key, index)
                if isinstance(value, str) and ("SPB" in name.upper() or "ROOT" in name.upper()):
                    candidate = Path(value)
                    if candidate.exists():
                        roots.append(candidate)
            for index in range(subkeys):
                child_name = winreg.EnumKey(key, index)
                try:
                    child = winreg.OpenKey(key, child_name)
                except OSError:
                    continue
                with child:
                    visit(child, f"{path}\\{child_name}")
        except OSError:
            return

    for hive, key_path in locations:
        try:
            key = winreg.OpenKey(hive, key_path)
        except OSError:
            continue
        with key:
            visit(key, key_path)
    return roots


def _common_roots() -> list[Path]:
    roots: list[Path] = []
    drives = {Path.cwd().drive.upper(), os.environ.get("SystemDrive", "").upper()}
    drives.update(f"{letter}:" for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ")
    bases = [
        Path(f"{drive}/Cadence")
        for drive in sorted(drive for drive in drives if drive)
    ]
    bases.extend(
        Path(f"{drive}/Cadence Design Systems")
        for drive in sorted(drive for drive in drives if drive)
    )
    bases.extend(
        Path(f"{drive}/Program Files/Cadence")
        for drive in sorted(drive for drive in drives if drive)
    )
    for base in bases:
        if not base.is_dir():
            continue
        try:
            roots.extend(path for path in base.iterdir() if path.is_dir())
        except OSError:
            continue
    return roots


def locate_cadence(root: str | Path | None = None, executable: str | Path | None = None) -> CadenceInstallation:
    """Find an Allegro executable using explicit, environment, registry and common paths."""
    if executable:
        path = Path(executable).expanduser().resolve()
        if path.is_file():
            return CadenceInstallation(root=_infer_installation_root(path), executable=path)
        raise Brd2IbomError(f"指定的 Allegro 可执行文件不存在：{path}")

    roots: list[Path] = []
    if root:
        roots.append(Path(root))
    roots.extend(_roots_from_environment())
    roots.extend(_roots_from_registry())
    roots.extend(_common_roots())

    seen: set[Path] = set()
    for candidate_root in roots:
        try:
            normalized = candidate_root.expanduser().resolve()
        except OSError:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        installation = _installation_from_root(normalized)
        if installation:
            return installation

    raise Brd2IbomError(
        "找不到 Cadence Allegro。请使用 --cadence-root 指定安装目录，"
        "或使用 --cadence-exe 指定 allegro.exe。"
    )

