"""Run with python3 -m unittest discover -s tests -v. Uses temporary homes only."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import subprocess
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("transfer", Path(__file__).resolve().parents[1] / "scripts/transfer.py")
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.source = self.root / "backup"
        self.source.mkdir()

    def archive(self, entries):
        archive = self.source / "home.tar"
        with tarfile.open(archive, "w") as tar:
            for name, data in entries:
                member = tarfile.TarInfo(name)
                member.size = len(data)
                member.mode = 0o600
                tar.addfile(member, io.BytesIO(data))
        (self.source / "manifest.json").write_text(json.dumps({"version": 1, "sha256": transfer.digest(archive)}))

    def restore(self, apply=False, include=None):
        args = argparse.Namespace(source=str(self.source), apply=apply, include=include)
        with contextlib.redirect_stdout(io.StringIO()):
            transfer.restore(args, self.home)

    def test_dry_run_and_conflict_backup_and_hidden_opt_in(self):
        self.archive([("Documents/work.txt", b"new"), (".ssh/key", b"private")])
        (self.home / "Documents").mkdir()
        target = self.home / "Documents/work.txt"
        target.write_text("old")
        self.restore()
        self.assertEqual(target.read_text(), "old")
        self.assertEqual(list(self.home.glob('.restore-backup-*')), [])
        self.restore(apply=True)
        self.assertEqual(target.read_text(), "new")
        self.assertFalse((self.home / ".ssh").exists())
        saved = next(self.home.glob('.restore-backup-*'))
        self.assertEqual((saved / "Documents/work.txt").read_text(), "old")
        self.restore(apply=True, include=[".ssh"])
        self.assertEqual((self.home / ".ssh/key").read_text(), "private")

    def test_corruption_rejected_without_writes(self):
        self.archive([("Documents/work.txt", b"new")])
        with (self.source / "home.tar").open("ab") as f:
            f.write(b"corruption")
        with self.assertRaises(ValueError):
            self.restore(apply=True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_traversal_rejected(self):
        self.archive([("../outside", b"bad")])
        with self.assertRaises(ValueError):
            self.restore(apply=True)
        self.assertFalse((self.root / "outside").exists())

    def test_symlink_parent_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.home / "Documents").symlink_to(outside)
        self.archive([("Documents/work.txt", b"bad")])
        with self.assertRaises(ValueError):
            self.restore(apply=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_archive_symlink_is_not_restored(self):
        archive = self.source / 'home.tar'
        with tarfile.open(archive, 'w') as tar:
            member = tarfile.TarInfo('Documents/link')
            member.type = tarfile.SYMTYPE
            member.linkname = '/tmp/do-not-follow'
            tar.addfile(member)
        (self.source / 'manifest.json').write_text(json.dumps({'version': 1, 'sha256': transfer.digest(archive)}))
        self.restore(apply=True)
        self.assertFalse((self.home / 'Documents/link').is_symlink())

    def test_dry_run_displays_symlink_target(self):
        archive = self.source / 'home.tar'
        with tarfile.open(archive, 'w') as tar:
            member = tarfile.TarInfo('Documents/link')
            member.type = tarfile.SYMTYPE
            member.linkname = '../other'
            tar.addfile(member)
        (self.source / 'manifest.json').write_text(json.dumps({'version': 1, 'sha256': transfer.digest(archive)}))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            transfer.restore(argparse.Namespace(source=str(self.source), apply=False, include=None), self.home)
        self.assertIn("'Documents/link' -> '../other'", output.getvalue())
        self.assertFalse((self.home / 'Documents').exists())

    def test_missing_selection_rejected(self):
        self.archive([('Documents/a', b'hello')])
        with self.assertRaises(ValueError):
            self.restore(apply=True, include=['.ssh'])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_missing_intermediate_directories_are_private(self):
        self.archive([('private/nested/key', b'secret')])
        previous = os.umask(0o022)
        try:
            self.restore(apply=True)
        finally:
            os.umask(previous)
        for name in ('private', 'private/nested'):
            self.assertEqual((self.home / name).stat().st_mode & 0o777, 0o700)

    def test_failed_download_preserves_existing_target(self):
        self.archive([('Documents/work.txt', b'new')])
        (self.home / 'Documents').mkdir()
        target = self.home / 'Documents/work.txt'; target.write_text('old')
        with tarfile.open(self.source / 'home.tar') as tar:
            with mock.patch.object(tar, 'extractfile', side_effect=OSError('network failed')):
                with self.assertRaises(OSError):
                    transfer.restore_tar(argparse.Namespace(apply=True, include=None), self.home, tar)
        self.assertEqual(target.read_text(), 'old')
        self.assertEqual(list(self.home.rglob('.restore-file-*')), [])

    def test_insufficient_space_does_not_touch_home(self):
        self.archive([('Documents/work.txt', b'new')])
        with mock.patch.object(transfer.shutil, 'disk_usage', return_value=argparse.Namespace(free=1)):
            with self.assertRaises(ValueError):
                self.restore(apply=True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_restore_keeps_archive_order(self):
        self.archive([('deep/folder/a', b'a'), ('shallow', b'b')])
        with tarfile.open(self.source / 'home.tar') as tar:
            original = tar.extractfile
            visited = []
            def extract(member):
                visited.append(member.name)
                return original(member)
            with mock.patch.object(tar, 'extractfile', side_effect=extract):
                transfer.restore_tar(argparse.Namespace(apply=True, include=None), self.home, tar)
        self.assertEqual(visited, ['deep/folder/a', 'shallow'])

    def test_default_paths_include_custom_directories(self):
        for name in ['Code', '.config', '.cache', '.restore-backup-old']:
            (self.home / name).mkdir()
        self.assertEqual(set(transfer.default_paths(self.home)), {'Code', '.config'})

    def test_auxiliary_archive_corruption_rejected(self):
        self.archive([('Documents/a', b'hello')])
        extra = self.source / 'efi.tar'
        extra.write_bytes(b'original')
        path = self.source / 'manifest.json'
        manifest = json.loads(path.read_text())
        manifest['checksums'] = {'efi.tar': transfer.digest(extra)}
        path.write_text(json.dumps(manifest))
        extra.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.restore(apply=True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_system_backup_archives_expected_sources(self):
        def run(cmd, **kwargs):
            output = ''
            code = 0
            if cmd[0] == 'findmnt':
                output = 'vfat\n' if cmd[-1] == '/boot' else ''
                code = 0 if cmd[-1] == '/boot' else 1
            return subprocess.CompletedProcess(cmd, code, output, '')
        with mock.patch.object(transfer.subprocess, 'run', side_effect=run), \
             mock.patch.object(transfer.subprocess, 'check_output', return_value='test-head\n'), \
             mock.patch.object(transfer.shutil, 'which', return_value='/usr/bin/mock'):
            archive = mock.Mock()
            warnings = transfer.prepare_system_backup(self.source, self.root, archive)
        self.assertEqual([call.args[1].name for call in archive.call_args_list], ['repo.tar', 'etc.tar', 'efi.tar'])
        self.assertEqual(archive.call_args_list[-1].args[0], Path('/boot'))
        self.assertTrue(warnings)
        self.assertTrue((self.source / 'reports/git-status.txt').exists())

    def test_system_backup_rejects_ambiguous_esp(self):
        with mock.patch.object(transfer.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'vfat\n', '')), \
             mock.patch.object(transfer.subprocess, 'check_output', return_value='head\n'), \
             mock.patch.object(transfer.shutil, 'which', return_value='/usr/bin/mock'):
            archive = mock.Mock()
            with self.assertRaises(ValueError):
                transfer.prepare_system_backup(self.source, self.root, archive)
        self.assertEqual(archive.call_count, 2)



if __name__ == '__main__':
    unittest.main()
