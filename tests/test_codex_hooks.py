import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install" / "_codex_hooks.py"


class CodexHooksInstallerTests(unittest.TestCase):
    def run_installer(self, root: Path, platform: str = "posix") -> tuple[Path, Path]:
        config = root / "config.toml"
        hooks = root / "hooks.json"
        env = os.environ.copy()
        env["NESTWORK_CODEX_PLATFORM"] = platform
        completed = subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                str(config),
                str(hooks),
                str(REPO_ROOT),
                "test-host",
                "codex",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return config, hooks

    def test_registers_current_codex_hook_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config, hooks = self.run_installer(Path(directory))

            self.assertIn(
                f'hooksPath = "{hooks.as_posix()}"',
                config.read_text(encoding="utf-8"),
            )
            data = json.loads(hooks.read_text(encoding="utf-8"))
            self.assertNotIn("Stop", data["hooks"])
            handler = data["hooks"]["SessionEnd"][0]["hooks"][0]
            self.assertIn("launch-local-history-sync.py", handler["command"])
            self.assertEqual(handler["timeout"], 3)

    def test_reinstall_preserves_other_hooks_and_moves_nestwork_to_session_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.toml"
            hooks = root / "hooks.json"
            config.write_text('[core]\nhooksPath = "old.json"\n\n[profiles.test]\nmodel = "x"\n')
            hooks.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "Stop": [
                                {"hooks": [{"type": "command", "command": "keep-this"}]},
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "bash /old/nestwork/scripts/hooks/sync-local-history.sh host codex",
                                        }
                                    ]
                                },
                            ],
                            "SessionEnd": [
                                {"hooks": [{"type": "command", "command": "keep-end"}]}
                            ],
                            "Other": [{"hooks": [{"command": "untouched"}]}],
                        }
                    }
                ),
                encoding="utf-8",
            )

            self.run_installer(root)
            self.run_installer(root)

            updated_config = config.read_text(encoding="utf-8")
            self.assertEqual(updated_config.count("hooksPath ="), 1)
            self.assertIn("[profiles.test]", updated_config)
            updated_hooks = json.loads(hooks.read_text(encoding="utf-8"))
            stops = updated_hooks["hooks"]["Stop"]
            self.assertEqual(len(stops), 1)
            self.assertEqual(stops[0]["hooks"][0]["command"], "keep-this")
            ends = updated_hooks["hooks"]["SessionEnd"]
            self.assertEqual(len(ends), 2)
            self.assertEqual(ends[0]["hooks"][0]["command"], "keep-end")
            self.assertIn("launch-local-history-sync.py", ends[1]["hooks"][0]["command"])
            self.assertEqual(updated_hooks["hooks"]["Other"][0]["hooks"][0]["command"], "untouched")

    def test_windows_command_uses_python_launcher_instead_of_bash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, hooks = self.run_installer(Path(directory), platform="windows")
            command = json.loads(hooks.read_text(encoding="utf-8"))["hooks"][
                "SessionEnd"
            ][0]["hooks"][0]["command"]
            self.assertIn("launch-local-history-sync.py", command)
            self.assertNotIn("bash -lc", command)


if __name__ == "__main__":
    unittest.main()
