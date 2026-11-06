# ⚙️ Workflow & Quy Trình Làm Việc

Ghi chú cá nhân về quy trình làm việc hàng ngày và cách sync dotfiles.

---

## 🔄 Quy trình sync Dotfiles

### Khi thay đổi config trên máy hiện tại

```bash
cd ~/dotfiles

# Xem những gì đã thay đổi
git status
git diff

# Commit và push
git add -p
# Thêm riêng file mới đã kiểm tra bằng git add <đường-dẫn>
git diff --cached
git commit -m "feat: mô tả thay đổi"
git push
```

### Khi cài lên máy mới

> Xem [README.md](../README.md) để biết quy trình cài đặt và liên kết hướng dẫn chi tiết.

```bash
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles
./setup.sh
```

Khi thiếu cấu hình Hyprland, script chạy installer JaKooLit rồi dừng. Trong installer JaKooLit, chọn `dots` (và `nvidia`, `sddm` cho máy hiện tại khi chưa có display manager), đăng nhập và kiểm tra Hyprland, sau đó chạy lại `./setup.sh` để áp cấu hình cá nhân. Nếu đã có `hyprland.conf`, script tiếp tục ngay; kiểm tra trước đó là cấu hình JaKooLit hoạt động.

### Cập nhật snapshot package từ hệ thống hiện tại

```bash
# Xuất riêng package được cài chủ động từ repo chính thức và gói ngoài
pacman -Qqen > packages/explicit-repo.txt
pacman -Qqem > packages/explicit-foreign.txt
pacman -Qqm > packages/all-foreign.txt
```

Snapshot chỉ phản ánh máy, **không tự thay đổi** danh sách cài của setup. Đối chiếu rồi thêm gói chính thức vào `pkglist.txt`; với gói AUR thêm tiền tố `aur/`, không đưa tên package local không tồn tại trên AUR vào tự động. Có thể xem các gói chính thức đã cài nhưng chưa có trong danh sách:

```bash
comm -23 <(sort -u packages/explicit-repo.txt) <(awk '{sub(/#.*/, ""); for (i=1; i<=NF; i++) if ($i !~ /^aur\//) print $i}' pkglist.txt | sort -u)
```

Với Flatpak, xem `flatpak list --app --columns=application`, rồi so sánh/chỉnh `packages/flatpak-apps.txt`. Lưu ý lệnh liệt kê có thể gồm ứng dụng cài system và user, còn setup cài từ Flathub cho user; không ghi đè danh sách nếu chưa xem nguồn và ID.

---

## ⌨️ Kiểm tra phím tắt Hyprland

Phím tắt phụ thuộc cấu hình JaKooLit được cài và các override cá nhân. Xem bindings đang dùng trong terminal Hyprland:

```bash
hyprctl binds
```

Đối chiếu `~/.config/hypr/configs/Keybinds.conf` (nếu bản JaKooLit đang dùng có file này) và `hypr/.config/hypr/UserConfigs/UserKeybinds.conf` trong repo. Không mặc định Super+M luôn là thoát phiên hoặc Super+Q luôn mở terminal.

## Sao lưu trước khi cài lại

Chạy `./scripts/backup.sh` theo [reinstall.md](reinstall.md). Script giữ cả repo chưa commit trên OneDrive mã hóa, không tự push GitHub. Các lệnh Git ở đầu trang dùng để đồng bộ mã/config lên GitHub, không phải các bước bắt buộc để tạo backup.

## 🧰 Lệnh thường dùng

Script dọn dung lượng có chế độ xem trước và sẽ hỏi trước khi xóa package mồ côi, cache build Yay hoặc thùng rác:

```bash
./scripts/cleanup.sh --dry-run
./scripts/cleanup.sh
```

Script dùng `paccache` (package `pacman-contrib`) để giữ hai phiên bản package, dọn journal đã lưu trữ và các thư mục tải tạm Pacman rỗng, cũ. Thùng rác được xử lý ở thư mục dữ liệu người dùng; thùng rác trên ổ đĩa khác không được quét. Chế độ xem trước có thể cần `sudo` để đọc các thư mục cache thuộc người dùng khác.

```bash
# Xem dung lượng ổ đĩa
df -h

# Xem thư mục nào chiếm nhiều nhất
du -sh ~/* | sort -rh | head -10

# Kiểm tra RAM
free -h

# Xem process nặng nhất
htop

# Tìm file lớn hơn 100MB
find ~ -size +100M -type f 2>/dev/null

# Reload Hyprland config (không cần restart)
hyprctl reload

# Xem lỗi phiên boot hiện tại
journalctl -b -p err

# Neovim — cập nhật plugins
nvim --headless "+Lazy! sync" +qa
```

---

## 📁 Cấu trúc Dotfiles (hiện tại)

```
dotfiles/
├── hypr/           → UserConfigs/ override chồng lên JaKooLit upstream
├── zsh/            → .zshrc (Oh-My-Zsh + aliases)
├── nvim/           → .config/nvim/ (LazyVim)
├── scripts/        → cleanup.sh, backup.sh, restore.sh, cloud_backup.py và transfer.py
├── docs/           → Tài liệu này
├── pkglist.txt     → Package chính thức và AUR được setup.sh cài
├── packages/       → Snapshot package thực tế trên máy
├── README.md       → Hướng dẫn cài đặt chính
└── setup.sh        → Cài nền/package/shell và áp cấu hình qua Stow
```

---

*Cập nhật lần cuối: 2026-11-05*
