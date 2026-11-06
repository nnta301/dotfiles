# Sau setup: dữ liệu, tài khoản và kiểm tra ứng dụng

Đối chiếu với script ngày 05/11/2026. `setup.sh` đã cài package, Flatpak, Oh My Zsh, plugins, theme, font trong danh sách và áp dụng cấu hình bằng Stow. Không cần cài lại từng thành phần đó bằng các lệnh riêng.

## 1. Phục hồi dữ liệu trước khi bật đồng bộ

Làm phần restore trong [reinstall.md](reinstall.md): xem trước bằng `restore.sh --dry-run`, sau đó dùng `--apply`. Cấu hình ẩn cần chọn riêng bằng `--include`; không chép đè cả home hay `/etc` lên hệ thống mới. Xem [backup/restore](backup-restore.md) về backup file bị thay thế và các giới hạn.

Các mục ẩn như `.ssh`, `.gnupg` và cấu hình ứng dụng cần chọn riêng sau khi kiểm tra, ví dụ:

```bash
./scripts/restore.sh archbackup:arch-20261105T010000Z-abcdefgh --include .ssh --include .gnupg --dry-run
```

Thay ID bằng bản thật; nếu một mục không có trong backup, bỏ mục đó khỏi lệnh. Chỉ thêm `--apply` thay `--dry-run` sau khi xem kết quả. Không restore toàn bộ `.config` một cách mù quáng: một số thư mục như `.config/nvim` có thể là symlink Stow và script sẽ dừng do xung đột; xem trước, chọn cấu hình ứng dụng cần thiết và xử lý symlink thủ công. Symlink trong backup được liệt kê nhưng không tự khôi phục.

## 2. Git và SSH

Kiểm tra danh tính Git hiện có:

```bash
git config --global user.name
git config --global user.email
```

Nếu trống hoặc muốn đổi, đặt tên/email thật:

```bash
git config --global user.name "Tên của bạn"
git config --global user.email "email@example.com"
```

Nếu đã phục hồi `.ssh`, kiểm tra khóa cũ trước khi tạo mới. Chỉ khi muốn tạo khóa mới và chưa có file cùng tên, chạy `ssh-keygen -t ed25519 -C "email@example.com"`, thay email thật. Không xác nhận ghi đè khóa đang có. Chỉ đưa file **public key** `.pub` vào GitHub → Settings → SSH and GPG keys; không đưa private key vào repo.

## 3. OneDrive và tài khoản ứng dụng

Alias mở OneDrive trên Chrome tên là `onedrive-web`; lệnh `onedrive` bên dưới chạy client đồng bộ. Mở terminal mới sau khi áp cấu hình Zsh để nhận thay đổi alias.

Sau khi đối chiếu dữ liệu local đã restore với dữ liệu trên web, xác thực OneDrive theo lời nhắc của client:

```bash
onedrive
```

