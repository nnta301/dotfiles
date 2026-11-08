import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/cleanup.sh'
STUBS = {'pacman': 'exit 1', 'sudo': 'exit 0', 'paccache': 'exit 0', 'journalctl': 'exit 0',
         'flatpak': 'echo "flatpak $*" >> "$HOME/calls"'}


class CleanupTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name) / 'home'
        self.bin = Path(tmp.name) / 'bin'
        self.bin.mkdir()
        for name, body in STUBS.items():
            self.stub(name, body)
        self.stub('pgrep', 'exit 1')
        self.files = ['.cache/google-chrome/data', '.config/Code/CachedData/data', '.config/discord/Cache/data',
                      '.npm/data', '.m2/repository/lib.jar']
        self.kept = ['.cache/cliphist/db', '.config/Code/User/workspaceStorage/state', '.m2/settings.xml']
        for name in self.files + self.kept:
            (self.home / name).parent.mkdir(parents=True, exist_ok=True)
            (self.home / name).write_text('x')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/sh\n' + body + '\n')
        path.chmod(0o755)

    def run_cleanup(self, *args, answer='y'):
        env = {k: v for k, v in os.environ.items() if not k.startswith('XDG_')}
        env.update(HOME=str(self.home), PATH=f"{self.bin}:{os.environ['PATH']}")
        return subprocess.run(['bash', str(SCRIPT), *args], input=(answer + '\n') * 30, text=True,
                              capture_output=True, env=env)

    def exists(self):
        return [name for name in self.files if (self.home / name).exists()]

    def test_confirmed_cleanup_empties_caches_but_keeps_user_state(self):
        result = self.run_cleanup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.exists(), [])
        self.assertTrue((self.home / '.npm').is_dir())
        for name in self.kept:
            self.assertTrue((self.home / name).exists(), name)
        self.assertIn('flatpak uninstall --unused', (self.home / 'calls').read_text())

    def test_dry_run_and_refusal_delete_nothing(self):
        for args, answer in ((['--dry-run'], 'y'), ([], 'n')):
            with self.subTest(args=args):
                self.assertEqual(self.run_cleanup(*args, answer=answer).returncode, 0)
                self.assertEqual(self.exists(), self.files)
                self.assertFalse((self.home / 'calls').exists())

    def test_running_app_cache_is_skipped(self):
        self.stub('pgrep', 'for last; do :; done; [ "$last" = chrome ]')
        self.run_cleanup()
        self.assertEqual(self.exists(), ['.cache/google-chrome/data'])

    def test_symlinked_cache_is_not_followed(self):
        outside = self.home.parent / 'outside'
        outside.mkdir()
        (outside / 'keep').write_text('x')
        target = self.home / '.cache/pip'
        target.symlink_to(outside)
        self.run_cleanup()
        self.assertTrue((outside / 'keep').exists())


if __name__ == '__main__':
    unittest.main()
