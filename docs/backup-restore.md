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

Mặc định dùng `archbackup:`. Nếu đã đặt tên khác, dùng `--remote ten-crypt:`. Chỉ chấp nhận remote **crypt trỏ trực tiếp vào OneDrive**, có bật mã hóa nội dung. Script từ chối `no_data_encryption=true` trong cấu hình hoặc biến môi trường và buộc bật mã hóa khi truyền dữ liệu.

Script tự:

- Tạo đích có ngày UTC và ID ngẫu nhiên, không ghi đè bản cũ.
- Dừng `onedrive.service` của user nếu đang active. Không tự đóng ứng dụng hay tiến trình sync chạy riêng.
- Lưu báo cáo phân vùng/package/dịch vụ, Git bundle và cả repo chưa commit.
- Sao lưu `/etc`, EFI và so sánh archive với nguồn. ESP phải được mount duy nhất tại `/efi`, `/boot/efi` hoặc `/boot`, có Windows Boot Manager.
- Gửi home và các archive theo phần nhỏ, mã hóa qua crypt, tải lại từng phần để đối chiếu checksum. Chỉ ghi manifest hoàn tất sau khi mọi bước thành công.

Home mặc định gồm thư mục riêng, file ẩn và **dữ liệu local trong OneDrive**; không tự bỏ dữ liệu đó vì chưa chứng minh tất cả đã lên cloud. Bỏ `.cache`, `.restore-backup-*`, filesystem khác mount trong home, đối tượng runtime; symlink chỉ giữ liên kết. Script đọc `sync_dir` từ cấu hình client trong `$XDG_CONFIG_HOME/onedrive/config` (mặc định `~/.config/onedrive/config`), nếu chưa có thì dùng `~/OneDrive`. Thư mục cloud `ArchBackups` bên trong thư mục sync bị loại để tránh backup lặp. Nếu chạy client với cấu hình riêng, thêm `--onedrive-dir /đường/dẫn/thư-mục-sync` vào lệnh backup. Đường dẫn `--include` không tồn tại hoặc bị loại sẽ làm script dừng trước upload, kể cả khi các lựa chọn khác hợp lệ. Nếu chọn nhiều đường dẫn, xem `skipped` trong manifest để biết các mục cụ thể bị loại.

Tùy chọn giới hạn home (thay toàn bộ danh sách mặc định, không cộng thêm):

```bash
./scripts/backup.sh --include Documents --include Code --include .ssh
```

`/etc`, EFI, repo và báo cáo vẫn được lưu. Dữ liệu database/Docker volumes ngoài home không được tự export. Không phải snapshot nhất quán của ứng dụng đang chạy; file thay đổi hoặc biến mất lúc đọc sẽ làm backup dừng để tránh bỏ sót dữ liệu. Đóng ứng dụng, kiểm tra file rồi chạy lại. Mỗi lần truyền hoặc tải lại gặp lỗi được thử tối đa bốn lần, với khoảng chờ 30 giây, 2 phút và 5 phút giữa các lần (rclone có thể tự retry thêm); Ctrl+C để hủy. Checksum sai không bao giờ được chấp nhận; backup không tiếp tục từ lần chạy cũ.

Script dùng bộ nhớ cho các phần 64 MiB và một thư mục tạm nhỏ dưới `~/.cache/dotfiles-backup` cho báo cáo/Git bundle; vẫn cần dung lượng cho bundle, bộ nhớ và file tạm của công cụ. Không nén archive, nên không dựa vào giả định nén sẽ đủ chỗ.

### OneDrive sync sau backup

**Script chỉ dừng dịch vụ sync trong phiên hiện tại**, kể cả khi upload lỗi sau khi đã dừng nó; không disable service. Nếu service được enable, nó có thể tự khởi động lại sau đăng nhập hoặc reboot. Trước khi reboot thử USB rồi quay lại Arch, loại `ArchBackups` khỏi sync và kiểm tra filter; nếu chưa làm được, tạm ngăn service khởi động bằng các lệnh dưới đây. Nếu bật lại ngay, client có thể tải cả thư mục backup cloud về và làm đầy ổ 70 GB. Trước khi bật lại, loại `ArchBackups` khỏi sync của cả Linux và Windows nếu có client chạy trên hai hệ điều hành.

Trong terminal Arch cũ, xem trạng thái và ghi lại kết quả trước khi thay đổi:

```bash
systemctl --user is-enabled onedrive.service
systemctl --user is-active onedrive.service
```

Nếu chưa cấu hình được filter mà phải reboot, tạm chạy `systemctl --user disable --now onedrive.service`. Lệnh này thay đổi cấu hình tự khởi động; chỉ bật lại bằng `systemctl --user enable --now onedrive.service` khi filter đã được xác minh và trước đó bạn muốn service tự khởi động. Nó không ngăn client chạy thủ công hay trên Windows.

