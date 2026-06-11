import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SRC = REPO_ROOT / "scripts" / "hooks" / "nestwork.sh"
MATCHER_SRC = REPO_ROOT / "scripts" / "hooks" / "_match-file.py"

# Keep test repos hermetic: a developer's global git config (commit signing,
# hooks, templates) must not leak into the throwaway repos.
GIT_ENV = dict(os.environ)
GIT_ENV.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, env=GIT_ENV,
    )


class NestworkHookTests(unittest.TestCase):
    """End-to-end coverage for the atomic per-write hook (pre/post/stop).

    Two clones (A = the agent under test, B = another machine) share a bare
    origin, mirroring the real multi-machine topology. The hook script
    resolves the repo from its own location, so it is copied into clone A.
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.origin = base / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.origin)], check=True)
        # Point the bare HEAD at main so clones check out the pushed branch.
        subprocess.run(
            ["git", "-C", str(self.origin), "symbolic-ref", "HEAD", "refs/heads/main"],
            check=True, env=GIT_ENV,
        )

        self.a = base / "clone-a"
        self._init_clone(self.a, seed=True)
        self.b = base / "clone-b"
        subprocess.run(
            ["git", "clone", "-q", str(self.origin), str(self.b)],
            check=True, env=GIT_ENV,
        )
        self._configure(self.b)

        self.hook = self.a / "scripts" / "hooks" / "nestwork.sh"
        self.hook.parent.mkdir(parents=True)
        shutil.copy(HOOK_SRC, self.hook)
        shutil.copy(MATCHER_SRC, self.hook.parent / "_match-file.py")

        self.memory = self.a / "agents" / "h1" / "a1" / "memory.md"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _configure(self, repo) -> None:
        for args in (
            ("config", "user.name", "test"),
            ("config", "user.email", "test@example.com"),
        ):
            self.assertEqual(git(repo, *args).returncode, 0)

    def _init_clone(self, repo, seed=False) -> None:
        repo.mkdir()
        for args in (("init", "-q"), ("checkout", "-q", "-b", "main")):
            self.assertEqual(git(repo, *args).returncode, 0)
        self._configure(repo)
        if seed:
            memory = repo / "agents" / "h1" / "a1" / "memory.md"
            memory.parent.mkdir(parents=True)
            memory.write_text("# MEMORY -- h1/a1\n\nbaseline\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-q", "-m", "init")
            git(repo, "remote", "add", "origin", str(self.origin))
            self.assertEqual(
                git(repo, "push", "-q", "-u", "origin", "main").returncode, 0
            )

    def run_hook(self, phase, file_path=None):
        stdin = json.dumps({"tool_input": {"file_path": str(file_path)}}) if file_path else ""
        return subprocess.run(
            ["bash", str(self.hook), phase, "h1", "a1"],
            capture_output=True, text=True, input=stdin, env=GIT_ENV,
        )

    def remote_change(self, content):
        """Another machine updates the agent's memory and pushes."""
        mem_b = self.b / "agents" / "h1" / "a1" / "memory.md"
        mem_b.write_text(content, encoding="utf-8")
        git(self.b, "add", ".")
        self.assertEqual(git(self.b, "commit", "-q", "-m", "remote update").returncode, 0)
        self.assertEqual(git(self.b, "push", "-q", "origin", "main").returncode, 0)

    def test_post_commits_and_pushes_matching_write(self) -> None:
        self.memory.write_text("# MEMORY -- h1/a1\n\nnew fact\n", encoding="utf-8")
        result = self.run_hook("post", self.memory)

        self.assertEqual(result.returncode, 0, result.stderr)
        log = git(self.a, "log", "-1", "--format=%s")
        self.assertEqual(log.stdout.strip(), "memory: update h1/a1")
        local = git(self.a, "rev-parse", "main").stdout.strip()
        remote = git(self.origin, "rev-parse", "refs/heads/main").stdout.strip()
        self.assertEqual(local, remote)
        # The agent dir is fully committed (the copied hook scripts are
        # intentionally untracked, so scope the cleanliness check).
        self.assertEqual(
            git(self.a, "status", "--porcelain", "--", "agents").stdout.strip(), ""
        )

    def test_post_ignores_write_outside_agent_dir(self) -> None:
        head_before = git(self.a, "rev-parse", "HEAD").stdout.strip()
        other = self.a / "projects" / "x.md"
        other.parent.mkdir()
        other.write_text("not agent memory\n", encoding="utf-8")

        result = self.run_hook("post", other)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.a, "rev-parse", "HEAD").stdout.strip(), head_before)

    def test_pre_fast_forwards_to_remote_update(self) -> None:
        self.remote_change("# MEMORY -- h1/a1\n\nremote fact\n")

        result = self.run_hook("pre", self.memory)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("remote fact", self.memory.read_text(encoding="utf-8"))

    def test_pre_blocks_on_divergent_committed_conflict(self) -> None:
        self.remote_change("# MEMORY -- h1/a1\n\nremote version\n")
        self.memory.write_text("# MEMORY -- h1/a1\n\nlocal version\n", encoding="utf-8")
        git(self.a, "add", ".")
        self.assertEqual(git(self.a, "commit", "-q", "-m", "local update").returncode, 0)

        result = self.run_hook("pre", self.memory)

        # exit 2 is the documented "block the Write tool" contract.
        self.assertEqual(result.returncode, 2, result.stderr)
        # No rebase left in progress.
        self.assertFalse((self.a / ".git" / "rebase-merge").exists())
        self.assertFalse((self.a / ".git" / "rebase-apply").exists())

    def test_pre_blocks_when_autostash_is_left_behind(self) -> None:
        """Uncommitted edit conflicting with a remote commit must not be
        silently parked in the stash while the Write proceeds."""
        self.remote_change("# MEMORY -- h1/a1\n\nremote version\n")
        self.memory.write_text("# MEMORY -- h1/a1\n\nuncommitted local\n", encoding="utf-8")

        result = self.run_hook("pre", self.memory)

        self.assertEqual(result.returncode, 2, result.stderr)
        # The edit survives somewhere recoverable: either still in the working
        # tree or parked in the stash (then the hook must say so).
        in_tree = "uncommitted local" in self.memory.read_text(encoding="utf-8")
        stash = git(self.a, "stash", "list").stdout.strip()
        if not in_tree:
            self.assertNotEqual(stash, "")
            self.assertIn("stash", result.stderr)

    def test_post_retries_push_after_remote_advance(self) -> None:
        """Non-conflicting remote commit between write and push: the hook must
        soft-reset, rebase, re-commit and land both commits on origin."""
        other_b = self.b / "agents" / "h2" / "b1" / "notes.md"
        other_b.parent.mkdir(parents=True)
        other_b.write_text("other agent\n", encoding="utf-8")
        git(self.b, "add", ".")
        self.assertEqual(git(self.b, "commit", "-q", "-m", "other agent note").returncode, 0)
        self.assertEqual(git(self.b, "push", "-q", "origin", "main").returncode, 0)

        self.memory.write_text("# MEMORY -- h1/a1\n\nracing fact\n", encoding="utf-8")
        result = self.run_hook("post", self.memory)

        self.assertEqual(result.returncode, 0, result.stderr)
        local = git(self.a, "rev-parse", "main").stdout.strip()
        remote = git(self.origin, "rev-parse", "refs/heads/main").stdout.strip()
        self.assertEqual(local, remote)
        subjects = git(self.a, "log", "--format=%s", "-3").stdout
        self.assertIn("memory: update h1/a1", subjects)
        self.assertIn("other agent note", subjects)

    def test_stop_commits_dirty_agent_dir_without_matcher(self) -> None:
        self.memory.write_text("# MEMORY -- h1/a1\n\nend of turn\n", encoding="utf-8")
        result = self.run_hook("stop")

        self.assertEqual(result.returncode, 0, result.stderr)
        log = git(self.a, "log", "-1", "--format=%s")
        self.assertEqual(log.stdout.strip(), "memory: update h1/a1")
        local = git(self.a, "rev-parse", "main").stdout.strip()
        remote = git(self.origin, "rev-parse", "refs/heads/main").stdout.strip()
        self.assertEqual(local, remote)

    def test_stop_is_noop_when_clean(self) -> None:
        head_before = git(self.a, "rev-parse", "HEAD").stdout.strip()
        result = self.run_hook("stop")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.a, "rev-parse", "HEAD").stdout.strip(), head_before)


if __name__ == "__main__":
    unittest.main()
