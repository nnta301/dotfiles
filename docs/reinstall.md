# Chuẩn bị cài lại máy

Kiểm tra ngày 04/11/2026: máy dùng Arch, Hyprland JaKooLit, kernel Linux, `nvidia-open`, OneDrive client và có các phân vùng Windows/BitLocker. Đây là ảnh chụp tại thời điểm kiểm tra, cần đối chiếu lại trước khi cài.

## Trước khi cài

1. Sao lưu dữ liệu cá nhân, dự án, thư mục home và cấu hình ứng dụng ra ổ ngoài. Xác nhận mở được các file trong bản sao. Thư mục repo đang nằm trong `~/OneDrive`, trên cùng phân vùng Linux với hệ điều hành; không coi đó là bản sao độc lập.
2. Kiểm tra OneDrive đã đồng bộ đầy đủ bằng client và đối chiếu file trên dịch vụ. Dịch vụ `onedrive.service` được cấu hình bật ở máy cũ, nhưng điều đó không chứng minh toàn bộ dữ liệu đã được đồng bộ. Giữ thêm bản sao ngoại tuyến.
3. Commit các thay đổi cần giữ, push và kiểm tra chúng đã xuất hiện trên remote; cũng sao lưu repo ra ổ ngoài. Tại lần kiểm tra này nhánh local còn 2 commit chưa push và có thay đổi chưa commit.
4. Sao lưu riêng và bảo vệ bằng mã hóa những thứ không nằm trong repo: SSH/GPG keys, thông tin khôi phục 2FA, cấu hình và dữ liệu ứng dụng, database, profile trình duyệt, cấu hình VPN, kết nối mạng, và các credential cần thiết. Không commit secrets vào repo. Kiểm tra quyền truy cập tài khoản và mã khôi phục BitLocker trước khi thao tác phân vùng.
   Ghi lại tên người dùng, UID/GID và các nhóm cần dùng trước khi cài lại; đối chiếu quyền sở hữu khi khôi phục file từ bản sao. Xem bước tạo tài khoản trong [hướng dẫn cài đặt](cai-arch-tu-windows.md).
5. Xác nhận đúng ổ đĩa, phân vùng và điểm mount trong trình cài đặt. Máy có các phân vùng NTFS và BitLocker cùng ổ; tránh format nhầm Windows hoặc EFI. `/boot` hiện là phân vùng EFI chỉ 96 MB, còn khoảng 4 MB ở lần kiểm tra. Với trường hợp cài lại Arch cũ, làm [bước sao lưu EFI](cai-arch-tu-windows.md#02-sao-lưu-efi-trước-khi-cài-lại-arch-cũ) và [bước xử lý boot Arch cũ](cai-arch-tu-windows.md#41-lấy-lại-chỗ-từ-boot-arch-cũ-khi-efi-gần-đầy) theo đúng điều kiện trong hướng dẫn. Không format EFI hoặc tự xóa file Windows.

## Khôi phục sau khi cài

Nếu cài Arch song song và giữ Windows, xem [hướng dẫn dual boot từng bước](cai-arch-tu-windows.md), gồm nhánh cài lại trên phân vùng Arch cũ sau khi xác minh và sao lưu.

1. Cài Arch, mạng, driver và bootloader phù hợp với phần cứng; xác nhận cả hệ điều hành khác vẫn khởi động. Cài JaKooLit upstream theo README và xác nhận phiên Hyprland hoạt động.
2. Clone repo, chạy `./setup.sh`, chọn mục 1 để cài package, chuẩn bị shell và áp cấu hình. Script lưu các file trùng và thư mục `UserConfigs` cũ vào `~/.dotfiles-backup.*`; kiểm tra thông báo nếu Stow dừng do xung đột.
3. `packages/explicit-repo.txt` là danh sách 178 package chính thức được cài chủ động tại thời điểm kiểm tra; `packages/explicit-foreign.txt` là các gói ngoài repo được cài chủ động. `packages/all-foreign.txt` liệt kê cả các gói ngoài được cài làm dependency. Tên và nguồn package có thể thay đổi, nhất là gói `-git`; xem từng danh sách trước khi cài, không cài mù toàn bộ driver hoặc các gói JaKooLit cũ. `pkglist.txt` là danh sách setup.sh cài: dòng `aur/` dùng yay, các dòng khác dùng Pacman; không phải snapshot toàn bộ máy.
4. `packages/flatpak-apps.txt` ghi lại ID ứng dụng Flatpak; cần cấu hình remote và cài lại nếu muốn. Dữ liệu của các ứng dụng vẫn cần sao lưu riêng.
5. Kiểm tra Oh My Zsh, theme `agnosterzak`, plugins và bộ gõ sau khi chạy setup. Profile Fcitx5 đã được lưu trong repo. Cấu hình fastfetch và nhiều thành phần giao diện khác vẫn do JaKooLit quản lý; nếu đã chỉnh riêng, hãy sao lưu chúng từ máy cũ.
6. Đăng nhập lại OneDrive và các dịch vụ; khôi phục dữ liệu từ bản sao, kiểm tra project, bộ gõ và ứng dụng trước khi xóa bản sao cũ.

Repo không sao lưu dữ liệu cá nhân, tài khoản, cấu hình toàn hệ thống hay phiên bản JaKooLit upstream. Vì vậy cần giữ bản sao độc lập cho đến khi kiểm tra xong máy mới.
