# Xóa Arch cũ, chia lại dung lượng và cài Arch mới

Đây là nhánh bổ sung cho [quy trình cài lại](reinstall.md): **xóa phân vùng root Arch cũ**, điều chỉnh cách chia dung lượng, rồi cài lên root mới. Khác với format root cũ, cách này thay đổi bảng phân vùng. Xóa/format sẽ làm mất dữ liệu Arch, kể cả home nếu chung root.

Phạm vi: cùng một ổ GPT, Windows UEFI, một ESP dùng chung, root Arch ext4 không mã hóa và home nằm trong root. Giữ nguyên EFI, Microsoft Reserved, Recovery và các phân vùng dữ liệu khác. Không hướng dẫn di chuyển phân vùng, thay bảng GPT, RAID/LVM, nhiều ESP hoặc chuyển sang ổ khác.

## 1. Chuẩn bị khi Arch cũ vẫn còn chạy

1. Làm phần backup trong [reinstall.md](reinstall.md), đọc `REPORT.txt`, kiểm tra checksum trên OneDrive và thử truy cập/giải mã từ thiết bị khác. Giữ backup độc lập, lưu BitLocker recovery key ngoài máy. Script backup **không xóa hay chia phân vùng**.
2. Lưu sơ đồ ổ và nhận diện root cũ bằng UUID/PARTUUID, model, dung lượng trong `reports/disks.txt` và `reports/mounts.txt`. Chụp thêm Disk Management của Windows để biết thứ tự phân vùng.
3. Thử chọn **Windows Boot Manager trực tiếp trong boot menu UEFI** và xác nhận Windows vào được. Không chỉ thử Windows qua GRUB: xóa root Arch có thể làm GRUB mất cấu hình và không hoạt động. Nếu Windows không boot trực tiếp, xử lý trước khi xóa Arch.
4. Chuẩn bị USB Arch, thử boot UEFI và có mạng. Tắt Fast Startup/hibernate Windows theo mục 0.1 của [hướng dẫn cài đặt](arch-windows-dual-boot.md), rồi shutdown hoàn toàn.
5. Chốt dung lượng muốn dành cho Arch và Windows. Root mới phải đủ cho hệ điều hành, package và dữ liệu sẽ restore; kích thước archive không phải dung lượng trống cần thiết sau cài.

## 2. Chọn nhánh theo mục đích

| Mục đích | Quy trình |
|---|---|
| Chỉ tạo lại Arch trong vùng Arch cũ, giữ nguyên hoặc giảm dung lượng | Xóa root cũ ở mục 3, tạo root mới ở mục 5. Phần dư giữ Unallocated. |
| Tăng dung lượng Arch từ Windows | Trong Windows, thu nhỏ đúng phân vùng bằng Disk Management theo mục 0.1 của hướng dẫn chính; giữ Unallocated. Sau khi xóa Arch cũ, chỉ gộp được các vùng trống **liền nhau**. Nếu bị phân vùng khác ngăn cách, dừng. |
| Giảm Arch để tăng Windows | Xóa root cũ ở mục 3, tăng Windows trước ở mục 4, giữ lại một vùng Unallocated cho Arch rồi làm mục 5. |

Không thể cộng hai vùng trống bị ngăn cách thành một phân vùng ext4 thông thường. Không xóa Recovery hay di chuyển Windows để cố làm theo ví dụ. Nếu bố cục không phù hợp, giữ nguyên và lập phương án riêng từ sơ đồ thật.

## 3. Xóa đúng root Arch cũ từ USB

