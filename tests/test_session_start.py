import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SRC = REPO_ROOT / "scripts" / "hooks" / "session-start.sh"
READ_SRC = REPO_ROOT / "scripts" / "comms" / "read.sh"
SEND_SRC = REPO_ROOT / "scripts" / "comms" / "send.sh"


class SessionStartTests(unittest.TestCase):
    """End-to-end coverage for the tiered SessionStart context bundle.

    The hook resolves the repo from its own location, so it is copied into a
    throwaway repo. HOME is redirected so the upstream-check cache can be
    seeded deterministically (a seeded cache also keeps the hook off the
    network: the 24h-TTL hit short-circuits the curl).
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.repo = base / "nest"
        self.home = base / "home"
        self.home.mkdir()
        self.repo.mkdir()
        self.env = dict(os.environ)
        self.env.update({
            "HOME": str(self.home),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
        })

        def git(*args):
            return subprocess.run(
                ["git", "-C", str(self.repo), *args],
                capture_output=True, text=True, env=self.env,
            )

        self.git = git
        git("init", "-q")
        git("checkout", "-q", "-b", "main")
        git("config", "user.name", "test")
        git("config", "user.email", "test@example.com")

        (self.repo / "queen").mkdir()
        (self.repo / "queen" / "agent-rules.md").write_text(
            "# AGENT RULES\n\n- lead with the conclusion\n", encoding="utf-8"
        )
        (self.repo / "queen" / "strategy.md").write_text("# STRATEGY\n", encoding="utf-8")
        (self.repo / "shared").mkdir()
        (self.repo / "shared" / "memory.md").write_text("# SHARED MEMORY\n", encoding="utf-8")
        memory = self.repo / "agents" / "h1" / "a1" / "memory.md"
        memory.parent.mkdir(parents=True)
        memory.write_text("# MEMORY\n", encoding="utf-8")
        (self.repo / "workflow").mkdir()
        (self.repo / "workflow" / "lessons.md").write_text("# LESSONS\n", encoding="utf-8")
        (self.repo / "workflow" / "_template.md").write_text("# TEMPLATE\n", encoding="utf-8")
        (self.repo / "AGENTS.md").write_text(
            "# NESTWORK BOOTSTRAP\n\n<!-- protocol-version: 2.4 -->\n", encoding="utf-8"
        )
        (self.repo / ".gitignore").write_text("agents/*/*/local/\n", encoding="utf-8")

        self.hook = self.repo / "scripts" / "hooks" / "session-start.sh"
        self.hook.parent.mkdir(parents=True)
        shutil.copy(HOOK_SRC, self.hook)
        comms = self.repo / "scripts" / "comms"
        comms.mkdir(parents=True)
        shutil.copy(READ_SRC, comms / "read.sh")
        shutil.copy(SEND_SRC, comms / "send.sh")

        git("add", ".")
        git("commit", "-q", "-m", "init")

        self.seed_cache("2.4")  # version match -> no advisory, no network call

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def seed_cache(self, upstream_version) -> None:
        cache = self.home / ".cache" / "nestwork"
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "upstream-check").write_text(
            f"{int(time.time())} {upstream_version}\n", encoding="utf-8"
        )

    def run_hook(self):
        result = subprocess.run(
            ["bash", str(self.hook), "h1", "a1"],
            capture_output=True, text=True, env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_bundle_inlines_rules_and_lists_read_on_start_manifest(self) -> None:
        out = self.run_hook()

        self.assertIn("nestwork context bundle for h1/a1", out)
        # agent-rules is the only file small enough to inline fully.
        self.assertIn("=== agent-rules (queen/agent-rules.md) ===", out)
        self.assertIn("lead with the conclusion", out)
        # The rest arrives as absolute paths the agent must Read.
        self.assertIn("=== READ-ON-START", out)
        self.assertIn(f"- {self.repo}/queen/strategy.md", out)
        self.assertIn(f"- {self.repo}/shared/memory.md", out)
        self.assertIn(f"- {self.repo}/agents/h1/a1/memory.md", out)

    def test_missing_files_are_skipped_silently(self) -> None:
        (self.repo / "shared" / "memory.md").unlink()
        out = self.run_hook()
        self.assertNotIn("shared/memory.md", out)
        self.assertIn(f"- {self.repo}/queen/strategy.md", out)

    def test_read_on_demand_lists_workflow_but_not_template(self) -> None:
        out = self.run_hook()
        self.assertIn("=== READ-ON-DEMAND", out)
        self.assertIn(f"- {self.repo}/workflow/lessons.md", out)
        self.assertNotIn("_template.md", out)

    def test_unread_mail_is_snapshotted_into_manifest(self) -> None:
        env = dict(self.env)
        env["NESTWORK_SELF"] = "h2/b1"
        sent = subprocess.run(
            ["bash", str(self.repo / "scripts" / "comms" / "send.sh"),
             "h1/a1", "task", "tier1 test"],
            cwd=self.repo, capture_output=True, text=True, input="hello", env=env,
        )
        self.assertEqual(sent.returncode, 0, sent.stderr)

        out = self.run_hook()

        inbox = self.repo / "agents" / "h1" / "a1" / "local" / "inbox.md"
        self.assertTrue(inbox.exists())
        snapshot = inbox.read_text(encoding="utf-8")
        self.assertIn("1 unread message(s) for h1/a1", snapshot)
        self.assertIn("tier1 test", snapshot)
        self.assertIn(f"- {self.repo}/agents/h1/a1/local/inbox.md", out)

    def test_empty_mailbox_deletes_stale_inbox_snapshot(self) -> None:
        inbox = self.repo / "agents" / "h1" / "a1" / "local" / "inbox.md"
        inbox.parent.mkdir(parents=True)
        inbox.write_text("stale\n", encoding="utf-8")

        out = self.run_hook()

        self.assertFalse(inbox.exists())
        self.assertNotIn("local/inbox.md", out)

    def test_upstream_advisory_only_when_newer(self) -> None:
        out = self.run_hook()
        self.assertNotIn("upstream protocol-version", out)

        self.seed_cache("9.9")
        out = self.run_hook()
        self.assertIn("upstream protocol-version 9.9 available (local 2.4)", out)
        self.assertIn("update.sh", out)

        # Upstream older than local must not advise a downgrade.
        self.seed_cache("1.0")
        out = self.run_hook()
        self.assertNotIn("upstream protocol-version", out)


if __name__ == "__main__":
    unittest.main()
