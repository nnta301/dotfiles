# Rà soát ngày 05/11/2026

## Các lỗi đã xử lý

- Restore home: tải file thay thế vào file tạm, kiểm tra kích thước trước khi di chuyển file cũ; thiếu dung lượng thì dừng trước khi ghi. Chặn đích nằm trên filesystem khác mount dưới home. Đọc theo thứ tự archive để giảm tải lại chunk qua mạng.
- Backup cloud: nhận diện thư mục sync OneDrive từ cấu hình hoặc `--onedrive-dir`, loại thư mục chứa backup cũ; báo lỗi nếu đường dẫn được chọn không tồn tại. Giới hạn kích thước tải từng object và kiểm tra chunk trùng tên/checksum.
- Setup: kiểm tra symlink cha trước khi di chuyển `UserConfigs`; kiểm tra cú pháp riêng từng script upstream; phát hiện các gói NVIDIA xung đột với `nvidia-open`.
- Đổi alias mở OneDrive web sang `onedrive-web`, tránh che lệnh client `onedrive`.
- Bỏ mã ví dụ LazyVim không bao giờ được chạy, giữ plugin TeXpresso trong `texpresso.lua`. Ghi rõ binary TeXpresso cài ngoài repo cần cài lại riêng.
- Đổi gói IntelliJ sang `intellij-idea-oss`. Database Extra hiện hành khai báo gói này thay thế/cung cấp `intellij-idea-community-edition`; không sửa snapshot package lịch sử trong `packages/`.

## Đối chiếu upstream và giới hạn

Đã đối chiếu tên 183 gói chính thức với database Core/Extra tải từ mirror Arch, và 23 gói AUR qua RPC. Sau đổi tên IntelliJ, các tên gói đều có trong nguồn tương ứng tại thời điểm kiểm tra. Đây là kiểm tra sự tồn tại, không chứng minh tất cả gói build/cài thành công cùng nhau. AUR đang đánh dấu outdated cho `hyde-cli-git`, `teamviewer`, `zsh-theme-powerlevel10k-git`; giữ nguyên theo danh sách ứng dụng đã chọn, cần đọc PKGBUILD và lỗi build nếu phát sinh.

JaKooLit thông báo chuyển bảo trì sang LinuxBeginnings. Script NVIDIA của hai nguồn được kiểm tra vẫn chứa `nvidia-dkms`; setup hiện có điều chỉnh có kiểm tra cho máy dùng `nvidia-open`. Chưa chuyển fork tự động vì chưa thử bộ cấu hình mới với overlay này. Việc installer kết thúc và tạo `hyprland.conf` không đủ chứng minh mọi thành phần cài thành công: vẫn cần xem log, khởi động thử desktop rồi mới áp overlay.

Máy đang chạy Hyprland 0.56.2 và `hyprctl configerrors` không báo lỗi. Điều này không thay thế thử HDMI, đăng nhập đồ họa hay cài mới. Các liên kết Hyprland 0.54.0 trong hướng dẫn màn hình được ghi rõ phiên bản thay vì coi đó là tài liệu mới nhất. Giữ lockfile Neovim để có thể khôi phục phiên bản plugin; chưa nâng đồng loạt plugin chỉ để lấy phiên bản mới nhất.

Kiểm thử tự động bao gồm restore khi mất mạng/thiếu dung lượng, archive traversal, chunk/checksum, export hệ thống, GNU tar, rclone crypt trên đích local tạm và các chốt kiểm tra setup. Chạy lại bằng:

```bash
python3 -m unittest discover -s tests -v
```

**Chưa kiểm thử backup/restore với tài khoản OneDrive thật và chưa cài lại đầy đủ trên máy/VM trống.** Phải tạo backup hoàn tất, chạy restore dry-run và giữ khóa crypt truy cập được từ ngoài Arch trước khi format. Kiểm tra dung lượng chỉ là ảnh chụp tại thời điểm chạy; tiến trình khác vẫn có thể làm đầy ổ. Export hệ thống bị ngắt có thể để lại file tải dở trong thư mục đích: chỉ dùng khi lệnh kết thúc thành công. Restore home không rollback toàn bộ các file đã phục hồi trước một lỗi.

## Nguồn đối chiếu

- [Arch: IntelliJ IDEA OSS](https://archlinux.org/packages/extra/x86_64/intellij-idea-oss/), [database Extra](https://geo.mirror.pkgbuild.com/extra/os/x86_64/extra.db).
- [AUR RPC](https://aur.archlinux.org/rpc), [hyde-cli-git](https://aur.archlinux.org/packages/hyde-cli-git), [TeamViewer](https://aur.archlinux.org/packages/teamviewer), [Powerlevel10k git](https://aur.archlinux.org/packages/zsh-theme-powerlevel10k-git).
- [JaKooLit installer](https://github.com/JaKooLit/Arch-Hyprland), [LinuxBeginnings installer](https://github.com/LinuxBeginnings/Arch-Hyprland).
- [rclone cat và giới hạn đọc](https://rclone.org/commands/rclone_cat/), [rclone crypt](https://rclone.org/crypt/).
- [TeXpresso Neovim](https://github.com/let-def/texpresso.vim), [Lazy lockfile](https://lazy.folke.io/usage/lockfile).
