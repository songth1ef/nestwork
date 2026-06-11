import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class DocsConsistencyTests(unittest.TestCase):
    def test_readme_uses_protocol_v2_agent_layout(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("agents/<host>/<agent-id>/", readme)
        self.assertNotIn("agents/<tool>-<hostname>/", readme)

    def test_project_context_exists_in_template(self) -> None:
        project_context = REPO_ROOT / "projects" / "nestwork.md"

        self.assertTrue(project_context.exists())
        self.assertIn("git 原生的 AI agent 上下文协议", project_context.read_text(encoding="utf-8"))

    def test_bootstrap_manual_commit_checks_only_agent_path(self) -> None:
        bootstrap = (REPO_ROOT / "scripts" / "install" / "_bootstrap.py").read_text(encoding="utf-8")

        self.assertIn("git -C {hp} diff --cached --quiet -- agents/{host}/{aid}/", bootstrap)

    def test_compile_commit_checks_only_shared_memory(self) -> None:
        compile_script = (REPO_ROOT / "scripts" / "maintenance" / "compile.sh").read_text(encoding="utf-8")

        self.assertIn("git diff --cached --quiet -- shared/memory.md", compile_script)

    def test_geo_content_assets_exist(self) -> None:
        required_paths = [
            "llms.txt",
            "docs/README.md",
            "docs/ai-agent-memory.md",
            "docs/claude-code-memory.md",
            "docs/codex-persistent-memory.md",
            "docs/git-native-memory-protocol.md",
            "docs/agents-md-best-practices.md",
            "docs/shared-context-for-ai-coding-agents.md",
            "docs/faq.md",
            "docs/comparisons/claude-mem.md",
        ]

        for path in required_paths:
            with self.subTest(path=path):
                self.assertTrue((REPO_ROOT / path).exists(), f"{path} should exist")

    def test_readme_keeps_core_geo_entities(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
        required_terms = [
            "ai agent memory",
            "git-native memory protocol",
            "claude code",
            "codex cli",
            "gemini cli",
            "persistent memory",
            "shared context",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, readme)

    def test_llms_txt_points_to_answer_ready_docs(self) -> None:
        llms = (REPO_ROOT / "llms.txt").read_text(encoding="utf-8")

        self.assertIn("nestwork", llms)
        self.assertIn("docs/ai-agent-memory.md", llms)
        self.assertIn("docs/claude-code-memory.md", llms)
        self.assertIn("docs/codex-persistent-memory.md", llms)
        self.assertIn("docs/agents-md-best-practices.md", llms)
        self.assertIn("docs/shared-context-for-ai-coding-agents.md", llms)

    def test_codex_docs_use_agents_md_as_primary_entrypoint(self) -> None:
        paths = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "README.zh.md",
            REPO_ROOT / "docs" / "codex-persistent-memory.md",
        ]

        for path in paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertIn("~/.codex/AGENTS.md", content)

    def test_docs_index_keeps_no_website_positioning(self) -> None:
        docs_index = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8").lower()

        self.assertIn("github repository", docs_index)
        self.assertIn("ai search systems", docs_index)
        self.assertIn("without a website", docs_index)

    def test_repository_version_metadata_is_consistent(self) -> None:
        """VERSION, CHANGELOG, both READMEs, and the protocol marker must agree.

        Derives expectations from VERSION and AGENTS.md instead of hardcoding
        values, so a release or protocol bump cannot silently drift (the
        failure mode that previously left VERSION three releases stale).
        """
        version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        readme_zh = (REPO_ROOT / "README.zh.md").read_text(encoding="utf-8")
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

        marker = re.search(r"protocol-version: (\d+\.\d+)", agents)
        self.assertIsNotNone(marker, "AGENTS.md must declare a protocol-version marker")
        protocol = marker.group(1)

        # VERSION must match the latest released CHANGELOG entry.
        released = re.search(r"^## v(\d+\.\d+\.\d+) - \d{4}-\d{2}-\d{2}$", changelog, re.M)
        self.assertIsNotNone(released, "CHANGELOG.md must have a released entry")
        self.assertEqual(released.group(1), version)

        # Both READMEs must carry the same version and protocol.
        self.assertIn(f"Version: v{version} | Protocol: {protocol}", readme)
        self.assertIn(f"badge/protocol-{protocol}-blue", readme)
        self.assertIn(f"版本：v{version} | 协议：{protocol}", readme_zh)

    def test_priority_chain_is_uniform_across_docs(self) -> None:
        """Every rendition of the priority chain must show all six layers.

        The chain is duplicated across README/AGENTS/docs for GEO reasons;
        this guards against partial copies going stale again (workflow/*.md
        was missing from two docs for several releases).
        """
        canonical = (
            "queen/agent-rules.md > queen/strategy.md > shared/memory.md > "
            "agents/*/*/memory.md > projects/*.md > workflow/*.md"
        )
        for path in sorted(REPO_ROOT.rglob("*.md")):
            if ".git" in path.parts:
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if "queen/agent-rules.md" not in line or ">" not in line:
                    continue
                if "shared/memory.md" not in line:
                    continue
                normalized = " ".join(line.split())
                with self.subTest(file=str(path.relative_to(REPO_ROOT)), line=lineno):
                    self.assertIn(
                        canonical,
                        normalized,
                        "priority chain rendition is missing layers",
                    )

    def test_claude_md_is_verbatim_mirror_of_agents_md(self) -> None:
        """CLAUDE.md = generated header + AGENTS.md, byte for byte.

        sync-claude-md.sh declares drift between the two files a bug; this
        enforces it (regenerate via `bash scripts/maintenance/sync-claude-md.sh`).
        """
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        claude = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

        header, sep, body = claude.partition("-->\n\n")
        self.assertTrue(sep, "CLAUDE.md must start with the generated-mirror header")
        self.assertIn("verbatim mirror of AGENTS.md", header)
        self.assertEqual(body, agents)


if __name__ == "__main__":
    unittest.main()
