import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPILE_SRC = REPO_ROOT / "scripts" / "maintenance" / "compile.sh"

# Keep test repos hermetic: a developer's global git config (commit signing,
# hooks, templates) must not leak into the throwaway repos.
GIT_ENV = dict(os.environ)
GIT_ENV.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})

MEMORY_HEADER = """\
# MEMORY -- {label}

> Private memory for this agent instance.
> Only {label} writes here.

---

"""


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, env=GIT_ENV,
    )


class CompileTests(unittest.TestCase):
    """compile.sh must pass agent memory through verbatim.

    Regression coverage for the printf %b bug that mangled backslash
    sequences (e.g. Windows paths, regexes) in compiled shared memory.
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.origin = base / "origin.git"
        self.repo = base / "nest"
        subprocess.run(["git", "init", "--bare", "-q", str(self.origin)], check=True)
        self.repo.mkdir()
        for args in (
            ("init", "-q"),
            ("checkout", "-q", "-b", "main"),
            ("config", "user.name", "test"),
            ("config", "user.email", "test@example.com"),
        ):
            self.assertEqual(git(self.repo, *args).returncode, 0)
        (self.repo / "shared").mkdir()
        (self.repo / "shared" / "memory.md").write_text("# SHARED MEMORY\n", encoding="utf-8")
        git(self.repo, "add", "shared")
        git(self.repo, "commit", "-q", "-m", "init")
        git(self.repo, "remote", "add", "origin", str(self.origin))
        self.assertEqual(git(self.repo, "push", "-q", "-u", "origin", "main").returncode, 0)

        self.script = self.repo / "scripts" / "maintenance" / "compile.sh"
        self.script.parent.mkdir(parents=True)
        shutil.copy(COMPILE_SRC, self.script)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_memory(self, label, body):
        path = self.repo / "agents" / label / "memory.md"
        path.parent.mkdir(parents=True)
        path.write_text(MEMORY_HEADER.format(label=label) + body, encoding="utf-8")

    def test_compile_preserves_content_verbatim(self) -> None:
        body = (
            "Windows path: C:\\temp\\new\\folder\n"
            "Regex token: \\d+\\n matches digits then a literal backslash-n\n"
            "Percent literal: 100%s done\n"
        )
        self.write_memory("hostx/agenty", body)
        self.write_memory("hostx/agentz", "_No memory yet._\n")

        result = subprocess.run(
            ["bash", str(self.script)],
            capture_output=True, text=True, env=GIT_ENV,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        shared = (self.repo / "shared" / "memory.md").read_text(encoding="utf-8")
        self.assertIn("## hostx/agenty", shared)
        # Backslash sequences and percent signs must survive untouched.
        self.assertIn("C:\\temp\\new\\folder", shared)
        self.assertIn("\\d+\\n matches digits", shared)
        self.assertIn("100%s done", shared)
        # Installer header noise must not leak into the compilation.
        self.assertNotIn("Only hostx/agenty writes here", shared)
        self.assertNotIn("_No memory yet._", shared)
        # Empty memories get the explicit placeholder.
        self.assertIn("## hostx/agentz", shared)
        self.assertIn("_No memory recorded yet._", shared)

        # Committed with the documented message and pushed.
        log = git(self.repo, "log", "-1", "--format=%s")
        self.assertTrue(log.stdout.startswith("memory: compile shared"), log.stdout)
        local_head = git(self.repo, "rev-parse", "main").stdout.strip()
        remote_head = git(self.origin, "rev-parse", "refs/heads/main").stdout.strip()
        self.assertEqual(local_head, remote_head)


if __name__ == "__main__":
    unittest.main()
