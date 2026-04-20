import re
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_INSTALLER = REPO_ROOT / "scripts" / "install" / "codex.ps1"


class CodexWindowsInstallerTests(unittest.TestCase):
    def test_installer_bootstraps_codex_agents_md(self) -> None:
        content = CODEX_INSTALLER.read_text(encoding="utf-8")

        self.assertIn('$CodexAgents = "$CodexDir\\AGENTS.md"', content)
        self.assertRegex(
            content,
            r'_bootstrap\.py"\)\s+`\s+"\$CodexAgents"',
            msg="Codex installer should inject hivequeen bootstrap into ~/.codex/AGENTS.md",
        )

    def test_end_hook_command_parses_in_windows_powershell(self) -> None:
        content = CODEX_INSTALLER.read_text(encoding="utf-8")
        match = re.search(r'\$HookCmd = "(?P<hook>(?:[^"`]|`.)*)"', content)
        self.assertIsNotNone(match, "Could not find $HookCmd in codex.ps1")

        hook = match.group("hook")
        parser = (
            "$ErrorActionPreference='Stop'; "
            "$HivequeenPath='C:\\tmp\\hivequeen'; "
            "$AgentRel='agents/desktop/codex'; "
            "$HiveHost='desktop'; "
            "$AgentId='codex'; "
            f"$hook=\"{hook}\"; "
            "[scriptblock]::Create($hook) | Out-Null"
        )

        completed = subprocess.run(
            [
                r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                "-NoProfile",
                "-Command",
                parser,
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            completed.returncode,
            0,
            msg=(
                "Codex end_hook must be valid Windows PowerShell syntax.\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
