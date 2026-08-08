<div align="center">

# 🏗️ Arch Linux Dotfiles

**Cấu hình cá nhân cho Arch Linux + Hyprland**

![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white)
![Hyprland](https://img.shields.io/badge/Hyprland-58E1FF?style=for-the-badge&logo=hyprland&logoColor=black)
![Wayland](https://img.shields.io/badge/Wayland-FFBC00?style=for-the-badge&logo=wayland&logoColor=black)

</div>

---

## 📐 Triết lý kiến trúc (Architecture Philosophy)

Repo này **không** lưu trữ toàn bộ cấu hình Hyprland. Thay vào đó, nó hoạt động như một lớp **override** (ghi đè) cá nhân chồng lên cấu hình upstream của [JaKooLit](https://github.com/JaKooLit/Arch-Hyprland).

```
[JaKooLit Upstream]  +  [Repo này - UserConfigs Override]
        ↓                            ↓
   Core config            Cài đặt phần cứng & cá nhân
   (không track)          (eDP-1 scale, fcitx5, EN vars)
```

**Ưu điểm:**
- ✅ Luôn nhận được bản cập nhật và sửa lỗi từ upstream JaKooLit
- ✅ Cấu hình cá nhân được version control riêng, nhỏ gọn
- ✅ Dễ tái cài đặt: chạy script upstream → áp dụng override này

---

## 📋 Mục lục

- [Thông tin hệ thống](#-thông-tin-hệ-thống)
- [Workflow cài đặt lại hệ thống](#-workflow-cài-đặt-lại-hệ-thống)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Chi tiết các UserConfigs Override](#-chi-tiết-các-userconfigs-override)
- [Keybindings](#-keybindings)

---

## 💻 Thông tin hệ thống

| Thành phần | Lựa chọn |
|---|---|
| **Distro** | Arch Linux (rolling release) |
| **Window Manager** | Hyprland (JaKooLit ecosystem) |
| **Terminal** | Kitty |
| **Shell** | Bash |
| **Status Bar** | Waybar |
| **Input Method** | Fcitx5 + Bamboo (Tiếng Việt) |
| **Audio** | PipeWire |
| **Dotfiles Manager** | GNU Stow |

---

## 🚀 Workflow cài đặt lại hệ thống

### Bước 1: Cài đặt JaKooLit Hyprland (Upstream)

> Đây là nguồn gốc của toàn bộ cấu hình Hyprland core. **Chạy script này trước.**

```bash
git clone --depth=1 https://github.com/JaKooLit/Arch-Hyprland.git ~/JaKooLit-Arch
cd ~/JaKooLit-Arch
chmod +x install.sh
./install.sh
```

Script sẽ tự động cài đặt Hyprland, waybar, và tất cả các phụ thuộc cần thiết,
đồng thời tạo ra các file cấu hình mặc định trong `~/.config/hypr/`.

---

### Bước 2: Sửa lỗi Deprecated Dispatchers (nếu cần)

> ⚠️ Nếu Hyprland phiên bản mới báo lỗi về các dispatcher/keyword đã deprecated
> từ upstream JaKooLit (ví dụ `togglesplit`, `pseudotile`, `vfr`),
> hãy chạy các lệnh sau để comment chúng ra tạm thời:

```bash
# Comment out 'togglesplit' dispatcher (deprecated → use layoutmsg)
sed -i '/togglesplit/s/^/#/' ~/.config/hypr/UserConfigs/UserKeybinds.conf

# Comment out 'pseudotile' dispatcher (deprecated → use layoutmsg)
sed -i '/pseudotile/s/^/#/' ~/.config/hypr/UserConfigs/UserKeybinds.conf

# Comment out 'vfr' misc option (deprecated)
sed -i '/^\s*vfr\s*=/s/^/#/' ~/.config/hypr/hyprland.conf
```

> 💡 Kiểm tra upstream đã cập nhật chưa trước khi áp dụng:
> [JaKooLit Issues](https://github.com/JaKooLit/Arch-Hyprland/issues)

---

### Bước 3: Áp dụng Personal Override (Repo này)

Clone repo này và dùng GNU Stow để symlink phần `UserConfigs` override vào đúng vị trí:

```bash
# Clone repo cá nhân
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles

# Xóa UserConfigs mặc định từ upstream (sẽ được thay bằng symlink)
rm -rf ~/.config/hypr/UserConfigs

# Áp dụng Hyprland UserConfigs override qua stow
stow hypr

# Áp dụng các config khác
stow bash
stow waybar
```

Sau khi stow, cấu trúc symlink sẽ là:

```
~/.config/hypr/UserConfigs/ → ~/dotfiles/hypr/.config/hypr/UserConfigs/
~/.config/waybar/            → ~/dotfiles/waybar/.config/waybar/
~/.bashrc                    → ~/dotfiles/bash/.bashrc
```

> Khởi động lại Hyprland để áp dụng tất cả thay đổi: `SUPER + M` → đăng nhập lại.

---

## 📁 Cấu trúc thư mục

```
dotfiles/
├── 📄 .gitignore
├── 📄 README.md              ← File này
├── 📄 pkglist.txt            ← Danh sách packages
├── 📄 setup.sh               ← Script tự động cài đặt (tùy chọn)
│
├── 📂 bash/                  ← Stow package: Bash
│   ├── .bashrc
│   └── .bash_profile
│
├── 📂 hypr/                  ← Stow package: Hyprland OVERRIDE
│   └── .config/
│       └── hypr/
│           └── UserConfigs/  ← CHỈ track folder này (không track core!)
│               ├── LaptopDisplay.conf    ← Monitor eDP-1 scale fix
│               ├── Startup_Apps.conf     ← exec-once = fcitx5 -d
│               ├── ENVariables.conf      ← QT_IM_MODULE, XMODIFIERS
│               ├── 01-UserDefaults.conf
│               ├── UserKeybinds.conf
│               ├── UserSettings.conf
│               ├── UserAnimations.conf
│               ├── UserDecorations.conf
│               ├── WindowRules.conf
│               ├── WorkSpaceRules.conf
│               └── Laptops.conf
│
└── 📂 waybar/                ← Stow package: Waybar
    └── .config/
        └── waybar/
            ├── config.jsonc
            └── style.css
```

---

## 🔧 Chi tiết các UserConfigs Override

### `LaptopDisplay.conf` — Cấu hình màn hình laptop

```conf
monitor = eDP-1, preferred, auto, 1
```

Thiết lập scale `1` (100%) cho màn hình nội bộ `eDP-1`. Scale mặc định của JaKooLit
có thể là `1.5` hoặc `2` tuỳ thiết bị.

---

### `Startup_Apps.conf` — Khởi động ứng dụng

```conf
exec-once = fcitx5 -d
```

Tự động khởi động Fcitx5 ở chế độ daemon khi Hyprland bắt đầu. Cần thiết để nhập
liệu tiếng Việt bằng bộ gõ Bamboo.

---

### `ENVariables.conf` — Biến môi trường Input Method

Các biến được thêm vào để Fcitx5 hoạt động đúng với các ứng dụng Qt/X11:

```conf
env = QT_IM_MODULE, fcitx
env = XMODIFIERS, @im=fcitx
```

> ⚠️ **Lưu ý:** `GTK_IM_MODULE` **không** được set ở đây.
> Kể từ GTK4, biến này không còn hoạt động đúng và có thể gây conflict.
> Fcitx5 với GTK4 sử dụng D-Bus activation, không cần biến này.

---

## ⌨️ Keybindings

| Phím tắt | Hành động |
|---|---|
| `SUPER + Q` | Mở terminal (Kitty) |
| `SUPER + C` | Đóng cửa sổ |
| `SUPER + E` | Mở file manager |
| `SUPER + R` | Mở app launcher |
| `SUPER + V` | Toggle floating |
| `SUPER + M` | Thoát Hyprland |
| `SUPER + [1-0]` | Chuyển workspace 1-10 |
| `SUPER + SHIFT + [1-0]` | Di chuyển cửa sổ sang workspace |
| `SUPER + Arrow Keys` | Di chuyển focus |
| `SUPER + SHIFT + Arrow Keys` | Di chuyển cửa sổ |
| `Print` | Screenshot toàn màn hình |
| `SUPER + SHIFT + S` | Screenshot vùng chọn |
| `XF86Audio*` | Điều chỉnh âm lượng |
| `XF86MonBrightness*` | Điều chỉnh độ sáng |

---

## 📜 License

Cấu hình cá nhân, tự do sử dụng và chỉnh sửa.

---

<div align="center">

*Made with ❤️ on Arch Linux*

</div>
