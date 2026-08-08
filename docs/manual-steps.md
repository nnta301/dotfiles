# 📋 Manual Steps — Sau khi chạy `setup.sh`

Những việc **không thể tự động hóa** và cần làm thủ công sau khi setup xong.

---

## 1. Đăng nhập & xác thực tài khoản

### GitHub / Git
```bash
# Cấu hình thông tin cơ bản
git config --global user.name "Tên của bạn"
git config --global user.email "email@example.com"

# Tạo SSH key và thêm vào GitHub
ssh-keygen -t ed25519 -C "email@example.com"
cat ~/.ssh/id_ed25519.pub   # Copy và paste vào GitHub → Settings → SSH Keys
```

### OneDrive (rclone)
```bash
rclone config   # Làm theo hướng dẫn, chọn "Microsoft OneDrive"
# Sau đó mount:
rclone mount OneDrive: ~/OneDrive --daemon
```

---

## 2. Cấp quyền & nhóm người dùng

```bash
# Thêm user vào nhóm cần thiết
sudo usermod -aG video,audio,input,seat $USER

# Nếu dùng Docker
sudo usermod -aG docker $USER

# Áp dụng nhóm mới (cần logout hoặc:)
newgrp docker
```

---

## 3. Cài đặt font

```bash
# Cài Nerd Fonts (ví dụ: JetBrainsMono)
yay -S ttf-jetbrains-mono-nerd

# Refresh font cache
fc-cache -fv
```

---

## 4. Thiết lập Bluetooth

```bash
bluetoothctl
# Trong bluetoothctl:
#   power on
#   scan on
#   pair <MAC>
#   connect <MAC>
#   trust <MAC>
```

---

## 5. Thiết lập màn hình & tỷ lệ scale (HiDPI)

Chỉnh trong `~/.config/hypr/hyprland.conf`:
```
monitor=,preferred,auto,1.5   # scale 1.5x cho màn HiDPI
```

---

## 6. Cài extension cho trình duyệt (thủ công)

Những extension **không thể sync tự động**:
- [uBlock Origin](https://ublockorigin.com/)
- [Bitwarden](https://bitwarden.com/)
- [Vimium](https://vimium.github.io/)

---

## 7. Thiết lập VSCode / Cursor

```bash
# Đăng nhập Settings Sync
# File → Preferences → Settings Sync → Sign in
```

---

*Cập nhật lần cuối: 2026-08-01*
