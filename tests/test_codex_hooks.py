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
    def run_installer(self, root: Path, platform: str = "posix", nest: str = str(REPO_ROOT)) -> tuple[Path, Path]:
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
                nest,
                "test-host",
                "codex",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return config, hooks

    def test_registers_per_write_sync_and_session_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config, hooks = self.run_installer(Path(directory))

            self.assertIn(
                f'hooksPath = "{hooks.as_posix()}"',
                config.read_text(encoding="utf-8"),
            )
            data = json.loads(hooks.read_text(encoding="utf-8"))["hooks"]
            # Per-write sync: same nestwork.sh phases as Claude Code / Kimi Code,
            # scoped to Codex's file-edit tool (apply_patch, Edit/Write aliases).
            for event, phase in (("PreToolUse", "pre"), ("PostToolUse", "post")):
                with self.subTest(event=event):
                    (entry,) = data[event]
                    self.assertEqual(entry["matcher"], "^(apply_patch|Edit|Write)$")
                    command = entry["hooks"][0]["command"]
                    self.assertIn("scripts/hooks/nestwork.sh", command)
                    self.assertTrue(command.endswith(f" {phase} test-host codex"), command)
            (stop,) = data["Stop"]
            self.assertNotIn("matcher", stop)
            self.assertTrue(stop["hooks"][0]["command"].endswith(" stop test-host codex"))
            # Local-history snapshot stays on SessionEnd, within Codex's 3 s cap.
            handler = data["SessionEnd"][0]["hooks"][0]
            self.assertIn("launch-local-history-sync.py", handler["command"])
            self.assertEqual(handler["timeout"], 3)

    def test_reinstall_is_idempotent_and_preserves_user_hooks(self) -> None:
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
            # The user's hook survives, the legacy sync-local-history entry is
            # gone, and two installs leave exactly one nestwork Stop entry.
            self.assertEqual([s["hooks"][0]["command"] for s in stops][0], "keep-this")
            self.assertEqual(len(stops), 2)
            self.assertIn("nestwork.sh stop", stops[1]["hooks"][0]["command"])
            self.assertFalse(any("sync-local-history.sh" in s["hooks"][0]["command"] for s in stops))
            for event in ("PreToolUse", "PostToolUse"):
                self.assertEqual(len(updated_hooks["hooks"][event]), 1, event)
            ends = updated_hooks["hooks"]["SessionEnd"]
            self.assertEqual(len(ends), 2)
            self.assertEqual(ends[0]["hooks"][0]["command"], "keep-end")
            self.assertIn("launch-local-history-sync.py", ends[1]["hooks"][0]["command"])
            self.assertEqual(updated_hooks["hooks"]["Other"][0]["hooks"][0]["command"], "untouched")

    def test_reinstall_from_a_path_without_nestwork_in_it(self) -> None:
        # Regression: ownership used to require the substring "nestwork" in the
        # hook command, so a nest at e.g. /opt/my-memory stacked a new copy of
        # every hook on each re-install.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for _ in range(2):
                _, hooks = self.run_installer(root, nest="/opt/my-memory")
            data = json.loads(hooks.read_text(encoding="utf-8"))["hooks"]
            for event in ("PreToolUse", "PostToolUse", "Stop", "SessionEnd"):
                self.assertEqual(len(data[event]), 1, event)

    def test_ownership_ignores_unrelated_hooks(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("codex_hooks", INSTALLER)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        self.assertTrue(mod.is_nestwork_hook("bash /opt/my-memory/scripts/hooks/nestwork.sh post h a"))
        self.assertTrue(mod.is_nestwork_hook(r"py C:\mem\scripts\hooks\launch-local-history-sync.py C:/mem h a"))
        self.assertFalse(mod.is_nestwork_hook("echo nestwork is great"))
        self.assertFalse(mod.is_nestwork_hook("bash ~/tools/nestwork-backup.sh"))

    def test_windows_command_uses_python_launcher_instead_of_bash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, hooks = self.run_installer(Path(directory), platform="windows")
            command = json.loads(hooks.read_text(encoding="utf-8"))["hooks"][
                "SessionEnd"
            ][0]["hooks"][0]["command"]
            self.assertIn("launch-local-history-sync.py", command)
            self.assertNotIn("bash -lc", command)

    def test_windows_sync_hooks_run_through_bash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, hooks = self.run_installer(Path(directory), platform="windows")
            data = json.loads(hooks.read_text(encoding="utf-8"))["hooks"]
            command = data["PreToolUse"][0]["hooks"][0]["command"]
            self.assertTrue(command.startswith("bash "), command)
            self.assertIn("scripts/hooks/nestwork.sh pre test-host codex", command)


if __name__ == "__main__":
    unittest.main()
