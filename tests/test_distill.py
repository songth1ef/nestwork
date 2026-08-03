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
        args_log = bin_dir / "codex-args.txt"
        fake_codex.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import pathlib",
                    "import sys",
                    "",
                    "args = sys.argv[1:]",
                    f"pathlib.Path({str(args_log)!r}).write_text('\\n'.join(args), encoding='utf-8')",
                    "output = pathlib.Path(args[args.index('--output-last-message') + 1])",
                    f"output.write_text({response!r}, encoding='utf-8')",
                    "sys.stdin.read()",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IEXEC)

    def create_fake_claude(self, bin_dir: Path, response: str) -> None:
        """A `claude` that echoes a canned answer on stdout and logs its argv.

        `claude -p` returns the answer on stdout rather than through an output
        file, so the shim differs from the codex one in more than its name.
        """
        bin_dir.mkdir(parents=True, exist_ok=True)
        fake_claude = bin_dir / "claude"
        args_log = bin_dir / "claude-args.txt"
        fake_claude.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import pathlib",
                    "import sys",
                    "",
                    "args = sys.argv[1:]",
                    f"pathlib.Path({str(args_log)!r}).write_text('\\n'.join(args), encoding='utf-8')",
                    "sys.stdin.read()",
                    f"sys.stdout.write({response!r})",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        fake_claude.chmod(fake_claude.stat().st_mode | stat.S_IEXEC)

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

    @unittest.skipIf(
        sys.platform == "win32",
        "PATH shims without an executable extension cannot shadow a real "
        "binary on win32, so the fixture would invoke the machine's own CLI",
    )
    def test_run_claude_dry_run_prints_candidate_and_disables_tools(self) -> None:
        """The claude runner must stay a pure text transform.

        Without `--tools ''` / `--setting-sources ''` the distiller loads the
        nest's own CLAUDE.md bootstrap and answers with a session-start summary
        instead of a shared/memory.md candidate -- the failure looks like a bad
        LLM response, not a missing flag, so it is asserted here.
        """
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            root = Path(tmp)
            self.create_repo_fixture(root)

            bin_dir = root / "bin"
            self.create_fake_claude(
                bin_dir,
                "```markdown\n# SHARED MEMORY\n\n- merged fact\n```\n",
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            completed = self.run_distill(root, "--run-claude", "--dry-run", env=env)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, "# SHARED MEMORY\n\n- merged fact\n")
            self.assertIn("Last compiled: old", (root / "shared" / "memory.md").read_text(encoding="utf-8"))

            argv = (bin_dir / "claude-args.txt").read_text(encoding="utf-8").splitlines()
            self.assertIn("-p", argv)
            self.assertIn("--tools", argv)
            self.assertIn("--setting-sources", argv)

    def test_runners_are_mutually_exclusive(self) -> None:
        """Asking for both runners must fail loudly instead of silently picking one."""
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            root = Path(tmp)
            self.create_repo_fixture(root)

            completed = self.run_distill(root, "--run-claude", "--run-codex")

            self.assertEqual(completed.returncode, 2)
            self.assertIn("mutually exclusive", completed.stderr)

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
            self.assertIn("--ignore-rules", (bin_dir / "codex-args.txt").read_text(encoding="utf-8"))
            self.assertEqual(
                (root / "shared" / "memory.md").read_text(encoding="utf-8"),
                "# SHARED MEMORY\n\n- merged and written\n",
            )

    def create_failing_codex(self, bin_dir: Path, stderr_text: str, exit_code: int) -> None:
        bin_dir.mkdir(parents=True, exist_ok=True)
        fake_codex = bin_dir / "codex"
        fake_codex.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import sys",
                    "sys.stdin.read()",
                    f"print({stderr_text!r}, file=sys.stderr)",
                    f"sys.exit({exit_code})",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IEXEC)

    def test_run_codex_failure_surfaces_codex_stderr(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            root = Path(tmp)
            self.create_repo_fixture(root)

            bin_dir = root / "bin"
            self.create_failing_codex(bin_dir, "error: unknown flag --ignore-rules", 2)

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            completed = self.run_distill(root, "--run-codex", env=env)

            self.assertEqual(completed.returncode, 1)
            self.assertIn("codex exec failed (exit 2)", completed.stderr)
            # The actionable part: codex's own stderr must reach the user.
            self.assertIn("unknown flag --ignore-rules", completed.stderr)
            # shared/memory.md untouched on failure.
            self.assertIn(
                "Last compiled: old",
                (root / "shared" / "memory.md").read_text(encoding="utf-8"),
            )

    @classmethod
    def tearDownClass(cls) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    unittest.main()
