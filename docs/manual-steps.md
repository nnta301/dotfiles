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

### OneDrive

Máy cũ có `onedrive-abraunegg` và đã bật `onedrive.service` cho người dùng. Sau khi cài gói và đăng nhập lại bằng lệnh `onedrive`, bật lại dịch vụ nếu bạn muốn đồng bộ tự động:

```bash
systemctl --user enable --now onedrive.service
```

Máy cũng có `rclone`, nhưng chưa xác định được có dùng rclone để đồng bộ OneDrive hay không. Nếu bạn dùng rclone:
```bash
rclone config   # Làm theo hướng dẫn, chọn "Microsoft OneDrive"
# Sau đó mount:
rclone mount OneDrive: ~/OneDrive --daemon
```

Không đưa refresh token hoặc cấu hình xác thực lên Git. Xem `reinstall.md` để chuẩn bị bản sao dữ liệu trước khi cài lại.

---

## 2. Cấp quyền & nhóm người dùng

Xem [bước tạo tài khoản và các nhóm tùy chọn](cai-arch-tu-windows.md) trước khi thêm quyền. Nhóm `input` có thể đọc sự kiện bàn phím; nhóm `docker` cấp quyền tương đương root, nên chỉ thêm khi cần.

---

## 3. Cài đặt Oh-My-Zsh

Mục 1 hoặc 4 trong `setup.sh` sẽ chuẩn bị Oh My Zsh, plugin và theme. Nếu làm thủ công, trước tiên kiểm tra `~/.oh-my-zsh`: installer JaKooLit có thể đã cài sẵn. Chỉ chạy trình cài chính thức sau nếu chưa có Oh My Zsh; trình cài có thể thay đổi `.zshrc`, nên sao lưu cấu hình hiện tại trước:

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

Sau đó, chỉ clone plugin chưa có (lệnh sẽ lỗi nếu thư mục đích đã tồn tại):
```bash
# zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-autosuggestions \
    ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

# zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-syntax-highlighting \
    ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

# agnosterzak theme: clone rồi sao chép file theme theo hướng dẫn tác giả
mkdir -p ~/.oh-my-zsh/custom/themes
git clone https://github.com/zakaziko99/agnosterzak-ohmyzsh-theme \
    ~/agnosterzak-ohmyzsh-theme
cp ~/agnosterzak-ohmyzsh-theme/agnosterzak.zsh-theme ~/.oh-my-zsh/custom/themes/
```

---

## 4. Cài đặt font

```bash
# Ví dụ một Nerd Font từ repo chính thức
sudo pacman -S --needed ttf-jetbrains-mono-nerd

# Refresh font cache
fc-cache -fv
```

---

## 5. Thiết lập màn hình (đã được xử lý bởi override)

`LaptopDisplay.conf` trong repo đã thiết lập:
```conf
monitor = eDP-1, preferred, auto, 1
```

Để chiếu giống laptop hoặc chỉ sử dụng màn hình ngoài, xem [hướng dẫn màn hình ngoài](man-hinh-ngoai.md). Tên cổng HDMI tùy thiết bị; kiểm tra bằng `hyprctl monitors`.

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
