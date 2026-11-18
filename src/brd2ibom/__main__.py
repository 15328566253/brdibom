from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .app import RunOptions, generate_from_brd, generate_from_json
from .errors import Brd2IbomError
from .gui import run_gui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brd2ibom",
        description="使用 Cadence Allegro 的 SKILL 批处理流程生成 InteractiveHtmlBom HTML。",
    )
    parser.add_argument("input", nargs="?", help="Allegro .brd 文件，或使用 --json 时的 JSON 文件")
    parser.add_argument("--json", action="store_true", help="把输入作为已生成的 iBOM JSON")
    parser.add_argument("--gui", action="store_true", help="打开文件选择界面")
    parser.add_argument("--output-dir", type=Path, help="HTML 输出目录，默认是输入文件旁边的 ibom")
    parser.add_argument("--cadence-root", type=Path, help="Cadence 安装根目录，例如 C:/Cadence/SPB_24.1")
    parser.add_argument("--cadence-exe", type=Path, help="直接指定 allegro.exe")
    parser.add_argument("--product", help="传给 Allegro 的产品名，例如 Allegro_performance")
    parser.add_argument("--python", dest="python_executable", type=Path, help="指定 Python 解释器")
    parser.add_argument("--ibom-script", type=Path, help="指定 generate_interactive_bom.py")
    parser.add_argument("--timeout", type=int, default=300, help="Allegro 导出超时时间，单位秒")
    parser.add_argument("--keep-workspace", action="store_true", help="保留 Allegro 临时工作目录和日志")
    parser.add_argument("--no-browser", action="store_true", help="生成后不自动打开浏览器")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.gui or not args.input:
        run_gui()
        return 0

    options = RunOptions(
        output_dir=args.output_dir,
        cadence_root=args.cadence_root,
        cadence_exe=args.cadence_exe,
        product=args.product,
        python_executable=args.python_executable,
        ibom_script=args.ibom_script,
        timeout_seconds=args.timeout,
        no_browser=args.no_browser,
        keep_workspace=args.keep_workspace,
    )
    try:
        if args.json:
            result = generate_from_json(Path(args.input), options)
            print(f"生成完成：{result}")
        else:
            results = generate_from_brd(Path(args.input), options)
            for result in results:
                print(f"生成完成：{result}")
        return 0
    except Brd2IbomError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

