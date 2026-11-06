#!/usr/bin/env python3
"""Chunked encrypted OneDrive backup via a dedicated rclone crypt remote."""
import argparse
import configparser
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

import transfer

CHUNK = 64 * 1024 * 1024


def remote_info(remote):
    if not re.fullmatch(r'[A-Za-z0-9_-]+:[A-Za-z0-9_/-]*', remote) or '..' in remote:
        raise ValueError('Dùng remote rclone dạng archbackup: hoặc archbackup:arch-<id>.')
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(subprocess.check_output(['rclone', 'config', 'redacted'], text=True))
    name = remote.split(':', 1)[0]
    if name not in config or config[name].get('type') != 'crypt':
        raise ValueError('Cần remote crypt đã cấu hình. Xem docs/backup-restore.md; không upload bản rõ.')
    # Reject unsafe crypt configuration even if it would otherwise look like a
    # valid OneDrive remote. Explicit CLI flags below also prevent environment
    # overrides from disabling encryption during an upload/download.
    try:
        unsafe_config = config[name].getboolean('no_data_encryption', fallback=False)
    except ValueError as exc:
        raise ValueError('Giá trị no_data_encryption không hợp lệ.') from exc
    env_names = ('RCLONE_CRYPT_NO_DATA_ENCRYPTION',
                 'RCLONE_CONFIG_' + re.sub(r'[^A-Z0-9]', '_', name.upper()) + '_NO_DATA_ENCRYPTION')
    for env_name in env_names:
        value = os.environ.get(env_name, '').strip().lower()
        if value and value not in ('false', '0'):
            raise ValueError(f'{env_name} phải tắt; không gửi dữ liệu bản rõ.')
    if unsafe_config:
        raise ValueError('Remote crypt đã tắt mã hóa nội dung; không sử dụng backup này.')
    underlying = config[name].get('remote', '')
    drive = underlying.split(':', 1)[0]
    if ':' not in underlying or drive not in config or config[drive].get('type') != 'onedrive':
        raise ValueError('Remote crypt phải trỏ trực tiếp đến thư mục riêng trên OneDrive.')
    return drive + ':', underlying.split(':', 1)[1].strip('/')


# Backoff applies after each failed attempt; rclone may also retry internally.
RETRY_DELAYS = (30, 120, 300)


def retry_transfer(operation, label):
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            return operation()
        except (FileNotFoundError, PermissionError):
            raise
        except (subprocess.CalledProcessError, OSError) as exc:
            if attempt == len(RETRY_DELAYS):
                raise
            delay = RETRY_DELAYS[attempt]
            print(f'{label} thất bại ({type(exc).__name__}); thử lại sau {delay} giây '
                  f'({attempt + 1}/{len(RETRY_DELAYS)}). Ctrl+C để dừng.', file=sys.stderr, flush=True)
            time.sleep(delay)


def download(remote):
    # Bound output even if the remote object is corrupt. Retry command/network
    # failures only; validation failures must not be mistaken for success.
    data = retry_transfer(
        lambda: subprocess.check_output(['rclone', '--crypt-no-data-encryption=false', 'cat', remote, '--count', str(CHUNK + 1)]),
        f'Tải {remote}')
    if len(data) > CHUNK:
        raise ValueError(f'Đối tượng cloud vượt giới hạn {CHUNK} byte: {remote}')
    return data


def upload_verified(remote, data):
    # Retry upload and read-back separately, avoiding nested network retries.
    # A checksum mismatch starts a new upload; it never publishes success.
    for attempt in range(len(RETRY_DELAYS) + 1):
        retry_transfer(
            lambda: subprocess.run(['rclone', '--crypt-no-data-encryption=false', 'rcat', remote, '--size', str(len(data))], input=data, check=True),
            f'Upload {remote}')
        received = download(remote)
        if hashlib.sha256(received).digest() == hashlib.sha256(data).digest():
            return
        if attempt == len(RETRY_DELAYS):
            raise ValueError(f'Đọc lại từ OneDrive không khớp: {remote}')
        delay = RETRY_DELAYS[attempt]
        print(f'Checksum upload không khớp; thử lại sau {delay} giây ({attempt + 1}/{len(RETRY_DELAYS)}).', file=sys.stderr, flush=True)
        time.sleep(delay)


