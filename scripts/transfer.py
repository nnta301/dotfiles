#!/usr/bin/env python3
"""Shared cloud-backup helpers and legacy local backup restore."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile

# Keep all top-level home data except reproducible cache and previous restore copies.
HOME_EXCLUDES = {".cache"}


def default_paths(home):
    return [p.name for p in home.iterdir()
            if p.name not in HOME_EXCLUDES and not p.name.startswith(".restore-backup-")]


def prepare_system_backup(out, repo, archive_func):
    warnings = []
    reports = out / "reports"
    reports.mkdir(mode=0o700)
    commands = {
        "disks": ["lsblk", "-o", "NAME,SIZE,MODEL,FSTYPE,UUID,PARTUUID,MOUNTPOINTS"],
        "mounts": ["findmnt", "-o", "TARGET,SOURCE,FSTYPE,UUID,OPTIONS"],
        "user-id": ["id"],
        "hardware": ["lspci", "-nn"],
        "packages": ["pacman", "-Q"],
        "explicit-repo": ["pacman", "-Qqen"],
        "explicit-foreign": ["pacman", "-Qqem"],
        "flatpak": ["flatpak", "list", "--app", "--columns=application"],
        "gpu-mode": ["envycontrol", "--query"],
        "system-services": ["systemctl", "list-unit-files", "--state=enabled"],
        "user-services": ["systemctl", "--user", "list-unit-files", "--state=enabled"],
        "processes": ["ps", "-u", str(os.getuid()), "-o", "pid,comm"],
    }
    for name, cmd in commands.items():
        if not shutil.which(cmd[0]):
            warnings.append(f"Không có công cụ ghi báo cáo {name}: {cmd[0]}")
            continue
        result = subprocess.run(cmd, capture_output=True, text=True)
        (reports / (name + ".txt")).write_text(result.stdout + result.stderr)
        if result.returncode:
            warnings.append(f"Báo cáo {name} chưa đầy đủ (mã {result.returncode}).")
    for source in [Path('/etc/fstab'), Path('/proc/cmdline')]:
        (reports / (source.name + '.txt')).write_text(source.read_text())

    # Preserve local history AND the work tree, without publishing anything.
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], text=True)
    status = git('status', '--short')
    (reports / 'git-status.txt').write_text(status)
    if status:
        warnings.append('Repo có thay đổi chưa commit; đã giữ trong repo.tar, chưa tự commit/push.')
    (reports / 'git-head.txt').write_text(git('rev-parse', 'HEAD'))
    subprocess.run(['git', '-C', str(repo), 'bundle', 'create', str(out / 'dotfiles.bundle'), '--all'], check=True)
    subprocess.run(['git', '-C', str(repo), 'bundle', 'verify', str(out / 'dotfiles.bundle')], check=True)
    archive_func(repo, out / 'repo.tar')

    print('Cần sudo để đọc /etc và EFI; không thay đổi nguồn.', flush=True)
    subprocess.run(['sudo', '-v'], check=True)
    archive_func(Path('/etc'), out / 'etc.tar', privileged=True)
    with (reports / 'uefi-entries.txt').open('w') as output:
        subprocess.run(['sudo', 'efibootmgr', '-v'], stdout=output, check=True)
    # Only accept the mounted ESP layout used by the repository, never guess a device.
    candidates = []
    for location in ['/efi', '/boot/efi', '/boot']:
        result = subprocess.run(['findmnt', '-n', '-o', 'FSTYPE', '--mountpoint', location], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == 'vfat':
            candidates.append(location)
    if len(candidates) != 1:
        raise ValueError(f'Không xác định duy nhất ESP đã mount: {candidates}. Chưa thể sao lưu EFI.')
    esp = Path(candidates[0])
    subprocess.run(['sudo', 'test', '-f', str(esp / 'EFI/Microsoft/Boot/bootmgfw.efi')], check=True)
    archive_func(esp, out / 'efi.tar', privileged=True)
    (reports / 'efi-source.txt').write_text(str(esp) + '\n')
    warnings.append('Không xuất database/Docker volumes hoặc dữ liệu ngoài home. Nếu có dữ liệu cần giữ ở đó, chưa được format.')
    warnings.append('Không xác minh OneDrive trên cloud, mật khẩu/2FA hoặc BitLocker recovery key. Archive không mã hóa.')
    return warnings


def pause_onedrive():
    # Pause only the known sync service, never kill applications with unsaved work.
    result = subprocess.run(['systemctl', '--user', 'is-active', '--quiet', 'onedrive.service'])
    if result.returncode == 0:
        subprocess.run(['systemctl', '--user', 'stop', 'onedrive.service'], check=True)
        return True
    return False


def relative(value):
    p = PurePosixPath(value)
    if not value or p.is_absolute() or ".." in p.parts or p == PurePosixPath("."):
        raise ValueError(f"Cần đường dẫn tương đối trong home: {value!r}")
    return p.as_posix()


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def inside(path, parent):
    return path == parent or parent in path.parents


def roots(values):
    result = []
    for name in sorted(set(map(relative, values)), key=lambda x: (len(PurePosixPath(x).parts), x)):
        if not any(name == r or name.startswith(r + "/") for r in result):
            result.append(name)
    return result


def check_parents(home, name):
    current = home
    for part in PurePosixPath(name).parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise ValueError(f"Thư mục cha không an toàn (symlink/không phải thư mục): {current}")


def restore(args, home):
    source = Path(args.source).expanduser().resolve(strict=True)
    manifest = json.loads((source / "manifest.json").read_text())
    archive = source / "home.tar"
    if manifest.get("version") != 1 or digest(archive) != manifest.get("sha256"):
        raise ValueError("Backup không hợp lệ hoặc checksum sai; không phục hồi.")
    for name, expected in manifest.get('checksums', {}).items():
        item = source / relative(name)
        if not inside(item.resolve(), source) or item.is_symlink() or digest(item) != expected:
            raise ValueError(f'Checksum sai hoặc đường dẫn không hợp lệ: {name}')
    with tarfile.open(archive) as tar:
        restore_tar(args, home, tar)



def mkdir_private(home, directory):
    """Create each missing directory with mode 700; keep existing modes."""
    current = home
    for part in directory.relative_to(home).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f'Thư mục cha là symlink: {current}')
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            if not current.is_dir():
                raise ValueError(f'Đường dẫn không phải thư mục: {current}')


def restore_tar(args, home, tar):
    includes = roots(args.include) if args.include else None
    members = tar.getmembers()
    seen = set()
    for m in members:
        name = relative(m.name)
        if name in seen:
            raise ValueError(f"Archive có đường dẫn trùng: {name}")
        seen.add(name)
        if not (m.isfile() or m.isdir() or m.issym() or m.islnk()):
            raise ValueError(f"Kiểu file không được hỗ trợ: {name}")
    if includes:
        for name in includes:
            if not any(n == name or n.startswith(name + "/") for n in seen):
                raise ValueError(f"Không có trong backup: {name}")
    chosen = [m for m in members if
              (any(m.name == n or m.name.startswith(n + "/") for n in includes)
               if includes else not PurePosixPath(m.name).parts[0].startswith("."))]
    print("Checksum OK. Mặc định chỉ phục hồi dữ liệu không ẩn; dùng --include để chọn cấu hình.")
    # Preflight all targets before any changes. Links are intentionally not restored.
    files = []
    for m in chosen:
        if m.issym() or m.islnk():
            print("SKIP liên kết (kiểm tra thủ công):", repr(m.name), "->", repr(m.linkname))
            continue
        check_parents(home, m.name)
        target = home / m.name
        if m.isdir() and (target.is_symlink() or (target.exists() and not target.is_dir())):
            raise ValueError(f"Đích thư mục xung đột: {target}")
        if m.isfile() and target.is_dir() and not target.is_symlink():
            raise ValueError(f"Đích file là thư mục: {target}")
        existing = target if m.isdir() else target.parent
        while not existing.exists():
            existing = existing.parent
        if existing.stat().st_dev != home.stat().st_dev:
            raise ValueError(f"Đích nằm trên filesystem khác trong home: {target}; kiểm tra mount trước khi restore.")
        files.append(m)
    if not args.apply:
        for m in files:
            print("WOULD RESTORE:", repr(m.name))
        print(f"Dry-run: {len(files)} mục; chưa thay đổi home. Thêm --apply để thực hiện.")
        return
    required = sum(m.size for m in files if m.isfile())
    available = shutil.disk_usage(home).free
    if required + 64 * 1024 * 1024 > available:
        raise ValueError(f"Không đủ chỗ restore: cần {required} byte dữ liệu mới và 64 MiB dự phòng; trống {available} byte. File cũ vẫn được giữ.")
    # Backup stays outside selected paths; changes are incremental, not a transaction.
    saved = Path(tempfile.mkdtemp(prefix=".restore-backup-", dir=home))
    print("File bị thay thế được giữ tại:", saved, flush=True)
    # Archive order avoids repeatedly fetching cloud chunks by directory depth.
    for m in files:
        target = home / m.name
        check_parents(home, m.name)
        if m.isdir():
            if not target.exists():
                mkdir_private(home, target)
            continue
        mkdir_private(home, target.parent)
        # Finish downloading first: failures must leave the existing target in place.
        fd, temporary = tempfile.mkstemp(prefix=".restore-file-", dir=target.parent)
        old = None
        try:
            with os.fdopen(fd, "wb") as output, tar.extractfile(m) as input_file:
                shutil.copyfileobj(input_file, output)
                output.flush()
                os.fsync(output.fileno())
            if Path(temporary).stat().st_size != m.size:
                raise ValueError(f"File tải chưa đủ: {m.name}")
            os.chmod(temporary, m.mode & 0o777)
            os.utime(temporary, (m.mtime, m.mtime))
            check_parents(home, m.name)
            if os.path.lexists(target):
                old = saved / m.name
                mkdir_private(home, old.parent)
                shutil.move(str(target), str(old))
            try:
                os.replace(temporary, target)
            except OSError:
                if old is not None and not os.path.lexists(target):
                    shutil.move(str(old), str(target))
                raise
        finally:
            Path(temporary).unlink(missing_ok=True)
    print("Đã phục hồi. File thuộc tài khoản hiện tại; không thay dịch vụ, EFI hay /etc.")
