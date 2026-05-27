import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
IDENTITY = REPO_ROOT / "scripts" / "install" / "_identity.py"
TMP_ROOT = REPO_ROOT / ".test-tmp"


class IdentityTests(unittest.TestCase):
    def run_identity(self, home: Path, tool: str, *args: str) -> list[str]:
        env = os.environ.copy()
        env["USERPROFILE"] = str(home)
        env["HOME"] = str(home)
        env.pop("NESTWORK_HOST", None)
        env.pop("NESTWORK_AGENT_ID", None)

        completed = subprocess.run(
            [sys.executable, str(IDENTITY), tool, *args],
            capture_output=True,
            env=env,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout.strip().splitlines()

    def test_persists_host_and_agent_id_per_tool(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)

            first = self.run_identity(home, "codex")
            second = self.run_identity(home, "codex")

            self.assertEqual(first, second)
            self.assertEqual((home / ".nestwork_host").read_text(encoding="utf-8").strip(), first[0])
            self.assertEqual((home / ".nestwork_id_codex").read_text(encoding="utf-8").strip(), first[1])

    def test_migrates_existing_claude_identity_to_tool_specific_file(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)
            (home / ".nestwork_host").write_text("desktop-rkv5ls4\n", encoding="utf-8")
            (home / ".nestwork_id").write_text("claude-rb46\n", encoding="utf-8")

            identity = self.run_identity(home, "claude", "--with-suffix")

            self.assertEqual(identity, ["desktop-rkv5ls4", "claude-rb46"])
            self.assertEqual(
                (home / ".nestwork_id_claude").read_text(encoding="utf-8").strip(),
                "claude-rb46",
            )

    def test_codex_install_does_not_replace_existing_claude_identity(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)
            (home / ".nestwork_host").write_text("desktop-rkv5ls4\n", encoding="utf-8")
            (home / ".nestwork_id").write_text("claude-i5bc\n", encoding="utf-8")

            codex = self.run_identity(home, "codex")
            claude = self.run_identity(home, "claude", "--with-suffix")

            self.assertEqual(codex, ["desktop-rkv5ls4", "codex"])
            self.assertEqual(claude, ["desktop-rkv5ls4", "claude-i5bc"])
            self.assertEqual((home / ".nestwork_id").read_text(encoding="utf-8").strip(), "claude-i5bc")
            self.assertEqual((home / ".nestwork_id_codex").read_text(encoding="utf-8").strip(), "codex")
            self.assertEqual((home / ".nestwork_id_claude").read_text(encoding="utf-8").strip(), "claude-i5bc")

    @classmethod
    def tearDownClass(cls) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    unittest.main()