class ChunkWriter:
    def __init__(self, remote, name, limit=CHUNK):
        self.remote, self.name, self.limit = remote, name, limit
        self.buffer = bytearray()
        self.parts = []
        self.sha = hashlib.sha256()
        self.size = 0

    def write(self, data):
        self.sha.update(data)
        self.size += len(data)
        view = memoryview(data)
        while view:
            count = min(len(view), self.limit - len(self.buffer))
            self.buffer.extend(view[:count])
            view = view[count:]
            if len(self.buffer) == self.limit:
                self.flush_part()
        return len(data)

    def flush_part(self):
        if not self.buffer:
            return
        name = f'{self.name}.part{len(self.parts):06d}'
        data = bytes(self.buffer)
        upload_verified(self.remote + '/' + name, data)
        self.parts.append({'name': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        self.buffer.clear()
        print(f'Đã upload và đọc lại: {name}', flush=True)

    def finish(self):
        self.flush_part()
        return {'parts': self.parts, 'size': self.size, 'sha256': self.sha.hexdigest()}


class ChunkReader(io.RawIOBase):
    """Seekable view of immutable parts, with one verified chunk cached in RAM."""
    def __init__(self, remote, description):
        super().__init__()
        self.remote, self.description = remote, description
        self.pos, self.cache_index, self.cache = 0, -1, b''
        self.offsets = []
        total = 0
        seen = set()
        if not isinstance(description, dict) or not isinstance(description.get('parts'), list):
            raise ValueError('Mô tả archive không hợp lệ.')
        if not re.fullmatch(r'[0-9a-f]{64}', description.get('sha256', '')):
            raise ValueError('Checksum archive không hợp lệ.')
        for part in description['parts']:
            if part['name'] in seen or not re.fullmatch(r'[0-9a-f]{64}', part.get('sha256', '')):
                raise ValueError('Chunk trùng tên hoặc checksum không hợp lệ.')
            seen.add(part['name'])
            if not re.fullmatch(r'[A-Za-z0-9_.-]+\.part[0-9]{6}', part['name']):
                raise ValueError('Tên chunk không hợp lệ.')
            if not isinstance(part['size'], int) or not 0 < part['size'] <= CHUNK:
                raise ValueError('Kích thước chunk không hợp lệ.')
            self.offsets.append(total)
            total += part['size']
        if total != description['size']:
            raise ValueError('Tổng kích thước chunk sai.')
        self.size = total

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        if whence not in (0, 1, 2):
            raise ValueError('whence không hợp lệ.')
        pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        if pos < 0:
            raise ValueError('Seek âm.')
        self.pos = pos
        return pos

    def read(self, size=-1):
        import bisect
        remaining = max(0, self.size - self.pos)
        size = remaining if size < 0 else min(size, remaining)
        result = bytearray()
        while size:
            index = bisect.bisect_right(self.offsets, self.pos) - 1
            part = self.description['parts'][index]
            if index != self.cache_index:
                data = download(self.remote + '/' + part['name'])
                if len(data) != part['size'] or hashlib.sha256(data).hexdigest() != part['sha256']:
                    raise ValueError(f'Chunk sai checksum: {part["name"]}')
                self.cache_index, self.cache = index, data
            start = self.pos - self.offsets[index]
            count = min(size, len(self.cache) - start)
            result.extend(self.cache[start:start + count])
            size -= count
            self.pos += count
        return bytes(result)

    def verify(self):
        self.seek(0)
        sha = hashlib.sha256()
        while data := self.read(1024 * 1024):
            sha.update(data)
        if sha.hexdigest() != self.description['sha256']:
            raise ValueError('Checksum archive sai.')
        self.seek(0)


def stream_system_archive(source, privileged, remote, name):
    prefix = ['sudo'] if privileged else []
    writer = ChunkWriter(remote, name)
    process = subprocess.Popen(prefix + ['tar', '--acls', '--xattrs', '-cpf', '-', '-C', str(source), '.'], stdout=subprocess.PIPE)
    try:
        while data := process.stdout.read(1024 * 1024):
            writer.write(data)
        if process.wait():
            raise ValueError(f'tar thất bại: {source}')
    finally:
        process.stdout.close()
        if process.poll() is None:
            process.terminate()
            process.wait()
    description = writer.finish()
    # Compare remote bytes with the still-existing source. No full local archive.
    reader = ChunkReader(remote, description)
    process = subprocess.Popen(prefix + ['tar', '--acls', '--xattrs', '-df', '-', '-C', str(source)], stdin=subprocess.PIPE)
    try:
        while data := reader.read(1024 * 1024):
            process.stdin.write(data)
        process.stdin.close()
        if process.wait():
            raise ValueError(f'Archive khác dữ liệu nguồn: {source}')
    finally:
        if not process.stdin.closed:
            process.stdin.close()
        if process.poll() is None:
            process.terminate()
            process.wait()
    return description


def sync_directory(home, override=None):
    if override:
        return Path(override).expanduser().absolute()
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config'))) / 'onedrive' / 'config'
    if config.is_file():
        values = re.findall(r'^\s*sync_dir\s*=\s*"([^"\n]+)"\s*(?:#.*)?$', config.read_text(), re.M)
        if len(values) > 1:
            raise ValueError('Có nhiều sync_dir; dùng --onedrive-dir để chỉ rõ thư mục sync.')
        if values:
            value = values[0]
            if value == '~' or value.startswith('~/'):
                return home / value[2:] if value != '~' else home
            path = Path(value)
            if not path.is_absolute():
                raise ValueError('sync_dir không phải đường dẫn tuyệt đối; dùng --onedrive-dir.')
            return path
    return home / 'OneDrive'


def home_entries(home, selected, exclusions, skipped):
    def visit(path, name):
        if any(transfer.inside(path, excluded) for excluded in exclusions):
            skipped.append(name)
            return
        info = path.lstat()
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)):
            skipped.append(name)
            return
        if stat.S_ISDIR(info.st_mode) and info.st_dev != home.stat().st_dev:
            skipped.append(name)
            return
        yield path, name, info
        if stat.S_ISDIR(info.st_mode):
            for child in sorted(path.iterdir()):
                yield from visit(child, name + '/' + child.name)
    for name in selected:
        yield from visit(home / name, name)


