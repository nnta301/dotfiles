# 🛠️ Troubleshooting & Notes

Ghi lại các lỗi từng gặp trên hệ thống Arch Linux và cách xử lý.

---

## 1. Lỗi Pacman: "Error reading fd 7" khi chạy cache clean

- **Nguyên nhân:** File tải tạm thời bị kẹt trong session hiện tại.
- **Cách xử lý:** Bỏ qua vì không ảnh hưởng đến hệ thống, hoặc xóa thủ công:
  ```bash
  sudo rm -rf /var/cache/pacman/pkg/*.part
  ```

---

## 2. Lỗi kẹt driver (NVIDIA / AMD)

- **Triệu chứng:** Màn hình đen sau khi boot, hoặc Hyprland không khởi động được.
- **Cách xử lý:**
  1. Boot vào TTY (Ctrl+Alt+F2)
  2. Kiểm tra log:
     ```bash
     journalctl -b -p err
     ```
  3. Nếu lỗi do driver NVIDIA, thử cài `nvidia-dkms`:
     ```bash
     sudo pacman -S nvidia-dkms nvidia-utils
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

## 5. Hyprland báo lỗi deprecated dispatchers (JaKooLit upstream)

- **Triệu chứng:** Log Hyprland có cảnh báo về `togglesplit`, `pseudotile`, hay `vfr`.
- **Nguyên nhân:** JaKooLit upstream chưa cập nhật các dispatcher cũ.
- **Cách xử lý tạm thời:**
  ```bash
  sed -i '/togglesplit/s/^/#/' ~/.config/hypr/UserConfigs/UserKeybinds.conf
  sed -i '/pseudotile/s/^/#/'  ~/.config/hypr/UserConfigs/UserKeybinds.conf
  sed -i '/^\s*vfr\s*=/s/^/#/' ~/.config/hypr/hyprland.conf
  ```
  > Kiểm tra upstream đã fix chưa: https://github.com/JaKooLit/Arch-Hyprland/issues

---

## 6. Fcitx5 không hoạt động trong ứng dụng Qt hoặc X11

- **Triệu chứng:** Không gõ được tiếng Việt trong các ứng dụng Qt (qBittorrent, etc.).
- **Cách kiểm tra:**
  ```bash
  # Kiểm tra fcitx5 đang chạy
  pgrep fcitx5

  # Kiểm tra biến môi trường
  env | grep -E 'IM_MODULE|XMODIFIERS'
  ```
- **Cách xử lý:** Đảm bảo `ENVariables.conf` có đúng nội dung:
  ```conf
  env = QT_IM_MODULE, fcitx
  env = XMODIFIERS, @im=fcitx
  ```
  **Không** set `GTK_IM_MODULE` — GTK4 không dùng biến này nữa (gây lỗi).

---

## 7. Neovim — lazy-lock.json tạo diff mỗi lần cập nhật plugin

- **Nguyên nhân:** `lazy-lock.json` lưu version hash của từng plugin, thay đổi mỗi lần `:Lazy update`.
- **Cách xử lý:** File này đã được exclude trong `.gitignore`. Nếu muốn pin versions:
  ```bash
  # Bỏ ignore tạm thời để commit
  git add -f nvim/.config/nvim/lazy-lock.json
  git commit -m "chore(nvim): pin plugin versions YYYY-MM-DD"
  ```

---

## 8. Hyprland không nhận màn hình sau khi resume từ sleep

- **Triệu chứng:** Màn hình trắng/đen sau khi mở laptop.
- **Cách xử lý tạm thời:** `SUPER + M` để thoát, rồi đăng nhập lại.
- **Fix lâu dài:** Kiểm tra JaKooLit upstream có script `swayidle` hoặc `hypridle` không,
  hoặc thêm vào `UserConfigs/Startup_Apps.conf`:
  ```conf
  exec-once = hypridle
  ```

---

*Cập nhật lần cuối: 2026-08-09*
