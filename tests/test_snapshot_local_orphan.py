import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_SRC = REPO_ROOT / "scripts" / "hooks" / "snapshot-local-orphan.sh"
BRANCH = "agent-history-h1-a1"

# Keep test repos hermetic: a developer's global git config (commit signing,
# hooks, templates) must not leak into the throwaway repos.
GIT_ENV = dict(os.environ)
GIT_ENV.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, env=GIT_ENV,
    )


class SnapshotLocalOrphanTests(unittest.TestCase):
    """End-to-end coverage for the v2.4 orphan-branch rolling snapshot.

    The script resolves the repo from its own location, so it is copied into
    a throwaway repo (with a bare origin) before being exercised.
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
        (self.repo / ".gitignore").write_text("agents/*/*/local/\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-q", "-m", "init")
        git(self.repo, "remote", "add", "origin", str(self.origin))
        self.assertEqual(git(self.repo, "push", "-q", "-u", "origin", "main").returncode, 0)

        self.script = self.repo / "scripts" / "hooks" / "snapshot-local-orphan.sh"
        self.script.parent.mkdir(parents=True)
        shutil.copy(SNAPSHOT_SRC, self.script)

        self.local = self.repo / "agents" / "h1" / "a1" / "local"
        self.local.mkdir(parents=True)
        (self.local / "history.jsonl").write_text('{"n":1}\n', encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def snapshot(self):
        result = subprocess.run(
            ["bash", str(self.script), "h1", "a1"],
            capture_output=True, text=True, env=GIT_ENV,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_snapshot_creates_single_parentless_commit_and_pushes(self) -> None:
        main_before = git(self.repo, "rev-parse", "main").stdout.strip()
        self.snapshot()

        head = git(self.repo, "rev-parse", f"refs/heads/{BRANCH}")
        self.assertEqual(head.returncode, 0, head.stderr)
        commit = head.stdout.strip()

        # Orphan: exactly one commit, no parent.
        count = git(self.repo, "rev-list", "--count", BRANCH).stdout.strip()
        self.assertEqual(count, "1")
        raw = git(self.repo, "cat-file", "-p", commit).stdout
        self.assertNotIn("parent ", raw)

        # Tree mirrors the original path layout with the local/ content.
        tree = git(self.repo, "ls-tree", "-r", "--name-only", BRANCH).stdout
        self.assertIn("agents/h1/a1/local/history.jsonl", tree)
        blob = git(self.repo, "show", f"{BRANCH}:agents/h1/a1/local/history.jsonl").stdout
        self.assertEqual(blob, '{"n":1}\n')

        # Force-pushed to origin; main untouched.
        remote = git(self.origin, "rev-parse", f"refs/heads/{BRANCH}").stdout.strip()
        self.assertEqual(remote, commit)
        self.assertEqual(git(self.repo, "rev-parse", "main").stdout.strip(), main_before)

    def test_unchanged_tree_is_idempotent(self) -> None:
        self.snapshot()
        first = git(self.repo, "rev-parse", BRANCH).stdout.strip()
        self.snapshot()
        second = git(self.repo, "rev-parse", BRANCH).stdout.strip()
        self.assertEqual(first, second)

    def test_changed_tree_replaces_snapshot_keeping_one_commit(self) -> None:
        self.snapshot()
        first = git(self.repo, "rev-parse", BRANCH).stdout.strip()

        (self.local / "history.jsonl").write_text('{"n":1}\n{"n":2}\n', encoding="utf-8")
        self.snapshot()

        second = git(self.repo, "rev-parse", BRANCH).stdout.strip()
        self.assertNotEqual(first, second)
        self.assertEqual(git(self.repo, "rev-list", "--count", BRANCH).stdout.strip(), "1")
        remote = git(self.origin, "rev-parse", f"refs/heads/{BRANCH}").stdout.strip()
        self.assertEqual(remote, second)

    def test_missing_local_dir_is_a_clean_noop(self) -> None:
        shutil.rmtree(self.local)
        self.snapshot()
        head = git(self.repo, "rev-parse", "--verify", f"refs/heads/{BRANCH}")
        self.assertNotEqual(head.returncode, 0)


if __name__ == "__main__":
    unittest.main()
