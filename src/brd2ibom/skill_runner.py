from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from typing import Callable
from pathlib import Path

from .cadence import CadenceInstallation
from .errors import Brd2IbomError
from .paths import default_export_config, default_export_json_script, default_json_decode_script, default_skill_bridge


@dataclass(frozen=True)
class SkillExportResult:
    workspace: Path
    json_files: tuple[Path, ...]
    log_file: Path


def _skill_path(path: Path) -> str:
    """Format a Windows path for an Allegro script string."""
    return path.resolve().as_posix().replace('"', '\\"')


def create_skill_script(
    script_path: Path,
    export_json_script: Path,
    json_decode_script: Path,
    config_path: Path,
    revision: str,
    company: str,
) -> None:
    """Create the short Allegro .scr bridge used by headless export."""
    lines = [
        f'skill load("{_skill_path(json_decode_script)}")',
        f'skill load("{_skill_path(export_json_script)}")',
        (
            'skill exportJson('
            f'?rev "{revision}" '
            f'?company "{company}" '
            f'?config "{_skill_path(config_path)}")'
        ),
        "exit",
    ]
    script_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _copy_board_workspace(board_path: Path) -> Path:
    workspace = Path(tempfile.mkdtemp(prefix="brd2ibom-"))
    shutil.copy2(board_path, workspace / board_path.name)

    variants_candidates = (
        board_path.parent / "Variants.lst",
        board_path.parent / "allegro" / "Variants.lst",
    )
    for variants in variants_candidates:
        if variants.is_file():
            shutil.copy2(variants, workspace / variants.name)
            break
    return workspace


def run_skill_export(
    board_path: Path,
    installation: CadenceInstallation,
    timeout_seconds: int,
    product: str | None = None,
    keep_workspace: bool = False,
    revision: str = "AUTO",
    company: str = "iBOM Tools",
    log_callback: Callable[[str], None] | None = None,
) -> SkillExportResult:
    """Run Allegro headlessly and export the opened BRD to generic JSON."""
    board_path = board_path.resolve()
    workspace = _copy_board_workspace(board_path)
    script_path = workspace / "ibom_export.scr"
    log_file = workspace / "allegro.log"
    config_path = default_export_config()
    if not config_path.is_file():
        raise Brd2IbomError(f"iBOM 导出配置不存在：{config_path}")

    create_skill_script(
        script_path=script_path,
        export_json_script=default_export_json_script(),
        json_decode_script=default_json_decode_script(),
        config_path=config_path,
        revision=revision,
        company=company,
    )

    command = [str(installation.executable)]
    if product:
        command.extend(["-product", product])
    command.extend(["-pcb", "-s", str(script_path), "-nograph", str(workspace / board_path.name)])

    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    environment = os.environ.copy()
    environment["CDSROOT"] = str(installation.root)
    tool_paths = [
        installation.root / "tools" / "bin",
        installation.root / "tools" / "pcb" / "bin",
    ]
    existing_path = environment.get("PATH", "")
    environment["PATH"] = os.pathsep.join([*(str(path) for path in tool_paths), existing_path])
    try:
        try:
            process = subprocess.Popen(
                command,
                cwd=workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=environment,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creation_flags,
            )
        except FileNotFoundError as exc:
            raise Brd2IbomError(f"无法启动 Allegro：{installation.executable}") from exc

        def read_output() -> None:
            with log_file.open("w", encoding="utf-8", errors="replace") as output:
                if process.stdout is None:
                    return
                for raw_line in process.stdout:
                    line = raw_line.rstrip("\r\n")
                    output.write(raw_line)
                    output.flush()
                    if log_callback and line:
                        try:
                            log_callback(line)
                        except Exception:
                            pass

        reader = threading.Thread(target=read_output, name="allegro-log-reader", daemon=True)
        reader.start()
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            process.wait()
            reader.join(timeout=5)
            raise Brd2IbomError(
                f"Allegro 导出超时，已达到 {timeout_seconds} 秒。日志位置：{log_file}"
            ) from exc
        reader.join(timeout=5)
        completed_returncode = process.returncode

        json_dir = workspace / "json"
        json_files = tuple(sorted(json_dir.glob("*.json"))) if json_dir.is_dir() else ()
        if completed_returncode != 0 or not json_files:
            detail = ""
            if log_file.is_file():
                content = log_file.read_text(encoding="utf-8", errors="replace").strip()
                if content:
                    detail = f"\n\nAllegro 日志：\n{content[-4000:]}"
            raise Brd2IbomError(
                f"Allegro 没有成功导出 JSON，退出码为 {completed_returncode}。"
                f"{detail}"
            )

        return SkillExportResult(workspace=workspace, json_files=json_files, log_file=log_file)
    except Exception:
        if not keep_workspace:
            shutil.rmtree(workspace, ignore_errors=True)
        raise

