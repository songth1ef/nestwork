import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_INSTALLER = REPO_ROOT / "scripts" / "install" / "codex.ps1"
CODEX_INSTALLER_SH = REPO_ROOT / "scripts" / "install" / "codex.sh"


class CodexWindowsInstallerTests(unittest.TestCase):
    def test_installer_bootstraps_codex_agents_md(self) -> None:
        content = CODEX_INSTALLER.read_text(encoding="utf-8")

        self.assertIn('$CodexAgents = "$CodexDir\\AGENTS.md"', content)
        self.assertRegex(
            content,
            r'_bootstrap\.py"\)\s+`\s+"\$CodexAgents"',
            msg="Codex installer should inject nestwork bootstrap into ~/.codex/AGENTS.md",
        )

    def test_windows_installer_registers_current_codex_hooks_file(self) -> None:
        content = CODEX_INSTALLER.read_text(encoding="utf-8")
        self.assertIn('$CodexConfig = "$CodexDir\\config.toml"', content)
        self.assertIn('$CodexHooks = "$CodexDir\\hooks.json"', content)
        self.assertIn("_codex_hooks.py", content)
        self.assertNotIn('$Settings = "$CodexDir\\config.json"', content)

    def test_bash_installer_registers_current_codex_hooks_file(self) -> None:
        content = CODEX_INSTALLER_SH.read_text(encoding="utf-8")

        self.assertIn('CODEX_CONFIG="$CODEX_DIR/config.toml"', content)
        self.assertIn('CODEX_HOOKS="$CODEX_DIR/hooks.json"', content)
        self.assertIn("_codex_hooks.py", content)
        self.assertNotIn('SETTINGS="$CODEX_DIR/config.json"', content)


if __name__ == "__main__":
    unittest.main()