**Nơi chạy: USB Arch, tài khoản root mặc định; không chạy trong Arch đã cài.** Làm [export archive từ OneDrive trong USB](backup-restore.md#4-lấy-báo-cáo-và-efi-trước-khi-phân-vùng) trước; mở báo cáo trong `metadata.tar` vào thư mục tạm riêng để đọc. Nếu không có mạng hoặc không giải mã được, dừng trước khi xóa. Đối chiếu lại:

```bash
lsblk -o NAME,SIZE,MODEL,TYPE,FSTYPE,UUID,PARTUUID,MOUNTPOINTS
fdisk -l
efibootmgr -v
findmnt /
swapon --show
```

Root `/` hiện phải thuộc môi trường live, không phải root Arch cũ. Phân vùng sắp xóa không được mount hoặc dùng làm swap. Nếu đang được sử dụng, dừng, xác định vì sao; không ép xóa. Các thông tin root cũ phải khớp bản sao. Không coi nhãn “Linux filesystem” là đủ nếu có nhiều phân vùng Linux.

Làm bước nhận diện EFI ở mục 4 của [hướng dẫn chính](arch-windows-dual-boot.md). Nếu EFI gần đầy, có thể làm mục 4.1 theo đúng điều kiện backup **trước khi xóa root**; sau đó quay lại đây. Việc xóa phân vùng root không tự giải phóng các file kernel cũ nằm trên ESP.

Mở `cfdisk` trên đúng **ổ**, ví dụ dưới phải thay theo model/thiết bị đã đối chiếu:

```bash
cfdisk /dev/nvme0n1
```

Nếu công cụ yêu cầu tạo bảng phân vùng mới, thoát ngay. Trong bảng hiện có:

1. Chọn duy nhất dòng root Arch cũ đã xác minh → **Delete**.
2. Kiểm tra dòng đó thành **Free space**; các phân vùng Windows/EFI/Recovery/dữ liệu vẫn nguyên vị trí và kích thước. Chưa ghi nếu không khớp.
3. Chọn **Write**, xác nhận `yes`, rồi **Quit**. Trước Write có thể Quit để hủy; sau Write không còn coi Arch cũ là hệ thống khởi động được. Nếu báo không đọc lại được bảng phân vùng, reboot lại USB và nhận diện lại trước mọi bước khác.

Đây là thao tác bỏ phân vùng, không phải xóa an toàn dữ liệu để bán ổ. Hành vi Delete/Write và điều kiện đọc lại bảng được mô tả trong [manual cfdisk](https://man.archlinux.org/man/cfdisk.8.en).

## 4. Nếu muốn dành thêm dung lượng cho Windows

Bỏ qua mục này nếu không tăng Windows. **Nơi thực hiện: Windows**, boot trực tiếp bằng Windows Boot Manager; không chọn GRUB cũ.

Mở `Win + X` → **Disk Management**, xác nhận đúng Disk và vùng Unallocated vừa tạo. Muốn mở rộng một phân vùng bằng Disk Management, vùng trống phải ở cùng ổ và **liền ngay bên phải** phân vùng đó. Nếu Recovery/ESP/phân vùng khác nằm giữa hoặc Extend Volume bị mờ, dừng; không xóa phân vùng ngăn cách. [Microsoft: Extend a volume](https://learn.microsoft.com/en-us/windows-server/storage/disk-management/extend-a-basic-volume).

Nếu đúng điều kiện, nhấp phải phân vùng Windows cần tăng → **Extend Volume**. Nhập lượng dung lượng muốn thêm, **không nhận toàn bộ mặc định** nếu còn cần chỗ cho Arch. Ví dụ riêng: vùng trống 200 GiB, muốn dành lại 120 GiB cho Arch thì chỉ thêm khoảng 80 GiB cho Windows; đối chiếu số MB và dung lượng còn lại trong giao diện, không sao chép con số khi ổ khác ví dụ.

Sau khi hoàn tất, kiểm tra còn đúng vùng Unallocated dự kiến. Không tạo New Simple Volume/NTFS trong vùng dành cho Arch. Chụp sơ đồ mới, shutdown Windows hoàn toàn rồi boot USB Arch lại. Nếu BitLocker yêu cầu khóa, dùng khóa đã lưu; không format để vượt yêu cầu.

## 5. Tạo root Arch mới và tiếp tục cài

**Nơi chạy: USB Arch.** Lặp lại `lsblk`, `fdisk -l` và nhận diện EFI ở mục 3; tên thiết bị có thể đổi sau reboot. Mở lại `cfdisk` trên đúng ổ, chọn **Free space** theo vị trí và kích thước đã chốt → **New**, nhập dung lượng Arch muốn dùng, ví dụ `120G` chỉ khi vùng trống đủ. Giữ loại `Linux filesystem`. Chỉ ghi sau khi kiểm tra các phân vùng khác không đổi. Có thể để phần dư Unallocated. Không dùng Resize để thu nhỏ filesystem cũ trong quy trình này.

Sau Write/Quit, chạy:

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,PARTLABEL,PARTUUID,MOUNTPOINTS
```

Ghi **tên root mới** và ESP hiện có. Số phân vùng và PARTUUID có thể khác trước; chữ ký filesystem cũ đôi khi vẫn hiện trước format, không phải bằng chứng dữ liệu đã được giữ. Nếu kernel chưa nhận bảng mới, reboot USB và kiểm tra lại.

Quay về [mục 4 của hướng dẫn chính](arch-windows-dual-boot.md#4-nhận-diện-ổ-efi-và-vùng-trống--không-xóa-windows), đoạn **format và mount sau Cách A/B/C**. Bỏ qua thao tác tạo phân vùng lần nữa. Thay ví dụ bằng tên root mới vừa xác minh; `mkfs.ext4` xóa dữ liệu trên phân vùng đó. Mount root mới tại `/mnt`, ESP cũ tại `/mnt/efi`, không format ESP. Tiếp tục mục 5–11 để cài base, tạo tài khoản, bootloader và setup.

Tạo `fstab` mới bằng `genfstab` và GRUB mới theo hướng dẫn. **Không phục hồi `fstab`, GRUB hay EFI cũ đè lên hệ thống mới**: UUID filesystem sẽ thay đổi khi format. Sau setup, dùng restore để lấy dữ liệu, kiểm tra cả Arch và Windows trước khi bỏ backup.

## Giới hạn kiểm tra

Các thao tác được đối chiếu manual cfdisk và tài liệu Microsoft, chưa thử repartition máy thật/VM. Không có con số thiết bị hoặc dung lượng nào ở đây là chỉ định cho ổ hiện tại của bạn. Nếu phải di chuyển phân vùng để đạt bố cục mong muốn, hướng dẫn này dừng ở đó.