def backup(args, home):
    drive, cloud_folder = remote_info(args.remote)
    if not cloud_folder:
        raise ValueError('Crypt phải trỏ tới thư mục riêng như onedrive:ArchBackups, không phải gốc drive.')
    remote = args.remote.rstrip('/') + ('' if args.remote.endswith(':') else '/') + 'arch-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]
    transfer.relative(cloud_folder)
    sync_dir = sync_directory(home, getattr(args, 'onedrive_dir', None))
    exclusions = [home / '.cache', sync_dir / cloud_folder]
    names = transfer.roots(args.include or transfer.default_paths(home))
    for name in names:
        transfer.check_parents(home, name)
    selected = [n for n in names if os.path.lexists(home / n)]
    if args.include and len(selected) != len(names):
        raise ValueError('Đường dẫn --include không tồn tại: ' + ', '.join(n for n in names if n not in selected))
    if not selected:
        raise ValueError('Không có dữ liệu được chọn.')
    # Conservative plain-size estimate; tar/encryption and duplicated repo need headroom.
    estimate = 0
    included_roots = set()
    for _, name, info in home_entries(home, selected, exclusions, []):
        if name in selected:
            included_roots.add(name)
        estimate += info.st_size + 4096 if stat.S_ISREG(info.st_mode) else 4096
    if args.include and len(included_roots) != len(selected):
        raise ValueError('Đường dẫn --include bị loại khỏi backup: ' + ', '.join(n for n in selected if n not in included_roots))
    if not estimate:
        raise ValueError('Các đường dẫn được chọn đều bị loại khỏi backup; chưa upload.')
    quota = json.loads(subprocess.check_output(['rclone', 'about', drive, '--json'], text=True))
    if 'free' not in quota:
        raise ValueError('Không đọc được dung lượng OneDrive còn trống.')
    if quota['free'] < estimate + 2 * 1024**3:
        raise ValueError('OneDrive không đủ dung lượng ước tính cộng 2 GiB dự phòng; chưa upload.')
    print(f'Home ước tính {estimate / 1024**3:.1f} GiB; OneDrive trống {quota["free"] / 1024**3:.1f} GiB.')
    print('Đích mã hóa:', remote, flush=True)
    print('Phải giữ mật khẩu crypt + salt và thông tin remote ngoài máy trước khi format.', flush=True)
    archives, skipped, links = {}, [], []
    paused = False
    # Force scratch into excluded .cache rather than user TMPDIR or OneDrive.
    cache = home / '.cache' / 'dotfiles-backup'
    if cache.is_symlink() or (home / '.cache').is_symlink():
        raise ValueError('Cache backup không được là symlink.')
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        paused = transfer.pause_onedrive()
        with tempfile.TemporaryDirectory(prefix='cloud-', dir=cache) as scratch:
            out = Path(scratch)
            def system_archive(source, target, privileged=False):
                archives[target.name] = stream_system_archive(source, privileged, remote, target.name)
            warnings = transfer.prepare_system_backup(out, Path(__file__).resolve().parents[1], archive_func=system_archive)
            warnings = [w.replace('Archive không mã hóa.', 'Cloud được mã hóa bằng rclone crypt.') for w in warnings]
            writer = ChunkWriter(remote, 'home.tar')
            with tarfile.open(fileobj=writer, mode='w|', dereference=False) as tar:
                for path, name, before in home_entries(home, selected, exclusions, skipped):
                    if stat.S_ISLNK(before.st_mode):
                        links.append(name)
                    tar.add(path, arcname=name, recursive=False)
                    tar.inodes.clear()
                    after = path.lstat()
                    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                        raise ValueError(f'File thay đổi trong lúc đọc: {name}')
            archives['home.tar'] = writer.finish()
            warnings.append('Cache, filesystem con, symlink đích và bản cloud cũ không được sao lưu; xem skipped/symlinks.')
            (out / 'REPORT.txt').write_text('\n'.join(warnings) + '\n')
            # Pack reports and bundle in a small separate archive for rescue from live USB.
            archives['metadata.tar'] = stream_system_archive(out, False, remote, 'metadata.tar')
            manifest = {'version': 2, 'created': datetime.now(timezone.utc).isoformat(),
                        'archives': archives, 'paths': selected, 'skipped': skipped, 'symlinks': links,
                        'warnings': warnings}
            upload_verified(remote + '/manifest.json', (json.dumps(manifest, ensure_ascii=True, indent=2) + '\n').encode())
            print('BACKUP CLOUD ĐÃ UPLOAD VÀ ĐỌC LẠI ĐẦY ĐỦ:', remote)
            print('\n'.join(warnings))
    except BaseException:
        print('Backup cloud chưa hoàn tất; không dùng bản này để format:', remote, file=sys.stderr)
        raise
    finally:
        if paused:
            print('Đã dừng OneDrive sync trong phiên này.', flush=True)
        print('Service OneDrive có thể tự chạy khi đăng nhập/reboot nếu đang enable, kể cả khi trước backup nó chưa chạy. '
              'Loại thư mục backup khỏi sync trước khi khởi động lại; xem docs/backup-restore.md.', flush=True)


