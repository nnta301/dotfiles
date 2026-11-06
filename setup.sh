#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║              Personal Dotfiles — Override Layer Setup            ║
# ║                                                                  ║
# ║  Installs the JaKooLit base when needed, then personal configs.  ║
# ║                                                                  ║
# ║  Usage: chmod +x setup.sh && ./setup.sh                         ║
# ╚══════════════════════════════════════════════════════════════════╝

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Helpers ──────────────────────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; }
header()  { echo -e "\n${CYAN}${BOLD}━━━ $1 ━━━${NC}"; }

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Stow packages managed by this repo (personal override layer only)
# NOTE: 'hypr' only contains UserConfigs/ — JaKooLit manages the core config.
STOW_PACKAGES=(zsh nvim hypr fcitx5)

# This personal repo targets the current RTX 2060 + stock linux kernel.
# Patch only the downloaded installer, never an installed system driver.
prepare_upstream_nvidia() {
    local upstream="$1" driver_script="$1/install-scripts/nvidia.sh"
    local matches menu_matches
    menu_matches=$(grep -Fc 'script will install nvidia-dkms, nvidia-utils, and nvidia-settings' "$upstream/install.sh") || true
    matches=$(grep -Ec '^[[:space:]]*nvidia-dkms[[:space:]]*$' "$driver_script") || true
    if [[ "$matches" != 1 || "$menu_matches" != 1 ]] || ! grep -Eq '^nvidia-open([[:space:]]*#.*)?[[:space:]]*$' "$DOTFILES_DIR/pkglist.txt"; then
        error "Installer NVIDIA hoặc pkglist.txt đã thay đổi; dừng để kiểm tra trước khi cài."
        return 1
    fi
    cp -- "$driver_script" "$driver_script.before-dotfiles"
    sed -i -E 's/^([[:space:]]*)nvidia-dkms[[:space:]]*$/\1nvidia-open/' "$driver_script"
    # Keep the upstream menu description consistent with the actual package.
    sed -i 's/script will install nvidia-dkms, nvidia-utils, and nvidia-settings/script will install nvidia-open, nvidia-utils, and nvidia-settings/' "$upstream/install.sh"
    bash -n "$driver_script" || return 1
    bash -n "$upstream/install.sh" || return 1
    info "Installer NVIDIA đã dùng nvidia-open, cùng driver với pkglist.txt."
    info "Trên máy này, chọn nvidia, dots và sddm trong menu JaKooLit."
}

