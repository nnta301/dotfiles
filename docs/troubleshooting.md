# 🛠️ Troubleshooting & Notes

Ghi lại các lỗi từng gặp trên hệ thống Arch Linux và cách xử lý.

## Installer JaKooLit không tạo cấu hình

Khi chạy `./setup.sh` mà chưa có `hyprland.conf`, `setup.sh` tải và chạy installer JaKooLit từ thư mục `~/.cache/jakoolit-install.*/Arch-Hyprland` được in trên màn hình. Nếu installer lỗi hoặc kết thúc mà không có file cấu hình, setup dừng. Kiểm tra mạng, thông báo và log trong thư mục đó; xác nhận đã chọn `dots`, rồi chạy lại setup sau khi khắc phục. Script chỉ kiểm tra sự tồn tại của file, không xác nhận được phiên Hyprland có hoạt động hay không.

---

## 1. Lỗi Pacman: "Error reading fd 7" khi chạy cache clean

- **Nguyên nhân có thể xảy ra:** Các thư mục tải tạm `download-*` còn sót trong cache bị Pacman đọc như package. Chúng khác với các file `.part`.
- **Cách xử lý:** Chạy `./scripts/cleanup.sh --dry-run` để kiểm tra, sau đó chạy `./scripts/cleanup.sh`. Script chỉ xóa các thư mục `download-*` rỗng, cũ hơn 24 giờ và bỏ qua nếu phát hiện Pacman/Yay đang chạy hoặc có lock. Các thư mục còn dữ liệu được liệt kê để kiểm tra riêng. Không xóa lock hay file `.part` khi chưa xác định giao dịch đã kết thúc.

---

## 2. Lỗi kẹt driver (NVIDIA / AMD)

- **Triệu chứng:** Màn hình đen sau khi boot, hoặc Hyprland không khởi động được.
- **Cách xử lý:**
  1. Boot vào TTY (Ctrl+Alt+F2)
  2. Kiểm tra log:
     ```bash
     journalctl -b -p err
     ```
  3. Xác định GPU và driver NVIDIA đang dùng trước khi thay đổi. Máy cũ dùng `nvidia-open`, setup đã chỉnh bản installer tải về để cũng dùng `nvidia-open`. Nếu từng chạy installer JaKooLit riêng và đã có `nvidia-dkms`, setup vẫn dừng khi phát hiện xung đột; không tự gỡ driver đang chạy. Kiểm tra tài liệu driver cho phần cứng và kernel của bạn, không tự thay driver chỉ vì màn hình đen.

---

## 3. AUR báo lỗi kiểm tra nguồn khi build

