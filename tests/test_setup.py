"""Exercise setup functions without installing packages or touching real HOME."""
import os
from pathlib import Path
import subprocess
import shutil
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
            (upstream / 'install.sh').write_text('echo "script will install nvidia-dkms, nvidia-utils, and nvidia-settings"\nif then\n')
            result = self.run_function(root, 'DOTFILES_DIR="$1"\nprepare_upstream_nvidia "$2"', REPO, upstream)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('syntax error', result.stderr)

    def test_patch_changes_only_known_nvidia_menu_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'home').mkdir()
            upstream = root / 'upstream'; (upstream / 'install-scripts').mkdir(parents=True)
            (upstream / 'install-scripts/nvidia.sh').write_text('nvidia_pkg=(\n  nvidia-dkms\n)\n')
            installer = upstream / 'install.sh'
            installer.write_text('# unrelated nvidia-dkms reference\necho "script will install nvidia-dkms, nvidia-utils, and nvidia-settings"\n')
            result = self.run_function(root, 'DOTFILES_DIR="$1"\nprepare_upstream_nvidia "$2"', REPO, upstream)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('# unrelated nvidia-dkms reference', installer.read_text())
            self.assertIn('script will install nvidia-open, nvidia-utils, and nvidia-settings', installer.read_text())

    def test_patch_stops_if_upstream_menu_has_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'home').mkdir()
            upstream = root / 'upstream'; (upstream / 'install-scripts').mkdir(parents=True)
            driver = upstream / 'install-scripts/nvidia.sh'
            driver.write_text('nvidia_pkg=(\n  nvidia-dkms\n)\n')
            (upstream / 'install.sh').write_text('echo "unknown nvidia-dkms usage"\n')
            result = self.run_function(root, 'DOTFILES_DIR="$1"\nprepare_upstream_nvidia "$2"', REPO, upstream)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('nvidia-dkms', driver.read_text())

    @unittest.skipUnless(shutil.which('stow'), 'GNU Stow missing')
    def test_fcitx5_runtime_files_stay_out_of_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); home = root / 'home'; home.mkdir()
            repo = root / 'repo'; source = repo / 'fcitx5/.config/fcitx5'; source.mkdir(parents=True)
            (source / 'profile').write_text('profile')
            result = self.run_function(root, 'DOTFILES_DIR="$1"\nSTOW_PACKAGES=(fcitx5)\nstow_configs', repo)
            self.assertEqual(result.returncode, 0, result.stderr)
            config = home / '.config/fcitx5'
            self.assertFalse(config.is_symlink())
            self.assertTrue((config / 'profile').is_symlink())
            (config / 'runtime.conf').write_text('runtime')
            self.assertFalse((source / 'runtime.conf').exists())

    @unittest.skipUnless(shutil.which('stow'), 'GNU Stow missing')
    def test_existing_folded_fcitx5_is_unfolded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); home = root / 'home'; (home / '.config').mkdir(parents=True)
            repo = root / 'repo'; source = repo / 'fcitx5/.config/fcitx5'; source.mkdir(parents=True)
            (source / 'profile').write_text('profile')
            subprocess.run(['stow', '-d', str(repo), '-t', str(home), 'fcitx5'], check=True)
            config = home / '.config/fcitx5'
            self.assertTrue(config.is_symlink())
            result = self.run_function(root, 'DOTFILES_DIR="$1"\nSTOW_PACKAGES=(fcitx5)\nstow_configs', repo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(config.is_symlink())
            self.assertTrue((config / 'profile').is_symlink())
            (config / 'runtime.conf').write_text('runtime')
            self.assertFalse((source / 'runtime.conf').exists())


if __name__ == '__main__':
    unittest.main()