# ═══════════════════════════════════════════════════════════════════
#  Preflight checks
# ═══════════════════════════════════════════════════════════════════
preflight_checks() {
    header "Preflight Checks"

    # Arch Linux
    if ! command -v pacman &>/dev/null; then
        error "Script này chỉ hỗ trợ Arch Linux (pacman không tìm thấy)"
        exit 1
    fi
    success "Arch Linux detected"
    if (( EUID == 0 )); then
        error "Hãy chạy setup.sh bằng tài khoản thường; script dùng sudo khi cần."
        exit 1
    fi
    # A full system update or the upstream installer may rebuild initramfs.
    # A small EFI mounted at /boot needs free working space for that operation.
    local boot_type boot_available
    boot_type=$(findmnt -n -o FSTYPE --target /boot) || { error "Không xác định được filesystem /boot."; exit 1; }
    boot_available=$(df -Pk /boot | awk 'NR==2 {print $4}') || { error "Không đọc được dung lượng /boot."; exit 1; }
    [[ "$boot_available" =~ ^[0-9]+$ ]] || { error "Không xác định được dung lượng /boot."; exit 1; }
    if [[ "$boot_type" == vfat ]] && (( boot_available < 32768 )); then
        error "/boot là EFI và còn dưới 32 MiB; xử lý dung lượng boot trước khi cập nhật."
        error "Xem docs/arch-windows-dual-boot.md và sao lưu EFI; không xóa file Windows."
        exit 1
    fi

    # The installer is interactive; stop afterwards so the user can verify
    # the new graphical session before applying the personal overlay.
    if [[ ! -f "$HOME/.config/hypr/hyprland.conf" ]]; then
        command -v git >/dev/null || { error "Cần git để tải JaKooLit; cài git trước."; exit 1; }
        local bootstrap_dir
        mkdir -p "$HOME/.cache"
        bootstrap_dir=$(mktemp -d "$HOME/.cache/jakoolit-install.XXXXXXXX")
        warn "Chưa có cấu hình Hyprland; tải và chạy installer JaKooLit tương tác."
        warn "Chọn 'dots' để cài cấu hình nền. Các lựa chọn khác phụ thuộc phần cứng."
        info "Installer và log: $bootstrap_dir/Arch-Hyprland"
        git clone --depth=1 https://github.com/JaKooLit/Arch-Hyprland.git "$bootstrap_dir/Arch-Hyprland"
        if grep -Eq '^nvidia-open([[:space:]]*#.*)?[[:space:]]*$' "$DOTFILES_DIR/pkglist.txt"; then
            prepare_upstream_nvidia "$bootstrap_dir/Arch-Hyprland"
        else
            warn "pkglist.txt không chọn nvidia-open; installer giữ driver NVIDIA mặc định upstream."
            warn "Chỉ chọn mục NVIDIA nếu đã kiểm tra driver phù hợp GPU/kernel của máy."
        fi
        (cd "$bootstrap_dir/Arch-Hyprland" && bash ./install.sh)
        if [[ ! -f "$HOME/.config/hypr/hyprland.conf" ]]; then
            error "Installer chưa tạo hyprland.conf; kiểm tra lựa chọn dots và log JaKooLit."
            exit 1
        fi
        success "Installer đã tạo cấu hình Hyprland."
        info "Đăng nhập Hyprland, kiểm tra hoạt động, rồi chạy lại ./setup.sh để áp dụng repo."
        exit 0
    else
        info "Đã có hyprland.conf; xác nhận đây là cấu hình JaKooLit hoạt động trước khi tiếp tục."
    fi
}

