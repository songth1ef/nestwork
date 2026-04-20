import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / "scripts" / "install" / "_bootstrap.py"
TMP_ROOT = REPO_ROOT / ".test-tmp"


class BootstrapInjectorTests(unittest.TestCase):
    def test_replaces_legacy_codex_global_startup_protocol(self) -> None:
        legacy = """# Global Startup Protocol

Before starting analysis, planning, or implementation in a new coding session, load:

- `C:\\Users\\Administrator\\.codex\\repos\\codex\\bootstrap.md`

Execution requirements:

- Treat `bootstrap.md` as the entry protocol for the user's long-term context repository.
"""

        target = TMP_ROOT / "bootstrap-test-AGENTS.md"
        try:
            TMP_ROOT.mkdir(exist_ok=True)
            target.write_text(legacy, encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    str(target),
                    "F:/code/playground/myhivequeen",
                    "desktop-rkv5ls4",
                    "codex",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            updated = target.read_text(encoding="utf-8")
            self.assertNotIn(".codex\\repos\\codex\\bootstrap.md", updated)
            self.assertNotIn("Global Startup Protocol", updated)
            self.assertIn("Hivequeen Startup Protocol", updated)
        finally:
            target.unlink(missing_ok=True)

    def test_removes_legacy_codex_startup_when_hivequeen_marker_exists(self) -> None:
        existing = """# Global Startup Protocol

Before starting analysis, planning, or implementation in a new coding session, load:

- `C:\\Users\\Administrator\\.codex\\repos\\codex\\bootstrap.md`

<!-- hivequeen:begin -->
old hivequeen block
<!-- hivequeen:end -->
"""

        target = TMP_ROOT / "bootstrap-test-AGENTS-with-marker.md"
        try:
            TMP_ROOT.mkdir(exist_ok=True)
            target.write_text(existing, encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    str(target),
                    "F:/code/playground/myhivequeen",
                    "desktop-rkv5ls4",
                    "codex",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            updated = target.read_text(encoding="utf-8")
            self.assertNotIn(".codex\\repos\\codex\\bootstrap.md", updated)
            self.assertNotIn("Global Startup Protocol", updated)
            self.assertNotIn("old hivequeen block", updated)
            self.assertIn("Hivequeen Startup Protocol", updated)
        finally:
            target.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
