# Kế hoạch: backup, restore và setup chạy tiếp được sau khi bị ngắt

Trạng thái: chưa bắt đầu. Chỉ làm sau khi đã cài lại máy xong.

## Điều kiện trước khi bắt đầu

- [ ] Máy mới đã restore xong và dùng ổn định.
- [ ] Trên `archbackup:` còn ít nhất một bản định dạng hiện tại (manifest `version: 2`) đã restore thành công. Không xóa bản này cho đến khi hết giai đoạn 3.
- [ ] `python3 -m unittest discover -s tests` qua toàn bộ trên máy mới.

## Vấn đề

`scripts/cloud_backup.py` tạo một luồng tar liên tục rồi cắt thành chunk 64 MiB. Ctrl+C, mất mạng quá số lần thử lại, hoặc sập máy đều làm mất toàn bộ lần chạy: lần sau tạo ID mới, upload lại từ đầu, và bản dở vẫn chiếm quota.

Không thể chỉ nhớ vị trí chunk cuối. File trên máy có thể đổi giữa hai lần chạy, nên luồng tar tạo lại sẽ lệch khỏi các chunk đã có và ghép lại thành archive hỏng.

## Mục tiêu

- Chạy lại đúng lệnh cũ thì tiếp tục, sau Ctrl+C, mất mạng hoặc sập máy.
- Mỗi lần ngắt chỉ mất phần đang upload dở, tối đa khoảng một phần (1–2 GiB).
- Bản dở không bao giờ restore được. `manifest.json` vẫn được upload cuối cùng.
- Restore vẫn đọc được bản `version: 2`.

Ngoài phạm vi: backup tăng dần, chống trùng lặp, chuyển sang `restic`. Nếu sau này muốn backup định kỳ thì cân nhắc lại `restic` thay vì mở rộng script này.

## Thiết kế

### Bố cục trên cloud (manifest `version: 3`)

```text
archbackup:arch-<thời gian>-<id>/
  plan.json              # upload trước khi có dữ liệu
  parts/0001/chunk-*     # các chunk 64 MiB của phần 1
  parts/0001/done.json   # upload sau khi chunk đã kiểm tra xong
  manifest.json          # upload cuối cùng
```

- `plan.json` gồm thời điểm tạo, tham số `--exclude`/`--volatile`, và danh sách file của từng phần.
- Mỗi phần là một tar độc lập, giải nén được mà không cần phần khác.
- `done.json` gồm SHA-256, kích thước, danh sách chunk và danh sách file thực sự nằm trong phần đó.
- Trạng thái chỉ nằm trên cloud, không cache dữ liệu ra ổ local. Máy hỏng ổ vẫn tiếp tục được từ máy khác có cùng home.

### Chia phần

- Mục tiêu mỗi phần khoảng 1,5 GiB, đặt trong một hằng số.
- File lớn hơn mức này đứng riêng một phần. Nó vẫn được cắt thành chunk 64 MiB, nên ngắt giữa file lớn sẽ upload lại cả file đó.
- `repo.tar`, `etc.tar`, `efi.tar` và các báo cáo là các phần riêng trong plan.

### Tiếp tục

1. Khi chạy `backup`, tìm thư mục mới nhất đúng mẫu `arch-*` có `plan.json` nhưng chưa có `manifest.json`.
2. Nếu tìm thấy và tham số khớp, in ID cùng số phần đã xong rồi tiếp tục. Tham số khác thì dừng và yêu cầu chọn `--resume <ID>` hoặc `--fresh`.
3. Chỉ phần có `done.json` mới được bỏ qua. Phần chưa có `done.json` bị xóa toàn bộ chunk rồi tạo lại.
4. Khi tất cả phần đã xong, kiểm tra lại toàn bộ `done.json` rồi upload `manifest.json`.

CLI mới của `backup`: `--resume <ID>`, `--fresh`. Mặc định là tự tiếp tục theo bước 1.

### Tính nhất quán

Các phần có thể được tạo cách nhau nhiều giờ hoặc nhiều ngày, nên bản backup không phản ánh đúng một thời điểm.

- File bị xóa hoặc biến mất sau khi chốt plan: ghi vào `skipped`.
- File mới sau khi chốt plan: không được đưa vào, ghi rõ trong tài liệu.
- Manifest ghi thời điểm bắt đầu, kết thúc và số lần resume. Restore in cảnh báo nếu khoảng cách lớn hơn 24 giờ.
- Giữ nguyên quy tắc hiện tại về `VOLATILE_PATHS`, `changed`, đọc lại file đang đổi và dừng khi file lớn đổi lúc đọc.