Trước khi bật dịch vụ, loại `ArchBackups` khỏi phạm vi sync theo [hướng dẫn backup](backup-restore.md#onedrive-sync-sau-backup) để không tải bản backup về đầy ổ. Khi đã kiểm tra tài khoản và cấu hình đồng bộ đúng, bật dịch vụ:

```bash
systemctl --user enable --now onedrive.service
```

Nếu đã có dịch vụ hoặc một tiến trình sync khác, kiểm tra trước để tránh chạy hai client cho cùng thư mục. Repo có rclone nhưng không tự thiết lập remote; không mount rclone đè lên `~/OneDrive` đang chứa dữ liệu của client OneDrive. Token không được push lên Git.

Các alias `zalo`, `teams`, `outlook` và `onedrive-web` dùng Chrome app ID. Sau khi đăng nhập Chrome, cài lại từng web app nếu dùng; ID/profile có thể thay đổi, hãy kiểm tra alias nếu lệnh không mở đúng. `parsecd` là alias tùy chọn: repo hiện không cài Parsec, nên chỉ dùng sau khi bạn tự cài ứng dụng phù hợp.

Đăng nhập Chrome, trình quản lý mật khẩu và các ứng dụng cần tài khoản; có thể cần 2FA. Kiểm tra extension sau khi đăng nhập/sync, cài lại phần còn thiếu từ nguồn chính thức. Không mặc định mọi extension đều thiếu hoặc không thể đồng bộ. Profile cũ không bảo đảm giữ phiên đăng nhập/mật khẩu.

## 4. Shell và bộ gõ

Setup chuẩn bị Oh My Zsh, theme và plugin; đăng xuất/đăng nhập lại sau khi áp cấu hình. Nếu muốn đổi shell đăng nhập sang Zsh:

```bash
chsh -s /bin/zsh
```

Profile Fcitx5 trong repo đã có Keyboard US và Bamboo. Mở `fcitx5-configtool`, kiểm tra chúng xuất hiện và thử nhập tiếng Việt; không thêm bản trùng. Kiểm tra phím chuyển bộ gõ trong Global Options, không giả định luôn là Super+Space.

## 5. Nhóm người dùng và dịch vụ

Setup cài package không đồng nghĩa đã bật mọi dịch vụ. Xem [phần nhóm tùy chọn](arch-windows-dual-boot.md#các-nhóm-tùy-chọn) trước khi thêm `input` hoặc `docker`. Chỉ bật Docker/database khi cần và sau khi chuẩn bị dữ liệu tương ứng; không bật toàn bộ danh sách dịch vụ cũ từ báo cáo backup.

Nếu dùng TeamViewer hoặc auto-cpufreq, kiểm tra unit thật bằng `systemctl list-unit-files 'teamviewer*' 'auto-cpufreq*'`; chỉ enable unit cần dùng sau khi đọc hướng dẫn package. Tránh đồng thời bật nhiều công cụ điều chỉnh năng lượng xung đột.

Với Bluetooth, kiểm tra dịch vụ trước khi ghép thiết bị:

```bash
systemctl is-active bluetooth.service
```

Nếu muốn dùng Bluetooth và dịch vụ chưa chạy, dùng `sudo systemctl enable --now bluetooth.service`, rồi ghép thiết bị trong Blueman. Việc ghép đôi có thể cần làm lại trên hệ điều hành mới.

## 6. Màn hình và Neovim

Xem [hướng dẫn màn hình ngoài](external-displays.md) cho hai chế độ mirror và chỉ màn hình ngoài. Xác định cổng thật bằng `hyprctl monitors`, không mặc định tên HDMI luôn giống máy cũ.

Nếu HDMI không xuất hình trên máy từng dùng EnvyControl, kiểm tra `envycontrol --query` và đọc hướng dẫn màn hình ngoài. Trên máy cũ, chế độ `hybrid` từng giúp HDMI hoạt động; không tự đổi GPU khi chưa kiểm tra driver, dung lượng `/boot` và phương án phục hồi. Đổi chế độ có thể cần tạo initramfs và reboot.

Mở `nvim` và chờ trình quản lý plugin hoàn tất, đọc lỗi nếu có. Dùng `:Lazy` để xem trạng thái; kiểm tra các công cụ ngôn ngữ cần cho project bằng giao diện của cấu hình đang cài. Không chạy cập nhật tất cả plugin chỉ để kiểm tra phục hồi: repo đã giữ phiên bản trong `lazy-lock.json`.

Giữ backup OneDrive và khóa giải mã ngoài máy cho đến khi đã kiểm tra tài liệu, code, bộ gõ, ứng dụng và cả Windows/Arch.

## TeXpresso trong Neovim

Plugin `texpresso.vim` trong repo cần chương trình `texpresso` riêng trong PATH. Máy được kiểm tra có `/usr/local/bin/texpresso`, nhưng file cài thủ công này không nằm trong `pkglist.txt` hoặc bản backup home. Sau cài lại, nếu dùng tính năng xem trước LaTeX này, kiểm tra `command -v texpresso` và cài theo [hướng dẫn upstream](https://github.com/let-def/texpresso). Chỉ cài plugin Neovim chưa đủ; các tính năng khác của Neovim vẫn dùng được.
