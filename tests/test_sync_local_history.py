import importlib.util
import json
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "hooks" / "sync-local-history.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_local_history", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SyncLocalHistoryTests(unittest.TestCase):
    def run_sync(self, build_fixture, agent_id, host="desktop", settings=None):
        """Build a fixture under a temp root, run main(), return the root.

        build_fixture(home, nestwork) populates the fake $HOME and nest.
        Caller must clean up via the returned context manager protocol —
        here we just run inside the temp root and return collected output.
        """
        module = load_sync_module()
        root = REPO_ROOT / ".tmp_sync_local_history_test"
        if root.exists():
            shutil.rmtree(root)
        root.mkdir()
        home = root / "home"
        nestwork = root / "nestwork"
        (nestwork / "agents" / host / agent_id).mkdir(parents=True)
        if settings is None:
            settings = {"sync_local_history": True}
        (nestwork / "agents" / host / "settings.json").write_text(
            json.dumps(settings), encoding="utf-8"
        )
        (home / ".claude").mkdir(parents=True)
        (home / ".codex").mkdir(parents=True)
        build_fixture(home, nestwork)

        argv = ["sync-local-history.py", str(nestwork), host, agent_id]
        with patch.object(module.Path, "home", return_value=home), patch.object(sys, "argv", argv):
            rc = module.main()
        return rc, nestwork / "agents" / host / agent_id / "local"

    def test_redaction_covers_tokens_in_any_field_and_drops_pastes(self) -> None:
        entry = {
            "display": "set OPENAI key",
            "pastedContents": "sk-" + "a" * 40,
            "context": {
                "apiKey": "sk-" + "b" * 40,
                "auth": "Bearer " + "c" * 30,
                "github": "ghp_" + "D" * 36,
            },
            "extras": [
                "AKIA" + "E" * 16,
                "postgres://user:hunter2pass@db.internal/prod",
                "password = supersecret99",
            ],
            "count": 3,
        }

        def fixture(home, nestwork):
            (home / ".claude" / "history.jsonl").write_text(
                json.dumps(entry) + "\n", encoding="utf-8"
            )

        try:
            rc, local = self.run_sync(fixture, "claude-x1")
            self.assertEqual(rc, 0)
            synced = (local / "history.jsonl").read_text(encoding="utf-8")
            # Tokens must be gone no matter which field they were in.
            self.assertNotIn("sk-" + "a" * 40, synced)
            self.assertNotIn("sk-" + "b" * 40, synced)
            self.assertNotIn("c" * 30, synced)
            self.assertNotIn("ghp_" + "D" * 36, synced)
            self.assertNotIn("AKIA" + "E" * 16, synced)
            self.assertNotIn("hunter2pass", synced)
            self.assertNotIn("supersecret99", synced)
            self.assertIn("<REDACTED>", synced)
            # pastedContents dropped entirely; non-string values untouched.
            self.assertNotIn("pastedContents", synced)
            self.assertIn('"count": 3', synced)
        finally:
            shutil.rmtree(REPO_ROOT / ".tmp_sync_local_history_test", ignore_errors=True)

    def test_claude_agent_mirrors_plans(self) -> None:
        def fixture(home, nestwork):
            (home / ".claude" / "history.jsonl").write_text(
                json.dumps({"display": "hello"}) + "\n", encoding="utf-8"
            )
            plans = home / ".claude" / "plans"
            plans.mkdir()
            (plans / "plan-1.md").write_text("step one\n", encoding="utf-8")

        try:
            rc, local = self.run_sync(fixture, "claude-x1")
            self.assertEqual(rc, 0)
            self.assertEqual(
                (local / "plans" / "plan-1.md").read_text(encoding="utf-8"),
                "step one\n",
            )
        finally:
            shutil.rmtree(REPO_ROOT / ".tmp_sync_local_history_test", ignore_errors=True)

    def test_disabled_gate_is_a_noop(self) -> None:
        def fixture(home, nestwork):
            (home / ".claude" / "history.jsonl").write_text(
                json.dumps({"display": "hello"}) + "\n", encoding="utf-8"
            )

        try:
            rc, local = self.run_sync(fixture, "claude-x1", settings={})
            self.assertEqual(rc, 0)
            self.assertFalse(local.exists())
        finally:
            shutil.rmtree(REPO_ROOT / ".tmp_sync_local_history_test", ignore_errors=True)

    def test_codex_agent_syncs_codex_history(self) -> None:
        module = load_sync_module()

        root = REPO_ROOT / ".tmp_sync_local_history_test"
        if root.exists():
            shutil.rmtree(root)
        try:
            root.mkdir()
            home = root / "home"
            nestwork = root / "nestwork"
            (nestwork / "agents" / "desktop" / "codex").mkdir(parents=True)
            (nestwork / "agents" / "desktop").mkdir(parents=True, exist_ok=True)
            (nestwork / "agents" / "desktop" / "settings.json").write_text(
                json.dumps({"sync_local_history": True}),
                encoding="utf-8",
            )

            (home / ".claude").mkdir(parents=True)
            (home / ".codex").mkdir(parents=True)
            (home / ".claude" / "history.jsonl").write_text(
                json.dumps({"display": "claude history", "project": str(home)}) + "\n",
                encoding="utf-8",
            )
            (home / ".codex" / "history.jsonl").write_text(
                json.dumps({"display": "codex history", "project": str(home)}) + "\n",
                encoding="utf-8",
            )

            argv = ["sync-local-history.py", str(nestwork), "desktop", "codex"]
            with patch.object(module.Path, "home", return_value=home), patch.object(sys, "argv", argv):
                self.assertEqual(0, module.main())

            synced = (
                nestwork / "agents" / "desktop" / "codex" / "local" / "history.jsonl"
            ).read_text(encoding="utf-8")
            self.assertIn("codex history", synced)
            self.assertNotIn("claude history", synced)
            self.assertIn("<HOME>", synced)
        finally:
            if root.exists():
                shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