### Mạng và ngắt

- Lỗi mạng: thử lại với khoảng chờ tối đa 5 phút, trong tối đa `--max-wait` (mặc định 6 giờ).
- Lỗi không tự hết (sai xác thực, hết quota): dừng ngay.
- Ctrl+C: dọn file tạm, in lệnh để chạy tiếp. Tuyệt đối không xóa gì trên cloud.
- Lần chạy sau dọn file tạm do lần sập máy để lại dưới `~/.cache/dotfiles-backup`.
- Dùng `flock` trên file local để chặn hai lần backup cùng lúc trên một máy.

### Restore

- Giữ nguyên nguyên tắc kiểm tra toàn bộ từ cloud trước khi ghi vào home.
- Lưu tiến độ ở `~/.cache/dotfiles-restore/<ID>.json`, gắn với SHA-256 của manifest. Manifest khác thì bỏ tiến độ cũ.
- Phần đã kiểm tra hoặc đã giải nén xong (sau `fsync`) được bỏ qua khi chạy lại.
- Dọn các file `.restore-file-*` còn sót lại sau khi sập máy.
- Chạy lại không được tạo thêm bản sao `.restore-backup-*` cho file đã được chính lần restore này ghi. Cần kiểm tra kỹ hành vi hiện tại của `restore_tar` trong `scripts/transfer.py`.
- `--dry-run` vẫn kiểm tra đủ và không ghi tiến độ làm thay đổi kết quả của lần chạy thật.

### Lệnh `prune` phải sửa cùng lúc

`prune` hiện chọn mọi thư mục chưa có `manifest.json` và cũ hơn 24 giờ. Với resume, đó có thể là bản đang chờ chạy tiếp, nên **nếu không sửa, `prune --apply` sẽ xóa tiến độ**.

- Mặc định chỉ chọn thư mục không có `plan.json`, hoặc có `plan.json` và cũ hơn 30 ngày (`--min-age-hours` vẫn đổi được).
- Bản xem trước phải in số phần đã xong của từng thư mục.

## `setup.sh`

`setup.sh` có nhiều bước chạy lại được: `pacman --needed`, `yay --needed`, `flatpak --or-update`, `stow -R`. Vì vậy ưu tiên là sửa các điểm kẹt khi bị ngắt, sau đó mới thêm đánh dấu bước để đỡ tốn thời gian.

Các điểm cần sửa, theo thứ tự trong script:

| Chỗ | Vấn đề khi bị ngắt | Cách sửa |
|---|---|---|
| Installer JaKooLit | Chỉ kiểm tra có `~/.config/hypr/hyprland.conf`. Nếu file đã được tạo mà installer chưa chạy xong, lần sau script coi như đã cài xong nền. | Chỉ ghi dấu "đã cài nền" khi installer thoát thành công. Hỏi người dùng nếu có `hyprland.conf` mà không có dấu này, để không chặn máy đã cài từ trước. |
| Thư mục `~/.cache/jakoolit-install.*` | Mỗi lần chạy lại clone một bản mới và để lại bản cũ. | Dùng lại hoặc dọn bản chưa hoàn tất, nhưng giữ log của lần chạy lỗi gần nhất. |
| `pacman -Syu` | Sập máy có thể để lại `/var/lib/pacman/db.lck`, lần sau báo lỗi khóa. | Nếu có lock mà không có tiến trình pacman, dừng và hướng dẫn kiểm tra. Không tự xóa lock, không tự sửa giao dịch dở. |
| `git clone` Oh My Zsh, plugin, theme | Sập máy khi đang clone để lại thư mục dở. Lần sau `[[ ! -e ]]` bỏ qua clone rồi báo lỗi bắt sửa tay. | Clone vào thư mục tạm cùng filesystem, kiểm tra file cần có, rồi `mv` vào đích. |
| `stow_configs`, sau khi chuyển `UserConfigs` | Từ lúc `mv` đến lúc `stow`, `~/.config/hypr/UserConfigs` không tồn tại, nên Hyprland có thể lỗi cấu hình nếu dừng ở đây. | Dùng `trap` để báo rõ trạng thái và lệnh chạy lại. Đưa `UserConfigs` từ bản sao về chỗ cũ nếu `stow` chưa chạy cho `hypr`. |
| `.dotfiles-backup.*` | Mỗi lần chạy tạo thêm một thư mục, kể cả khi rỗng. File cũ có thể nằm rải ở nhiều lần chạy dở. | Dùng lại thư mục của lần chưa hoàn tất, xóa thư mục rỗng khi kết thúc. |

