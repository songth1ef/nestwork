import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SEND = REPO_ROOT / "scripts" / "comms" / "send.sh"
READ = REPO_ROOT / "scripts" / "comms" / "read.sh"
ARCHIVE = REPO_ROOT / "scripts" / "comms" / "archive.sh"

# Keep test repos hermetic: a developer's global git config (commit signing,
# hooks, templates) must not leak into the throwaway repos.
GIT_ISOLATION = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}


def run(cmd, cwd, env=None, stdin=""):
    merged = dict(os.environ)
    merged.update(GIT_ISOLATION)
    if env:
        merged.update(env)
    return subprocess.run(
        cmd, cwd=cwd, env=merged, input=stdin,
        capture_output=True, text=True,
    )


def git(repo, *args):
    return run(["git", "-C", str(repo), *args], cwd=repo)


class CommsTests(unittest.TestCase):
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
        # Mirror the shipped .gitignore: local/ state never enters commits.
        (self.repo / ".gitignore").write_text("agents/*/*/local/\n", encoding="utf-8")
        self.assertEqual(git(self.repo, "add", ".gitignore").returncode, 0)
        self.assertEqual(
            git(self.repo, "commit", "-q", "-m", "init").returncode, 0
        )
        self.assertEqual(
            git(self.repo, "remote", "add", "origin", str(self.origin)).returncode, 0
        )
        self.assertEqual(
            git(self.repo, "push", "-q", "-u", "origin", "main").returncode, 0
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def send(self, sender, to, mtype="task", subject="handshake test", body="please reply"):
        result = run(
            ["bash", str(SEND), to, mtype, subject],
            cwd=self.repo, env={"NESTWORK_SELF": sender}, stdin=body,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def read(self, reader, *args):
        return run(
            ["bash", str(READ), *args],
            cwd=self.repo, env={"NESTWORK_SELF": reader},
        )

    def outbox_files(self, sender):
        outbox = self.repo / "agents" / sender / "outbox"
        return sorted(p for p in outbox.glob("*.md"))

    def test_send_writes_envelope_commits_and_pushes(self) -> None:
        self.send("hosta/agent1", "hostb/agent2")

        files = self.outbox_files("hosta/agent1")
        self.assertEqual(len(files), 1)
        content = files[0].read_text(encoding="utf-8")
        self.assertIn("from: hosta/agent1", content)
        self.assertIn("to: hostb/agent2", content)
        self.assertIn("type: task", content)
        self.assertIn("subject: handshake test", content)
        self.assertIn("please reply", content)

        # Delivery: send.sh itself commits and pushes (no hook involved).
        log = git(self.repo, "log", "-1", "--format=%s")
        self.assertTrue(log.stdout.startswith("comms: task to hostb/agent2"), log.stdout)
        local_head = git(self.repo, "rev-parse", "main").stdout.strip()
        remote_head = git(self.origin, "rev-parse", "refs/heads/main").stdout.strip()
        self.assertEqual(local_head, remote_head)

    def test_read_filters_recipient_and_marks_seen_outside_git(self) -> None:
        self.send("hosta/agent1", "hostb/agent2", subject="direct-msg")
        self.send("hosta/agent1", "all", mtype="broadcast", subject="broadcast-msg")
        self.send("hosta/agent1", "hostc/agent3", subject="other-msg")

        unread = self.read("hostb/agent2")
        self.assertEqual(unread.returncode, 0, unread.stderr)
        self.assertIn("direct-msg", unread.stdout)
        self.assertIn("broadcast-msg", unread.stdout)
        self.assertNotIn("other-msg", unread.stdout)

        marked = self.read("hostb/agent2", "--mark")
        self.assertIn("marked 2 message(s)", marked.stdout)

        seen = self.repo / "agents" / "hostb" / "agent2" / "local" / "comms" / "seen.txt"
        self.assertTrue(seen.exists())
        self.assertEqual(len(seen.read_text(encoding="utf-8").split()), 2)
        # Seen state must be git-ignored: marking read creates no commit churn.
        ignored = git(self.repo, "check-ignore", "agents/hostb/agent2/local/comms/seen.txt")
        self.assertEqual(ignored.returncode, 0)

        again = self.read("hostb/agent2")
        self.assertIn("(no unread messages for hostb/agent2)", again.stdout)

    def test_write_mode_creates_then_deletes_inbox_snapshot(self) -> None:
        self.send("hosta/agent1", "hostb/agent2", subject="inbox-msg")
        inbox = "agents/hostb/agent2/local/inbox.md"

        first = self.read("hostb/agent2", "--write", inbox)
        self.assertEqual(first.returncode, 0, first.stderr)
        snapshot = (self.repo / inbox).read_text(encoding="utf-8")
        self.assertIn("1 unread message(s) for hostb/agent2", snapshot)
        self.assertIn("inbox-msg", snapshot)

        self.read("hostb/agent2", "--mark")
        second = self.read("hostb/agent2", "--write", inbox)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertFalse((self.repo / inbox).exists())

    def test_legacy_committed_seen_txt_is_imported(self) -> None:
        self.send("hosta/agent1", "hostb/agent2", subject="legacy-msg")
        msg_id = self.outbox_files("hosta/agent1")[0].stem

        legacy = self.repo / "agents" / "hostb" / "agent2" / "comms" / "seen.txt"
        legacy.parent.mkdir(parents=True)
        legacy.write_text(msg_id + "\n", encoding="utf-8")

        result = self.read("hostb/agent2")
        self.assertIn("(no unread messages for hostb/agent2)", result.stdout)
        seen = self.repo / "agents" / "hostb" / "agent2" / "local" / "comms" / "seen.txt"
        self.assertIn(msg_id, seen.read_text(encoding="utf-8"))

    def test_archive_moves_old_messages_and_commits(self) -> None:
        outbox = self.repo / "agents" / "hosta" / "agent1" / "outbox"
        outbox.mkdir(parents=True)
        old_name = "20200101T000000+0000-agent1-deadbeef.md"
        (outbox / old_name).write_text(
            "---\nid: 20200101T000000+0000-agent1-deadbeef\n"
            "from: hosta/agent1\nto: hostb/agent2\ntype: message\n"
            "subject: stale\n---\n\nold body\n",
            encoding="utf-8",
        )
        git(self.repo, "add", "agents/hosta/agent1/outbox")
        git(self.repo, "commit", "-q", "-m", "seed old message")
        self.send("hosta/agent1", "hostb/agent2", subject="fresh-msg")

        result = run(
            ["bash", str(ARCHIVE), "30"],
            cwd=self.repo, env={"NESTWORK_SELF": "hosta/agent1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("archived 1 message(s)", result.stdout)

        self.assertFalse((outbox / old_name).exists())
        self.assertTrue((outbox / "archive" / old_name).exists())
        self.assertEqual(len(self.outbox_files("hosta/agent1")), 1)

        log = git(self.repo, "log", "-1", "--format=%s")
        self.assertTrue(log.stdout.startswith("comms: archive 1 message(s)"), log.stdout)

        # Archived messages drop out of the recipient's scan path.
        unread = self.read("hostb/agent2")
        self.assertIn("fresh-msg", unread.stdout)
        self.assertNotIn("stale", unread.stdout)


if __name__ == "__main__":
    unittest.main()
