from __future__ import annotations

import os
import importlib
import subprocess
import sys
from pathlib import Path

from .errors import Brd2IbomError
from .paths import default_ibom_script


def _find_output(directory: Path, before: set[Path]) -> Path:
    candidates = sorted(directory.glob("*.html"), key=lambda path: path.stat().st_mtime, reverse=True)
    for candidate in candidates:
        if candidate not in before or candidate.stat().st_size > 0:
            return candidate
    raise Brd2IbomError(f"InteractiveHtmlBom 没有生成 HTML：{directory}")


def generate_html(
    json_file: Path,
    output_dir: Path,
    no_browser: bool = False,
    python_executable: str | Path | None = None,
    ibom_script: str | Path | None = None,
) -> Path:
    """Generate one self-contained HTML file from a generic iBOM JSON file."""
    json_file = json_file.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    script = Path(ibom_script).resolve() if ibom_script else default_ibom_script()
    if not script.is_file():
        raise Brd2IbomError(f"InteractiveHtmlBom 生成脚本不存在：{script}")

    before = set(output_dir.glob("*.html"))
    args = [
        str(script),
        str(json_file),
        "--dest-dir",
        str(output_dir),
        "--name-format",
        f"{json_file.stem}_ibom",
        "--show-fabrication",
        "--hide-silkscreen",
        "--layer-view",
        "FB",
        "--dnp-field",
        "DNP",
        "--no-browser",
    ]
    env = os.environ.copy()
    env["INTERACTIVE_HTML_BOM_NO_DISPLAY"] = "1"
    if python_executable:
        command = [str(python_executable), *args]
        completed = subprocess.run(
            command,
            cwd=script.parent.parent,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stdout + "\n" + completed.stderr).strip()
            raise Brd2IbomError(f"InteractiveHtmlBom 生成失败。\n{detail[-4000:]}")
    else:
        package_root = script.parent.parent
        if str(package_root) not in sys.path:
            sys.path.insert(0, str(package_root))
        previous_argv = sys.argv
        previous_display = os.environ.get("INTERACTIVE_HTML_BOM_NO_DISPLAY")
        sys.argv = args
        os.environ["INTERACTIVE_HTML_BOM_NO_DISPLAY"] = "1"
        try:
            module = importlib.import_module("InteractiveHtmlBom.generate_interactive_bom")
            result = module.main()
            if result not in (None, 0):
                raise Brd2IbomError(f"InteractiveHtmlBom 生成失败，退出码为 {result}。")
        except SystemExit as exc:
            if exc.code not in (None, 0):
                raise Brd2IbomError(f"InteractiveHtmlBom 生成失败，退出码为 {exc.code}。") from exc
        except Exception as exc:
            raise Brd2IbomError(f"InteractiveHtmlBom 生成失败：{exc}") from exc
        finally:
            sys.argv = previous_argv
            if previous_display is None:
                os.environ.pop("INTERACTIVE_HTML_BOM_NO_DISPLAY", None)
            else:
                os.environ["INTERACTIVE_HTML_BOM_NO_DISPLAY"] = previous_display
    return _find_output(output_dir, before)

