from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Return the repository root while running from a checkout."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def default_ibom_script() -> Path:
    return project_root() / "vendor" / "InteractiveHtmlBom" / "InteractiveHtmlBom" / "generate_interactive_bom.py"


def default_export_json_script() -> Path:
    return project_root() / "vendor" / "exportJson" / "exportJson.il"


def default_json_decode_script() -> Path:
    return project_root() / "vendor" / "exportJson" / "jsonDecode.il"


def default_export_config() -> Path:
    return project_root() / "config" / "ibomExportDefaultConfig.json"


def default_skill_bridge() -> Path:
    return project_root() / "skill" / "ibom_bridge.il"

