import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/maintenance/memory-index.py"
DISTILL = ROOT / "scripts/maintenance/distill.py"

spec = importlib.util.spec_from_file_location("memory_index", SCRIPT)
memory_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory_index)

MARKED = f"# SHARED MEMORY\n\nUser header stays.\n\n{memory_index.BEGIN}\n{memory_index.END}\n\nFooter stays.\n"


def topic(description, body="- fact\n", updated="2026-09-27"):
    return f"---\ndescription: {description}\nupdated: {updated}\n---\n\n# Topic\n\n{body}"


class MemoryIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.shared = self.root / "shared"
        self.shared.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def run_index(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args],
                              capture_output=True, text=True)

    def test_generates_index_from_front_matter_and_keeps_outside_text(self):
        (self.shared / "memory.md").write_text(MARKED, encoding="utf-8")
        (self.shared / "owner.md").write_text(topic("Who the user is"), encoding="utf-8")
        (self.shared / "tooling").mkdir()
        (self.shared / "tooling/mailbox.md").write_text(topic("Agent mailbox usage"), encoding="utf-8")
        (self.shared / "resident.md").write_text("# resident\n", encoding="utf-8")

        result = self.run_index()
        self.assertEqual(result.returncode, 0, result.stdout)
        memory = (self.shared / "memory.md").read_text(encoding="utf-8")
        self.assertIn("User header stays.", memory)
        self.assertIn("Footer stays.", memory)
        self.assertIn("[`owner.md`](owner.md) — Who the user is (2026-09-27,", memory)
        self.assertIn("[`tooling/mailbox.md`](tooling/mailbox.md) — Agent mailbox usage", memory)
        self.assertNotIn("resident.md", memory.split(memory_index.BEGIN)[1])

        self.assertEqual(self.run_index("--check").returncode, 0)
        again = self.run_index()
        self.assertNotIn("UPDATED", again.stdout)

    def test_check_fails_on_stale_index_missing_description_and_oversize(self):
        (self.shared / "memory.md").write_text(MARKED, encoding="utf-8")
        (self.shared / "owner.md").write_text(topic("Who the user is"), encoding="utf-8")
        self.assertEqual(self.run_index("--check").returncode, 1)  # never generated

        self.run_index()
        self.assertEqual(self.run_index("--check").returncode, 0)
        (self.shared / "env.md").write_text("# no front matter\n", encoding="utf-8")
        result = self.run_index("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("env.md: missing `description`", result.stdout)

        (self.shared / "env.md").write_text(topic("Machines", "x" * 40000), encoding="utf-8")
        self.run_index()
        result = self.run_index("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("split it into env/", result.stdout)

    def test_unmarked_scopes_are_left_alone(self):
        legacy = "# SHARED MEMORY\n\n- legacy monolith\n"
        (self.shared / "memory.md").write_text(legacy, encoding="utf-8")
        (self.shared / "notes.md").write_text("no front matter\n", encoding="utf-8")
        self.assertEqual(self.run_index().returncode, 0)
        self.assertEqual(self.run_index("--check").returncode, 0)
        self.assertEqual((self.shared / "memory.md").read_text(encoding="utf-8"), legacy)

    def test_agent_scope_skips_mailbox_and_local_dirs(self):
        agent = self.root / "agents/host/claude-ab12"
        (agent / "outbox").mkdir(parents=True)
        (agent / "local").mkdir()
        (agent / "memory.md").write_text(MARKED, encoding="utf-8")
        (agent / "outbox/msg.md").write_text("mail\n", encoding="utf-8")
        (agent / "local/inbox.md").write_text("inbox\n", encoding="utf-8")
        (agent / "hosts.md").write_text(topic("This machine's quirks"), encoding="utf-8")
        result = self.run_index("--check")
        self.assertIn("stale", result.stdout)
        self.run_index()
        self.assertEqual(self.run_index("--check").returncode, 0)
        index = (agent / "memory.md").read_text(encoding="utf-8")
        self.assertIn("hosts.md", index)
        self.assertNotIn("msg.md", index)


class DistillTopicModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "shared").mkdir()
        (self.root / "shared/memory.md").write_text(MARKED, encoding="utf-8")
        (self.root / "shared/owner.md").write_text(topic("Who the user is", "- prefers Chinese\n"), encoding="utf-8")
        agent = self.root / "agents/host-a/claude-ab12"
        agent.mkdir(parents=True)
        (agent / "memory.md").write_text(MARKED, encoding="utf-8")
        (agent / "stack.md").write_text(topic("Stack notes", "- uses Vue 3\n"), encoding="utf-8")
        subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root)], check=True, capture_output=True)

    def tearDown(self):
        self.tmp.cleanup()

    def fake_claude(self, response):
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "claude"
        prompt_log = bin_dir / "prompt.txt"
        fake.write_text(
            "#!/usr/bin/env python3\nimport pathlib, sys\n"
            f"pathlib.Path({str(prompt_log)!r}).write_text(sys.stdin.read(), encoding='utf-8')\n"
            f"sys.stdout.write({response!r})\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
        return env, prompt_log

    def distill(self, env, *args):
        return subprocess.run([sys.executable, str(DISTILL), "--nestwork-path", str(self.root), *args],
                              capture_output=True, text=True, env=env)

    def test_prompt_lists_topic_files_and_agent_topics(self):
        result = self.distill(os.environ.copy())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("<<<FILE shared/owner.md", result.stdout)
        self.assertIn("Topic file `stack.md`", result.stdout)
        self.assertIn("- uses Vue 3", result.stdout)
        self.assertNotIn("<<<FILE shared/memory.md", result.stdout)

    def test_run_writes_topics_and_regenerates_index(self):
        response = ("Here you go.\n<<<FILE shared/engineering.md\n"
                    + topic("Stack and engineering preferences", "- uses Vue 3\n```ts\nconst a = 1\n```\n").rstrip()
                    + "\n>>>END\n")
        env, prompt_log = self.fake_claude(response)
        result = self.distill(env, "--run-claude", "--no-commit")
        self.assertEqual(result.returncode, 0, result.stderr)
        body = (self.root / "shared/engineering.md").read_text(encoding="utf-8")
        self.assertIn("const a = 1", body)
        self.assertIn("- prefers Chinese", (self.root / "shared/owner.md").read_text(encoding="utf-8"))
        index = (self.root / "shared/memory.md").read_text(encoding="utf-8")
        self.assertIn("[`engineering.md`](engineering.md) — Stack and engineering preferences", index)
        self.assertIn("User header stays.", index)

    def test_rejects_writes_outside_topic_files(self):
        for bad in ("shared/memory.md", "queen/agent-rules.md", "shared/a/b/c.md"):
            with self.subTest(path=bad):
                env, _ = self.fake_claude(f"<<<FILE {bad}\n{topic('x')}>>>END\n")
                result = self.distill(env, "--run-claude", "--no-commit")
                self.assertEqual(result.returncode, 1)
                self.assertIn("invalid topic path", result.stderr)
                (self.root / "bin").rename(self.root / f"bin-used-{bad.replace('/', '_')}")
        env, _ = self.fake_claude("<<<FILE shared/env.md\n# no front matter\n>>>END\n")
        result = self.distill(env, "--run-claude", "--no-commit")
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing `description`", result.stderr)
        self.assertFalse((self.root / "shared/env.md").exists())

    def test_compile_refuses_to_flatten_topic_mode(self):
        (self.root / "scripts/maintenance").mkdir(parents=True)
        compile_sh = self.root / "scripts/maintenance/compile.sh"
        compile_sh.write_bytes((ROOT / "scripts/maintenance/compile.sh").read_bytes())
        result = subprocess.run(["bash", str(compile_sh)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("topic files", result.stderr)
        self.assertIn(memory_index.BEGIN, (self.root / "shared/memory.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
