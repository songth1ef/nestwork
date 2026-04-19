import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class DocsConsistencyTests(unittest.TestCase):
    def test_readme_uses_protocol_v2_agent_layout(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("agents/<host>/<agent-id>/", readme)
        self.assertNotIn("agents/<tool>-<hostname>/", readme)

    def test_project_context_exists_in_template(self) -> None:
        project_context = REPO_ROOT / "projects" / "hivequeen.md"

        self.assertTrue(project_context.exists())
        self.assertIn("git 原生的 AI agent 上下文协议", project_context.read_text(encoding="utf-8"))

    def test_bootstrap_manual_commit_checks_only_agent_path(self) -> None:
        bootstrap = (REPO_ROOT / "scripts" / "install" / "_bootstrap.py").read_text(encoding="utf-8")

        self.assertIn("git -C {hp} diff --cached --quiet -- agents/{host}/{aid}/", bootstrap)

    def test_compile_commit_checks_only_shared_memory(self) -> None:
        compile_script = (REPO_ROOT / "scripts" / "maintenance" / "compile.sh").read_text(encoding="utf-8")

        self.assertIn("git diff --cached --quiet -- shared/memory.md", compile_script)


if __name__ == "__main__":
    unittest.main()
