# Backup mã hóa lên OneDrive và restore

Luồng chính dùng **OneDrive**, không cần ổ backup ngoài. USB vẫn dùng để boot cài Arch. `backup.sh` gửi archive theo từng phần tối đa 64 MiB qua rclone crypt, rồi tải lại từng phần để kiểm tra SHA-256. Không tạo `home.tar` lớn trên phân vùng Arch. Restore cũng đọc từng phần, không tải thêm một bản home đầy đủ xuống ổ trước khi phục hồi.

Cần Python 3.11+, rclone hỗ trợ `config redacted` (1.64+), GNU tar, Git và các công cụ Arch hiện có. Chạy bằng tài khoản thường; backup dùng sudo để đọc `/etc` và EFI. Chưa đăng nhập/cấu hình rclone thì script dừng trước upload. Rclone và OneDrive client là hai ứng dụng khác nhau: đăng nhập client `onedrive` không tự tạo remote cho rclone.

## 1. Cấu hình một lần trên Arch cũ

Kiểm tra `rclone version`, `python3 --version`. Máy hiện tại đã có rclone. Nếu máy khác thiếu, cài cùng cập nhật đầy đủ bằng `sudo pacman -Syu --needed rclone python`; riêng máy cũ có EFI gần đầy, phải xử lý theo hướng dẫn boot trước khi cập nhật hệ thống.

Chạy:

```bash
rclone config
```

Tạo hai remote, chọn theo **tên loại** vì số thứ tự menu có thể thay đổi:

1. Tạo remote tên `onedrive`, loại **Microsoft OneDrive**. Dùng client ID/secret mặc định nếu không tự đăng ký ứng dụng, làm theo trình duyệt để đăng nhập đúng tài khoản. Chọn đúng drive cá nhân chứa dữ liệu của bạn. Nếu đã có remote OneDrive đúng tài khoản, có thể dùng lại.
2. Tạo remote tên `archbackup`, loại **crypt**. Ở đường dẫn cần mã hóa nhập `onedrive:ArchBackups`. Chọn mã hóa tên file **standard**, mã hóa tên thư mục **true**. Đặt mật khẩu dài và salt/password thứ hai theo lời nhắc.
3. Lưu **mật khẩu crypt, salt, tên tài khoản và đường dẫn `onedrive:ArchBackups`** trong trình quản lý mật khẩu truy cập được từ điện thoại hoặc Windows. Nếu chọn salt trống, ghi rõ là trống. Đừng chỉ giữ chúng trong Arch hoặc bên trong chính backup mã hóa; thiếu các giá trị này sẽ không giải mã được sau khi format. Không commit `rclone.conf` vì nó chứa thông tin đăng nhập và khóa có thể khôi phục.

Kiểm tra đúng remote và dung lượng thật:

```bash
rclone listremotes
rclone about onedrive:
```

Không suy ra dung lượng đủ chỉ từ kích thước ổ: mỗi lần backup là bản độc lập, các lần cũ cũng chiếm quota. Script đọc quota trước upload và ước lượng phần home với dung lượng dự phòng; nếu nguồn thay đổi hay các archive bổ sung lớn, vẫn có thể hết quota và phải xử lý lỗi.

