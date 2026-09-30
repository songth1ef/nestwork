import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "maintenance" / "recent-digest.py"
spec = importlib.util.spec_from_file_location("recent_digest", SCRIPT)
digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(digest)


class RecentDigestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.nest = Path(self.tmp.name)
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        self.git("init", "-q")
        self.git("config", "user.name", "test")
        self.git("config", "user.email", "test@example.com")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git(self, *args, date=None):
        env = dict(self.env)
        if date:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        return subprocess.run(["git", "-C", str(self.nest), *args],
                              capture_output=True, text=True, env=env, check=True)

    def commit(self, files: dict, message: str, date=None) -> None:
        for rel, text in files.items():
            path = self.nest / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", message, date=date)

    def build(self, **kw) -> str:
        opts = dict(days=7, project_days=30, max_bytes=2048)
        opts.update(kw)
        return digest.build(self.nest, **opts)

    def test_projects_and_topics_are_summarised(self) -> None:
        self.commit({
            "projects/alpha.md": "# alpha\n\n## Current Goal\nShip v1\n\n## Next Action\n- Email the first customer\n\n## Last Verified\n2026-09-29 — on laptop\n",
            "agents/h/a/perf.md": "---\ndescription: Where real perf data lives; read before measuring\n---\nbody\n",
            "shared/owner.md": "# Owner profile\n\nbody\n",
        }, "work")
        out = self.build()
        self.assertIn("**alpha**", out)
        self.assertIn("goal: Ship v1", out)
        self.assertIn("next: Email the first customer", out)
        self.assertIn("verified: 2026-09-29", out)
        self.assertIn("`agents/h/a/perf.md` — Where real perf data lives", out)
        self.assertIn("`shared/owner.md` — Owner profile", out)

    def test_indexes_templates_local_and_locked_files_are_skipped(self) -> None:
        self.commit({
            "shared/memory.md": "# index\n",
            "shared/resident.md": "# resident\n",
            "projects/_template.md": "## Next Action\nnope\n",
            "local/recent.md": "# generated\n",
            "shared/secret.md": "\x00GITCRYPT\x00garbage",
        }, "noise")
        out = self.build()
        for noise in ("memory.md", "resident.md", "_template", "local/", "secret.md"):
            self.assertNotIn(noise, out)
        self.assertIn("No project or memory changes", out)

    def test_bulk_commit_collapses_to_one_line(self) -> None:
        files = {f"shared/t{n}.md": f"---\ndescription: topic {n}\n---\n" for n in range(8)}
        self.commit(files, "feat(memory): split shared into topics")
        self.commit({"agents/h/a/note.md": "---\ndescription: single update\n---\n"}, "note")
        out = self.build()
        self.assertIn("feat(memory): split shared into topics (8 files)", out)
        self.assertIn("single update", out)
        self.assertNotIn("topic 3", out)
        self.assertLess(out.index("single update"), out.index("split shared"))  # newest first

    def test_old_changes_fall_outside_the_window(self) -> None:
        self.commit({"agents/h/a/old.md": "---\ndescription: ancient\n---\n"}, "old",
                    date="2020-01-01T00:00:00")
        self.assertNotIn("ancient", self.build())

    def test_output_respects_byte_cap(self) -> None:
        files = {f"agents/h/a/n{n}.md": f"---\ndescription: {'长描述' * 60} {n}\n---\n" for n in range(5)}
        for rel, text in files.items():
            self.commit({rel: text}, f"add {rel}")
        out = self.build(max_bytes=700)
        self.assertLessEqual(len(out.encode("utf-8")), 700)
        self.assertIn("truncated", out)

    def test_cli_writes_out_file_atomically(self) -> None:
        self.commit({"agents/h/a/x.md": "---\ndescription: cli check\n---\n"}, "x")
        result = subprocess.run(
            ["python3", str(SCRIPT), "--nest", str(self.nest), "--out", "local/recent.md"],
            capture_output=True, text=True, env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        out = self.nest / "local/recent.md"
        self.assertIn("cli check", out.read_text(encoding="utf-8"))
        self.assertFalse(out.with_suffix(".md.tmp").exists())


if __name__ == "__main__":
    unittest.main()
