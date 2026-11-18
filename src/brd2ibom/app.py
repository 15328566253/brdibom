from __future__ import annotations

import shutil
import webbrowser
from dataclasses import dataclass
from typing import Callable
from pathlib import Path

from .cadence import locate_cadence
from .errors import Brd2IbomError
from .ibom import generate_html
from .skill_runner import run_skill_export


@dataclass(frozen=True)
class RunOptions:
    output_dir: Path | None = None
    cadence_root: Path | None = None
    cadence_exe: Path | None = None
    product: str | None = None
    python_executable: Path | None = None
    ibom_script: Path | None = None
    timeout_seconds: int = 300
    no_browser: bool = False
    keep_workspace: bool = False


def _validate_board(board_path: Path) -> Path:
    board_path = board_path.expanduser().resolve()
    if not board_path.is_file():
        raise Brd2IbomError(f"BRD 文件不存在：{board_path}")
    if board_path.suffix.lower() != ".brd":
        raise Brd2IbomError(f"输入文件不是 .brd：{board_path}")
    return board_path


def generate_from_brd(
    board_path: Path,
    options: RunOptions,
    log_callback: Callable[[str], None] | None = None,
) -> list[Path]:
    board_path = _validate_board(board_path)
    installation = locate_cadence(options.cadence_root, options.cadence_exe)
    export = run_skill_export(
        board_path=board_path,
        installation=installation,
        timeout_seconds=options.timeout_seconds,
        product=options.product,
        keep_workspace=options.keep_workspace,
        log_callback=log_callback,
    )
    output_dir = (options.output_dir or board_path.parent / "ibom").resolve()
    results: list[Path] = []
    try:
        for json_file in export.json_files:
            if log_callback:
                log_callback(f"正在生成 HTML：{json_file.name}")
            result = generate_html(
                json_file=json_file,
                output_dir=output_dir,
                no_browser=True,
                python_executable=options.python_executable,
                ibom_script=options.ibom_script,
            )
            results.append(result)
            if log_callback:
                log_callback(f"HTML 已生成：{result}")
    finally:
        if not options.keep_workspace:
            shutil.rmtree(export.workspace, ignore_errors=True)

    if not results:
        raise Brd2IbomError("没有找到可生成 HTML 的 JSON 文件。")
    if not options.no_browser:
        for result in results:
            webbrowser.open(result.as_uri())
    return results


def generate_from_json(json_path: Path, options: RunOptions) -> Path:
    json_path = json_path.expanduser().resolve()
    if not json_path.is_file():
        raise Brd2IbomError(f"JSON 文件不存在：{json_path}")
    output_dir = (options.output_dir or json_path.parent / "ibom").resolve()
    result = generate_html(
        json_file=json_path,
        output_dir=output_dir,
        no_browser=True,
        python_executable=options.python_executable,
        ibom_script=options.ibom_script,
    )
    if not options.no_browser:
        webbrowser.open(result.as_uri())
    return result

