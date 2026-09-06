import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class DocsConsistencyTests(unittest.TestCase):
    def test_current_protocol_is_discoverable_beyond_readme_banner(self) -> None:
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        protocol = re.search(r"protocol-version: (\d+\.\d+)", agents).group(1)
        for name in ("README.md", "README.zh.md"):
            content = (REPO_ROOT / name).read_text(encoding="utf-8")
            with self.subTest(path=name):
                self.assertRegex(content, rf"(?m)^- v{re.escape(protocol)}[ （(]")
                self.assertIn("docs/context-loading.md", content)
                self.assertNotIn("v1 → v2.0 → v2.1 → v2.2", content)
        for name in ("docs/README.md", "llms.txt"):
            content = (REPO_ROOT / name).read_text(encoding="utf-8")
            with self.subTest(path=name):
                self.assertIn(protocol, content)
                self.assertIn("context-loading.md", content)

    def test_startup_guides_keep_history_out_of_required_reads(self) -> None:
        for name in ("docs/claude-code-memory.md", "docs/agents-md-best-practices.md"):
            content = (REPO_ROOT / name).read_text(encoding="utf-8")
            with self.subTest(path=name):
                for path in ("queen/agent-rules.md", "shared/resident.md",
                             "agents/<host>/<agent-id>/resident.md"):
                    self.assertIn(path, content)
                self.assertIn("context-loading.md", content)
                self.assertNotRegex(content, r"(?m)^- `(?:queen/strategy|shared/memory|agents/.+/memory)\.md`")
                self.assertNotRegex(content, r"(?m)^\d+\. Load (strategy|shared memory|this agent's private memory)")
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        row = next(line for line in agents.splitlines()
                   if line.startswith("| Only when the machine changes")
                   and "must apply without being looked up" in line)
        self.assertIn("/resident.md", row)
        self.assertNotIn("/memory.md", row)

    def test_mailbox_docs_match_on_demand_consumption(self) -> None:
        for name in ("docs/agent-mailbox.md", "scripts/comms/README.md"):
            content = (REPO_ROOT / name).read_text(encoding="utf-8")
            tier = content.split("- **Tier 1", 1)[1].split("- **Tier 2", 1)[0]
            with self.subTest(path=name):
                self.assertIn("READ-ON-DEMAND", tier)
                self.assertIn("never READ-ON-START", tier)
                self.assertNotIn("automatically on every session start", tier)
        stale = ("启动时自动收未读", "unread message automatically",
                 "unread messages automatically when it starts",
                 "unread note automatically when it starts")
        for path in (REPO_ROOT / "docs" / "blog").glob("*.md"):
            content = path.read_text(encoding="utf-8")
            for phrase in stale:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertNotIn(phrase, content)

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

    def test_readmes_have_no_version_scoped_sections(self) -> None:
        """No `## vX.Y new: ...` headings in either README.

        A version-scoped section freezes on the release that created it: the
        repo carried a "v2.2 new" section for three protocol releases, so
        readers saw v2.2 advertised as the newest thing. Version slices belong
        in CHANGELOG; the README describes what exists now.
        """
        pattern = re.compile(r"^#+\s*v\d+\.\d+\s", re.IGNORECASE)

        for name in ("README.md", "README.zh.md"):
            text = (REPO_ROOT / name).read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if line.lstrip().startswith("#") and pattern.match(line.strip()):
                    self.fail(
                        f"{name}:{lineno} is a version-scoped heading "
                        f"({line.strip()!r}). Describe the feature under a "
                        f"permanent heading and put the version slice in CHANGELOG."
                    )

    def test_advertised_tool_list_covers_every_installer(self) -> None:
        """Every shipped installer must appear in the README badge and llms.txt.

        Expectations are derived from `scripts/install/*.sh`, so adding a tool
        without updating the docs turns this red instead of silently leaving
        the answer-engine surface advertising an outdated list. `generic` is
        excluded: it is a fallback, not a named tool.
        """
        installers = {
            path.stem
            for path in (REPO_ROOT / "scripts" / "install").glob("*.sh")
            if not path.stem.startswith("_") and path.stem != "generic"
        }
        self.assertTrue(installers, "expected at least one installer to exist")

        surfaces = {
            "README.md badge": _readme_badge(REPO_ROOT / "README.md"),
            "README.zh.md badge": _readme_badge(REPO_ROOT / "README.zh.md"),
            "llms.txt": (REPO_ROOT / "llms.txt").read_text(encoding="utf-8").lower(),
        }

        for surface, text in surfaces.items():
            for tool in sorted(installers):
                with self.subTest(surface=surface, tool=tool):
                    self.assertIn(
                        tool,
                        text,
                        f"{surface} does not mention the '{tool}' installer",
                    )

    def test_installer_entry_file_matches_readme_and_uninstaller(self) -> None:
        """The file an installer writes must be the file the docs advertise.

        Both sides are derived: the path comes from the `_bootstrap.py` call in
        `scripts/install/<tool>.sh`, the advertised path from that tool's row in
        the Supported tools table. Kimi Code shipped writing its bootstrap to
        `~/.kimi-code/NESTWORK.md`, a filename Kimi Code never loads (it reads
        `$KIMI_CODE_HOME/AGENTS.md` and `<project>/AGENTS.md`, nothing else) --
        and the README advertised the same wrong path, so the two agreed with
        each other while the agent started with no nestwork context at all. The
        install printed success either way, which is why this failure mode has
        to be caught here rather than at install time.

        The uninstaller is checked against the same derived list: whatever an
        installer writes, its uninstaller must be able to remove.
        """
        for script in sorted((REPO_ROOT / "scripts" / "install").glob("*.sh")):
            tool = script.stem
            if tool.startswith("_") or tool == "generic":
                continue

            targets = _bootstrap_targets(script)
            with self.subTest(tool=tool):
                self.assertTrue(targets, f"{script.name} calls no _bootstrap.py")

                for readme in ("README.md", "README.zh.md"):
                    cell = _supported_tools_entry_cell(REPO_ROOT / readme, tool)
                    self.assertTrue(
                        any(target in cell for target in targets),
                        f"{readme} advertises {cell!r} as the entry file for "
                        f"'{tool}', but {script.name} writes the bootstrap to "
                        f"{targets}",
                    )

                uninstaller = REPO_ROOT / "scripts" / "uninstall" / f"{tool}.sh"
                removed = _unbootstrap_targets(uninstaller)
                for target in targets:
                    self.assertIn(
                        target,
                        removed,
                        f"{script.name} writes {target}, but "
                        f"{uninstaller.name} never removes it",
                    )


