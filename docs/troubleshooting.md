# 🛠️ Troubleshooting & Notes

Ghi lại các lỗi từng gặp trên hệ thống Arch Linux và cách xử lý.

---

## 1. Lỗi Pacman: "Error reading fd 7" khi chạy cache clean

- **Nguyên nhân:** Do file tải tạm thời bị kẹt trong session hiện tại.
- **Cách xử lý:** Bỏ qua vì không ảnh hưởng đến hệ thống, hoặc xóa thủ công:
  ```bash
  sudo rm -rf /var/cache/pacman/pkg/*.part
  ```

---

## 2. Lỗi kẹt driver (vd: NVIDIA / AMD)

- **Triệu chứng:** Màn hình đen sau khi boot, hoặc Hyprland không khởi động được.
- **Cách xử lý:**
  1. Boot vào TTY (Ctrl+Alt+F2)
  2. Kiểm tra log:
     ```bash
     journalctl -b -p err
     ```
  3. Nếu lỗi do driver NVIDIA, thử cài `nvidia-dkms` thay vì `nvidia`:
     ```bash
     sudo pacman -S nvidia-dkms nvidia-utils
     ```
  4. Rebuild initramfs:
     ```bash
     sudo mkinitcpio -P
     ```

---

## 3. Lỗi `yay` không build được package AUR

- **Triệu chứng:** `ERROR: One or more files did not pass the validity check!`
- **Nguyên nhân:** Keyring chưa được cập nhật.
- **Cách xử lý:**
  ```bash
  sudo pacman -Sy archlinux-keyring
  sudo pacman-key --populate archlinux
  ```

---

## 4. Stow báo lỗi xung đột file

- **Triệu chứng:** `WARNING! stowing <pkg> would cause conflicts`
- **Nguyên nhân:** File config gốc vẫn còn tồn tại (chưa được backup/xóa).
- **Cách xử lý:** `setup.sh` đã tự động backup vào `~/.dotfiles-backup/`. Nếu vẫn lỗi:
  ```bash
  stow --adopt -d ~/dotfiles -t ~ <tên_package>
  cd ~/dotfiles && git checkout -- <tên_package>/
  ```

---

## 5. Hyprland không nhận màn hình sau khi resume từ sleep

- **Triệu chứng:** Màn hình trắng/đen sau khi mở laptop.
- **Cách xử lý tạm thời:** `Super + Shift + E` để thoát, rồi đăng nhập lại.
- **Fix lâu dài:** Thêm vào `hyprland.conf`:
  ```
  misc {
      vfr = true
  }
  ```

---

*Cập nhật lần cuối: 2026-08-01*
