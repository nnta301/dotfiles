import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

ZSHRC = Path(__file__).resolve().parents[1] / 'zsh/.zshrc'


@unittest.skipUnless(shutil.which('zsh'), 'zsh missing')
class LauncherTests(unittest.TestCase):
    def test_launcher_passes_arguments_even_over_an_old_alias(self):
        launchers = ZSHRC.read_text().split('# ── App Launchers', 1)[1].split('\n', 1)[1]
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); output = directory / 'args'
            stub = directory / 'idea'
            stub.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > "{output}.tmp"\nmv "{output}.tmp" "{output}"\n')
            stub.chmod(0o755)
            script = directory / 'launchers.zsh'
            script.write_text(launchers)
            # An alias already in the shell must not break re-sourcing.
            subprocess.run(['zsh', '-fc', f"setopt aliases; alias idea='(idea &)'; source {script}; unalias idea; idea . --flag"],
                           check=True, env={**os.environ, 'PATH': f"{directory}:{os.environ['PATH']}"})
            deadline = time.monotonic() + 5
            while not output.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertEqual(output.read_text().split(), ['.', '--flag'])


if __name__ == '__main__':
    unittest.main()