def _readme_badge(path: Path) -> str:
    """The tools badge line, lowercased and URL-unescaped enough to match names."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if "badge/tools-" in line:
            return line.replace("%20", " ").replace("%7C", "|").lower()
    raise AssertionError(f"{path.name} has no tools badge")


def _bootstrap_targets(script: Path) -> list[str]:
    """Every path a shell installer hands to `_bootstrap.py`, in `~/...` form."""
    return _helper_targets(script, r"(?<![a-z])_bootstrap\.py")


def _unbootstrap_targets(script: Path) -> list[str]:
    """Every path a shell uninstaller hands to `_unbootstrap.py`, in `~/...` form."""
    return _helper_targets(script, r"_unbootstrap\.py")


def _helper_targets(script: Path, helper: str) -> list[str]:
    text = script.read_text(encoding="utf-8")

    variables: dict[str, str] = {}
    for name, raw in re.findall(r'^([A-Z_][A-Z_0-9]*)="([^"]*)"', text, re.MULTILINE):
        variables[name] = _expand_shell_path(raw, variables)

    pattern = re.compile(helper + r'"\s*\\?\s*"([^"]+)"')
    return [_expand_shell_path(raw, variables) for raw in pattern.findall(text)]


def _expand_shell_path(value: str, variables: dict[str, str]) -> str:
    """Resolve `${VAR:-default}`, `$VAR` and `$HOME` far enough to compare paths."""
    value = re.sub(r"\$\{[A-Z_][A-Z_0-9]*:-([^}]*)\}", r"\1", value)
    # Longest name first so `$CODEX_DIR` is not eaten by a shorter prefix.
    for name in sorted(variables, key=len, reverse=True):
        value = value.replace("${" + name + "}", variables[name])
        value = value.replace("$" + name, variables[name])
    return value.replace("$HOME/", "~/")


def _supported_tools_entry_cell(path: Path, tool: str) -> str:
    """The "Entry file" cell of the Supported tools row that installs `tool`."""
    needle = f"scripts/install/{tool}.sh"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and needle in line:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 3:
                return cells[2]
    raise AssertionError(f"{path.name} has no Supported tools row installing '{tool}'")


if __name__ == "__main__":
    unittest.main()
