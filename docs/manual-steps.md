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

## 3. Cài đặt Oh-My-Zsh

Oh-My-Zsh không cài qua pacman; cần cài thủ công trước khi stow zsh/:

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

Sau đó cài plugins:
```bash
# zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-autosuggestions \
    ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

# zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-syntax-highlighting \
    ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

# agnosterzak theme
git clone https://github.com/zakaziko99/agnosterzak-ohmyzsh-theme \
    ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/themes/agnosterzak
# Sau đó copy file theme vào thư mục themes
```

---

## 4. Cài đặt font

```bash
# Nerd Fonts (đã có trong pkglist.txt)
yay -S ttf-jetbrains-mono-nerd ttf-firacode-nerd

# Refresh font cache
fc-cache -fv
```

---

## 5. Thiết lập màn hình (đã được xử lý bởi override)

`LaptopDisplay.conf` trong repo đã thiết lập:
```conf
monitor = eDP-1, preferred, auto, 1
```

Nếu bạn có thêm màn hình ngoài, thêm dòng tương ứng vào `LaptopDisplay.conf`:
```conf
monitor = HDMI-A-1, preferred, auto, 1
```

---

## 6. Thiết lập Fcitx5 Bamboo (Vietnamese Input)

Sau khi stow và khởi động lại Hyprland:

```bash
# Mở Fcitx5 Configuration GUI
fcitx5-configtool
```

1. Thêm "Bamboo" vào Input Method
2. Đặt Bamboo làm input method thứ 2 (sau "Keyboard - English")
3. Kiểm tra hoạt động: mở bất kỳ app nào, nhấn `SUPER + SPACE` để chuyển input

---

## 7. Thiết lập Bluetooth

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

## 8. Cài extension cho trình duyệt (thủ công)

Những extension **không thể sync tự động**:
- [uBlock Origin](https://ublockorigin.com/)
- [Bitwarden](https://bitwarden.com/)
- [Vimium](https://vimium.github.io/)

---

## 9. Neovim — First Launch

Lần đầu mở Neovim sau khi stow:

```bash
nvim
# LazyVim sẽ tự động cài plugins lần đầu
# Chờ khoảng 1-2 phút cho đến khi hoàn tất
```

Cài LSP servers qua Mason:
```
:Mason   → tìm và cài các server cần thiết
```

---

*Cập nhật lần cuối: 2026-08-09*
