import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_SRC = REPO_ROOT / "scripts" / "maintenance" / "sync-claude-md.sh"
UPDATE_SRC = REPO_ROOT / "scripts" / "maintenance" / "update.sh"

GIT_ENV = dict(os.environ)
GIT_ENV.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, env=GIT_ENV,
    )


def init_repo(path):
    path.mkdir(parents=True)
    for args in (
        ("init", "-q"),
        ("checkout", "-q", "-b", "main"),
        ("config", "user.name", "test"),
        ("config", "user.email", "test@example.com"),
    ):
        assert git(path, *args).returncode == 0
    return path


class SyncClaudeMdTests(unittest.TestCase):
    def test_regenerates_claude_md_as_header_plus_agents_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repo(Path(tmp) / "nest")
            script = repo / "scripts" / "maintenance" / "sync-claude-md.sh"
            script.parent.mkdir(parents=True)
            shutil.copy(SYNC_SRC, script)
            agents = "# NESTWORK BOOTSTRAP\n\nprotocol body\n"
            (repo / "AGENTS.md").write_text(agents, encoding="utf-8")
            (repo / "CLAUDE.md").write_text("stale mirror\n", encoding="utf-8")

            result = subprocess.run(
                ["bash", str(script)], capture_output=True, text=True, env=GIT_ENV
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")
            header, sep, body = claude.partition("-->\n\n")
            self.assertTrue(sep)
            self.assertIn("verbatim mirror of AGENTS.md", header)
            self.assertEqual(body, agents)


class UpdateShTests(unittest.TestCase):
    """update.sh pulls only the protocol layer and skips paths missing
    upstream instead of aborting mid-update."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)

        # Upstream ships a newer AGENTS.md (and nothing else from the list).
        self.upstream = init_repo(base / "upstream")
        (self.upstream / "AGENTS.md").write_text("upstream protocol v-next\n", encoding="utf-8")
        git(self.upstream, "add", ".")
        git(self.upstream, "commit", "-q", "-m", "upstream release")

        # Private nest: older protocol + private data that must survive.
        self.nest = init_repo(base / "nest")
        script = self.nest / "scripts" / "maintenance" / "update.sh"
        script.parent.mkdir(parents=True)
        shutil.copy(UPDATE_SRC, script)
        self.script = script
        (self.nest / "AGENTS.md").write_text("old protocol\n", encoding="utf-8")
        (self.nest / "queen").mkdir()
        (self.nest / "queen" / "agent-rules.md").write_text("my rules\n", encoding="utf-8")
        git(self.nest, "add", ".")
        git(self.nest, "commit", "-q", "-m", "private init")
        git(self.nest, "remote", "add", "upstream", str(self.upstream))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_update(self, answer="y\n"):
        return subprocess.run(
            ["bash", str(self.script)],
            capture_output=True, text=True, input=answer, env=GIT_ENV,
        )

    def test_applies_protocol_file_skips_missing_and_keeps_private_data(self) -> None:
        result = self.run_update()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("incoming protocol changes", result.stdout)
        # The one file upstream ships is applied...
        self.assertEqual(
            (self.nest / "AGENTS.md").read_text(encoding="utf-8"),
            "upstream protocol v-next\n",
        )
        # ...paths absent upstream are skipped with a note, not a hard abort...
        self.assertIn("[skip] CLAUDE.md (not present upstream)", result.stdout)
        # ...and private layers are untouched.
        self.assertEqual(
            (self.nest / "queen" / "agent-rules.md").read_text(encoding="utf-8"),
            "my rules\n",
        )
        log = git(self.nest, "log", "-1", "--format=%s")
        self.assertEqual(log.stdout.strip(), "chore: update nestwork protocol from upstream")

    def test_declining_makes_no_changes(self) -> None:
        head_before = git(self.nest, "rev-parse", "HEAD").stdout.strip()
        result = self.run_update(answer="n\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("aborted", result.stdout)
        self.assertEqual((self.nest / "AGENTS.md").read_text(encoding="utf-8"), "old protocol\n")
        self.assertEqual(git(self.nest, "rev-parse", "HEAD").stdout.strip(), head_before)

    @unittest.skipUnless(shutil.which("git-crypt"), "git-crypt not installed")
    def test_encrypted_nest_keeps_short_version_and_ciphertext(self) -> None:
        """A plaintext upstream VERSION must not pass through git-crypt smudge."""
        (self.upstream / "VERSION").write_text("0.6.0\n", encoding="utf-8")
        git(self.upstream, "add", "VERSION")
        git(self.upstream, "commit", "-q", "-m", "release version")
        result = subprocess.run(["git-crypt", "init"], cwd=self.nest,
                                env=GIT_ENV, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.nest / ".gitattributes").write_text(
            "* filter=git-crypt diff=git-crypt\n.gitattributes !filter !diff\n",
            encoding="utf-8",
        )
        (self.nest / "VERSION").write_text("0.5.0\n", encoding="utf-8")
        git(self.nest, "add", ".")
        git(self.nest, "add", "--renormalize", ".")
        git(self.nest, "commit", "-q", "-m", "encrypt private nest")
        rules_before = git(self.nest, "rev-parse", "HEAD:queen/agent-rules.md").stdout

        result = self.run_update()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.nest / "VERSION").read_text(), "0.6.0\n")
        self.assertEqual((self.nest / "AGENTS.md").read_text(), "upstream protocol v-next\n")
        for path in ("VERSION", "AGENTS.md"):
            blob = subprocess.check_output(
                ["git", "-C", str(self.nest), "cat-file", "blob", f"HEAD:{path}"],
                env=GIT_ENV,
            )
            self.assertTrue(blob.startswith(b"\x00GITCRYPT\x00"), path)
        self.assertEqual(git(self.nest, "rev-parse", "HEAD:queen/agent-rules.md").stdout,
                         rules_before)

    def test_dirty_worktree_is_rejected_without_committing_user_changes(self) -> None:
        (self.nest / "queen" / "agent-rules.md").write_text("uncommitted rules\n")
        git(self.nest, "add", "queen/agent-rules.md")
        head_before = git(self.nest, "rev-parse", "HEAD").stdout

        result = self.run_update()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("commit or stash", result.stderr)
        self.assertEqual(git(self.nest, "rev-parse", "HEAD").stdout, head_before)
        self.assertEqual((self.nest / "AGENTS.md").read_text(), "old protocol\n")


if __name__ == "__main__":
    unittest.main()
