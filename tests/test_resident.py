import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ResidentTests(unittest.TestCase):
    def test_budget_uses_bytes_and_ignores_history(self):
        spec = importlib.util.spec_from_file_location('resident', ROOT / 'scripts/maintenance/check-resident.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'queen').mkdir()
            self.assertEqual(module.check(root), 1)
            (root / 'queen/agent-rules.md').write_text('rules')
            (root / 'shared').mkdir()
            (root / 'shared/memory.md').write_text('history' * 100000)
            self.assertEqual(module.check(root), 0)
            (root / 'shared/resident.md').write_text('字' * 1500, encoding='utf-8')
            self.assertEqual(module.check(root), 1)

    def test_bootstrap_is_idempotent_and_keeps_user_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'AGENTS.md'
            output.write_text('User-owned prefix\n')
            cmd = [sys.executable, str(ROOT / 'scripts/install/_bootstrap.py'), str(output), '/nest', 'host', 'agent']
            subprocess.run(cmd, check=True, capture_output=True)
            once = output.read_text()
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertEqual(once, output.read_text())
            self.assertTrue(once.startswith('User-owned prefix'))
            hot = once.split('Read only these resident files', 1)[1].split('On demand:', 1)[0]
            self.assertNotIn('/memory.md', hot)
            self.assertNotIn('/strategy.md', hot)
            self.assertIn('/shared/resident.md', hot)
            self.assertIn('/agents/host/agent/resident.md', hot)
