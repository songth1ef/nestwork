import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DISTILL = REPO_ROOT / "scripts" / "maintenance" / "distill.py"
TMP_ROOT = REPO_ROOT / ".test-tmp"


class DistillTests(unittest.TestCase):
    def create_repo_fixture(self, root: Path) -> None:
        (root / "shared").mkdir(parents=True, exist_ok=True)
        (root / "agents" / "host-a" / "codex").mkdir(parents=True, exist_ok=True)
        (root / "agents" / "host-b" / "claude-ab12").mkdir(parents=True, exist_ok=True)
        (root / "agents" / "host-c" / "gemini").mkdir(parents=True, exist_ok=True)

        (root / "shared" / "memory.md").write_text(
            "# SHARED MEMORY\n\n> Last compiled: old\n",
            encoding="utf-8",
        )
        (root / "agents" / "host-a" / "codex" / "memory.md").write_text(
            "# MEMORY -- host-a/codex\n\n- prefers Chinese\n",
            encoding="utf-8",
        )
        (root / "agents" / "host-b" / "claude-ab12" / "memory.md").write_text(
            "# MEMORY -- host-b/claude-ab12\n\n- uses Vue 3\n",
            encoding="utf-8",
        )
        (root / "agents" / "host-c" / "gemini" / "memory.md").write_text(
            "# MEMORY -- host-c/gemini\n\n_No memory yet._\n",
            encoding="utf-8",
        )

    def create_fake_codex(self, bin_dir: Path, response: str) -> None:
        bin_dir.mkdir(parents=True, exist_ok=True)
        fake_codex = bin_dir / "codex"
        fake_codex.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import pathlib",
                    "import sys",
                    "",
                    "args = sys.argv[1:]",
                    "output = pathlib.Path(args[args.index('--output-last-message') + 1])",
                    f"output.write_text({response!r}, encoding='utf-8')",
                    "sys.stdin.read()",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IEXEC)

    def run_distill(self, root: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(DISTILL), "--nestwork-path", str(root), *args],
            capture_output=True,
            text=True,
            env=env,
        )

    def test_prompt_mode_reads_all_non_empty_agent_memories(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            root = Path(tmp)
            self.create_repo_fixture(root)

            completed = self.run_distill(root)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("## Current shared/memory.md:", completed.stdout)
            self.assertIn("Private memory from agent: host-a/codex", completed.stdout)
            self.assertIn("Private memory from agent: host-b/claude-ab12", completed.stdout)
            self.assertNotIn("Private memory from agent: host-c/gemini", completed.stdout)

    def test_run_codex_dry_run_prints_candidate_without_writing(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            root = Path(tmp)
            self.create_repo_fixture(root)

            bin_dir = root / "bin"
            self.create_fake_codex(
                bin_dir,
                "```markdown\n# SHARED MEMORY\n\n- merged fact\n```\n",
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            completed = self.run_distill(root, "--run-codex", "--dry-run", env=env)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, "# SHARED MEMORY\n\n- merged fact\n")
            self.assertIn("Last compiled: old", (root / "shared" / "memory.md").read_text(encoding="utf-8"))

    def test_run_codex_no_commit_updates_shared_memory_file(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            root = Path(tmp)
            self.create_repo_fixture(root)

            bin_dir = root / "bin"
            self.create_fake_codex(
                bin_dir,
                "```markdown\n# SHARED MEMORY\n\n- merged and written\n```\n",
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            completed = self.run_distill(root, "--run-codex", "--no-commit", env=env)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Updated", completed.stdout)
            self.assertEqual(
                (root / "shared" / "memory.md").read_text(encoding="utf-8"),
                "# SHARED MEMORY\n\n- merged and written\n",
            )

    @classmethod
    def tearDownClass(cls) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    unittest.main()