def restore(args, home):
    remote_info(args.source)
    remote = args.source.rstrip('/')
    manifest = json.loads(download(remote + '/manifest.json'))
    if manifest.get('version') != 2:
        raise ValueError('Manifest cloud không hợp lệ.')
    archives = manifest['archives']
    expected = {'home.tar', 'repo.tar', 'etc.tar', 'efi.tar', 'metadata.tar'}
    if set(archives) != expected:
        raise ValueError('Backup cloud thiếu archive bắt buộc.')
    if args.export_system:
        destination = Path(args.export_system).expanduser()
        if os.path.lexists(destination):
            raise ValueError(f'Thư mục export đã tồn tại: {destination}')
        parent = destination.parent
        while not parent.exists():
            parent = parent.parent
        readers = {name: ChunkReader(remote, archives[name]) for name in sorted(expected - {'home.tar'})}
        required = sum(reader.size for reader in readers.values())
        if shutil.disk_usage(parent).free < required + 64 * 1024 * 1024:
            raise ValueError('Không đủ dung lượng export archive và 64 MiB dự phòng; chưa tạo thư mục.')
        destination.mkdir(mode=0o700, parents=True, exist_ok=False)
        for name, reader in readers.items():
            temporary = destination / (name + '.partial')
            try:
                sha = hashlib.sha256()
                with temporary.open('xb') as output:
                    while data := reader.read(1024 * 1024):
                        output.write(data)
                        sha.update(data)
                    output.flush()
                    os.fsync(output.fileno())
                if sha.hexdigest() != reader.description['sha256']:
                    raise ValueError(f'Checksum archive sai: {name}')
                os.replace(temporary, destination / name)
            finally:
                temporary.unlink(missing_ok=True)
        print('Đã xuất archive hệ thống vào', destination, '— không tự áp vào hệ thống.')
        return
    # Verify every archive before any write to the target home.
    for name, description in archives.items():
        print('Kiểm tra từ cloud:', name, flush=True)
        ChunkReader(remote, description).verify()
    reader = ChunkReader(remote, archives['home.tar'])
    with tarfile.open(fileobj=reader, mode='r:') as tar:
        transfer.restore_tar(args, home, tar)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('backup')
    b.add_argument('--remote', default='archbackup:', help='Remote crypt trên OneDrive (mặc định archbackup:)')
    b.add_argument('--include', action='append', help='Thay phạm vi home bằng các đường dẫn tương đối đã chọn')
    b.add_argument('--onedrive-dir', help='Thư mục sync local nếu dùng cấu hình client riêng; dùng để bỏ bản cloud cũ')
    r = sub.add_parser('restore')
    r.add_argument('source', help='archbackup:arch-<id> hoặc thư mục backup local phiên bản cũ')
    r.add_argument('--include', action='append')
    g = r.add_mutually_exclusive_group()
    g.add_argument('--apply', action='store_true')
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--export-system', metavar='NEW_DIRECTORY', help='Chỉ tải archive hệ thống/repo vào thư mục mới')
    args = parser.parse_args()
    if os.geteuid() == 0 and not (args.command == 'restore' and args.export_system):
        parser.error('Chạy bằng user thường; script chỉ dùng sudo khi đọc hệ thống.')
    try:
        if args.command == 'backup':
            backup(args, Path.home().resolve())
        elif ':' not in args.source:
            if args.export_system:
                raise ValueError('--export-system dành cho backup cloud.')
            transfer.restore(args, Path.home().resolve())
        else:
            restore(args, Path.home().resolve())
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as exc:
        print('LỖI:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
