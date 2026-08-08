#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║                    Arch Linux Dotfiles Setup                     ║
# ║                                                                  ║
# ║  Script tự động cài đặt packages và link config bằng GNU Stow   ║
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
NC='\033[0m' # No Color

# ── Helper Functions ─────────────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; }

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKGLIST="$DOTFILES_DIR/pkglist.txt"

# ── Stow packages (tên thư mục con trong dotfiles) ──────────────
STOW_PACKAGES=(bash hypr waybar)

# ═══════════════════════════════════════════════════════════════════
#  Bước 1: Kiểm tra hệ thống
# ═══════════════════════════════════════════════════════════════════
check_system() {
    echo ""
    echo -e "${CYAN}${BOLD}══════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}   🏗️  Arch Linux Dotfiles Setup Script${NC}"
    echo -e "${CYAN}${BOLD}══════════════════════════════════════════════${NC}"
    echo ""

    # Kiểm tra Arch Linux
    if ! command -v pacman &>/dev/null; then
        error "Script này chỉ hỗ trợ Arch Linux (pacman không tìm thấy)"
        exit 1
    fi
    success "Đang chạy trên Arch Linux"

    # Kiểm tra quyền sudo
    if ! sudo -v &>/dev/null; then
        error "Cần quyền sudo để cài đặt packages"
        exit 1
    fi
    success "Quyền sudo OK"
}

# ═══════════════════════════════════════════════════════════════════
#  Bước 2: Cập nhật hệ thống
# ═══════════════════════════════════════════════════════════════════
update_system() {
    info "Cập nhật hệ thống..."
    sudo pacman -Syu --noconfirm
    success "Hệ thống đã được cập nhật"
}