# ═══════════════════════════════════════════════════════════════════
#  Backup existing real files before stowing
# ═══════════════════════════════════════════════════════════════════
backup_existing() {
    local pkg="$1"
    local backup_dir="$BACKUP_DIR"

    while IFS= read -r file; do
        local rel_path="${file#"$DOTFILES_DIR/$pkg/"}"
        local target="$HOME/$rel_path"
        local parent="$target"

        # A directory managed by Stow may already point into the repo.
        # Never move a file through a symlinked parent (it could be the source).
        while [[ "$parent" != "$HOME" && "$parent" != / ]]; do
            parent=${parent%/*}
            if [[ -L "$parent" ]]; then
                if [[ "$(readlink -f -- "$target")" == "$(readlink -f -- "$file")" ]]; then
                    continue 2
                fi
                error "Thư mục cha là symlink: $parent; kiểm tra thủ công trước khi tiếp tục."
                return 1
            fi
        done

        if [[ -f "$target" && ! -L "$target" ]]; then
            mkdir -p "$backup_dir/$(dirname "$rel_path")" || return 1
            mv -- "$target" "$backup_dir/$rel_path" || return 1
            warn "  Backup: ~/$rel_path → $backup_dir/$rel_path"
        fi
    done < <(find "$DOTFILES_DIR/$pkg" -type f)
}

# ═══════════════════════════════════════════════════════════════════
#  Apply stow packages
# ═══════════════════════════════════════════════════════════════════
stow_configs() {
    header "Applying Stow Packages"
    info "Packages: ${STOW_PACKAGES[*]}"
    # Check before moving UserConfigs: traversing a parent symlink could move
    # files from another checkout (or the source repo itself).
    local parent
    for parent in "$HOME/.config" "$HOME/.config/hypr"; do
        if [[ -L "$parent" ]]; then
            error "Thư mục cha là symlink: $parent; chưa di chuyển hay áp cấu hình."
            return 1
        fi
    done
    BACKUP_DIR=$(mktemp -d "$HOME/.dotfiles-backup.XXXXXXXX")
    info "Bản sao cấu hình cũ: $BACKUP_DIR"
    echo ""

    for pkg in "${STOW_PACKAGES[@]}"; do
        if [[ ! -d "$DOTFILES_DIR/$pkg" ]]; then
            warn "  Bỏ qua '$pkg' (thư mục không tồn tại)"
            continue
        fi

        # Special handling for hypr: only UserConfigs/ needs to replace upstream's copy
        if [[ "$pkg" == "hypr" ]]; then
            local uc_target="$HOME/.config/hypr/UserConfigs"
            if [[ -d "$uc_target" && ! -L "$uc_target" ]]; then
                mkdir -p "$BACKUP_DIR/.config/hypr"
                mv -- "$uc_target" "$BACKUP_DIR/.config/hypr/UserConfigs"
                warn "  Đã chuyển UserConfigs cũ vào $BACKUP_DIR/.config/hypr/UserConfigs"
            fi
        fi

        backup_existing "$pkg" || return 1

        info "  Stowing: $pkg"
        local -a stow_options=()
        # Avoid linking the entire fcitx5 directory into the repo: the input
        # method writes runtime files alongside the managed profile.
        if [[ "$pkg" == fcitx5 ]]; then
            stow_options+=(--no-folding)
        fi
        if ! stow -d "$DOTFILES_DIR" -t "$HOME" "${stow_options[@]}" -R "$pkg"; then
            error "  Stow thất bại do xung đột; giữ nguyên repo. Kiểm tra cấu hình và bản sao tại $BACKUP_DIR."
            return 1
        fi
        success "  Linked: $pkg"
    done
}

# ═══════════════════════════════════════════════════════════════════
#  Install official packages and shell prerequisites
# ═══════════════════════════════════════════════════════════════════
install_extra_pkgs() {
    header "Cài package từ pkglist.txt"
    local list="$DOTFILES_DIR/pkglist.txt" line pkg
    local -a packages=() aur_packages=() words=()
    [[ -r "$list" ]] || { error "Không đọc được $list"; return 1; }
    while IFS= read -r line || [[ -n "$line" ]]; do
        line=${line%%#*}
        read -r -a words <<< "$line"
        for pkg in "${words[@]}"; do
            if [[ "$pkg" == aur/* ]]; then
                pkg=${pkg#aur/}
                if [[ ! "$pkg" =~ ^[a-zA-Z0-9@._+-]+$ || "$pkg" == -* ]]; then
                    error "Tên package AUR không hợp lệ: $pkg"
                    return 1
                fi
                aur_packages+=("$pkg")
                continue
            fi
            if [[ ! "$pkg" =~ ^[a-zA-Z0-9@._+:-]+$ || "$pkg" == -* ]]; then
                error "Tên package không hợp lệ: $pkg"
                return 1
            fi
            packages+=("$pkg")
        done
    done < "$list"
    (( ${#packages[@]} )) || { error "Danh sách package trống: $list"; return 1; }
    if printf '%s\n' "${packages[@]}" | grep -qx nvidia-open; then
        local driver
        for driver in nvidia nvidia-dkms nvidia-open-dkms; do
            if pacman -Q "$driver" >/dev/null 2>&1; then
                error "Máy đang cài $driver nhưng pkglist.txt yêu cầu nvidia-open."
                error "Dừng để kiểm tra driver trước khi tiếp tục; không tự gỡ driver đang chạy."
                return 1
            fi
        done
    fi
    info "Cập nhật hệ thống và cài ${#packages[@]} package từ repo chính thức."
    sudo pacman -Syu --needed -- "${packages[@]}"
    success "Đã cài package chính thức."

    if (( ${#aur_packages[@]} )); then
        header "Cài package AUR từ pkglist.txt"
        if ! command -v yay >/dev/null; then
            local build_dir
            build_dir=$(mktemp -d "${TMPDIR:-/tmp}/dotfiles-yay.XXXXXXXX")
            info "Chưa có yay; tải PKGBUILD vào $build_dir và build bằng makepkg."
            git clone https://aur.archlinux.org/yay.git "$build_dir/yay"
            info "Kiểm tra PKGBUILD tại $build_dir/yay/PKGBUILD trước khi tiếp tục."
            read -rp "Nhấn Enter để tiếp tục hoặc Ctrl+C để dừng. "
            (cd "$build_dir/yay" && makepkg -si)
            command -v yay >/dev/null || { error "Cài yay thất bại."; return 1; }
        fi
        local aur_check
        if ! aur_check=$(yay -Si --aur -- "${aur_packages[@]}" 2>&1); then
            error "Không thể xác minh toàn bộ danh sách AUR; kiểm tra tên gói và kết nối."
            printf '%s\n' "$aur_check" >&2
            return 1
        fi
        info "Cài ${#aur_packages[@]} package AUR bằng yay; kiểm tra các lời nhắc trước khi xác nhận."
        yay -S --aur --needed -- "${aur_packages[@]}"
        success "Đã cài package AUR."
    fi
}

install_flatpaks() {
    header "Cài ứng dụng Flatpak"
    local list="$DOTFILES_DIR/packages/flatpak-apps.txt" line
    local -a apps=()
    command -v flatpak >/dev/null || { error "Chưa cài flatpak; cài package flatpak trước."; return 1; }
    [[ -r "$list" ]] || { error "Không đọc được $list"; return 1; }
    while IFS= read -r line || [[ -n "$line" ]]; do
        line=${line%%#*}
        [[ -z "$line" ]] && continue
        if [[ ! "$line" =~ ^[A-Za-z0-9_]+(\.[A-Za-z0-9_-]+)+$ ]]; then
            error "ID Flatpak không hợp lệ: $line"; return 1
        fi
        apps+=("$line")
    done < "$list"
    (( ${#apps[@]} )) || { info "Danh sách Flatpak trống."; return 0; }
    info "Thêm Flathub cho user nếu chưa có và cài ${#apps[@]} ứng dụng."
    flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    flatpak install --user --or-update flathub "${apps[@]}"
}

install_zsh_assets() {
    header "Oh My Zsh và các thành phần shell"
    local zsh_dir="$HOME/.oh-my-zsh"
    local custom_dir="$zsh_dir/custom"
    if [[ ! -e "$zsh_dir" ]]; then
        git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git "$zsh_dir"
    fi
    if [[ ! -f "$zsh_dir/oh-my-zsh.sh" ]]; then
        error "$zsh_dir đã tồn tại nhưng không có oh-my-zsh.sh; kiểm tra thủ công."
        return 1
    fi
    mkdir -p "$custom_dir/plugins" "$custom_dir/themes"
    local plugin name url
    for name in zsh-autosuggestions zsh-syntax-highlighting; do
        plugin="$custom_dir/plugins/$name"
        if [[ ! -e "$plugin" ]]; then
            url="https://github.com/zsh-users/$name.git"
            git clone --depth=1 "$url" "$plugin"
        fi
        if [[ ! -f "$plugin/$name.plugin.zsh" ]]; then
            error "Thiếu file plugin trong $plugin; kiểm tra thủ công."
            return 1
        fi
    done
    if [[ ! -f "$custom_dir/themes/agnosterzak.zsh-theme" && ! -f "$zsh_dir/themes/agnosterzak.zsh-theme" ]]; then
        local theme_dir="$custom_dir/themes/agnosterzak"
        if [[ ! -e "$theme_dir" ]]; then
            git clone --depth=1 https://github.com/zakaziko99/agnosterzak-ohmyzsh-theme.git "$theme_dir"
        fi
        [[ -f "$theme_dir/agnosterzak.zsh-theme" ]] || { error "Không tìm thấy theme trong $theme_dir"; return 1; }
        cp -- "$theme_dir/agnosterzak.zsh-theme" "$custom_dir/themes/agnosterzak.zsh-theme"
    fi
    success "Oh My Zsh, plugins và theme đã sẵn sàng."
}

# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
main() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║    Personal Dotfiles — Override Layer        ║${NC}"
    echo -e "${CYAN}${BOLD}║    JaKooLit base + personal configuration    ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""

    if (( $# )); then
        error "Không hỗ trợ tham số: chạy ./setup.sh để cài toàn bộ."
        exit 2
    fi
    preflight_checks
    install_extra_pkgs
    install_flatpaks
    install_zsh_assets
    stow_configs

    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║   ✅ Hoàn tất! Đăng xuất & đăng nhập lại.  ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Các cấu hình đã áp dụng: ${STOW_PACKAGES[*]}"
    echo ""
}

main "$@"
