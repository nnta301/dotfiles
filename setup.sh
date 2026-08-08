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
STOW_PACKAGES=(zsh nvim hypr)

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

    # stow
    if ! command -v stow &>/dev/null; then
        info "Cài đặt GNU Stow..."
        sudo pacman -S --needed --noconfirm stow
    fi
    success "GNU Stow available"

    # Check JaKooLit upstream was run (look for its core config)
    if [[ ! -f "$HOME/.config/hypr/hyprland.conf" ]]; then
        warn "Không tìm thấy ~/.config/hypr/hyprland.conf"
        warn "Hãy chạy JaKooLit upstream install script trước:"
        warn "  git clone --depth=1 https://github.com/JaKooLit/Arch-Hyprland.git ~/JaKooLit-Arch"
        warn "  cd ~/JaKooLit-Arch && ./install.sh"
        echo ""
        read -rp "$(echo -e "${YELLOW}Tiếp tục mà không có upstream? [y/N]:${NC} ")" cont
        [[ "${cont,,}" == "y" ]] || { info "Thoát."; exit 0; }
    else
        success "JaKooLit upstream config found"
    fi
}

# ═══════════════════════════════════════════════════════════════════
#  Backup existing real files before stowing
# ═══════════════════════════════════════════════════════════════════
backup_existing() {
    local pkg="$1"
    local backup_dir="$HOME/.dotfiles-backup/$(date +%Y%m%d_%H%M%S)"

    while IFS= read -r file; do
        local rel_path="${file#"$DOTFILES_DIR/$pkg/"}"
        local target="$HOME/$rel_path"

        if [[ -f "$target" && ! -L "$target" ]]; then
            mkdir -p "$backup_dir/$(dirname "$rel_path")"
            cp "$target" "$backup_dir/$rel_path"
            rm "$target"
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
                warn "  Xóa UserConfigs upstream để thay bằng symlink..."
                rm -rf "$uc_target"
            fi
        fi

        backup_existing "$pkg"

        info "  Stowing: $pkg"
        stow -d "$DOTFILES_DIR" -t "$HOME" -R "$pkg" 2>/dev/null || {
            warn "  Xung đột — thử stow --adopt..."
            stow -d "$DOTFILES_DIR" -t "$HOME" --adopt "$pkg"
            cd "$DOTFILES_DIR" && git checkout -- "$pkg/" 2>/dev/null || true
        }
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
#  Install AUR packages not handled by JaKooLit
# ═══════════════════════════════════════════════════════════════════
install_extra_pkgs() {
    header "Extra Packages (not in JaKooLit upstream)"

    if ! command -v yay &>/dev/null; then
        warn "yay chưa được cài. Bỏ qua AUR packages."
        warn "Cài yay: https://github.com/Jguer/yay"
        return
    fi

    info "Cài đặt packages cá nhân..."
    yay -S --needed --noconfirm \
        fcitx5 fcitx5-gtk fcitx5-qt fcitx5-configtool fcitx5-bamboo \
        zsh zsh-completions zsh-autosuggestions zsh-syntax-highlighting \
        lsd pokemon-colorscripts-git \
        oh-my-zsh-git \
        lazygit ripgrep fd fzf bat eza \
        2>/dev/null || warn "Một số package có thể đã được cài hoặc không có trong AUR"
    success "Extra packages done"
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
    echo "  1) Áp dụng tất cả (stow + patch + extra packages)"
    echo "  2) Chỉ stow configs (zsh, nvim, hypr UserConfigs)"
    echo "  3) Chỉ patch deprecated dispatchers"
    echo "  4) Chỉ cài extra packages"
    echo "  5) Thoát"
    echo ""
    read -rp "$(echo -e "${CYAN}Lựa chọn [1-5]:${NC} ")" choice

    preflight_checks

    case "$choice" in
        1)
            stow_configs
            patch_deprecations
            install_extra_pkgs
            ;;
        2)
            stow_configs
            ;;
        3)
            patch_deprecations
            ;;
        4)
            install_extra_pkgs
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
    echo -e "  Symlinks đã tạo:"
    for pkg in "${STOW_PACKAGES[@]}"; do
        echo -e "    ${CYAN}$pkg${NC} → $DOTFILES_DIR/$pkg"
    done
    echo ""
}

main "$@"
