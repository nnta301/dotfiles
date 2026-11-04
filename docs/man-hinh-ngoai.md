# Sử dụng màn hình ngoài hoặc máy chiếu

Hướng dẫn này dành cho phiên Hyprland đang chạy. Mở terminal trong Hyprland, cắm HDMI và chọn đúng nguồn HDMI trên màn hình ngoài. Các lệnh thay đổi cấu hình **tạm thời**, không sửa file trong repo.

## Xác định tên màn hình

```bash
hyprctl monitors
```

Tìm tên ở dòng `Monitor ...`. Ví dụ: màn hình laptop là `eDP-1`, màn hình ngoài là `HDMI-A-3`. **Tên HDMI có thể thay đổi** theo cổng, máy chiếu hoặc chế độ GPU; thay tên ví dụ trong các lệnh bên dưới bằng tên thực tế. Mục `availableModes` cho biết độ phân giải và tần số quét mà màn hình báo hỗ trợ.

## 1. Chiếu giống màn hình laptop

Dùng khi thuyết trình: màn hình ngoài hiển thị cùng nội dung với laptop.

```bash
hyprctl keyword monitor "HDMI-A-3,preferred,auto,1,mirror,eDP-1"
```

Thay `HDMI-A-3` bằng tên màn hình ngoài và `eDP-1` bằng tên màn hình laptop nếu khác. `preferred` chọn chế độ được màn hình ngoài đề xuất; `1` là tỉ lệ hiển thị 100%. Màn hình ngoài nhận bản sao hình của laptop, nên độ nét phụ thuộc độ phân giải laptop.

## 2. Chỉ sử dụng màn hình ngoài

Phù hợp khi dùng laptop như máy bàn. Đặt màn hình ngoài trước và chỉ tắt laptop khi màn hình ngoài đã hiển thị được:

```bash
hyprctl keyword monitor "HDMI-A-3,preferred,auto,1"
hyprctl monitors
```

Kiểm tra hình trên màn hình ngoài, rồi chạy:

```bash
hyprctl keyword monitor "eDP-1,disable"
```

Hyprland chuyển các cửa sổ và workspace khỏi màn hình bị tắt. Màn hình ngoài dùng chế độ `preferred` của chính nó và scale 100%; `preferred` không nhất thiết là tần số quét cao nhất. Để chọn chế độ cụ thể, lấy giá trị từ `availableModes`, ví dụ nếu màn hình báo hỗ trợ:

```bash
hyprctl keyword monitor "HDMI-A-3,2560x1440@144,auto,1"
```

Nếu hình không ổn định, dùng lại `preferred`. Không chọn độ phân giải hoặc tần số màn hình không báo hỗ trợ.

## Bật lại màn hình laptop

Trước khi rút dây HDMI, bật lại màn hình laptop và xác nhận đã có hình:

```bash
hyprctl keyword monitor "eDP-1,preferred,auto,1"
```

Có thể chạy `hyprctl reload` để tải lại cấu hình Hyprland đã lưu; điều này áp dụng lại các thiết lập màn hình trong cấu hình hiện tại. Kiểm tra hình trên laptop trước khi rút dây. Nếu không thấy tên màn hình trong ví dụ, thay bằng tên hiển thị trong `hyprctl monitors all`.

## Không nhận màn hình HDMI

Kiểm tra nguồn HDMI, dây và adapter; sau đó chạy `hyprctl monitors all` trong terminal Hyprland. Nếu màn hình không xuất hiện, kiểm tra driver và GPU. Trên laptop Dell G5 5500 từng kiểm tra, màn hình ngoài chỉ xuất hình sau khi chuyển EnvyControl từ `integrated` sang `hybrid`; đây là kết quả của máy đó, không phải quy tắc cho mọi laptop.

Đổi chế độ GPU có thể yêu cầu khởi động lại và tạo lại initramfs. Trước khi đổi, kiểm tra dung lượng `/boot`, có bản sao và USB khôi phục; xem [checklist cài lại](reinstall.md). Nếu lệnh đổi chế độ báo lỗi tạo initramfs, xử lý lỗi trước khi reboot.

Tham khảo [Hyprland: cấu hình màn hình](https://wiki.hypr.land/0.54.0/Configuring/Monitors/) và [hyprctl](https://wiki.hypr.land/0.54.0/Configuring/Using-hyprctl/).