`One or more files did not pass the validity check` không đủ để kết luận keyring Arch bị cũ. Đọc các dòng trước lỗi để phân biệt checksum không khớp, chữ ký PGP hoặc tải nguồn thất bại. Đối chiếu nguồn và PKGBUILD với maintainer; không dùng `--skipinteg` để bỏ qua lỗi. Key dùng ký nguồn AUR có thể thuộc keyring GPG của user, khác keyring package chính thức của Pacman. Xem [makepkg](https://man.archlinux.org/man/makepkg.8.en).

---

## 4. Stow báo lỗi xung đột file

- **Triệu chứng:** `WARNING! stowing <pkg> would cause conflicts`
- **Nguyên nhân:** File config gốc vẫn còn tồn tại (chưa được backup/xóa).
- **Cách xử lý:** `setup.sh` chuyển file trùng và `UserConfigs` cũ vào `~/.dotfiles-backup.*`. Nếu vẫn lỗi, xem thông báo Stow và xử lý từng symlink hoặc thư mục xung đột; script không tự chạy `--adopt` hay `git checkout`.

Nếu từng Stow từ checkout cũ, không xóa symlink hoặc chạy unstow từ checkout mới một cách máy móc. Xác định đường dẫn mà symlink đang trỏ tới (thay ví dụ bằng đúng đường dẫn có trong thông báo):

```bash
ls -ld ~/.config ~/.config/hypr ~/.config/nvim
readlink -f ~/.config/nvim
```

Nếu checkout cũ vẫn còn, kiểm tra nội dung và trạng thái Git của nó, sao lưu thay đổi cần giữ. Chỉ sau khi xác nhận symlink thực sự do checkout đó tạo, chạy `stow -n -D` từ checkout cũ với đúng package để xem trước; nếu kết quả đúng mới chạy lại không có `-n`. Ví dụ cho `nvim`, thay đường dẫn cũ bằng đường dẫn thực tế:

```bash
cd /duong/dan/checkout-cu
stow -n -D -t "$HOME" nvim
# Sau khi xem kỹ kết quả và xác nhận đúng:
stow -D -t "$HOME" nvim
```

Lặp lại riêng cho package bị ảnh hưởng. Nếu checkout cũ đã bị di chuyển/xóa hoặc symlink thuộc ứng dụng khác, không đoán nguồn và không dùng lệnh trên: kiểm tra từng liên kết, giữ bản sao cấu hình và xử lý thủ công. Sau đó chạy lại setup từ checkout mới; các file đã chuyển trước đó vẫn nằm trong thư mục backup mà setup đã in.

---

## 5. Hyprland báo lỗi deprecated dispatchers (JaKooLit upstream)

- **Triệu chứng:** Log Hyprland có cảnh báo về `togglesplit`, `pseudotile`, hay `vfr`.
- **Nguyên nhân:** JaKooLit upstream chưa cập nhật các dispatcher cũ.
- **Cách xử lý:** Kiểm tra thông báo cụ thể và hướng dẫn upstream trước khi sửa cấu hình. Sao lưu file, kiểm tra nó có phải symlink Stow hay không bằng `ls -l`; nếu file được repo quản lý, chỉnh bản trong repo. Không tự chạy các lệnh vá cũ trên mọi phiên bản. Xem [issue upstream](https://github.com/JaKooLit/Arch-Hyprland/issues).

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
  Repo không đặt `GTK_IM_MODULE` toàn cục để ứng dụng GTK chạy Wayland có thể dùng đường nhập liệu Wayland. GTK3/GTK4 vẫn có cơ chế IM module; lựa chọn phụ thuộc ứng dụng và compositor. Đối chiếu [Fcitx trên Wayland](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland), không coi lỗi riêng một ứng dụng là lý do đổi biến cho toàn phiên.

---

## 7. Neovim — lazy-lock.json tạo diff mỗi lần cập nhật plugin

- **Nguyên nhân:** `lazy-lock.json` lưu version hash của từng plugin, thay đổi mỗi lần `:Lazy update`.
- **Cách xử lý:** Repo lưu lockfile để khôi phục phiên bản plugin. Kiểm tra diff sau `:Lazy update` và commit nếu muốn giữ các phiên bản mới.

---

## 8. Màn hình đen sau sleep hoặc HDMI không nhận

Trong terminal/TTY còn truy cập được, xem `journalctl -b -p err`; trong phiên Hyprland kiểm tra `hyprctl monitors all`. Đọc [hướng dẫn màn hình ngoài](external-displays.md) về tên cổng và chế độ GPU. Lưu công việc trước khi đăng xuất/reboot. Không mặc định một phím tắt sẽ thoát phiên và không thêm `exec-once = hypridle` khi chưa kiểm tra cấu hình đã khởi chạy daemon hay chưa.

## 9. Backup/restore báo lỗi

- Backup cloud không có `manifest.json` qua remote crypt: bước bắt buộc chưa hoàn tất. Đọc lỗi đầu tiên và `REPORT.txt` nếu có; không dùng bản đó làm cơ sở format.
- Không xác định ESP: kiểm tra mount thực tế, Windows Boot Manager và phạm vi dual boot; không mount một phân vùng đoán mò để vượt kiểm tra.
- Checksum sai hoặc thiếu file: giữ nguyên bản gốc, kiểm tra remote, khóa crypt và kết nối OneDrive; không sửa checksum cho khớp để ép restore.
- Restore báo symlink/thư mục xung đột: kiểm tra đường dẫn đích; không xóa đích liên kết chỉ để tiếp tục. File đã thay thế nằm trong `~/.restore-backup-*`.

Xem [backup/restore](backup-restore.md) và [checklist cài lại](reinstall.md). Restore mặc định xem trước, chỉ ghi với `--apply`; EFI và `/etc` không tự phục hồi.

*Cập nhật lần cuối: 2026-11-05*