# ═══════════════════════════════════════════════════════════════════
#  Bước 3: Cài đặt packages từ pkglist.txt
# ═══════════════════════════════════════════════════════════════════
install_packages() {
    if [[ ! -f "$PKGLIST" ]]; then
        error "Không tìm thấy $PKGLIST"
        exit 1
    fi

    info "Cài đặt packages từ pkglist.txt..."

    # Lọc bỏ comment, dòng trống, và ghi chú AUR
    local official_pkgs
    official_pkgs=$(grep -v '^\s*#\|^\s*$' "$PKGLIST" | grep -v '# AUR' | sed 's/\s*#.*//' | tr '\n' ' ')

    local aur_pkgs
    aur_pkgs=$(grep '# AUR' "$PKGLIST" | sed 's/\s*#.*//' | tr '\n' ' ')

    # Cài packages từ official repo
    if [[ -n "$official_pkgs" ]]; then
        info "Cài đặt packages từ official repo..."
        # shellcheck disable=SC2086
        sudo pacman -S --needed --noconfirm $official_pkgs
        success "Đã cài đặt official packages"
    fi

    # Cài packages từ AUR
    if [[ -n "$aur_pkgs" ]]; then
        if command -v yay &>/dev/null; then
            info "Cài đặt AUR packages bằng yay..."
            # shellcheck disable=SC2086
            yay -S --needed --noconfirm $aur_pkgs
            success "Đã cài đặt AUR packages"
        else
            warn "yay chưa được cài đặt. Bỏ qua AUR packages: $aur_pkgs"
            warn "Cài yay: git clone https://aur.archlinux.org/yay.git /tmp/yay && cd /tmp/yay && makepkg -si"
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════════
#  Bước 4: Cài đặt yay (AUR helper)
# ═══════════════════════════════════════════════════════════════════
install_yay() {
    if command -v yay &>/dev/null; then
        success "yay đã được cài đặt"
        return
    fi

    info "Cài đặt yay (AUR helper)..."
    local tmp_dir
    tmp_dir=$(mktemp -d)
    git clone https://aur.archlinux.org/yay.git "$tmp_dir/yay"
    cd "$tmp_dir/yay" && makepkg -si --noconfirm
    cd "$DOTFILES_DIR"
    rm -rf "$tmp_dir"
    success "Đã cài đặt yay"
}

# ═══════════════════════════════════════════════════════════════════
#  Bước 5: Link config bằng GNU Stow
# ═══════════════════════════════════════════════════════════════════
stow_configs() {
    # Kiểm tra stow đã cài chưa
    if ! command -v stow &>/dev/null; then
        info "Cài đặt GNU Stow..."
        sudo pacman -S --needed --noconfirm stow
    fi

    info "Linking config files bằng GNU Stow..."

    for pkg in "${STOW_PACKAGES[@]}"; do
        if [[ -d "$DOTFILES_DIR/$pkg" ]]; then
            # Backup file gốc nếu tồn tại (không phải symlink)
            backup_existing "$pkg"

            info "  Stow: $pkg"
            stow -d "$DOTFILES_DIR" -t "$HOME" -R "$pkg" 2>/dev/null || {
                warn "  Không thể stow $pkg — có thể có xung đột file. Thử stow --adopt..."
                stow -d "$DOTFILES_DIR" -t "$HOME" --adopt "$pkg"
                # Restore từ git sau khi adopt
                cd "$DOTFILES_DIR" && git checkout -- "$pkg/" 2>/dev/null || true
            }
            success "  Đã link: $pkg"
        else
            warn "  Bỏ qua $pkg (thư mục không tồn tại)"
        fi
    done
}

# ── Backup file gốc trước khi stow ──────────────────────────────
backup_existing() {
    local pkg="$1"
    local backup_dir="$HOME/.dotfiles-backup/$(date +%Y%m%d_%H%M%S)"

    # Tìm tất cả file trong stow package
    while IFS= read -r file; do
        local rel_path="${file#"$DOTFILES_DIR/$pkg/"}"
        local target="$HOME/$rel_path"

        # Nếu file tồn tại và KHÔNG phải symlink → backup
        if [[ -f "$target" && ! -L "$target" ]]; then
            mkdir -p "$backup_dir/$(dirname "$rel_path")"
            cp "$target" "$backup_dir/$rel_path"
            rm "$target"
            warn "  Backup: ~/$rel_path → $backup_dir/$rel_path"
        fi
    done < <(find "$DOTFILES_DIR/$pkg" -type f)
}

# ═══════════════════════════════════════════════════════════════════
#  Bước 6: Bật services cần thiết
# ═══════════════════════════════════════════════════════════════════
enable_services() {
    info "Bật các services cần thiết..."

    # System services
    local system_services=(NetworkManager bluetooth)
    for svc in "${system_services[@]}"; do
        if systemctl list-unit-files "${svc}.service" &>/dev/null; then
            sudo systemctl enable --now "${svc}.service" 2>/dev/null || true
            success "  Enabled: $svc"
        fi
    done

    # User services (PipeWire)
    local user_services=(pipewire pipewire-pulse wireplumber)
    for svc in "${user_services[@]}"; do
        systemctl --user enable --now "${svc}.service" 2>/dev/null || true
        success "  Enabled (user): $svc"
    done
}

# ═══════════════════════════════════════════════════════════════════
#  Bước 7: Dọn dẹp hệ thống
# ═══════════════════════════════════════════════════════════════════
cleanup_system() {
    local cleanup_script="$DOTFILES_DIR/scripts/cleanup.sh"

    if [[ ! -f "$cleanup_script" ]]; then
        error "Không tìm thấy $cleanup_script"
        exit 1
    fi

    info "Chạy script dọn dẹp hệ thống..."
    bash "$cleanup_script"
    success "Dọn dẹp hoàn tất!"
}

# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
main() {
    check_system

    echo ""
    echo -e "${BOLD}Chọn hành động:${NC}"
    echo "  1) Cài đặt đầy đủ (packages + stow + services)"
    echo "  2) Chỉ cài packages"
    echo "  3) Chỉ link config (stow)"
    echo "  4) Chỉ bật services"
    echo "  5) Dọn dẹp hệ thống"
    echo "  6) Thoát"
    echo ""
    read -rp "$(echo -e "${CYAN}Lựa chọn [1-6]:${NC} ")" choice

    case "$choice" in
        1)
            update_system
            install_yay
            install_packages
            stow_configs
            enable_services
            ;;
        2)
            update_system
            install_yay
            install_packages
            ;;
        3)
            stow_configs
            ;;
        4)
            enable_services
            ;;
        5)
            cleanup_system
            ;;
        6)
            info "Thoát."
            exit 0
            ;;
        *)
            error "Lựa chọn không hợp lệ"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}   ✅ Hoàn tất! Khởi động lại để áp dụng.${NC}"
    echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}Reboot:${NC} sudo reboot"
    echo -e "  ${CYAN}Hoặc:${NC}  Hyprland (nếu đã cài) → đăng nhập lại"
    echo ""
}

main "$@"