Nguồn: [rclone OneDrive](https://rclone.org/onedrive/) và [crypt](https://rclone.org/crypt/). Crypt mã hóa nội dung trước khi gửi; mật khẩu/salt phải được giữ để cấu hình lại remote sau này.

## 2. Chạy backup

Lưu công việc, đóng ứng dụng đang ghi dữ liệu. Trong repo:

```bash
./scripts/backup.sh
```

Mặc định dùng `archbackup:`. Nếu đã đặt tên khác, dùng `--remote ten-crypt:`. Chỉ chấp nhận remote **crypt trỏ trực tiếp vào OneDrive**, không gửi archive chứa bí mật lên remote bản rõ.

Script tự:

- Tạo đích có ngày UTC và ID ngẫu nhiên, không ghi đè bản cũ.
- Dừng `onedrive.service` của user nếu đang active. Không tự đóng ứng dụng hay tiến trình sync chạy riêng.
- Lưu báo cáo phân vùng/package/dịch vụ, Git bundle và cả repo chưa commit.
- Sao lưu `/etc`, EFI và so sánh archive với nguồn. ESP phải được mount duy nhất tại `/efi`, `/boot/efi` hoặc `/boot`, có Windows Boot Manager.
- Gửi home và các archive theo phần nhỏ, mã hóa qua crypt, tải lại từng phần để đối chiếu checksum. Chỉ ghi manifest hoàn tất sau khi mọi bước thành công.

Home mặc định gồm thư mục riêng, file ẩn và **dữ liệu local trong OneDrive**; không tự bỏ dữ liệu đó vì chưa chứng minh tất cả đã lên cloud. Bỏ `.cache`, `.restore-backup-*`, filesystem khác mount trong home, đối tượng runtime; symlink chỉ giữ liên kết. Script đọc `sync_dir` từ cấu hình client trong `$XDG_CONFIG_HOME/onedrive/config` (mặc định `~/.config/onedrive/config`), nếu chưa có thì dùng `~/OneDrive`. Thư mục cloud `ArchBackups` bên trong thư mục sync bị loại để tránh backup lặp. Nếu chạy client với cấu hình riêng, thêm `--onedrive-dir /đường/dẫn/thư-mục-sync` vào lệnh backup. Đường dẫn `--include` không tồn tại sẽ làm script dừng trước upload.

Tùy chọn giới hạn home (thay toàn bộ danh sách mặc định, không cộng thêm):

```bash
./scripts/backup.sh --include Documents --include Code --include .ssh
```

`/etc`, EFI, repo và báo cáo vẫn được lưu. Dữ liệu database/Docker volumes ngoài home không được tự export. Không phải snapshot nhất quán của ứng dụng đang chạy; file thay đổi lúc đọc có thể khiến script dừng.

Script dùng bộ nhớ cho các phần 64 MiB và một thư mục tạm nhỏ dưới `~/.cache/dotfiles-backup` cho báo cáo/Git bundle; vẫn cần dung lượng cho bundle, bộ nhớ và file tạm của công cụ. Không nén archive, nên không dựa vào giả định nén sẽ đủ chỗ.

### OneDrive sync sau backup

**Script giữ dịch vụ sync ở trạng thái dừng**, kể cả khi upload lỗi sau khi đã dừng nó. Nếu bật lại ngay, client có thể tải cả thư mục backup cloud về và làm đầy ổ 70 GB. Trước khi bật lại, loại `ArchBackups` khỏi sync của cả Linux và Windows nếu có client chạy trên hai hệ điều hành.

Với client abraunegg trên Linux, kiểm tra `~/.config/onedrive/config` và các bộ lọc đang có. Thêm `/ArchBackups` vào `skip_dir`, giữ lại các mục cũ, không thay toàn bộ danh sách nếu đã cấu hình. Thay đổi filter có thể yêu cầu `--resync`; kiểm tra bằng dry-run và theo [tài liệu client](https://github.com/abraunegg/onedrive/blob/master/docs/usage.md#using-client-side-filtering-rules-to-determine-what-should-be-synced-with-microsoft-onedrive). Chỉ khi cấu hình đúng mới chạy `systemctl --user start onedrive.service`. Script không tự sửa bộ lọc hoặc chạy resync dữ liệu cá nhân.

## 3. Kiểm tra backup trước khi xóa Arch

Script in đích dạng `archbackup:arch-20261105T010000Z-abcdefgh`. Ghi lại đúng ID. Liệt kê các thư mục qua crypt:

```bash
rclone lsf archbackup: --dirs-only
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --dry-run
```

Đổi ID ví dụ. Dry-run đọc/giải mã và kiểm tra **tất cả archive**, liệt kê dữ liệu home sẽ khôi phục, không ghi vào home. Việc này tải dữ liệu qua mạng nên có thể lâu. Tên trên giao diện web OneDrive đã mã hóa; dùng rclone qua `archbackup:` để xem tên thật.

Nếu không có manifest hoặc checksum lỗi, chưa có bản hoàn tất để cài lại. Script không tự xóa bản dở dang, không resume lần chạy cũ; chạy lại tạo ID khác và cần quota cho cả hai. Chỉ xóa đúng bản dở dang sau khi nhận diện chắc chắn, không xóa cả thư mục ArchBackups.

Chạy thử truy cập backup từ Windows/máy khác bằng remote được cấu hình lại với cùng mật khẩu/salt trước khi format. Kiểm tra tài khoản/2FA và BitLocker recovery key mở được ngoài Arch. Một bản cloud vẫn có thể mất do mất tài khoản hoặc thao tác xóa; giữ thêm bản dữ liệu không thể mất nếu có điều kiện.

## 4. Lấy báo cáo và EFI trước khi phân vùng

Archive hệ thống được lưu thành các phần mã hóa, không thể tải một file bất kỳ trên web rồi mở bằng tar. Dùng script xuất các archive tham khảo:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh \
  --export-system /tmp/arch-rescue
```

Thư mục đích phải **chưa tồn tại**, đủ chỗ. Lệnh kiểm tra và tải `efi.tar`, `etc.tar`, `repo.tar`, `metadata.tar`, không phục hồi vào hệ thống. `metadata.tar` chứa `reports/`, `REPORT.txt` và Git bundle. Mở/giải nén vào thư mục riêng để đọc; không giải nén đè `/etc` hay EFI. Lệnh này không kiểm tra archive home; cần dry-run đầy đủ ở bước 3 trước khi format.

**Nếu đang ở USB Arch live:** cần mạng; có thể cài công cụ vào môi trường live (không phải `/mnt`):

```bash
pacman -Sy --needed python git rclone
git clone https://github.com/nnta301/dotfiles.git /tmp/dotfiles
cd /tmp/dotfiles
rclone config
```

Tạo lại `onedrive` và `archbackup` đúng hướng dẫn bước 1 với mật khẩu/salt đã lưu; nếu không có trình duyệt, theo luồng xác thực headless của rclone trên thiết bị khác. Sau đó chạy `restore.sh ... --export-system /tmp/arch-rescue` như trên. **Chỉ chế độ export-system cho phép root trong USB**; backup/restore home vẫn cần user thường. Kiểm tra `df -h /tmp` vì bộ nhớ live có hạn; nếu không đủ hoặc chưa tải được backup thì dừng trước khi format.

Repo trên GitHub phải có script mới trước khi clone từ USB. Nếu chưa push, giữ thêm bộ script hiện tại trên Windows/thiết bị khác để dùng. Đừng xóa Arch khi công cụ giải mã/phục hồi duy nhất còn nằm trong Arch.

## 5. Restore sau cài mới

Sau khi cài Arch và hoàn tất `setup.sh`, cấu hình lại hai remote như bước 1. Chạy từ repo bằng user thường:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --dry-run
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --apply
```

Mặc định chỉ phục hồi các mục cấp đầu không ẩn để giữ cấu hình mới. Mỗi file được tải hoàn chỉnh vào file tạm và kiểm tra kích thước trước khi chuyển file trùng vào `~/.restore-backup-*` rồi thay thế; không xóa file thừa. Lỗi tải file hiện tại không làm mất file cũ. Thư mục mới quyền 700, file thuộc user mới và giữ mode thường, bỏ setuid/setgid; không phục hồi ACL/xattrs/owner cũ cho home. Symlink/hardlink được báo bỏ qua. Mất mạng giữa chừng có thể để lại một phần đã restore; kiểm tra home và bản sao file cũ, không có rollback toàn bộ.

Muốn lấy SSH keys hoặc một cấu hình cụ thể, chọn riêng:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --include .ssh --dry-run
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --include .ssh --apply
```

Restore không cần đủ chỗ cho cả archive cộng dữ liệu giải nén, nhưng vẫn cần chỗ cho dữ liệu phục hồi và các file cũ được giữ lại. Trước khi ghi home, script kiểm tra dung lượng trống theo tổng kích thước file được chọn cộng 64 MiB dự phòng; không phục hồi vào filesystem khác mount dưới home. EFI, `/etc`, dịch vụ và database không tự phục hồi. Đăng nhập lại các ứng dụng/2FA; profile Chrome không bảo đảm giữ phiên đăng nhập. Backup local phiên bản cũ vẫn dùng được bằng `restore.sh /đường/dẫn/arch-backup-*`.

## Kiểm chứng

Chạy `python3 -m unittest discover -s tests -v`. Test gồm đọc/ghi chunk, checksum, traversal, export, restore, GNU tar thực và rclone crypt với đích local tạm. Chưa kiểm thử tài khoản OneDrive thật hoặc toàn bộ cài lại máy; cần xác thực và chạy thử trên tài khoản của bạn trước khi format.
