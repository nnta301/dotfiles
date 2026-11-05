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
- [Sử dụng màn hình ngoài hoặc máy chiếu](docs/external-displays.md)
- [Phím Tắt](#-phím-tắt)
- [Kết quả rà soát và giới hạn kiểm thử](docs/review.md)

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

**Dual boot với Windows:** xem [hướng dẫn cài Arch và môi trường từng bước](docs/arch-windows-dual-boot.md). Hướng dẫn có cả nhánh tạo phân vùng Arch mới và cài lại vào phân vùng Arch cũ; đọc điều kiện, sao lưu và xác minh thiết bị trước khi format.

Muốn xóa Arch cũ để chia lại dung lượng trước khi cài, xem [hướng dẫn repartition](docs/repartition-arch.md).

Các bước tóm tắt dưới đây dành cho hệ thống đã cài Arch.

**Chuyển dữ liệu khi cài lại:** dùng [script backup/restore](docs/backup-restore.md) để tự lưu home, repo, thông tin máy, `/etc`, EFI lên OneDrive qua rclone crypt và phục hồi dữ liệu có kiểm tra checksum. Không đưa bản sao dữ liệu lên GitHub.

Trước khi cài lại, xem [checklist sao lưu và khôi phục](docs/reinstall.md), bao gồm dữ liệu cá nhân, OneDrive, package và phân vùng EFI.

### Cài JaKooLit và cấu hình cá nhân

Trên Arch đã cài, đăng nhập bằng tài khoản thường có `sudo`, mạng và Git:

```bash
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles
./setup.sh
```

Nếu chưa có `~/.config/hypr/hyprland.conf`, script tải và chạy installer JaKooLit; trong menu của JaKooLit, chọn `dots` để cài cấu hình nền. Installer vẫn có các câu hỏi về GPU, SDDM và những tùy chọn khác. Trên máy RTX 2060 Mobile hiện tại, chọn `nvidia`, `dots` và `sddm`; setup chỉnh bản installer vừa tải để dùng `nvidia-open` giống `pkglist.txt`. Khi installer kết thúc, script dừng: đăng nhập Hyprland và kiểm tra hoạt động, rồi chạy lại `~/dotfiles/setup.sh` để cài package và áp dụng cấu hình cá nhân.

Nếu đã có `hyprland.conf`, script bỏ qua bước cài nền: file này chỉ là dấu hiệu, không chứng minh đó là cấu hình JaKooLit. Hãy xác nhận nền JaKooLit đang hoạt động trước khi áp dụng. Đọc [hướng dẫn chi tiết](docs/arch-windows-dual-boot.md) về phần cứng và các giới hạn tương thích.

Sau khi nền hoạt động, `./setup.sh` cài toàn bộ package chính thức và AUR trong `pkglist.txt`, ứng dụng Flatpak trong `packages/flatpak-apps.txt`, chuẩn bị shell và áp dụng cấu hình qua Stow. Các installer vẫn có thể hỏi xác nhận; script backup file trùng vào `~/.dotfiles-backup.*` và dừng nếu gặp lỗi.

---

## 📁 Cấu Trúc Repository

```
dotfiles/
├── 📄 .gitignore                  ← Loại trừ secrets, cache và backup cá nhân
├── 📄 README.md                   ← File này
├── 📄 pkglist.txt                 ← Package chính thức và AUR được setup.sh cài
├── 📂 packages/                   ← Danh sách package ghi lại từ máy hiện tại
├── 📄 setup.sh                    ← Cài nền, package và áp cấu hình
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
    ├── cleanup.sh                 ← Dọn cache Pacman + orphan + journal
    ├── backup.sh                  ← Backup mã hóa lên OneDrive
    ├── restore.sh                 ← Kiểm tra và phục hồi dữ liệu home
    ├── cloud_backup.py            ← Upload/đọc cloud theo từng phần
    └── transfer.py                ← Kiểm tra và restore backup local cũ
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

> Repo không đặt `GTK_IM_MODULE` toàn cục để GTK chạy Wayland có thể dùng đường nhập liệu Wayland. Cách cấu hình còn phụ thuộc ứng dụng/compositor; xem [Fcitx trên Wayland](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland).

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
