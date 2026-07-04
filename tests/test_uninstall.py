import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / "scripts" / "install" / "_bootstrap.py"
HOOKS = REPO_ROOT / "scripts" / "install" / "_hooks.py"
CODEX_HOOKS = REPO_ROOT / "scripts" / "install" / "_codex_hooks.py"
UNBOOTSTRAP = REPO_ROOT / "scripts" / "uninstall" / "_unbootstrap.py"
UNHOOKS = REPO_ROOT / "scripts" / "uninstall" / "_unhooks.py"
CODEX_UNHOOKS = REPO_ROOT / "scripts" / "uninstall" / "_codex_unhooks.py"
TMP_ROOT = REPO_ROOT / ".test-tmp"


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )


class UnbootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        self.target = TMP_ROOT / "unbootstrap-test.md"

    def tearDown(self) -> None:
        self.target.unlink(missing_ok=True)

    def install_block(self, preexisting: str = "") -> None:
        if preexisting:
            self.target.write_text(preexisting, encoding="utf-8")
        completed = run(BOOTSTRAP, self.target, "/tmp/nest", "hosta", "claude-ab12")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_removes_block_and_preserves_user_content(self) -> None:
        user_content = "# My own rules\n\nKeep me around.\n"
        self.install_block(preexisting=user_content)
        installed = self.target.read_text(encoding="utf-8")
        self.assertIn("Nestwork Startup Protocol", installed)

        completed = run(UNBOOTSTRAP, self.target)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        remaining = self.target.read_text(encoding="utf-8")
        self.assertNotIn("nestwork:begin", remaining)
        self.assertNotIn("Nestwork Startup Protocol", remaining)
        self.assertIn("# My own rules", remaining)
        self.assertIn("Keep me around.", remaining)

    def test_deletes_file_that_only_held_the_block(self) -> None:
        self.install_block()
        completed = run(UNBOOTSTRAP, self.target)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(self.target.exists())

    def test_noop_without_markers(self) -> None:
        content = "# Unrelated file\n"
        self.target.write_text(content, encoding="utf-8")
        completed = run(UNBOOTSTRAP, self.target)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.target.read_text(encoding="utf-8"), content)
        self.assertIn("nothing to remove", completed.stdout)

    def test_noop_on_missing_file(self) -> None:
        completed = run(UNBOOTSTRAP, TMP_ROOT / "does-not-exist.md")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_install_uninstall_roundtrip_is_stable(self) -> None:
        user_content = "before\n"
        self.install_block(preexisting=user_content)
        run(UNBOOTSTRAP, self.target)
        first = self.target.read_text(encoding="utf-8")
        self.install_block(preexisting="")
        run(UNBOOTSTRAP, self.target)
        second = self.target.read_text(encoding="utf-8")
        self.assertEqual(first, second)


class UnhooksTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        self.settings = TMP_ROOT / "unhooks-settings.json"

    def tearDown(self) -> None:
        self.settings.unlink(missing_ok=True)

    def test_removes_all_five_events_and_keeps_user_hooks(self) -> None:
        user_hook = {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "echo user-hook"}],
        }
        self.settings.write_text(
            json.dumps({"model": "opus", "hooks": {"PreToolUse": [user_hook]}}),
            encoding="utf-8",
        )

        completed = run(HOOKS, self.settings, "/tmp/nest", "hosta", "claude-ab12")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        installed = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(len(installed["hooks"]), 5)

        completed = run(UNHOOKS, self.settings, "hosta", "claude-ab12")
        self.assertEqual(completed.returncode, 0, completed.stderr)

        cleaned = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(cleaned.get("model"), "opus")
        self.assertEqual(cleaned["hooks"], {"PreToolUse": [user_hook]})

    def test_removes_hooks_even_without_identity(self) -> None:
        self.settings.write_text("{}", encoding="utf-8")
        run(HOOKS, self.settings, "/tmp/nest", "hosta", "claude-ab12")

        completed = run(UNHOOKS, self.settings, "", "")
        self.assertEqual(completed.returncode, 0, completed.stderr)

        cleaned = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertNotIn("hooks", cleaned)

    def test_noop_on_missing_settings(self) -> None:
        completed = run(UNHOOKS, TMP_ROOT / "no-settings.json", "h", "a")
        self.assertEqual(completed.returncode, 0, completed.stderr)


class CodexUnhooksTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        self.config = TMP_ROOT / "unhooks-config.toml"
        self.hooks = TMP_ROOT / "unhooks-hooks.json"

    def tearDown(self) -> None:
        self.config.unlink(missing_ok=True)
        self.hooks.unlink(missing_ok=True)

    def test_removes_stop_hook_and_keeps_user_hooks(self) -> None:
        user_entry = {
            "hooks": [{"type": "command", "command": "echo user-stop", "timeout": 5}]
        }
        self.hooks.write_text(
            json.dumps({"hooks": {"Stop": [user_entry]}}), encoding="utf-8"
        )

        completed = run(
            CODEX_HOOKS, self.config, self.hooks, "/tmp/nestwork", "hosta", "codex"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        installed = json.loads(self.hooks.read_text(encoding="utf-8"))
        self.assertEqual(len(installed["hooks"]["Stop"]), 2)

        completed = run(CODEX_UNHOOKS, self.hooks)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        cleaned = json.loads(self.hooks.read_text(encoding="utf-8"))
        self.assertEqual(cleaned["hooks"]["Stop"], [user_entry])

    def test_noop_on_missing_hooks_file(self) -> None:
        completed = run(CODEX_UNHOOKS, TMP_ROOT / "no-hooks.json")
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
