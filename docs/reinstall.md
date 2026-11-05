# Cài lại Arch với backup OneDrive

Cập nhật 05/11/2026: luồng chính dùng **backup mã hóa trên OneDrive**, không cần ổ backup ngoài. USB chỉ để boot cài Arch. Giữ Windows dual boot UEFI/GPT; xem phạm vi phần cứng/phân vùng trong [hướng dẫn cài đặt](arch-windows-dual-boot.md).

## 1. Chuẩn bị OneDrive một lần

Làm [bước cấu hình rclone/crypt](backup-restore.md#1-cấu-hình-một-lần-trên-arch-cũ): tạo `onedrive:` trỏ đúng tài khoản và `archbackup:` mã hóa vào `onedrive:ArchBackups`. Giữ mật khẩu crypt, salt và cách đăng nhập/2FA ngoài Arch. Không chỉ lưu khóa bên trong backup mã hóa.

Kiểm tra quota thật bằng `rclone about onedrive:`. Ổ Arch 70 GB không bảo đảm backup luôn vừa quota: các bản backup cũ, repo lưu riêng và dung lượng còn lại trên cloud đều tính vào giới hạn. Script ước lượng trước upload và không tạo bản home lớn trên ổ local đang gần đầy.

## 2. Backup từ Arch cũ

Lưu công việc, đóng ứng dụng đang ghi dữ liệu. Trong repo thật:

```bash
cd ~/OneDrive/Documents/dotfiles
./scripts/backup.sh
```

Thay `cd` nếu repo ở nơi khác. Nhập mật khẩu sudo khi được hỏi. Script tự lưu home, repo chưa commit, Git bundle, báo cáo máy, `/etc`, EFI; gửi từng phần mã hóa rồi tải lại kiểm tra. Không cần các bước tar hoặc git bundle thủ công.

Ghi lại đích được in, ví dụ `archbackup:arch-20261105T010000Z-abcdefgh`. Nếu lỗi, chưa dùng bản đó để format; không có manifest hoàn tất thì chưa phải bản backup đầy đủ. Script giữ OneDrive sync dừng để tránh tải cả backup ngược về ổ local. Xem [cách loại ArchBackups khỏi sync](backup-restore.md#onedrive-sync-sau-backup) trước khi bật lại client, kể cả trên Windows.

Database/Docker volumes ngoài home phải xuất riêng nếu có dữ liệu cần giữ. Cache, filesystem con và đích symlink không được tự lưu; xem báo cáo. Dữ liệu OneDrive chỉ có trên cloud không được coi là bản sao local đã nằm trong archive.

## 3. Kiểm tra có thể phục hồi trước khi xóa

Trong repo, thay ID bằng bản thật:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --dry-run
```

Lệnh kiểm tra toàn bộ archive trên cloud và liệt kê dữ liệu sẽ restore. Dùng thiết bị khác hoặc USB live để thử đăng nhập, cấu hình lại crypt với khóa đã lưu và tải các archive tham khảo:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --export-system /tmp/arch-rescue
```

Xem [cách chuẩn bị công cụ trong USB](backup-restore.md#4-lấy-báo-cáo-và-efi-trước-khi-phân-vùng). Đích export phải là thư mục mới và đủ chỗ. `metadata.tar` chứa báo cáo phân vùng và `REPORT.txt`; `efi.tar` dùng đối chiếu trước xử lý boot cũ. Thử đọc dữ liệu quan trọng, giải quyết mọi cảnh báo về phần chưa sao lưu. Export hệ thống không thay thế dry-run kiểm tra home.

**Trước format phải có:** backup hoàn tất và truy cập được ngoài Arch, khóa giải mã/2FA, BitLocker recovery key, USB UEFI có mạng và sơ đồ đúng root/ESP. Không xóa Arch nếu công cụ hoặc khóa phục hồi duy nhất nằm trong Arch.

Các thay đổi repo chưa push không có khi clone GitHub. Push mã/config đã kiểm tra hoặc giữ bộ script trên Windows/thiết bị khác. `repo.tar` trong cloud giữ thay đổi chưa commit nhưng vẫn cần công cụ và khóa để lấy lại.

## 4. Cài lại hoặc chia lại phân vùng

Tạo USB theo [hướng dẫn dual boot](arch-windows-dual-boot.md). Tắt Fast Startup/hibernate Windows và kiểm tra Windows Boot Manager boot trực tiếp. Sau khi boot USB, lấy báo cáo và EFI từ cloud như bước 3 **trước khi xóa/format**.

- Giữ nguyên kích thước root cũ: làm Cách A ở hướng dẫn chính.
- Muốn xóa Arch để chia lại dung lượng: làm [nhánh repartition](repartition-arch.md).
- EFI gần đầy: mục 4.1 hướng dẫn chính dùng `efi.tar` đã export để so sánh; không format ESP. Root mới mount `/mnt`, ESP mount `/mnt/efi`, kernel nằm trên ext4 ở `/boot`.

Tạo fstab và GRUB mới, không chép cấu hình boot cũ đè lên máy mới.

## 5. Setup và restore trên Arch mới

Đăng nhập user thường, clone repo và chạy:

```bash
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles
./setup.sh
```

Nếu setup cài nền JaKooLit rồi dừng, trên máy hiện tại chọn `nvidia`, `dots`, `sddm` khi phù hợp, đăng nhập kiểm tra Hyprland rồi chạy setup lần nữa. Nếu đã hoàn tất thì không cần lặp lại.

Cấu hình lại rclone/crypt bằng **cùng mật khẩu và salt**, sau đó:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --dry-run
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --apply
```

Mặc định phục hồi dữ liệu không ẩn; muốn cấu hình/khóa, dùng `--include .ssh` hoặc đường dẫn cụ thể sau khi xem trước. File trùng được giữ ở `~/.restore-backup-*`; không tự phục hồi `/etc`, EFI hay database. Nếu muốn lấy repo chưa push, export hệ thống rồi mở `repo.tar` vào thư mục riêng trống, kiểm tra và chạy setup từ bản đó.

Đăng nhập lại dịch vụ, kiểm tra project, tài liệu, bộ gõ, màn hình và cả Windows/Arch. Không bật OneDrive sync cả thư mục ArchBackups và không xóa backup cho đến khi xác nhận đầy đủ. Xem [chi tiết restore và giới hạn](backup-restore.md), [các bước sau setup](manual-steps.md).
