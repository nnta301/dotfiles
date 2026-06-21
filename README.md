<div align="center">

# 🏗️ Arch Linux Dotfiles

**Cấu hình cá nhân cho Arch Linux + Hyprland + NVIDIA**

![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white)
![Hyprland](https://img.shields.io/badge/Hyprland-58E1FF?style=for-the-badge&logo=hyprland&logoColor=black)
![NVIDIA](https://img.shields.io/badge/NVIDIA-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-FFBC00?style=for-the-badge&logo=wayland&logoColor=black)

</div>

---

## 📋 Mục lục

- [Mục tiêu hệ thống](#-mục-tiêu-hệ-thống)
- [Thông tin hệ thống](#-thông-tin-hệ-thống)
- [Cài đặt Arch Linux từ đầu](#-cài-đặt-arch-linux-từ-đầu)
- [Cấu hình sau cài đặt](#-cấu-hình-sau-cài-đặt)
- [Áp dụng Dotfiles bằng GNU Stow](#-áp-dụng-dotfiles-bằng-gnu-stow)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Keybindings](#-keybindings)

---

## 🎯 Mục tiêu hệ thống

| Thành phần | Lựa chọn |
|---|---|
| **Distro** | Arch Linux (rolling release) |
| **Window Manager** | Hyprland (Wayland compositor) |
| **GPU Driver** | NVIDIA (proprietary) |
| **Terminal** | Kitty |
| **Shell** | Bash |
| **Status Bar** | Waybar |
| **Notifications** | Mako |
| **App Launcher** | Hyprlauncher |
| **File Manager** | Dolphin |
| **Input Method** | Fcitx5 + Bamboo (Tiếng Việt) |
| **Audio** | PipeWire |
| **Screenshot** | Grim + Slurp + Swappy |
| **Dotfiles Manager** | GNU Stow |

---

## 💻 Thông tin hệ thống

```
OS:       Arch Linux (x86_64)
WM:       Hyprland (Wayland)
GPU:      NVIDIA (proprietary driver)
Terminal: Kitty
Shell:    Bash
Editor:   Neovim
```

---

## 🔧 Cài đặt Arch Linux từ đầu

> **📖 Tài liệu tham khảo chính:**
> [Arch Wiki - Installation Guide](https://wiki.archlinux.org/title/Installation_guide)

### Bước 0: Chuẩn bị USB Boot

1. **Tải ISO Arch Linux** từ [archlinux.org/download](https://archlinux.org/download/)
2. **Tạo USB bootable:**
   - **Linux/macOS:**
     ```bash
     # Xác định USB (thường là /dev/sdX)
     lsblk
     
     # Ghi ISO vào USB (⚠️ thay /dev/sdX bằng thiết bị USB thực tế)
     sudo dd bs=4M if=archlinux-*.iso of=/dev/sdX status=progress oflag=sync
     ```
   - **Windows:** Sử dụng [Rufus](https://rufus.ie/) hoặc [Ventoy](https://www.ventoy.net/)
3. **Boot vào USB:** Khởi động lại → vào BIOS (F2/F12/DEL) → chọn boot từ USB

---

### Bước 1: Thiết lập ban đầu trong Live Environment

```bash
# ── Kiểm tra chế độ boot (UEFI) ──
# Nếu thư mục tồn tại → đang boot UEFI ✅
cat /sys/firmware/efi/fw_platform_size

# ── Kết nối Internet ──
# Ethernet: tự động kết nối
# Wi-Fi:
iwctl
  station wlan0 scan
  station wlan0 get-networks
  station wlan0 connect "TÊN_WIFI"
  exit

# Kiểm tra kết nối
ping -c 3 archlinux.org

# ── Đồng bộ thời gian ──
timedatectl set-ntp true
timedatectl status
```

---

### Bước 2: Phân vùng ổ đĩa

```bash
# Xem danh sách ổ đĩa
lsblk

# Phân vùng với fdisk hoặc cfdisk (giao diện trực quan hơn)
cfdisk /dev/nvme0n1    # hoặc /dev/sda
```

**Bảng phân vùng đề xuất (UEFI + GPT):**

| Phân vùng | Loại | Kích thước | Mount point |
|---|---|---|---|
| `/dev/nvme0n1p1` | EFI System | 512M - 1G | `/boot/efi` |
| `/dev/nvme0n1p2` | Linux swap | = RAM hoặc RAM×1.5 | `[SWAP]` |
| `/dev/nvme0n1p3` | Linux filesystem | Phần còn lại | `/` |

```bash
# ── Format phân vùng ──
mkfs.fat -F32 /dev/nvme0n1p1      # EFI
mkswap /dev/nvme0n1p2              # Swap
mkfs.ext4 /dev/nvme0n1p3           # Root (hoặc mkfs.btrfs cho Btrfs)

# ── Mount phân vùng ──
mount /dev/nvme0n1p3 /mnt
mount --mkdir /dev/nvme0n1p1 /mnt/boot/efi
swapon /dev/nvme0n1p2
```

---

### Bước 3: Cài đặt hệ thống cơ bản

```bash
# ── Chọn mirror gần nhất (tùy chọn) ──
reflector --country Vietnam,Singapore,Japan --sort rate --save /etc/pacman.d/mirrorlist

# ── Cài đặt base system ──
pacstrap -K /mnt base base-devel linux linux-headers linux-firmware \
    networkmanager grub efibootmgr sudo neovim git
```

---

### Bước 4: Cấu hình hệ thống

```bash
# ── Tạo fstab ──
genfstab -U /mnt >> /mnt/etc/fstab

# ── Chroot vào hệ thống mới ──
arch-chroot /mnt
```

**Bên trong chroot:**

```bash
# ── Timezone ──
ln -sf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime
hwclock --systohc

# ── Locale ──
# Mở /etc/locale.gen và uncomment:
#   en_US.UTF-8 UTF-8
#   vi_VN.UTF-8 UTF-8
sed -i 's/^#en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
sed -i 's/^#vi_VN.UTF-8/vi_VN.UTF-8/' /etc/locale.gen
locale-gen

echo "LANG=en_US.UTF-8" > /etc/locale.conf

# ── Hostname ──
echo "archlinux" > /etc/hostname

# ── Hosts file ──
cat >> /etc/hosts << EOF
127.0.0.1   localhost
::1         localhost
127.0.1.1   archlinux.localdomain archlinux
EOF

# ── Mật khẩu root ──
passwd

# ── Tạo user thường ──
useradd -m -G wheel -s /bin/bash nnta
passwd nnta

# Cho phép user dùng sudo
EDITOR=nvim visudo
# → Uncomment dòng: %wheel ALL=(ALL:ALL) ALL

# ── Cài bootloader (GRUB) ──
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg

# ── Bật NetworkManager ──
systemctl enable NetworkManager

# ── Thoát chroot & khởi động lại ──
exit
umount -R /mnt
reboot
```

> ⚠️ **Rút USB ra trước khi máy khởi động lại!**

---

## ⚙️ Cấu hình sau cài đặt

### Bước 5: Đăng nhập và cài đặt packages

```bash
# Đăng nhập bằng user đã tạo
# Kết nối Wi-Fi (nếu cần)
nmtui

# ── Cài đặt toàn bộ packages từ danh sách ──
# Lọc bỏ comment và dòng trống, rồi cài
grep -v '^#\|^$' ~/dotfiles/pkglist.txt | sudo pacman -S --needed -

# ── Hoặc cài thủ công theo nhóm ──
# NVIDIA
sudo pacman -S nvidia nvidia-utils nvidia-settings libva-nvidia-driver

# Hyprland + Wayland
sudo pacman -S hyprland xdg-desktop-portal-hyprland xdg-desktop-portal-gtk \
    wayland wayland-protocols qt5-wayland qt6-wayland xdg-utils

# Terminal
sudo pacman -S kitty

# Audio (PipeWire)
sudo pacman -S pipewire pipewire-alsa pipewire-pulse pipewire-jack wireplumber

# Input Method (Tiếng Việt)
sudo pacman -S fcitx5 fcitx5-gtk fcitx5-qt fcitx5-configtool
yay -S fcitx5-bamboo    # AUR package

# Utilities
sudo pacman -S stow grim slurp swappy wl-clipboard waybar mako \
    playerctl brightnessctl polkit-gnome hyprlauncher
```

### Bước 6: Cài đặt AUR Helper (tùy chọn)

```bash
# Cài yay
git clone https://aur.archlinux.org/yay.git /tmp/yay
cd /tmp/yay && makepkg -si
```

### Bước 7: Bật các service cần thiết

```bash
# Bluetooth
sudo systemctl enable --now bluetooth.service

# PipeWire (chạy ở user-level, không cần sudo)
systemctl --user enable --now pipewire.service
systemctl --user enable --now pipewire-pulse.service
systemctl --user enable --now wireplumber.service
```

---

## 🔗 Áp dụng Dotfiles bằng GNU Stow

[GNU Stow](https://www.gnu.org/software/stow/) tạo symlink từ thư mục dotfiles vào `$HOME`, giúp quản lý config dễ dàng với Git.

### Nguyên lý hoạt động

```
~/dotfiles/hypr/.config/hypr/hyprland.conf
    ↓ stow hypr
~/.config/hypr/hyprland.conf → symlink tới dotfiles
```

### Cách sử dụng

```bash
# 1. Clone repo
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles

# 2. Cài đặt tự động (khuyến nghị)
chmod +x setup.sh
./setup.sh

# ── Hoặc áp dụng thủ công từng package ──
stow bash           # → ~/.bashrc, ~/.bash_profile
stow hypr           # → ~/.config/hypr/hyprland.conf
stow waybar         # → ~/.config/waybar/{config.jsonc,style.css}

# Áp dụng tất cả packages cùng lúc
stow */

# 3. Gỡ symlink (khi cần)
stow -D hypr        # Xóa symlink của package hypr

# 4. Áp dụng lại (khi thêm file mới)
stow -R hypr        # Restow = xóa rồi tạo lại symlink
```

### Xử lý xung đột

Nếu file config đã tồn tại ở `$HOME` trước khi stow, cần backup rồi xóa:

```bash
# Backup config cũ
mv ~/.config/hypr/hyprland.conf ~/.config/hypr/hyprland.conf.bak

# Sau đó stow lại
stow hypr
```

---

## 📁 Cấu trúc thư mục

```
dotfiles/
├── 📄 .gitignore             ← Loại bỏ file không cần thiết
├── 📄 README.md              ← File này
├── 📄 pkglist.txt            ← Danh sách packages
├── 📄 setup.sh               ← Script tự động cài đặt
│
├── 📂 bash/                   ← Stow package: Bash
│   ├── .bashrc
│   └── .bash_profile
│
├── 📂 hypr/                   ← Stow package: Hyprland
│   └── .config/
│       └── hypr/
│           └── hyprland.conf
│
└── 📂 waybar/                 ← Stow package: Waybar
    └── .config/
        └── waybar/
            ├── config.jsonc
            └── style.css
```

> 💡 **Thêm config mới:** Tạo thư mục con theo cấu trúc tương đối từ `$HOME`, rồi chạy `stow <tên_thư_mục>`.

---

## ⌨️ Keybindings

| Phím tắt | Hành động |
|---|---|
| `SUPER + Q` | Mở terminal (Kitty) |
| `SUPER + C` | Đóng cửa sổ |
| `SUPER + E` | Mở file manager (Dolphin) |
| `SUPER + R` | Mở app launcher |
| `SUPER + V` | Toggle floating |
| `SUPER + M` | Thoát Hyprland |
| `SUPER + [1-0]` | Chuyển workspace 1-10 |
| `SUPER + SHIFT + [1-0]` | Di chuyển cửa sổ sang workspace |
| `SUPER + Arrow Keys` | Di chuyển focus |
| `SUPER + SHIFT + Arrow Keys` | Di chuyển cửa sổ |
| `Print` | Screenshot toàn màn hình |
| `SUPER + SHIFT + S` | Screenshot vùng chọn |
| `SUPER + Print` | Screenshot vùng chọn → Swappy |
| `XF86Audio*` | Điều chỉnh âm lượng |
| `XF86MonBrightness*` | Điều chỉnh độ sáng |

---

## 📜 License

Cấu hình cá nhân, tự do sử dụng và chỉnh sửa.

---

<div align="center">

*Made with ❤️ on Arch Linux*

</div>
