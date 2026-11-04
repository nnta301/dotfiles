<div align="center">

# 🏗️ Arch Linux Dotfiles

**Lớp cấu hình cá nhân cho hệ sinh thái Arch Linux + JaKooLit Hyprland**

![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white)
![Hyprland](https://img.shields.io/badge/Hyprland-58E1FF?style=for-the-badge&logo=hyprland&logoColor=black)
![Neovim](https://img.shields.io/badge/Neovim-57A143?style=for-the-badge&logo=neovim&logoColor=white)
![Zsh](https://img.shields.io/badge/Zsh-F15A24?style=for-the-badge&logo=zsh&logoColor=white)
![Fcitx5](https://img.shields.io/badge/Fcitx5_🇻🇳_Bamboo-4EAA25?style=for-the-badge)

</div>

---

## 📐 Triết Lý Kiến Trúc

Repo này **không** theo dõi toàn bộ cấu hình Hyprland. Thay vào đó, nó hoạt động như một
**lớp ghi đè cá nhân** nằm trên nền tảng của
[dotfiles Hyprland upstream của JaKooLit](https://github.com/JaKooLit/Arch-Hyprland).

```
┌─────────────────────────────────────────────────────────────────┐
│  Lớp 1: JaKooLit Upstream (KHÔNG được theo dõi ở đây)          │
│  └─ Cấu hình Hyprland lõi, Waybar, theme, scripts, animation   │
├─────────────────────────────────────────────────────────────────┤
│  Lớp 2: Repo Này — Cấu Hình Ghi Đè Cá Nhân                     │
│  ├─ hypr/   → UserConfigs/ cá nhân                            │
│  ├─ zsh/    → .zshrc với Oh-My-Zsh + tất cả alias cá nhân      │
│  └─ nvim/   → Cấu hình LazyVim đầy đủ (độc lập với WM)         │
└─────────────────────────────────────────────────────────────────┘
```

**Lý do chọn cách tiếp cận này:**
- ✅ Có thể cập nhật cấu hình nền từ upstream, sau khi kiểm tra tương thích
- ✅ Cấu hình cá nhân được quản lý version riêng, gọn và tập trung
- ✅ Cài đặt lại sạch sẽ: chạy script upstream → áp dụng overlay này → xong

---

## 📋 Mục Lục

- [Tóm Tắt Hệ Thống](#-tóm-tắt-hệ-thống)
- [Hướng dẫn cài đặt](#-hướng-dẫn-cài-đặt)
- [Cấu Trúc Repository](#-cấu-trúc-repository)
- [Hyprland UserConfigs — Các Ghi Đè Chính](#-hyprland-userconfigs--các-ghi-đè-chính)
- [Sử dụng màn hình ngoài hoặc máy chiếu](docs/man-hinh-ngoai.md)
- [Phím Tắt](#-phím-tắt)

---

## 💻 Tóm Tắt Hệ Thống

| Thành Phần | Lựa Chọn |
|---|---|
| **Distro** | Arch Linux (rolling release) |
| **Window Manager** | Hyprland qua [JaKooLit/Arch-Hyprland](https://github.com/JaKooLit/Arch-Hyprland) |
| **Terminal** | Kitty |
| **Shell** | Zsh + Oh-My-Zsh (theme: agnosterzak) |
| **Editor** | Neovim (bản phân phối LazyVim) |
| **Thanh Trạng Thái** | Waybar (quản lý bởi JaKooLit upstream) |
| **Phương Thức Nhập** | Fcitx5 + Bamboo (Tiếng Việt) |
| **Âm Thanh** | PipeWire |
| **Quản Lý Dotfiles** | GNU Stow |

---

## 🚀 Hướng dẫn cài đặt

**Dual boot với Windows:** xem [hướng dẫn cài Arch và môi trường từng bước](docs/cai-arch-tu-windows.md). Hướng dẫn có cả nhánh tạo phân vùng Arch mới và cài lại vào phân vùng Arch cũ; đọc điều kiện, sao lưu và xác minh thiết bị trước khi format.

Các bước tóm tắt dưới đây dành cho hệ thống đã cài Arch.

Trước khi cài lại, xem [checklist sao lưu và khôi phục](docs/reinstall.md), bao gồm dữ liệu cá nhân, OneDrive, package và phân vùng EFI.

### Bước 1 — Chạy Script Cài Đặt JaKooLit Upstream

> ⚠️ **Làm bước này trước.** Đây là bước tạo toàn bộ môi trường Hyprland bao gồm
> cấu hình lõi, Waybar, theme và tất cả các dependency.

```bash
git clone --depth=1 https://github.com/JaKooLit/Arch-Hyprland.git ~/JaKooLit-Arch
cd ~/JaKooLit-Arch
chmod +x install.sh
./install.sh
```

Bước này sẽ tạo `~/.config/hypr/` với các cấu hình mặc định upstream.
Đăng nhập vào Hyprland ít nhất một lần để xác nhận hoạt động bình thường trước khi tiếp tục.

---

### Bước 2 — Áp Dụng Cấu Hình Ghi Đè Cá Nhân (Repo Này)

```bash
# Clone repo này
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles

# Chạy script setup (xử lý stow + tương thích JaKooLit)
chmod +x setup.sh
./setup.sh  # chọn 1 để cài package, chuẩn bị shell và áp dụng cấu hình

# Script đọc pkglist.txt: gói aur/ dùng yay; cài Oh My Zsh và plugin còn thiếu.
# Script sẽ chuyển các cấu hình trùng sang ~/.dotfiles-backup.* trước khi stow.
# Khi gặp xung đột còn lại, script dừng để bạn kiểm tra.
```

Sau khi stow, đăng xuất và đăng nhập lại. `SUPER + M` có thể thoát phiên Hyprland tùy cấu hình; không tự khởi động lại phiên. Nếu gặp cảnh báo deprecated, kiểm tra cấu hình và upstream trước khi vá.

---

## 📁 Cấu Trúc Repository

```
dotfiles/
├── 📄 .gitignore                  ← Loại trừ secrets, cache, file lock nvim
├── 📄 README.md                   ← File này
├── 📄 pkglist.txt                 ← Package chính thức và AUR được setup.sh cài
├── 📂 packages/                   ← Danh sách package ghi lại từ máy hiện tại
├── 📄 setup.sh                    ← Script setup một lần
│
├── 📂 hypr/                       ← Cấu hình Hyprland cá nhân
│   └── .config/hypr/              ← UserConfigs
│       └── UserConfigs/           ← Thay thế các mặc định của upstream
│           ├── LaptopDisplay.conf     ← eDP-1 scale 1 (sửa lỗi phần cứng)
│           ├── Startup_Apps.conf      ← exec-once = fcitx5 -d
│           ├── ENVariables.conf       ← Biến môi trường Fcitx5 (Qt + X11)
│           ├── UserKeybinds.conf      ← Phím tắt cá nhân
│           ├── UserSettings.conf      ← Cài đặt Hyprland cá nhân
│           ├── UserAnimations.conf    ← Tùy chọn animation
│           ├── UserDecorations.conf   ← Tùy chọn decoration
│           ├── WindowRules.conf       ← Quy tắc cửa sổ
│           ├── WorkSpaceRules.conf    ← Quy tắc workspace
│           └── Laptops.conf           ← Hành vi khi đóng nắp máy
│
├── 📂 zsh/                        ← Stow package: Shell (chính)
│   └── .zshrc                     ← Oh-My-Zsh + lsd + fzf + alias ứng dụng
│
├── 📂 nvim/                       ← Stow package: Neovim (LazyVim)
│   └── .config/nvim/
│       ├── init.lua
│       ├── lazyvim.json
│       ├── stylua.toml
│       └── lua/
│           ├── config/            ← autocmds, keymaps, lazy, options
│           └── plugins/           ← các spec plugin tùy chỉnh
│
├── 📂 fcitx5/                     ← Profile bộ gõ tiếng Việt
└── 📂 scripts/                    ← Script tiện ích
    └── cleanup.sh                 ← Dọn dẹp cache Pacman + orphan + journal
```

> `lazy-lock.json` lưu phiên bản plugin Neovim để khôi phục nhất quán. Sau khi cập nhật plugin, kiểm tra và commit thay đổi lockfile nếu muốn giữ phiên bản mới.

---

## 🔧 Hyprland UserConfigs — Các Ghi Đè Chính

### `LaptopDisplay.conf` — Tỷ Lệ Màn Hình

```conf
# Tắt tỷ lệ HiDPI 1.5× mặc định của upstream cho eDP-1
monitor = eDP-1, preferred, auto, 1
```

Ghi đè cài đặt mặc định của JaKooLit vốn có thể đặt tỷ lệ phân số. `1` = 100%,
phù hợp với màn hình này mà không bị mờ ứng dụng XWayland.

---

### `Startup_Apps.conf` — Tự Khởi Động Fcitx5

```conf
exec-once = fcitx5 -d
```

Khởi chạy daemon Fcitx5 ở nền khi Hyprland khởi động, cần thiết để
bộ gõ tiếng Việt (engine Bamboo) hoạt động trên tất cả ứng dụng.

---

### `ENVariables.conf` — Môi Trường Phương Thức Nhập

```conf
env = QT_IM_MODULE, fcitx
env = XMODIFIERS, @im=fcitx
```

> ⚠️ **`GTK_IM_MODULE` bị bỏ qua có chủ ý.** GTK4 đã bỏ hỗ trợ cho
> `GTK_IM_MODULE` — đặt biến này gây lỗi hồi quy trong các ứng dụng GTK4. Fcitx5 xử lý
> tích hợp GTK4 tự động qua D-Bus portal.

---

## ⌨️ Phím Tắt

Phím tắt thông thường do cấu hình JaKooLit upstream quy định và có thể thay đổi giữa các phiên bản. Xem `~/.config/hypr/configs/Keybinds.conf` hoặc hướng dẫn phím tắt của upstream sau khi cài.

---

## 📜 Giấy Phép

Cấu hình cá nhân — tự do sử dụng và chỉnh sửa.

---

<div align="center">

*Tạo với ❤️ trên Arch Linux*

</div>
