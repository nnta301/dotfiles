# Rà soát ngày 05/11/2026

## Cập nhật sau rà soát

Đã xử lý thêm: từ chối crypt tắt mã hóa nội dung; chặn từng lựa chọn home tường minh bị loại; export kiểm tra dung lượng và chỉ đặt tên file hoàn chỉnh sau checksum; tạo từng thư mục restore mới với quyền 700; bổ sung ignore cho cấu hình và archive backup; bỏ luồng tạo backup local trùng lặp nhưng giữ restore backup cũ. `rclone` và `config` có thể chứa bí mật; `.gitignore` chỉ giảm nguy cơ, không thay việc kiểm tra `git diff --cached` trước commit.

Ngày 06/11/2026, [Arch Extra cung cấp Hyprland 0.57.1](https://archlinux.org/packages/extra/x86_64/hyprland/), trong khi máy cũ đã kiểm tra trên 0.56.2; chưa xác nhận overlay chạy trên 0.57.1. Theo thông báo upstream, JaKooLit đã chuyển bảo trì; bản gốc cũ có thể không tương thích Arch/Hyprland mới, còn LinuxBeginnings có thay đổi cấu hình lớn. Chưa kiểm thử toàn bộ overlay `.conf` với bản mới; không tự chuyển fork hoặc ghim revision chưa kiểm chứng. Cần thử VM/cài mới trước khi xóa hệ thống đang dùng.

Installer JaKooLit vẫn tải nhánh hiện hành. Chưa ghim revision vì chưa kiểm thử cài mới một revision cụ thể; xem đây là giới hạn cần xử lý trước khi format. Wiki Hyprland hiện tại dùng cú pháp mới, liên kết phiên bản cũ vẫn giữ cho các lệnh đang được hướng dẫn.

## Đối chiếu audit bổ sung

ChunkReader kiểm tra SHA-256 mỗi chunk khi tải, kể cả sau bước verify toàn bộ; có test giả lập chunk bị đổi giữa hai lần đọc. Chưa có bằng chứng định dạng cloud v2 hợp lệ từng được tạo với thiếu archive bắt buộc, nên không nới điều kiện manifest hoàn tất. Backup local cũ vẫn có luồng restore riêng.

Setup chỉ sửa thông báo NVIDIA đúng mẫu đã kiểm tra và từ chối khi installer thay đổi; nếu danh sách không có `nvidia-open`, installer giữ driver upstream và người dùng phải xác định lựa chọn phù hợp. Đã bỏ gói `oh-my-zsh-git` khỏi danh sách vì shell dùng bản clone trong home; không tự gỡ gói đã cài. Xem cách xử lý Stow từ checkout cũ trong troubleshooting. So sánh `/etc` đang hoạt động có thể thất bại nếu nguồn thay đổi; không hạ lỗi này thành cảnh báo thành công vì chưa xác minh được bản sao khớp nguồn.

## Các lỗi đã xử lý

- Restore home: tải file thay thế vào file tạm, kiểm tra kích thước trước khi di chuyển file cũ; thiếu dung lượng thì dừng trước khi ghi. Chặn đích nằm trên filesystem khác mount dưới home. Đọc theo thứ tự archive để giảm tải lại chunk qua mạng.
- Backup cloud: nhận diện thư mục sync OneDrive từ cấu hình hoặc `--onedrive-dir`, loại thư mục chứa backup cũ; báo lỗi nếu đường dẫn được chọn không tồn tại. Giới hạn kích thước tải từng object và kiểm tra chunk trùng tên/checksum.
- Setup: kiểm tra symlink cha trước khi di chuyển `UserConfigs`; kiểm tra cú pháp riêng từng script upstream; phát hiện các gói NVIDIA xung đột với `nvidia-open`.
- Đổi alias mở OneDrive web sang `onedrive-web`, tránh che lệnh client `onedrive`.
- Bỏ mã ví dụ LazyVim không bao giờ được chạy, giữ plugin TeXpresso trong `texpresso.lua`. Ghi rõ binary TeXpresso cài ngoài repo cần cài lại riêng.
- Đổi gói IntelliJ sang `intellij-idea-oss`. Database Extra hiện hành khai báo gói này thay thế/cung cấp `intellij-idea-community-edition`; không sửa snapshot package lịch sử trong `packages/`.

## Đối chiếu upstream và giới hạn

Trong lần rà soát ngày 05/11/2026, đã đối chiếu 183 gói chính thức với database Core/Extra và 23 gói AUR qua RPC; con số và cờ outdated chỉ là ảnh chụp của lần kiểm tra đó, không phản ánh danh sách hoặc kho hiện tại. Sau đổi tên IntelliJ, các tên gói đều có trong nguồn tương ứng tại thời điểm kiểm tra. Đây là kiểm tra sự tồn tại, không chứng minh tất cả gói build/cài thành công cùng nhau. AUR đang đánh dấu outdated cho `hyde-cli-git`, `teamviewer`, `zsh-theme-powerlevel10k-git`; giữ nguyên theo danh sách ứng dụng đã chọn, cần đọc PKGBUILD và lỗi build nếu phát sinh.

JaKooLit thông báo chuyển bảo trì sang LinuxBeginnings. Script NVIDIA của hai nguồn được kiểm tra vẫn chứa `nvidia-dkms`; setup hiện có điều chỉnh có kiểm tra cho máy dùng `nvidia-open`. Chưa chuyển fork tự động vì chưa thử bộ cấu hình mới với overlay này. Việc installer kết thúc và tạo `hyprland.conf` không đủ chứng minh mọi thành phần cài thành công: vẫn cần xem log, khởi động thử desktop rồi mới áp overlay.

Máy đang chạy Hyprland 0.56.2 và `hyprctl configerrors` không báo lỗi. Điều này không thay thế thử HDMI, đăng nhập đồ họa hay cài mới. Các liên kết Hyprland 0.54.0 trong hướng dẫn màn hình được ghi rõ phiên bản thay vì coi đó là tài liệu mới nhất. Giữ lockfile Neovim để có thể khôi phục phiên bản plugin; chưa nâng đồng loạt plugin chỉ để lấy phiên bản mới nhất.

Kiểm thử tự động bao gồm restore khi mất mạng/thiếu dung lượng, archive traversal, chunk/checksum, export hệ thống, GNU tar, rclone crypt trên đích local tạm và các chốt kiểm tra setup. Chạy lại bằng:

```bash
python3 -m unittest discover -s tests -v
```

**Chưa kiểm thử backup/restore với tài khoản OneDrive thật và chưa cài lại đầy đủ trên máy/VM trống.** Phải tạo backup hoàn tất, chạy restore dry-run và giữ khóa crypt truy cập được từ ngoài Arch trước khi format. Kiểm tra dung lượng chỉ là ảnh chụp tại thời điểm chạy; tiến trình khác vẫn có thể làm đầy ổ. Export hệ thống bị ngắt có thể để lại thư mục đích chứa các archive đã hoàn thành; chỉ coi toàn bộ export là thành công khi lệnh kết thúc không lỗi. Restore home không rollback toàn bộ các file đã phục hồi trước một lỗi.

## Nguồn đối chiếu

- [Arch: IntelliJ IDEA OSS](https://archlinux.org/packages/extra/x86_64/intellij-idea-oss/), [database Extra](https://geo.mirror.pkgbuild.com/extra/os/x86_64/extra.db).
- [AUR RPC](https://aur.archlinux.org/rpc), [hyde-cli-git](https://aur.archlinux.org/packages/hyde-cli-git), [TeamViewer](https://aur.archlinux.org/packages/teamviewer), [Powerlevel10k git](https://aur.archlinux.org/packages/zsh-theme-powerlevel10k-git).
- [JaKooLit installer](https://github.com/JaKooLit/Arch-Hyprland), [LinuxBeginnings installer](https://github.com/LinuxBeginnings/Arch-Hyprland).
- [rclone cat và giới hạn đọc](https://rclone.org/commands/rclone_cat/), [rclone crypt](https://rclone.org/crypt/).
- [TeXpresso Neovim](https://github.com/let-def/texpresso.vim), [Lazy lockfile](https://lazy.folke.io/usage/lockfile).