**Trên Windows**, kiểm tra đúng tài khoản OneDrive: chọn biểu tượng đám mây ở khay hệ thống → bánh răng **Settings** → **Account** → **Choose folders**, bỏ chọn `ArchBackups` rồi xác nhận. Theo [Microsoft](https://support.microsoft.com/en-gb/onedrive/choose-which-onedrive-folders-you-want-to-sync-on-windows-or-macos), bỏ chọn sẽ xóa bản local của thư mục đó khỏi máy Windows nhưng giữ bản trên cloud; trước đó phải xác nhận upload đã hoàn tất và không có file local chưa sync cần giữ. Thiết lập này áp dụng riêng cho từng máy/tài khoản. Nếu chưa chắc trạng thái, tạm dừng sync và kiểm tra trước khi thay đổi.

Với client abraunegg trên Linux, kiểm tra `~/.config/onedrive/config` và các bộ lọc đang có. Thêm `/ArchBackups` vào `skip_dir`, giữ lại các mục cũ, không thay toàn bộ danh sách nếu đã cấu hình. Thay đổi filter có thể yêu cầu `--resync`; kiểm tra bằng dry-run và theo [tài liệu client](https://github.com/abraunegg/onedrive/blob/master/docs/usage.md#using-client-side-filtering-rules-to-determine-what-should-be-synced-with-microsoft-onedrive). Chỉ khi cấu hình đúng mới chạy `systemctl --user start onedrive.service`. Script không tự sửa bộ lọc hoặc chạy resync dữ liệu cá nhân.

## 3. Kiểm tra backup trước khi xóa Arch

Script in đích dạng `archbackup:arch-20261105T010000Z-abcdefgh`. Ghi lại đúng ID. Liệt kê các thư mục qua crypt:

```bash
rclone lsf archbackup: --dirs-only
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --dry-run
```

Đổi ID ví dụ. Dry-run đọc/giải mã và kiểm tra **tất cả archive**, liệt kê dữ liệu home sẽ khôi phục, không ghi vào home. Việc này tải dữ liệu qua mạng nên có thể lâu. Lỗi tải tạm thời được thử lại theo các khoảng chờ trên; checksum sai vẫn làm lệnh dừng. Mỗi lần dry-run và apply đều kiểm tra lại toàn bộ archive; việc quét tar và restore có thể tải lại nhiều chunk, kể cả khi chỉ chọn `--include .ssh`. Dự trù băng thông và thời gian, không bỏ qua verify. Tên trên giao diện web OneDrive đã mã hóa; dùng rclone qua `archbackup:` để xem tên thật.

Nếu rclone báo mã 3 hoặc 4 khi tìm `manifest.json`, script dừng ngay; kiểm tra đúng remote và ID. Các lỗi mạng khác vẫn được thử lại, và file chunk vừa upload vẫn được retry nếu tạm thời chưa xuất hiện. Nếu không có manifest hoặc checksum lỗi, chưa có bản hoàn tất để cài lại. Script không tự xóa bản dở dang, không resume lần chạy cũ; chạy lại tạo ID khác và cần quota cho cả hai. Chỉ xóa đúng bản dở dang sau khi nhận diện chắc chắn, không xóa cả thư mục ArchBackups.

Chạy thử truy cập backup từ Windows/máy khác bằng remote được cấu hình lại với cùng mật khẩu/salt trước khi format. Kiểm tra tài khoản/2FA và BitLocker recovery key mở được ngoài Arch. Một bản cloud vẫn có thể mất do mất tài khoản hoặc thao tác xóa; giữ thêm bản dữ liệu không thể mất nếu có điều kiện.

## 4. Lấy báo cáo và EFI trước khi phân vùng

Archive hệ thống được lưu thành các phần mã hóa, không thể tải một file bất kỳ trên web rồi mở bằng tar. Dùng script xuất các archive tham khảo:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh \
  --export-system /tmp/arch-rescue
```

Thư mục đích phải **chưa tồn tại**. Trước khi tạo thư mục, script kiểm tra đủ chỗ cho tổng archive hệ thống cộng 64 MiB dự phòng. Lệnh kiểm tra và tải `efi.tar`, `etc.tar`, `repo.tar`, `metadata.tar`, không phục hồi vào hệ thống. Mỗi archive chỉ được đặt tên hoàn chỉnh sau khi tải xong và kiểm tra checksum; lỗi có thể để lại thư mục đích với các archive đã hoàn thành, hãy dùng thư mục mới khi thử lại. `metadata.tar` chứa `reports/`, `REPORT.txt` và Git bundle. Mở/giải nén vào thư mục riêng để đọc; không giải nén đè `/etc` hay EFI. Lệnh này không kiểm tra archive home; cần dry-run đầy đủ ở bước 3 trước khi format.

**Nếu đang ở USB Arch live:** cần mạng. Kiểm tra vùng ghi live và `/tmp` trước vì cả cài package lẫn export có thể dùng RAM/tmpfs:

```bash
df -h / /tmp
df -h /run/archiso/cowspace
```

Nếu đường dẫn cowspace không tồn tại, kiểm tra mount bằng `findmnt` và dừng nếu không xác định được dung lượng. Nếu thiếu, xem [ArchWiki archiso](https://wiki.archlinux.org/title/Archiso) để điều chỉnh `cow_spacesize` phù hợp RAM; không mặc định 1 GiB luôn đủ. Cài công cụ **chỉ trong môi trường live tạm**, không phải `/mnt`:


```bash
pacman -Sy --needed python git rclone
git clone https://github.com/nnta301/dotfiles.git /tmp/dotfiles
cd /tmp/dotfiles
rclone config
```

Lệnh `pacman -Sy` ở đây chỉ dành cho live ISO tạm để cài công cụ cứu hộ; không áp dụng cách cập nhật một phần này cho hệ thống Arch đã cài. Nếu lỗi dependency hoặc không đủ vùng ghi, dừng và xử lý live ISO, không tiếp tục format.

Tạo lại `onedrive` và `archbackup` đúng hướng dẫn bước 1 với mật khẩu/salt đã lưu; nếu không có trình duyệt, theo luồng xác thực headless của rclone trên thiết bị khác. Sau đó chạy `restore.sh ... --export-system /tmp/arch-rescue` như trên. **Chỉ chế độ export-system cho phép root trong USB**; backup/restore home vẫn cần user thường. Kiểm tra `df -h /tmp` vì bộ nhớ live có hạn; nếu không đủ hoặc chưa tải được backup thì dừng trước khi format.

Repo trên GitHub phải có script mới trước khi clone từ USB. Nếu chưa push, giữ thêm checkout trên Windows/thiết bị khác; `.gitattributes` yêu cầu LF cho file text khi checkout mới. Khi chép qua filesystem Windows có thể mất bit thực thi: trong USB dùng `bash ./scripts/restore.sh ...` hoặc kiểm tra nội dung và `chmod +x scripts/restore.sh` sau khi chép. Nếu bản checkout được tạo trước `.gitattributes` còn CRLF, tạo lại bản sao từ commit có `.gitattributes` rồi kiểm tra trước, không chỉnh tự động lên bản duy nhất. Đừng xóa Arch khi công cụ giải mã/phục hồi duy nhất còn nằm trong Arch.

## 5. Restore sau cài mới

Sau khi cài Arch và hoàn tất `setup.sh`, cấu hình lại hai remote như bước 1. Chạy từ repo bằng user thường:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --dry-run
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --apply
```

Mặc định chỉ phục hồi các mục cấp đầu không ẩn để giữ cấu hình mới. Mỗi file được tải hoàn chỉnh vào file tạm và kiểm tra kích thước trước khi chuyển file trùng vào `~/.restore-backup-*` rồi thay thế; không xóa file thừa. Lỗi tải file hiện tại không làm mất file cũ. Thư mục mới, kể cả các thư mục cha trung gian, được tạo với quyền tối đa 700; thư mục đã tồn tại giữ quyền cũ, file thuộc user mới và giữ mode thường, bỏ setuid/setgid; không phục hồi ACL/xattrs/owner cũ cho home. Symlink trong archive được báo bỏ qua khi restore; dry-run in tên và đích liên kết để kiểm tra thủ công. Không tự tạo lại link tuyệt đối hoặc trỏ ra ngoài home khi chưa xác định đích. Các file hardlink trong home được backup thành các file riêng, vì vậy nội dung có thể được phục hồi nhưng mối liên kết giữa chúng không được giữ. Mất mạng giữa chừng có thể để lại một phần đã restore; kiểm tra home và bản sao file cũ, không có rollback toàn bộ.

Muốn lấy SSH keys hoặc một cấu hình cụ thể, chọn riêng:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --include .ssh --dry-run
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --include .ssh --apply
```

Restore không cần đủ chỗ cho cả archive cộng dữ liệu giải nén, nhưng vẫn cần chỗ cho dữ liệu phục hồi và các file cũ được giữ lại. Trước khi ghi home, script kiểm tra dung lượng trống theo tổng kích thước file được chọn cộng 64 MiB dự phòng; không phục hồi vào filesystem khác mount dưới home. EFI, `/etc`, dịch vụ và database không tự phục hồi. Đăng nhập lại các ứng dụng/2FA; profile Chrome không bảo đảm giữ phiên đăng nhập. Không còn tạo backup local bằng `transfer.py`; backup local phiên bản cũ vẫn khôi phục được bằng `restore.sh /đường/dẫn/arch-backup-*`.

## Kiểm chứng

Chạy `python3 -m unittest discover -s tests -v`. Test gồm đọc/ghi chunk, checksum, traversal, export, restore, GNU tar thực và rclone crypt với đích local tạm. Chưa kiểm thử tài khoản OneDrive thật hoặc toàn bộ cài lại máy; cần xác thực và chạy thử trên tài khoản của bạn trước khi format.
