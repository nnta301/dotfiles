# ⚙️ Workflow & Quy Trình Làm Việc

Ghi chú cá nhân về quy trình làm việc hàng ngày, phím tắt Hyprland, và cách sync dotfiles.

---

## 🔄 Quy trình sync Dotfiles

### Khi thay đổi config trên máy hiện tại
```bash
cd ~/OneDrive/Documents/dotfiles

# Xem những gì đã thay đổi
git status
git diff

# Commit và push
git add -A
git commit -m "feat: mô tả thay đổi"
git push
```

### Khi cài lên máy mới
```bash
git clone <repo-url> ~/OneDrive/Documents/dotfiles
cd ~/OneDrive/Documents/dotfiles
chmod +x setup.sh
./setup.sh
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
| `Super + Enter` | Mở terminal |
| `Super + Q` | Đóng cửa sổ hiện tại |
| `Super + D` | Mở rofi launcher |
| `Super + F` | Toggle fullscreen |
| `Super + V` | Toggle floating |
| `Super + 1~9` | Chuyển workspace |
| `Super + Shift + 1~9` | Di chuyển cửa sổ sang workspace |
| `Super + H/J/K/L` | Di chuyển focus (vim-style) |
| `Super + R` | Resize mode |
| `Super + Shift + E` | Thoát Hyprland |
| `Super + L` | Khóa màn hình |
| `Print` | Chụp toàn màn hình |
| `Super + Print` | Chụp vùng chọn |

---

## 🖥️ Quy trình làm việc hàng ngày

```
Sáng:
  1. Mở terminal → kiểm tra update: sudo pacman -Syu
  2. Mở editor (Cursor/VSCode)
  3. Pull latest code: git pull

Khi cài thêm package:
  1. Cài: sudo pacman -S <pkg> hoặc yay -S <pkg>
  2. Cập nhật pkglist.txt
  3. Commit lên dotfiles repo

Cuối tuần:
  1. Chạy cleanup: ./setup.sh → chọn 5 (Dọn dẹp hệ thống)
  2. Kiểm tra dung lượng: df -h
  3. Backup snapshot nếu cần
```

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
```

---

## 📁 Cấu trúc Dotfiles

```
dotfiles/
├── bash/           → .bashrc, .bash_profile, aliases
├── hypr/           → hyprland.conf, animations, keybinds
├── waybar/         → config, style.css
├── scripts/        → cleanup.sh và các script tiện ích khác
├── docs/           → Tài liệu này
│   ├── manual-steps.md
│   ├── troubleshooting.md
│   └── workflow.md
├── pkglist.txt     → Danh sách packages cần cài
├── README.md
└── setup.sh        → Script setup tự động
```

---

*Cập nhật lần cuối: 2026-08-01*
