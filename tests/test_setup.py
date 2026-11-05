"""Exercise setup functions without installing packages or touching real HOME."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SOURCE = (REPO / 'setup.sh').read_text().rsplit('main "$@"', 1)[0]


class SetupTests(unittest.TestCase):
    def run_function(self, root, tail, *args):
        script = root / 'test-setup.sh'
        script.write_text(SOURCE + '\n' + tail + '\n')
        return subprocess.run(['bash', str(script), *map(str, args)],
                              env={**os.environ, 'HOME': str(root / 'home')},
                              capture_output=True, text=True)

    def test_symlink_parent_rejected_before_moving_userconfigs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); home = root / 'home'; home.mkdir()
            config = root / 'real-config'; (config / 'hypr/UserConfigs').mkdir(parents=True)
            original = config / 'hypr/UserConfigs/test.conf'; original.write_text('keep')
            (home / '.config').symlink_to(config)
            result = self.run_function(root, 'stow_configs')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(original.read_text(), 'keep')
            self.assertEqual(list(home.glob('.dotfiles-backup.*')), [])

    def test_upstream_installer_syntax_is_also_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'home').mkdir()
            upstream = root / 'upstream'; (upstream / 'install-scripts').mkdir(parents=True)
            (upstream / 'install-scripts/nvidia.sh').write_text('nvidia_pkg=(\n  nvidia-dkms\n)\n')
            (upstream / 'install.sh').write_text('if then\n')
            result = self.run_function(root, 'DOTFILES_DIR="$1"\nprepare_upstream_nvidia "$2"', REPO, upstream)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('syntax error', result.stderr)


if __name__ == '__main__':
    unittest.main()
