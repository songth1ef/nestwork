import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/maintenance/measure-context.py"

spec = importlib.util.spec_from_file_location("measure_context", SCRIPT)
measure_context = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure_context)

INDEX = "# SHARED MEMORY\n\n<!-- nestwork:topic-index:begin -->\n- [`git.md`](git.md)\n<!-- nestwork:topic-index:end -->\n"


def topic(description, body):
    return f"---\ndescription: {description}\n---\n\n{body}\n"


class MeasureContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for d in ("queen", "shared", "workflow", "projects", "agents/host/claude-ab12/outbox"):
            (self.root / d).mkdir(parents=True)
        self.write("queen/agent-rules.md", "rules\n")
        self.write("queen/strategy.md", "strategy " * 200)
        self.write("shared/resident.md", "resident\n")
        self.write("workflow/method.md", "method " * 300)
        self.write("projects/app.md", "project " * 100)
        self.write("agents/host/claude-ab12/memory.md", "agent memory " * 150)
        self.write("agents/host/claude-ab12/resident.md", "agent resident\n")
        self.write("agents/host/claude-ab12/outbox/msg.md", "mail " * 5000)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        (self.root / rel).write_text(text, encoding="utf-8")

    def run_json(self, *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), "--agent", "host/claude-ab12", "--json", *args],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_topic_mode_scenarios_are_ordered_and_skip_mailbox(self):
        self.write("shared/memory.md", INDEX)
        self.write("shared/git.md", topic("git rules", "rule " * 400))
        self.write("shared/env.md", topic("machines", "env " * 800))
        report = self.run_json("--task", "shared/git.md")
        s = report["scenarios"]
        self.assertEqual(s["resident"]["files"], 3)
        self.assertEqual(s["task"]["files"], 5)  # resident + index + one topic
        # full = rules + strategy + index + 2 topics + agent memory + workflow
        self.assertEqual(s["full"]["files"], 7)
        self.assertLess(s["resident"]["tokens"], s["task"]["tokens"])
        self.assertLess(s["task"]["tokens"], s["full"]["tokens"])
        self.assertLessEqual(s["full"]["bytes"], s["nest"]["bytes"])
        self.assertLess(s["nest"]["bytes"], 5000 * 5)  # outbox excluded

    def test_default_task_picks_median_shared_topic(self):
        self.write("shared/memory.md", INDEX)
        for name, size in (("a", 10), ("b", 200), ("c", 4000)):
            self.write(f"shared/{name}.md", topic(name, "x" * size))
        self.assertEqual(self.run_json()["tasks"], ["shared/b.md"])

    def test_legacy_single_file_memory(self):
        self.write("shared/memory.md", "# SHARED MEMORY\n\n" + "fact " * 1000)
        report = self.run_json()
        self.assertEqual(report["tasks"], [])
        self.assertEqual(report["scenarios"]["task"]["files"], 3)  # no index to route through
        self.assertGreater(report["scenarios"]["full"]["tokens"], report["scenarios"]["resident"]["tokens"])

    def test_missing_task_file_is_an_error(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), "--task", "shared/nope.md"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not found", result.stderr)

    def test_estimate_weights_cjk_and_latin_differently(self):
        count, method = measure_context.token_counter()
        if not method.startswith("estimate"):
            self.skipTest("tiktoken installed; estimator not in use")
        self.assertEqual(count("字" * 100), 105)
        self.assertEqual(count("a" * 420), 100)


if __name__ == "__main__":
    unittest.main()
