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
        env.pop("HIVEQUEEN_HOST", None)
        env.pop("HIVEQUEEN_AGENT_ID", None)

        completed = subprocess.run(
            [sys.executable, str(IDENTITY), tool, *args],
            capture_output=True,
            env=env,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout.strip().splitlines()

    def test_persists_host_and_agent_id_in_single_two_line_file(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)

            first = self.run_identity(home, "codex")
            second = self.run_identity(home, "codex")

            self.assertEqual(first, second)
            self.assertEqual((home / ".hivequeen_id").read_text(encoding="utf-8").splitlines(), first)
            self.assertFalse((home / ".hivequeen_host").exists())

    def test_migrates_split_v2_identity_files_to_single_file(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)
            (home / ".hivequeen_host").write_text("desktop-rkv5ls4\n", encoding="utf-8")
            (home / ".hivequeen_id").write_text("claude-rb46\n", encoding="utf-8")

            identity = self.run_identity(home, "claude", "--with-suffix")

            self.assertEqual(identity, ["desktop-rkv5ls4", "claude-rb46"])
            self.assertEqual(
                (home / ".hivequeen_id").read_text(encoding="utf-8").splitlines(),
                ["desktop-rkv5ls4", "claude-rb46"],
            )

    @classmethod
    def tearDownClass(cls) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    unittest.main()
