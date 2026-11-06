import argparse
import contextlib
import io
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import cloud_backup as cloud


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.remote = {}
        self.upload = mock.patch.object(cloud, 'upload_verified', side_effect=lambda path, data: self.remote.__setitem__(path, data))
        self.download = mock.patch.object(cloud, 'download', side_effect=lambda path: self.remote[path])
        self.upload.start(); self.download.start()
        self.addCleanup(self.upload.stop); self.addCleanup(self.download.stop)

    def packed(self, name, data):
        writer = cloud.ChunkWriter('test:backup', name, limit=1000)
        writer.write(data)
        return writer.finish()

    def tarbytes(self, name='Documents/test.txt', data=b'hello'):
        result = io.BytesIO()
        with tarfile.open(fileobj=result, mode='w') as tar:
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o600
            tar.addfile(info, io.BytesIO(data))
        return result.getvalue()

    def test_chunks_seek_and_verify(self):
        data = bytes(range(256)) * 100
        description = self.packed('home.tar', data)
        reader = cloud.ChunkReader('test:backup', description)
        reader.verify()
        reader.seek(998)
        self.assertEqual(reader.read(2000), data[998:2998])
        reader.seek(-20, 2)
        self.assertEqual(reader.read(), data[-20:])

    def test_corrupt_chunk_rejected(self):
        description = self.packed('home.tar', b'important')
        self.remote['test:backup/home.tar.part000000'] = b'corrupted'
        with self.assertRaises(ValueError):
            cloud.ChunkReader('test:backup', description).verify()

    def manifest(self, home_data):
        descriptions = {name: self.packed(name, home_data if name == 'home.tar' else b'reference')
                        for name in ['home.tar', 'etc.tar', 'efi.tar', 'repo.tar', 'metadata.tar']}
        self.remote['test:backup/manifest.json'] = json.dumps({'version': 2, 'archives': descriptions}).encode()

    def test_remote_dry_run_and_restore_no_full_local_archive(self):
        self.manifest(self.tarbytes())
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cloud, 'remote_info'):
            home = Path(tmp)
            args = argparse.Namespace(source='test:backup', export_system=None, apply=False, include=None)
            cloud.restore(args, home)
            self.assertEqual(list(home.iterdir()), [])
            args.apply = True
            cloud.restore(args, home)
            self.assertEqual((home / 'Documents/test.txt').read_bytes(), b'hello')
            self.assertFalse((home / 'home.tar').exists())

    def test_chunk_changed_after_verification_is_rejected(self):
        self.manifest(self.tarbytes())
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cloud, 'remote_info'):
            home = Path(tmp)
            destination = home / 'Documents/test.txt'
            destination.parent.mkdir()
            destination.write_bytes(b'old data')
            original = cloud.download
            reads = {}
            def changed_after_verify(path):
                data = original(path)
                if '/home.tar.part' in path:
                    reads[path] = reads.get(path, 0) + 1
                    if reads[path] > 1:
                        return bytes([data[0] ^ 1]) + data[1:]
                return data
            args = argparse.Namespace(source='test:backup', export_system=None, apply=True, include=None)
            with mock.patch.object(cloud, 'download', side_effect=changed_after_verify):
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    cloud.restore(args, home)
            self.assertEqual(destination.read_bytes(), b'old data')

    def test_export_only_system(self):
        self.manifest(self.tarbytes())
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cloud, 'remote_info'):
            destination = Path(tmp) / 'export'
            cloud.restore(argparse.Namespace(source='test:backup', export_system=str(destination)), Path(tmp))
            self.assertEqual({p.name for p in destination.iterdir()}, {'efi.tar', 'etc.tar', 'repo.tar', 'metadata.tar'})

    def test_remote_traversal_rejected_before_home_write(self):
        self.manifest(self.tarbytes('../outside'))
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cloud, 'remote_info'):
            args = argparse.Namespace(source='test:backup', export_system=None, apply=True, include=None)
            with self.assertRaises(ValueError):
                cloud.restore(args, Path(tmp))
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_duplicate_chunk_rejected(self):
        description = self.packed('home.tar', b'hello')
        description['parts'] *= 2
        description['size'] *= 2
        with self.assertRaises(ValueError):
            cloud.ChunkReader('test:backup', description)

    def test_custom_sync_folder_is_excluded_from_both_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp); config = home / '.config/onedrive'; config.mkdir(parents=True)
            (config / 'config').write_text('sync_dir = "~/Cloud"\n')
            (home / 'Cloud/ArchBackups').mkdir(parents=True)
            (home / 'Cloud/ArchBackups/old').write_text('previous cloud backup')
            (home / 'Cloud/document').write_text('keep me')
            with mock.patch.dict(os.environ, {'XDG_CONFIG_HOME': str(home / '.config')}):
                sync = cloud.sync_directory(home)
            self.assertEqual(sync, home / 'Cloud')
            skipped = []
            names = [name for _, name, _ in cloud.home_entries(home, ['Cloud'], [sync / 'ArchBackups'], skipped)]
            self.assertEqual(names, ['Cloud', 'Cloud/document'])
            self.assertEqual(skipped, ['Cloud/ArchBackups'])

    def test_missing_explicit_include_fails_before_upload(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cloud, 'remote_info', return_value=('drive:', 'ArchBackups')):
            with self.assertRaises(ValueError):
                cloud.backup(argparse.Namespace(remote='test:', include=['missing']), Path(tmp))
            self.assertEqual(self.remote, {})

    def test_plain_remote_refused(self):
        with mock.patch.object(cloud.subprocess, 'check_output', return_value='[test]\ntype = onedrive\n'):
            with self.assertRaises(ValueError):
                cloud.remote_info('test:')

    def test_crypt_remote_requires_onedrive(self):
        config = '[encrypted]\ntype = crypt\nremote = drive:ArchBackups\n[drive]\ntype = onedrive\n'
        with mock.patch.object(cloud.subprocess, 'check_output', return_value=config):
            self.assertEqual(cloud.remote_info('encrypted:'), ('drive:', 'ArchBackups'))

    def test_crypt_refuses_disabled_content_encryption(self):
        config = '[encrypted]\ntype = crypt\nremote = drive:ArchBackups\nno_data_encryption = true\n[drive]\ntype = onedrive\n'
        with mock.patch.object(cloud.subprocess, 'check_output', return_value=config):
            with self.assertRaises(ValueError):
                cloud.remote_info('encrypted:')
        config = config.replace('no_data_encryption = true\n', '')
        for key in ('RCLONE_CRYPT_NO_DATA_ENCRYPTION', 'RCLONE_CONFIG_ENCRYPTED_NO_DATA_ENCRYPTION'):
            with self.subTest(key=key), mock.patch.dict(os.environ, {key: 'true'}), \
                 mock.patch.object(cloud.subprocess, 'check_output', return_value=config):
                with self.assertRaises(ValueError):
                    cloud.remote_info('encrypted:')

    def test_excluded_explicit_selection_stops_before_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp); (home / '.cache').mkdir()
            (home / '.cache/important').write_text('data')
            with mock.patch.object(cloud, 'remote_info', return_value=('drive:', 'ArchBackups')):
                with self.assertRaisesRegex(ValueError, 'bị loại'):
                    cloud.backup(argparse.Namespace(remote='test:', include=['.cache']), home)
            self.assertEqual(self.remote, {})

    def test_mixed_selection_rejects_excluded_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp); (home / '.cache').mkdir(); (home / 'Documents').mkdir()
            with mock.patch.object(cloud, 'remote_info', return_value=('drive:', 'ArchBackups')):
                with self.assertRaisesRegex(ValueError, 'bị loại'):
                    cloud.backup(argparse.Namespace(remote='test:', include=['Documents', '.cache']), home)
            self.assertEqual(self.remote, {})

    def test_export_insufficient_space_does_not_create_destination(self):
        self.manifest(self.tarbytes())
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cloud, 'remote_info'), \
             mock.patch.object(cloud.shutil, 'disk_usage', return_value=argparse.Namespace(free=1)):
            destination = Path(tmp) / 'export'
            with self.assertRaises(ValueError):
                cloud.restore(argparse.Namespace(source='test:backup', export_system=str(destination)), Path(tmp))
            self.assertFalse(destination.exists())

    def test_export_failure_does_not_publish_partial_archive(self):
        self.manifest(self.tarbytes())
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cloud, 'remote_info'):
            destination = Path(tmp) / 'export'
            original = cloud.download
            def fail_chunk(path):
                if path.endswith('efi.tar.part000000'):
                    raise OSError('network failure')
                return original(path)
            with mock.patch.object(cloud, 'download', side_effect=fail_chunk):
                with self.assertRaises(OSError):
                    cloud.restore(argparse.Namespace(source='test:backup', export_system=str(destination)), Path(tmp))
            self.assertEqual(list(destination.iterdir()), [])

    def test_full_backup_streams_home_and_publishes_manifest_last(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp); documents = home / 'Documents'; documents.mkdir()
            (documents / 'hello').write_text('valuable')
            def prepare(out, repo, archive_func):
                for name in ['repo.tar', 'etc.tar', 'efi.tar']:
                    archive_func(documents, out / name)
                (out / 'dotfiles.bundle').write_bytes(b'fake bundle')
                return ['test warning']
            args = argparse.Namespace(remote='test:', include=None)
            with mock.patch.object(cloud, 'remote_info', return_value=('drive:', 'ArchBackups')), \
                 mock.patch.object(cloud.subprocess, 'check_output', return_value=json.dumps({'free': 10 * 1024**3})), \
                 mock.patch.object(cloud.transfer, 'pause_onedrive', return_value=False), \
                 mock.patch.object(cloud.transfer, 'prepare_system_backup', side_effect=prepare):
                cloud.backup(args, home)
            manifest_path = list(self.remote)[-1]
            self.assertTrue(manifest_path.endswith('/manifest.json'))
            manifest = json.loads(self.remote[manifest_path])
            self.assertEqual(set(manifest['archives']), {'home.tar', 'efi.tar', 'etc.tar', 'repo.tar', 'metadata.tar'})
            reader = cloud.ChunkReader(manifest_path.rsplit('/', 1)[0], manifest['archives']['home.tar'])
            with tarfile.open(fileobj=reader, mode='r:') as tar:
                self.assertEqual(tar.extractfile('Documents/hello').read(), b'valuable')
            self.assertEqual(list(home.rglob('home.tar')), [])

    @unittest.skipUnless(os.name == 'posix', 'requires non-UTF-8 POSIX filename')
    def test_non_utf8_name_roundtrip_and_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'source'; home.mkdir()
            raw_path = os.fsencode(home) + b'/name-\xff'
            with open(raw_path, 'wb') as output:
                output.write(b'valuable')
            def prepare(out, repo, archive_func):
                for name in ['repo.tar', 'etc.tar', 'efi.tar']:
                    archive_func(home, out / name)
                return []
            args = argparse.Namespace(remote='test:', include=None)
            with mock.patch.object(cloud, 'remote_info', return_value=('drive:', 'ArchBackups')), \
                 mock.patch.object(cloud.subprocess, 'check_output', return_value=json.dumps({'free': 10 * 1024**3})), \
                 mock.patch.object(cloud.transfer, 'pause_onedrive', return_value=False), \
                 mock.patch.object(cloud.transfer, 'prepare_system_backup', side_effect=prepare):
                cloud.backup(args, home)
            manifest_path = next(name for name in self.remote if name.endswith('/manifest.json'))
            manifest = json.loads(self.remote[manifest_path].decode('utf-8'))
            self.assertEqual(os.fsencode(manifest['paths'][0]), b'name-\xff')
            target = Path(tmp) / 'target'; target.mkdir()
            output = io.TextIOWrapper(io.BytesIO(), encoding='utf-8', errors='strict')
            with mock.patch.object(cloud, 'remote_info'), contextlib.redirect_stdout(output):
                cloud.restore(argparse.Namespace(source=manifest_path.rsplit('/', 1)[0], export_system=None, apply=False, include=None), target)
            self.assertEqual(list(target.iterdir()), [])
            with mock.patch.object(cloud, 'remote_info'), contextlib.redirect_stdout(output):
                cloud.restore(argparse.Namespace(source=manifest_path.rsplit('/', 1)[0], export_system=None, apply=True, include=None), target)
            with open(os.fsencode(target) + b'/name-\xff', 'rb') as restored:
                self.assertEqual(restored.read(), b'valuable')

    def test_warns_sync_may_restart_when_initially_inactive(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp); (home / 'data').write_text('test')
            output = io.StringIO()
            with mock.patch.object(cloud, 'remote_info', return_value=('drive:', 'ArchBackups')), \
                 mock.patch.object(cloud.subprocess, 'check_output', return_value=json.dumps({'free': 10 * 1024**3})), \
                 mock.patch.object(cloud.transfer, 'pause_onedrive', return_value=False), \
                 mock.patch.object(cloud.transfer, 'prepare_system_backup', side_effect=ValueError('stop')), \
                 contextlib.redirect_stdout(output):
                with self.assertRaises(ValueError):
                    cloud.backup(argparse.Namespace(remote='test:', include=None), home)
            self.assertIn('có thể tự chạy', output.getvalue())

    def test_upload_failure_does_not_publish_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp); (home / 'data').write_text('important')
            with mock.patch.object(cloud, 'remote_info', return_value=('drive:', 'ArchBackups')), \
                 mock.patch.object(cloud.subprocess, 'check_output', return_value=json.dumps({'free': 10 * 1024**3})), \
                 mock.patch.object(cloud.transfer, 'pause_onedrive', return_value=False), \
                 mock.patch.object(cloud.transfer, 'prepare_system_backup', side_effect=ValueError('failed archive')):
                with self.assertRaises(ValueError):
                    cloud.backup(argparse.Namespace(remote='test:', include=None), home)
            self.assertFalse(any(name.endswith('/manifest.json') for name in self.remote))

    def test_real_rclone_crypt_local_roundtrip(self):
        if not shutil.which('rclone'):
            self.skipTest('rclone missing')
        # Restore real upload/download only for an isolated local crypt remote.
        self.upload.stop(); self.download.stop()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            encrypted = directory / 'encrypted'; encrypted.mkdir()
            with mock.patch.dict(os.environ, {'RCLONE_CONFIG': str(directory / 'rclone.conf')}):
                subprocess.run(['rclone', 'config', 'create', 'localtest', 'crypt',
                                'remote', str(encrypted), 'password', 'test-only-password', '--obscure'],
                               check=True, capture_output=True)
                # Even a process environment override must not disable data encryption.
                with mock.patch.dict(os.environ, {'RCLONE_CRYPT_NO_DATA_ENCRYPTION': 'true'}):
                    cloud.upload_verified('localtest:payload', b'private test data')
                    self.assertEqual(cloud.download('localtest:payload'), b'private test data')
                blobs = [p.read_bytes() for p in encrypted.iterdir() if p.is_file()]
                self.assertTrue(blobs)
                self.assertNotIn(b'private test data', blobs)

    def test_stream_system_tar_real_subprocess_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp); (source / 'file').write_text('payload')
            description = cloud.stream_system_archive(source, False, 'test:backup', 'repo.tar')
            reader = cloud.ChunkReader('test:backup', description)
            reader.verify()
            with tarfile.open(fileobj=reader, mode='r:') as tar:
                self.assertEqual(tar.extractfile('./file').read(), b'payload')


