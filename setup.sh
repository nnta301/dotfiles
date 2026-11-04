#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║              Personal Dotfiles — Override Layer Setup            ║
# ║                                                                  ║
# ║  This script applies ONLY the personal override layer.           ║
# ║  It assumes JaKooLit's upstream script has already been run.     ║
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

    # Check JaKooLit upstream was run (look for its core config)
    if [[ "$choice" != 4 && ! -f "$HOME/.config/hypr/hyprland.conf" ]]; then
        warn "Không tìm thấy ~/.config/hypr/hyprland.conf"
        warn "Hãy chạy JaKooLit upstream install script trước:"
        warn "  git clone --depth=1 https://github.com/JaKooLit/Arch-Hyprland.git ~/JaKooLit-Arch"
        warn "  cd ~/JaKooLit-Arch && ./install.sh"
        echo ""
        read -rp "$(echo -e "${YELLOW}Tiếp tục mà không có upstream? [y/N]:${NC} ")" cont
        [[ "${cont,,}" == "y" ]] || { info "Thoát."; exit 0; }
    elif [[ "$choice" != 4 ]]; then
        success "JaKooLit upstream config found"
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
        if ! stow -d "$DOTFILES_DIR" -t "$HOME" -R "$pkg"; then
            error "  Stow thất bại do xung đột; giữ nguyên repo. Kiểm tra cấu hình và bản sao tại $BACKUP_DIR."
            return 1
        fi
        success "  Linked: $pkg"
    done
}

# ═══════════════════════════════════════════════════════════════════
#  Patch deprecated Hyprland dispatchers (upstream JaKooLit)
# ═══════════════════════════════════════════════════════════════════
patch_deprecations() {
    header "Patching Deprecated Hyprland Dispatchers"
    warn "Kiểm tra upstream JaKooLit trước khi chạy bước này:"
    warn "  https://github.com/JaKooLit/Arch-Hyprland/issues"
    echo ""
    read -rp "$(echo -e "${CYAN}Áp dụng patch deprecated dispatchers? [y/N]:${NC} ")" apply

    if [[ "${apply,,}" == "y" ]]; then
        local keybinds="$HOME/.config/hypr/UserConfigs/UserKeybinds.conf"
        local hyprconf="$HOME/.config/hypr/hyprland.conf"

        if [[ -f "$keybinds" ]]; then
            sed -i '/togglesplit/s/^/#/' "$keybinds" 2>/dev/null || true
            sed -i '/pseudotile/s/^/#/' "$keybinds" 2>/dev/null || true
            success "  Commented out togglesplit / pseudotile in UserKeybinds.conf"
        fi
        if [[ -f "$hyprconf" ]]; then
            sed -i '/^\s*vfr\s*=/s/^/#/' "$hyprconf" 2>/dev/null || true
            success "  Commented out vfr in hyprland.conf"
        fi
    else
        info "  Bỏ qua patch."
    fi
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
    if (( EUID == 0 )); then
        error "Hãy chạy setup.sh bằng tài khoản thường; script dùng sudo khi cần."
        return 1
    fi
    if printf '%s\n' "${packages[@]}" | grep -qx nvidia-open && pacman -Q nvidia-dkms >/dev/null 2>&1; then
        error "Máy đang cài nvidia-dkms nhưng pkglist.txt yêu cầu nvidia-open."
        error "Dừng để bạn kiểm tra driver phù hợp và sửa danh sách trước khi tiếp tục."
        return 1
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
        info "Cài ${#aur_packages[@]} package AUR bằng yay; kiểm tra các lời nhắc trước khi xác nhận."
        yay -S --aur --needed -- "${aur_packages[@]}"
        success "Đã cài package AUR."
    fi
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
    echo -e "${CYAN}${BOLD}║    (assumes JaKooLit upstream already run)   ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${BOLD}Chọn hành động:${NC}"
    echo "  1) Cài package + shell và áp dụng cấu hình"
    echo "  2) Chỉ stow configs (zsh, nvim, hypr, fcitx5)"
    echo "  3) Chỉ patch deprecated dispatchers"
    echo "  4) Chỉ cài package và thành phần shell"
    echo "  5) Thoát"
    echo ""
    read -rp "$(echo -e "${CYAN}Lựa chọn [1-5]:${NC} ")" choice

    if [[ "$choice" == 5 ]]; then info "Thoát."; exit 0; fi
    preflight_checks

    case "$choice" in
        1)
            install_extra_pkgs
            install_zsh_assets
            stow_configs
            ;;
        2)
            command -v stow >/dev/null || { error "Chưa có stow; chọn mục 1 hoặc cài stow trước."; exit 1; }
            stow_configs
            ;;
        3)
            patch_deprecations
            ;;
        4)
            install_extra_pkgs
            install_zsh_assets
            ;;
        5)
            info "Thoát."
            exit 0
            ;;
        *)
            error "Lựa chọn không hợp lệ"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║   ✅ Hoàn tất! Đăng xuất & đăng nhập lại.  ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    if [[ "$choice" == 1 || "$choice" == 2 ]]; then
        echo -e "  Các cấu hình đã áp dụng: ${STOW_PACKAGES[*]}"
    fi
    echo ""
}

main "$@"
