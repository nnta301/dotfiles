#!/bin/bash
echo "🧹 Bắt đầu dọn dẹp hệ thống Arch Linux..."

echo "1. Dọn dẹp cache của Pacman và Yay..."
# Lệnh này sẽ xóa các phiên bản cũ của phần mềm trong cache, 
# chỉ giữ lại phiên bản mới nhất đang được cài đặt.
sudo pacman -Sc --noconfirm
yay -Sc --noconfirm

# (Tuỳ chọn) Nếu bạn dùng pacman-contrib, bạn có thể dùng lệnh sau để giữ lại 3 phiên bản gần nhất đề phòng cần downgrade:
# paccache -r

echo "2. Dọn dẹp các gói mồ côi (Orphan packages)..."
# Gói mồ côi là những dependencies được tải về cho một phần mềm, 
# nhưng sau khi bạn xoá phần mềm đó thì chúng vẫn bị kẹt lại.
ORPHANS=$(pacman -Qtdq)
if [ -n "$ORPHANS" ]; then
    sudo pacman -Rns $ORPHANS --noconfirm
    echo "Đã xóa các gói mồ côi."
else
    echo "Không có gói mồ côi nào cần xóa."
fi

echo "3. Dọn dẹp Log hệ thống (Systemd Journal)..."
# Log hệ thống có thể chiếm vài GB nếu không giới hạn.
# Lệnh này xóa các log cũ và chỉ giữ lại tối đa 100MB.
sudo journalctl --vacuum-size=100M

echo "4. Xóa cache thư mục người dùng (Tuỳ chọn)..."
# Xoá bớt bộ nhớ tạm của các ứng dụng (như trình duyệt, IDE, npm, pip...)
rm -rf ~/.cache/yay/*
rm -rf ~/.local/share/Trash/*

echo "✨ Dọn dẹp hoàn tất! Hãy chạy lại 'df -h' để xem kết quả."
