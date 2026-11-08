#!/usr/bin/env bash
# Dọn cache Arch Linux; chạy --dry-run để xem trước.
set -u

dry_run=false
case "${1:-}" in
    '') ;;
    --dry-run|-n) dry_run=true ;;
    --help|-h)
        echo 'Cách dùng: ./scripts/cleanup.sh [--dry-run]'
        echo 'Giữ 2 phiên bản package trong cache; hỏi trước khi xóa orphan, journal cũ, cache ứng dụng, thùng rác và dữ liệu phải tải lại.'
        exit 0 ;;
    *) echo "Tham số không hợp lệ: $1" >&2; exit 2 ;;
esac
if (( $# > 1 )); then echo 'Quá nhiều tham số.' >&2; exit 2; fi

failed=0
ask() {
    local answer
    read -r -p "$1 [y/N] " answer || return 1
    [[ $answer == [yY] || $answer == [yY][eE][sS] ]]
}
run() {
    if "$@"; then return 0; fi
    echo "Lỗi khi chạy: $*" >&2
    failed=1
    return 1
}
show_size() {
    if [[ -e $1 ]]; then du -sh -- "$1" 2>/dev/null || true; fi
}
# clear_cache LABEL PROCESS DIR...: empty the directories, keeping them in place.
# Skipped while PROCESS is running, because the app may still be writing there.
clear_cache() {
    local label=$1 process=$2 dir
    shift 2
    local -a dirs=()
    for dir in "$@"; do
        if [[ -d $dir && ! -L $dir ]] && [[ -n $(find "$dir" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
            dirs+=("$dir")
        fi
    done
    (( ${#dirs[@]} )) || return 0
    du -sch -- "${dirs[@]}" 2>/dev/null | tail -n 1 | sed "s|total|$label|" || true
    if [[ -n $process ]] && pgrep -x "$process" >/dev/null 2>&1; then
        echo "$process đang chạy; bỏ qua. Tắt ứng dụng rồi chạy lại."
    elif $dry_run; then
        echo "Xem trước: sẽ hỏi trước khi xóa $label."
    elif ask "Xóa $label?"; then
        for dir in "${dirs[@]}"; do
            run find "$dir" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + || true
        done
    fi
}

if ! command -v pacman >/dev/null; then
    echo 'Cần pacman để chạy script này trên Arch Linux.' >&2
    exit 1
fi

echo '🧹 Dung lượng trước khi dọn:'
df -h / "$HOME"
show_size /var/cache/pacman/pkg
show_size "${XDG_CACHE_HOME:-$HOME/.cache}/yay"
show_size "${XDG_DATA_HOME:-$HOME/.local/share}/Trash"

echo
echo '1. Cache package (giữ 2 phiên bản mỗi package)'
if command -v paccache >/dev/null; then
    if $dry_run; then
        run paccache -d -k 2 || true
    else
        run sudo paccache -r -k 2 || true
    fi
else
    echo 'Bỏ qua: cài pacman-contrib để dùng paccache.'
fi

echo
echo '2. Thư mục tải tạm Pacman rỗng, cũ hơn 24 giờ'
# Chỉ xử lý cache mặc định, không đụng file .part có thể dùng để tiếp tục tải.
# Không chạy khi có giao dịch Pacman hoặc yay đang hoạt động.
cache_dir=/var/cache/pacman/pkg
if [[ -e /var/lib/pacman/db.lck ]] || pgrep -x 'pacman|yay' >/dev/null 2>&1; then
    echo 'Pacman/yay có thể đang hoạt động hoặc còn lock; bỏ qua mục này.'
elif [[ -d $cache_dir ]]; then
    if $dry_run; then
        echo 'Các thư mục rỗng đủ điều kiện (cần sudo để kiểm tra đầy đủ):'
        run sudo find "$cache_dir" -mindepth 1 -maxdepth 1 -type d -name 'download-*' -mmin +1440 -empty -print || true
    else
        # rmdir chỉ xóa thư mục còn rỗng tại thời điểm thực thi.
        run sudo find "$cache_dir" -mindepth 1 -maxdepth 1 -type d -name 'download-*' -mmin +1440 -empty -print -exec rmdir -- {} + || true
    fi
    echo 'Thư mục download-* còn lại (có thể chứa dữ liệu hoặc chưa đủ tuổi):'
    run sudo find "$cache_dir" -mindepth 1 -maxdepth 1 -type d -name 'download-*' -print || true
fi

echo
echo '3. Package mồ côi'
orphans=()
orphan_output=$(pacman -Qtdq 2>&1)
orphan_status=$?
if (( orphan_status == 0 )); then
    mapfile -t orphans <<< "$orphan_output"
    printf '%s\n' "${orphans[@]}"
    if $dry_run; then
        echo 'Xem trước: sẽ hỏi trước khi gỡ các package trên.'
    elif ask 'Gỡ các package mồ côi này?'; then
        run sudo pacman -Rns -- "${orphans[@]}" || true
    fi
elif (( orphan_status == 1 )) && [[ -z $orphan_output ]]; then
    echo 'Không có package mồ côi.'
else
    echo "Không thể kiểm tra package mồ côi: $orphan_output" >&2
    failed=1
fi

echo
echo '4. Journal hệ thống (giới hạn journal đã lưu trữ ở 100 MB)'
if command -v journalctl >/dev/null; then
    if $dry_run; then
        journalctl --disk-usage || failed=1
        echo 'Xem trước: sẽ hỏi trước khi chạy sudo journalctl --vacuum-size=100M'
    else
        journalctl --disk-usage || failed=1
        if ask 'Xóa journal cũ? Log dùng để chẩn đoán lỗi driver/boot có thể mất.'; then
            run sudo journalctl --vacuum-size=100M || true
        fi
    fi
else
    echo 'Bỏ qua: không tìm thấy journalctl.'
fi

echo
echo '5. Cache build yay và thùng rác người dùng'
yay_cache="${XDG_CACHE_HOME:-$HOME/.cache}/yay"
trash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/Trash"
if [[ -d $yay_cache && ! -L $yay_cache ]]; then
    show_size "$yay_cache"
    if $dry_run; then
        echo 'Xem trước: sẽ hỏi trước khi xóa nội dung cache yay.'
    elif pgrep -x yay >/dev/null 2>&1; then
        echo 'yay đang chạy; bỏ qua cache build.'
    elif ask 'Xóa toàn bộ cache build yay? Các package AUR có thể phải tải/build lại.'; then
        run find "$yay_cache" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + || true
    fi
fi
if [[ -d $trash_dir && ! -L $trash_dir ]]; then
    show_size "$trash_dir"
    if $dry_run; then
        echo 'Xem trước: sẽ hỏi trước khi dọn thùng rác người dùng.'
    elif ask 'Xóa vĩnh viễn nội dung thùng rác người dùng?'; then
        for dir in "$trash_dir/files" "$trash_dir/info"; do
            if [[ -d $dir && ! -L $dir ]]; then
                run find "$dir" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + || true
            fi
        done
    fi
fi

echo
echo '6. Cache ứng dụng (tự tạo lại khi cần)'
# Service Worker storage, workspaceStorage, extensions and cliphist hold user state.
cache_home=${XDG_CACHE_HOME:-$HOME/.cache}
config_home=${XDG_CONFIG_HOME:-$HOME/.config}
clear_cache 'cache Chrome' chrome "$cache_home/google-chrome"
clear_cache 'cache VS Code' code "$config_home/Code/CachedExtensionVSIXs" \
    "$config_home/Code/CachedData" "$config_home/Code/Cache" "$config_home/Code/logs"
clear_cache 'cache Discord' Discord "$config_home/discord/Cache"
clear_cache 'cache npm' npm "$HOME/.npm"
clear_cache 'cache pip' pip "$cache_home/pip"

echo
echo '7. Dữ liệu phải tải lại hoặc gỡ khỏi hệ thống'
clear_cache 'thư viện Maven (build sau phải tải lại)' mvn "$HOME/.m2/repository"
if command -v paccache >/dev/null; then
    if $dry_run; then
        run paccache -d -u -k 0 || true
    elif ask 'Xóa cache của các package đã gỡ? Sẽ không hạ cấp được về các bản đó từ cache.'; then
        run sudo paccache -r -u -k 0 || true
    fi
fi
if command -v flatpak >/dev/null; then
    if $dry_run; then
        echo 'Xem trước: sẽ hỏi trước khi gỡ Flatpak runtime không còn dùng.'
    elif ask 'Gỡ Flatpak runtime không còn dùng? Flatpak sẽ liệt kê và hỏi lại.'; then
        run flatpak uninstall --unused || true
    fi
fi

echo
echo 'Dung lượng sau khi dọn:'
df -h / "$HOME"
if (( failed )); then
    echo 'Một số bước gặp lỗi; xem thông báo ở trên.' >&2
    exit 1
fi
echo 'Hoàn tất.'