class UploadRetryTests(unittest.TestCase):
    def test_download_retries_transient_errors(self):
        error = subprocess.CalledProcessError(1, ['rclone'])
        with mock.patch.object(cloud.subprocess, 'check_output', side_effect=[error, b'data']) as fetch, \
             mock.patch.object(cloud.time, 'sleep') as sleep:
            self.assertEqual(cloud.download('test:part'), b'data')
        self.assertEqual(fetch.call_count, 2)
        sleep.assert_called_once_with(30)

    def test_missing_rclone_fails_without_wait(self):
        with mock.patch.object(cloud.subprocess, 'check_output', side_effect=FileNotFoundError('rclone')), \
             mock.patch.object(cloud.time, 'sleep') as sleep:
            with self.assertRaises(FileNotFoundError):
                cloud.download('test:part')
        sleep.assert_not_called()

    def test_missing_manifest_fails_without_backoff(self):
        for code in (3, 4):
            with self.subTest(code=code), \
                 mock.patch.object(cloud.subprocess, 'check_output', side_effect=subprocess.CalledProcessError(code, ['rclone'])) as fetch, \
                 mock.patch.object(cloud.time, 'sleep') as sleep:
                with self.assertRaises(subprocess.CalledProcessError):
                    cloud.download('test:backup/manifest.json')
                self.assertEqual(fetch.call_count, 1)
                sleep.assert_not_called()

    def test_missing_chunk_still_retries_for_eventual_visibility(self):
        error = subprocess.CalledProcessError(3, ['rclone'])
        with mock.patch.object(cloud.subprocess, 'check_output', side_effect=[error, b'data']) as fetch, \
             mock.patch.object(cloud.time, 'sleep') as sleep:
            self.assertEqual(cloud.download('test:backup/home.tar.part000000'), b'data')
        self.assertEqual(fetch.call_count, 2)
        sleep.assert_called_once_with(30)

    def test_download_exhausts_retries(self):
        error = subprocess.CalledProcessError(1, ['rclone'])
        with mock.patch.object(cloud.subprocess, 'check_output', side_effect=error) as fetch, \
             mock.patch.object(cloud.time, 'sleep') as sleep:
            with self.assertRaises(subprocess.CalledProcessError):
                cloud.download('test:part')
        self.assertEqual(fetch.call_count, 4)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [30, 120, 300])

    def test_retry_after_failed_transfer(self):
        error = subprocess.CalledProcessError(1, ['rclone'])
        with mock.patch.object(cloud.subprocess, 'run', side_effect=[error, None]) as run, \
             mock.patch.object(cloud, 'download', return_value=b'data'), \
             mock.patch.object(cloud.time, 'sleep'):
            cloud.upload_verified('test:part', b'data')
        self.assertEqual(run.call_count, 2)

    def test_persistent_checksum_mismatch_fails(self):
        with mock.patch.object(cloud.subprocess, 'run') as run, \
             mock.patch.object(cloud, 'download', return_value=b'wrong'), \
             mock.patch.object(cloud.time, 'sleep'):
            with self.assertRaises(ValueError):
                cloud.upload_verified('test:part', b'data')
        self.assertEqual(run.call_count, 4)


if __name__ == '__main__':
    unittest.main()
