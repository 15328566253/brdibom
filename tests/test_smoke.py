from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from brd2ibom.cadence import CadenceInstallation, locate_cadence
from brd2ibom.config import load_settings, save_settings, settings_path
from brd2ibom.skill_runner import create_skill_script


class SkillScriptTests(unittest.TestCase):
    def test_script_uses_forward_slashes_and_quoted_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "bridge.scr"
            create_skill_script(
                script_path=script,
                export_json_script=root / "with space" / "exportJson.il",
                json_decode_script=root / "with space" / "jsonDecode.il",
                config_path=root / "config.json",
                revision="AUTO",
                company="iBOM Tools",
            )
            content = script.read_text(encoding="utf-8")
            self.assertIn("skill load(\"", content)
            self.assertIn("with space", content)
            self.assertIn("exportJson(?rev \"AUTO\"", content)
            self.assertTrue(all("\\" not in line.split('"')[1] for line in content.splitlines() if 'load("' in line))


class CadenceInstallationTests(unittest.TestCase):
    def test_version_is_read_from_spb_root(self) -> None:
        installation = CadenceInstallation(
            root=Path("C:/Cadence/SPB_24.1"),
            executable=Path("C:/Cadence/SPB_24.1/tools/pcb/bin/allegro.exe"),
        )
        self.assertEqual(installation.version, "24.1")

    def test_locator_finds_allegro_under_explicit_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "SPB_24.1"
            executable = root / "tools" / "pcb" / "bin" / "allegro.exe"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"test")
            installation = locate_cadence(root=root)
            self.assertEqual(installation.executable, executable.resolve())

    def test_locator_supports_allegro_tools_bin_layout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "SPB_24.1"
            executable = root / "tools" / "bin" / "allegro.exe"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"test")
            installation = locate_cadence(root=root)
            self.assertEqual(installation.executable, executable.resolve())
            self.assertEqual(installation.root, root.resolve())

    def test_locator_uses_common_cadence_scan_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Cadence" / "SPB_24.1"
            executable = root / "tools" / "bin" / "allegro.exe"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"test")
            with patch("brd2ibom.cadence._common_roots", return_value=[root]):
                installation = locate_cadence()
            self.assertEqual(installation.executable, executable.resolve())


class SettingsTests(unittest.TestCase):
    def test_settings_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"APPDATA": directory}):
            save_settings({"cadence_root": "C:/Cadence/SPB_24.1"})
            self.assertEqual(load_settings()["cadence_root"], "C:/Cadence/SPB_24.1")
            self.assertTrue(settings_path().is_file())


if __name__ == "__main__":
    unittest.main()

