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
    def test_codex_agent_syncs_codex_history(self) -> None:
        module = load_sync_module()

        root = REPO_ROOT / ".tmp_sync_local_history_test"
        if root.exists():
            shutil.rmtree(root)
        try:
            root.mkdir()
            home = root / "home"
            hivequeen = root / "hivequeen"
            (hivequeen / "agents" / "desktop" / "codex").mkdir(parents=True)
            (hivequeen / "agents" / "desktop").mkdir(parents=True, exist_ok=True)
            (hivequeen / "agents" / "desktop" / "settings.json").write_text(
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

            argv = ["sync-local-history.py", str(hivequeen), "desktop", "codex"]
            with patch.object(module.Path, "home", return_value=home), patch.object(sys, "argv", argv):
                self.assertEqual(0, module.main())

            synced = (
                hivequeen / "agents" / "desktop" / "codex" / "local" / "history.jsonl"
            ).read_text(encoding="utf-8")
            self.assertIn("codex history", synced)
            self.assertNotIn("claude history", synced)
            self.assertIn("<HOME>", synced)
        finally:
            if root.exists():
                shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
