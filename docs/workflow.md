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

> Xem [README.md](../README.md) để biết quy trình 3 bước đầy đủ.

```bash
# 1. Chạy JaKooLit upstream trước
git clone --depth=1 https://github.com/JaKooLit/Arch-Hyprland.git ~/JaKooLit-Arch
cd ~/JaKooLit-Arch && ./install.sh

# 2. Clone repo cá nhân và áp dụng override
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles
chmod +x setup.sh && ./setup.sh
```

### Cập nhật pkglist.txt từ hệ thống hiện tại

```bash
# Export danh sách package đang cài (bỏ qua AUR)
pacman -Qqen > pkglist.txt

# Kèm AUR packages
pacman -Qqm >> pkglist.txt
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
├── pkglist.txt     → Danh sách packages tham khảo
├── README.md       → Hướng dẫn cài đặt chính
└── setup.sh        → Script stow tự động
```

---

*Cập nhật lần cuối: 2026-08-09*
