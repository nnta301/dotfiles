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
git add -A
git commit -m "feat: mô tả thay đổi"
git push
```

### Khi cài lên máy mới

> Xem [README.md](../README.md) để biết quy trình cài đặt và liên kết hướng dẫn chi tiết.

```bash
# 1. Chạy JaKooLit upstream trước
git clone --depth=1 https://github.com/JaKooLit/Arch-Hyprland.git ~/JaKooLit-Arch
cd ~/JaKooLit-Arch && ./install.sh

# 2. Clone repo cá nhân và áp dụng override
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles
chmod +x setup.sh && ./setup.sh
```

### Cập nhật snapshot package từ hệ thống hiện tại

```bash
# Xuất riêng package được cài chủ động từ repo chính thức và gói ngoài
pacman -Qqen > packages/explicit-repo.txt
pacman -Qqem > packages/explicit-foreign.txt
pacman -Qqm > packages/all-foreign.txt
```

---

## ⌨️ Phím tắt Hyprland (thường dùng)

| Phím tắt | Hành động |
|----------|-----------| 
| `SUPER + Q` | Mở terminal (Kitty) |
| `SUPER + C` | Đóng cửa sổ hiện tại |
| `SUPER + R` | Mở app launcher |
| `SUPER + E` | Mở file manager |
| `SUPER + F` | Toggle fullscreen |
| `SUPER + V` | Toggle floating |
| `SUPER + 1~0` | Chuyển workspace |
| `SUPER + Shift + 1~0` | Di chuyển cửa sổ sang workspace |
| `SUPER + Arrow Keys` | Di chuyển focus |
| `SUPER + M` | Thoát Hyprland |
| `Print` | Chụp toàn màn hình |
| `SUPER + Shift + S` | Chụp vùng chọn |

---

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

# Xem log Hyprland
journalctl --user -u hyprland -f

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
├── scripts/        → cleanup.sh và các script tiện ích
├── docs/           → Tài liệu này
├── pkglist.txt     → Package chính thức và AUR được setup.sh cài
├── packages/       → Snapshot package thực tế trên máy
├── README.md       → Hướng dẫn cài đặt chính
└── setup.sh        → Script stow tự động
```

---

*Cập nhật lần cuối: 2026-08-09*