Đánh dấu bước:

- Các bước: cài nền, package chính thức, AUR, Flatpak, zsh, stow. Mỗi bước chỉ được đánh dấu sau khi thành công.
- Lưu ở `~/.local/state/dotfiles-setup/`, kèm `/etc/machine-id`. **Dấu phải bị bỏ qua nếu machine-id khác**, vì restore home từ backup có thể mang dấu của máy cũ sang máy mới và làm setup bỏ qua việc cài.
- Bước package kèm thêm SHA-256 của danh sách tương ứng (`pkglist.txt`, `packages/flatpak-apps.txt`). Danh sách đổi thì chạy lại bước đó.
- Bước `stow` luôn chạy lại, vì nhanh và không gây hại.
- Thêm `--from-start` để bỏ qua mọi dấu. Script hiện từ chối mọi tham số, nên sửa cả đoạn kiểm tra này.
- In danh sách bước sẽ bỏ qua trước khi chạy.

## Các giai đoạn

Mỗi giai đoạn là một commit riêng, test qua mới sang giai đoạn sau.

1. **Tách phần, chưa resume.** Thêm plan, part và manifest `version: 3`. Restore đọc cả v2 và v3.
2. **Resume cho backup.** Thêm `done.json`, phát hiện bản dở, `--resume`, `--fresh`, `--max-wait`, `flock`. Sửa `prune` trong cùng giai đoạn này.
3. **Resume cho restore.** Thêm tiến độ local và dọn file tạm.
4. **Cập nhật tài liệu.** Sửa `docs/backup-restore.md`, đặc biệt các câu hiện nói không có resume.
5. **Sửa điểm kẹt của `setup.sh`.** Làm theo bảng trong mục `setup.sh`. Giai đoạn này độc lập với backup, có thể làm trước nếu cần.
6. **Đánh dấu bước cho `setup.sh`.** Thêm dấu theo `machine-id` và `--from-start`.

`cleanup.sh` không cần sửa. `transfer.py` chỉ cần sửa nếu cùng dùng logic với restore.

## Kiểm thử

Thêm vào `tests/test_cloud_backup.py`, dùng rclone remote local hoặc giả lập:

- Ngắt ở từng thời điểm: trước `plan.json`, giữa chunk, sau chunk cuối nhưng trước `done.json`, trước `manifest.json`.
- Chạy lại sau mỗi lần ngắt, xác nhận phần đã xong không upload lại và kết quả restore đúng.
- Có file bị đổi, bị xóa hoặc thêm mới giữa hai lần chạy.
- Tham số khác plan thì dừng, `--fresh` tạo ID mới.
- Bản không có manifest không restore được.
- Checksum sai ở một chunk của phần đã xong thì không phát hành manifest.
- `prune` giữ bản còn resume được và xóa bản quá hạn.
- Bản v2 vẫn restore được.
- Ctrl+C không xóa gì trên cloud.

Sau đó thử thật trên một thư mục nhỏ với OneDrive: Ctrl+C, tắt mạng giữa chừng, kill -9, rồi chạy lại.

Với `setup.sh`, dùng `HOME` tạm và giả lập `pacman`, `yay`, `flatpak`, `git`, `stow`:

- Ngắt ở từng bước rồi chạy lại, xác nhận bước đã xong được bỏ qua và kết quả cuối giống lần chạy không bị ngắt.
- Thư mục clone dở không làm lần sau bị kẹt.
- Ngắt giữa `mv UserConfigs` và `stow` không làm mất `UserConfigs`.
- Dấu có `machine-id` khác bị bỏ qua. Đổi `pkglist.txt` thì bước package chạy lại.
- `--from-start` chạy lại mọi bước.

Sau đó thử toàn bộ trên máy ảo trắng, ngắt ít nhất một lần trong lúc cài.

## Hoàn thành khi

- Tất cả test qua, CI xanh.
- Một bản backup thật đã bị ngắt ít nhất một lần, chạy tiếp xong, và `restore --dry-run` thành công.
- Restore thật một thư mục con từ bản đó đúng nội dung.
- Sau đó mới được xóa bản v2 cũ.
- `setup.sh` bị ngắt rồi chạy lại trên máy ảo trắng vẫn cho kết quả hoàn chỉnh.
