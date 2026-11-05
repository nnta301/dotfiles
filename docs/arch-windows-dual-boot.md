# Cài Arch Linux từ Windows và thiết lập dotfiles

Hướng dẫn này dành cho người mới muốn **giữ Windows và cài Arch Linux song song trên cùng ổ đĩa**. Đọc hết phần phạm vi và sao lưu trước khi bắt đầu. Có thể mở tài liệu trên điện thoại vì máy sẽ khởi động lại nhiều lần. Các trang gốc được dẫn ở cuối; giao diện có thể thay đổi.

## 0. Phạm vi và chuẩn bị

Lộ trình hỗ trợ Windows đã cài trên máy x86-64 ở chế độ **UEFI/GPT**, một EFI System Partition (ESP) hiện có của Windows trên cùng ổ, và Arch trên một phân vùng ext4 riêng: tạo mới từ vùng trống hoặc cài lại vào phân vùng Arch cũ đã xác định chắc chắn. Dùng GRUB trong ESP hiện có, kernel/initramfs trên phân vùng ext4 của Arch, NetworkManager, không tạo swap, không mã hóa Arch, không hibernate Linux, không RAID/LVM, tắt Secure Boot. Muốn cấu hình khác cần một lộ trình riêng.

**Không format/xóa ESP, Windows, Recovery, Microsoft Reserved hay phân vùng dữ liệu khác; không thay đổi kích thước ESP/Recovery/MSR.** Chỉ thu nhỏ Windows theo mục 0.1; nếu muốn mở rộng Windows bằng vùng Arch cũ, dùng nhánh [chia lại dung lượng](repartition-arch.md) theo điều kiện riêng. Thao tác phân vùng luôn có nguy cơ mất dữ liệu nếu chọn nhầm. Nếu có nhiều ESP, nhiều ổ giống nhau, Windows dùng Legacy/MBR, RAID/Intel RST, không xác định được ESP hay vùng trống, dừng và nhờ hỗ trợ; không đoán theo tên `/dev/...`.

**Đang dùng Arch và chuẩn bị cài lại?** Làm trước [checklist thao tác trên Arch cũ](reinstall.md), từ cấu hình backup OneDrive đến kiểm tra USB. Xong checklist mới quay lại các bước phân vùng bên dưới.

Nếu máy đã có Arch và định cài lại, bạn có thể dùng lại phân vùng root cũ theo nhánh riêng ở mục 4; thao tác format sẽ xóa Arch và mọi dữ liệu trên phân vùng đó. Ảnh chụp ở [reinstall.md](reinstall.md) cho thấy máy này từng có nhiều phân vùng Windows/BitLocker và Arch: phải kiểm tra lại trạng thái thực tế.

**Trước khi xóa Arch cũ**, mở terminal trong Arch đang chạy và ghi lại kết quả các lệnh chỉ đọc sau để đối chiếu với USB:

```bash
findmnt -no SOURCE,UUID,FSTYPE /
findmnt -T /home -o TARGET,SOURCE,FSTYPE,UUID
lsblk -o NAME,SIZE,MODEL,FSTYPE,UUID,PARTUUID,MOUNTPOINTS
```

Ghi root filesystem UUID, PARTUUID, tên ổ/model, kích thước, và lưu kết quả ở nơi ngoài ổ máy. Nếu `/home` chung root, toàn bộ home sẽ bị xóa khi format root; sao lưu và kiểm tra bản sao trước. Nếu `/home` riêng hoặc root dùng mã hóa/LVM/Btrfs, hướng dẫn cài lại đơn phân vùng này không áp dụng: dừng, lập phương án riêng. UUID filesystem sẽ thay đổi sau khi format, còn PARTUUID giúp đối chiếu chính phân vùng; tên `/dev/...` có thể đổi giữa các lần boot.

Nếu cài lại Arch trên máy cũ và EFI gần đầy, làm thêm **mục 0.2** để sao lưu EFI trước khi tắt Arch. Mục 4.1 sẽ dùng bản sao đó để xử lý file boot Arch cũ từ USB cài đặt.

- Sao lưu file, dự án, khóa, dữ liệu ứng dụng ra ổ độc lập và xác nhận mở được bản sao. Lưu **BitLocker recovery key** ngoài máy trước mọi thay đổi firmware, boot hoặc phân vùng; kiểm tra mở được khóa. Windows có thể yêu cầu khóa sau khi đổi Secure Boot/bootloader. Không đăng khóa lên Git. Xem [Microsoft: tìm khóa khôi phục](https://support.microsoft.com/windows/find-your-bitlocker-recovery-key-6b71ad27-0b89-ea08-f143-056f5ab347d6).
- Cần USB trống ít nhất 4 GB (sẽ bị xóa), nguồn điện, internet; nên dành ít nhất 40 GB **vùng trống liên tục** cho Arch và nhiều hơn tùy nhu cầu. Không dùng vùng chứa bản sao lưu. Ngắt các ổ ngoài không liên quan.
- Trong Windows, `Win + R` → `msinfo32`: `BIOS Mode` phải là `UEFI`. Trong Disk Management kiểm tra ổ là GPT qua Properties → Volumes. Nắm rõ phím boot menu theo tài liệu hãng. Không đổi RAID/RST hay các thiết lập ổ khác khi chưa hiểu tác động.
- `root` là tài khoản quản trị; `sudo` chạy một lệnh quản trị bằng mật khẩu tài khoản thường. Khi nhập mật khẩu Linux, ký tự không hiển thị.

## 0.1. Chuẩn bị vùng trống trong Windows

**Nơi thực hiện: Windows.** Sao lưu xong và kiểm tra khóa BitLocker trước. Mở PowerShell hoặc Command Prompt **Run as administrator**, chạy lệnh sau để tắt cả Fast Startup và hibernation của Windows (Hibernate sẽ không còn dùng được cho đến khi bật lại):

```powershell
powercfg /H off
```

Theo [ArchWiki](https://wiki.archlinux.org/title/Dual_boot_with_Windows), sau khi đổi thiết lập cần **Shut down hoàn toàn**, không chỉ Restart, trước khi chạy Linux với ESP dùng chung. Đừng hibernate Windows hay Linux trong quy trình này.

Nếu định **cài lại vào root Arch cũ**, sau khi đã ghi nhận root và sao lưu theo mục 0, bỏ qua các bước thu nhỏ 1–3; kiểm tra EFI ở bước 4. Nếu cài mới vào vùng trống, làm các bước 1–4:

1. Trong Windows, `Win + X` → **Disk Management** (hoặc `Win + R` → `diskmgmt.msc`). Ghi lại số Disk, dung lượng, model ổ; chụp sơ đồ phân vùng để đối chiếu sau. Tìm phân vùng NTFS chứa `C:` mà bạn muốn thu nhỏ, không chọn EFI/Recovery.
2. Nhấp phải `C:` → **Shrink Volume**. Ví dụ để dành khoảng 60 GiB, nhập `61440` MB, miễn Windows cho phép và còn đủ chỗ cho Windows. Nhấn **Shrink**. Nếu giới hạn nhỏ hơn mong muốn, không ép bằng công cụ khác; file không di chuyển được có thể giới hạn mức thu nhỏ. Xem [Microsoft Shrink a Basic Volume](https://learn.microsoft.com/windows-server/storage/disk-management/shrink-a-basic-volume).
3. Xác nhận xuất hiện một vùng màu đen **Unallocated** đúng dung lượng trên đúng Disk. **Để nguyên Unallocated**: không tạo New Simple Volume, không format NTFS. Ghi lại dung lượng và vị trí của vùng trống giữa các phân vùng để so sánh trong Linux.
4. Ghi lại ESP mà Windows đang dùng: Disk Management có mục **EFI System Partition**, thường FAT32 và không có ký tự ổ; có thể kiểm tra thêm ở Linux bằng `efibootmgr -v` và đường dẫn Microsoft. Không coi chỉ kích thước hay thứ tự là đủ để nhận diện. Nếu không xác định được ESP chứa Windows Boot Manager, dừng.
5. Sau khi tạo USB ở mục 2, tắt Windows hoàn toàn bằng **Shut down** trước khi khởi động USB. Trước khi đổi Secure Boot, xem hướng dẫn hãng và BitLocker: thay đổi firmware có thể yêu cầu recovery key; nếu cần tạm ngưng bảo vệ, làm theo [Microsoft](https://learn.microsoft.com/windows/security/operating-system-security/data-protection/bitlocker/operations-guide) rồi bật lại sau khi hoàn tất và kiểm tra Windows. Tạm ngưng bảo vệ làm khóa có thể được truy cập trong thời gian đó.

## 0.2. Sao lưu EFI trước khi cài lại Arch cũ

**Nơi thực hiện ban đầu: Arch cũ.** Dùng `./scripts/backup.sh` theo [reinstall.md](reinstall.md): script mã hóa và gửi EFI, cấu hình hệ thống, repo và dữ liệu lên OneDrive. Sau khi có thông báo hoàn tất, kiểm tra bằng `restore.sh <remote-id> --dry-run`. Không cần tự tạo tar EFI trên ổ ngoài.

Trước khi xóa Arch, giữ mật khẩu/salt crypt, thông tin đăng nhập và BitLocker recovery key ngoài máy. Boot thử USB, có mạng và thử tải lại archive hệ thống theo [hướng dẫn export từ cloud](backup-restore.md#4-lấy-báo-cáo-và-efi-trước-khi-phân-vùng). Lệnh export tạo `efi.tar`, `etc.tar`, `repo.tar`, `metadata.tar` trong thư mục mới như `/tmp/arch-rescue`; không tự phục hồi chúng vào hệ thống.

Trong USB, mở báo cáo từ `metadata.tar` ở thư mục tạm riêng để đối chiếu root/ESP. Mục 4.1 dùng `/tmp/arch-rescue/efi.tar` làm ví dụ: phải thay nếu export ở nơi khác. Dữ liệu `/tmp` mất sau reboot, nhưng bản gốc trên cloud vẫn phải được giữ; nếu reboot USB thì tải lại trước thao tác xóa.

Mục 4.1 chỉ áp dụng cho bố cục cũ `/boot` là ESP FAT chứa `vmlinuz-linux`, `initramfs-linux.img`, `intel-ucode.img`. Báo cáo mount/cmdline trong backup và file thực tế phải khớp. Không truy cập được cloud, không có khóa hoặc không đối chiếu được thì dừng trước khi xóa/format. Backup cloud không thay thế việc xác minh đúng thiết bị.

## 1. Tải ISO và kiểm tra trên Windows

**Nơi thực hiện: Windows, trình duyệt.** Vào [Arch Linux Downloads](https://archlinux.org/download/), chọn một HTTP mirror và tải file `archlinux-...-x86_64.iso`. Trang tải công bố SHA256 cho bản mới nhất; tên và giá trị đổi theo phiên bản.

Mở **PowerShell** trong Windows. Gõ `Get-FileHash -Algorithm SHA256 ` (có dấu cách cuối), kéo file ISO từ File Explorer vào cửa sổ để tự điền đường dẫn có dấu nháy, rồi nhấn Enter. Ví dụ, thay tên bằng file bạn tải:

```powershell
Get-FileHash -Algorithm SHA256 "C:\Users\An\Downloads\archlinux-2026.11.01-x86_64.iso"
```

So sánh `Hash` với SHA256 của **đúng bản ISO** trên trang Arch. Nếu khác, tải lại và kiểm tra lại. Checksum phát hiện file tải sai; để xác thực chữ ký của bản phát hành, làm thêm bước PGP theo trang tải Arch.

## 2. Tạo USB boot và vào môi trường cài đặt

**Nơi thực hiện: Windows.** Tải [Rufus chính thức](https://rufus.ie/), chạy file `.exe`. Trong Rufus:

1. Cắm USB, ở **Device** chọn đúng USB theo tên và dung lượng. **Mọi dữ liệu trên USB sẽ bị xóa**.
2. Ở **Boot selection**, nhấn **SELECT**, chọn ISO Arch vừa kiểm tra. Chọn `GPT` ở **Partition scheme**, nhấn **START**; nếu Rufus hỏi ISO Image mode hay DD Image mode, chọn **DD Image mode**. Xác nhận xóa đúng USB và đợi hoàn tất.
3. **Shut down hoàn toàn** Windows, sau đó bật máy và mở boot menu bằng phím của hãng (thường F12, Esc hoặc F9; xem tài liệu máy). Chọn mục USB có chữ **UEFI**. Trong firmware, tắt Secure Boot cho lộ trình này; không thay đổi tùy chọn lưu trữ/RAID nếu không hiểu tác động. Chọn `Arch Linux install medium`.

**Nơi thực hiện từ đây đến hết mục 7: màn hình dòng lệnh của USB Arch (live environment)**, trừ khi có ghi `chroot`. Live environment tự đăng nhập root. Sau khi boot, xác nhận thực sự ở UEFI:

```bash
cat /sys/firmware/efi/fw_platform_size
```

Kết quả `64` phù hợp hướng dẫn. Nếu file không tồn tại hoặc kết quả khác, khởi động lại và chọn đúng mục USB UEFI; không tiếp tục phân vùng.

## 3. Kết nối internet trong USB

Cắm Ethernet nếu có, chờ một chút rồi thử:

```bash
ping -c 3 archlinux.org
```

Nếu dùng Wi-Fi, chạy `iwctl`, sau đó các lệnh dưới đây **bên trong dấu nhắc `[iwd]#`**:

```text
device list
station wlan0 scan
station wlan0 get-networks
station wlan0 connect "Ten WiFi"
exit
```

Thay `wlan0` bằng tên hiển thị từ `device list`, thay `Ten WiFi` bằng SSID thực tế; nhập mật khẩu khi được hỏi. Lệnh `exit` chỉ thoát iwctl. Chạy lại `ping -c 3 archlinux.org` ở dòng lệnh USB. Nếu không có mạng, dừng và xử lý kết nối trước khi tiếp tục.

## 4. Nhận diện ổ, EFI và vùng trống — không xóa Windows

**Nơi thực hiện: USB Arch.** Các lệnh ở đây cần quyền root, USB Arch mặc định đã đăng nhập root. Liệt kê ổ, kiểu phân vùng, UUID và hệ thống file:

```bash
lsblk -o NAME,SIZE,MODEL,TYPE,FSTYPE,PARTTYPE,PARTLABEL,UUID,MOUNTPOINTS
fdisk -l
efibootmgr -v
```

Đối chiếu **model, dung lượng, sơ đồ và kích thước vùng Unallocated đã ghi trong Windows**, hoặc thông tin root Arch cũ đã ghi ở mục 0 nếu cài lại. `fdisk -l` cho thấy các phân vùng; dùng `cfdisk` ở bước sau để thấy dòng `Free space`. `efibootmgr -v` hiển thị mục `Windows Boot Manager`, trong đó `HD(...,GPT,...)` có PARTUUID của ESP. So sánh bằng:

```bash
lsblk -o NAME,SIZE,FSTYPE,PARTTYPE,PARTUUID,PARTLABEL
```

ESP là phân vùng FAT32 có kiểu `EFI System`, chứa đường dẫn Microsoft. Trường `PARTUUID` phải khớp GUID trong `HD(...,GPT,...)`; UUID của filesystem là giá trị khác. Nếu không có Windows Boot Manager trong `efibootmgr`, hoặc các thông tin không khớp, **dừng**. Không tự format hay tạo ESP mới. Các lệnh sau dùng **ví dụ** ổ `/dev/nvme0n1` và ESP `/dev/nvme0n1p1`; tên thật của bạn có thể khác.

Xác nhận ESP bằng cách mount **chỉ đọc**, sau đó tháo:

```bash
mkdir -p /mnt/esp-check
mount -o ro /dev/nvme0n1p1 /mnt/esp-check
ls /mnt/esp-check/EFI/Microsoft/Boot/bootmgfw.efi
df -h /mnt/esp-check
umount /mnt/esp-check
```

Đổi `/dev/nvme0n1p1` thành ESP đã xác minh. Nếu thiếu file, không mount được hoặc không chắc, dừng. Nếu lệnh lỗi, vẫn kiểm tra và unmount nếu đã mount (`mountpoint /mnt/esp-check` rồi `umount /mnt/esp-check`). Ghi lại dung lượng còn trống. Để dự phòng cho GRUB và Windows, hướng dẫn này yêu cầu **ít nhất 32 MiB trống**; đây là ngưỡng thận trọng, không bảo đảm mọi cập nhật sẽ đủ chỗ. Nếu thiếu và đang cài lại Arch cũ đúng phạm vi mục 0.2, làm mục 4.1. Trường hợp khác, dừng để lập phương án riêng; không format ESP.

### 4.1. Lấy lại chỗ từ boot Arch cũ khi EFI gần đầy

**Chỉ thực hiện từ USB Arch**, nếu EFI đang chứa boot Arch cũ như đã ghi và bạn đã sẵn sàng cài lại ngay. **Sau bước xóa, Arch cũ sẽ không boot bình thường**; cần tiếp tục cài Arch mới hoặc khôi phục boot từ bản sao. Không làm trên máy chỉ cài mới Arch, máy có boot khác chưa hiểu, hoặc khi chưa xác nhận được bản sao và BitLocker recovery key.

1. Mount EFI đã xác minh ở mục 4 **chỉ đọc** lại, đổi tên phân vùng ví dụ thành tên đã đối chiếu:

   ```bash
   mount -o ro /dev/nvme0n1p1 /mnt/esp-check
   findmnt -no SOURCE,FSTYPE,OPTIONS /mnt/esp-check
   ls -lh /mnt/esp-check/vmlinuz-linux /mnt/esp-check/initramfs-linux.img /mnt/esp-check/intel-ucode.img
   ls /mnt/esp-check/EFI/Microsoft/Boot/bootmgfw.efi
   ```

   Xác nhận đúng ESP FAT32, tùy chọn có `ro`, các file khớp với kết quả mục 0.2 và còn Windows Boot Manager. Nếu thiếu hoặc khác, dừng.
2. Tải lại archive hệ thống từ OneDrive bằng quy trình [export trong USB](backup-restore.md#4-lấy-báo-cáo-và-efi-trước-khi-phân-vùng), vào thư mục mới `/tmp/arch-rescue` trong ví dụ. Chỉ tiếp tục khi lệnh xác minh/tải thành công. Đối chiếu archive EFI với ESP đang mount chỉ đọc:

   ```bash
   tar -tf /tmp/arch-rescue/efi.tar
   tar -C /mnt/esp-check -df /tmp/arch-rescue/efi.tar
   ```

   Kiểm tra có Windows Boot Manager và ba file boot Arch đã xác định; đọc lỗi hoặc so sánh khác biệt thì **dừng**, không xóa gì. Giữ bản gốc trên OneDrive và khóa giải mã đến khi cả hai hệ điều hành hoạt động. Nếu dùng bản backup ngoài máy khác, thay đúng đường dẫn đã kiểm tra; không mặc định một file tên giống là bản hợp lệ.
3. **Điểm không thể quay lại ngay:** chỉ khi đã sao lưu, xác nhận đúng EFI và chấp nhận Arch cũ sẽ không boot, tháo EFI chỉ đọc rồi mount lại đọc/ghi:

   ```bash
   umount /mnt/esp-check
   mount -o rw /dev/nvme0n1p1 /mnt/esp-check
   findmnt -no SOURCE,FSTYPE,OPTIONS /mnt/esp-check
   ```

   Xác nhận lại `SOURCE` đúng EFI, `FSTYPE` là `vfat` và tùy chọn có `rw`. Nếu mount thất bại hoặc không khớp, **dừng**. Không chạy lệnh xóa trong trường hợp đó.
4. Chỉ xóa ba file Arch cũ đã xác định ở thư mục gốc EFI. `rm -i` hỏi riêng từng file: chỉ trả lời `y` khi đúng file và đã chấp nhận cài lại. **Không xóa `EFI/`, `EFI/Microsoft`, `EFI/Boot`, `EFI/Dell` hay thư mục `grub`; không dùng `rm -rf` hoặc format EFI.**

   ```bash
   rm -i -- /mnt/esp-check/vmlinuz-linux /mnt/esp-check/initramfs-linux.img /mnt/esp-check/intel-ucode.img
   sync
   df -h /mnt/esp-check
   ls /mnt/esp-check/EFI/Microsoft/Boot/bootmgfw.efi
   ```

   Nếu không còn ít nhất 32 MiB trống, Windows Boot Manager thiếu hoặc lệnh báo lỗi, dừng; không tự xóa thêm. Ngưỡng này không bảo đảm đủ cho mọi bản cập nhật Windows.
5. Tháo EFI trước khi mount root mới:

   ```bash
   umount /mnt/esp-check
   ```

   Tiếp tục **Cách A** dưới đây nếu giữ phân vùng root cũ; nếu xóa rồi chia lại, làm **Cách C**. Sau khi format root cũ và mount EFI tại `/mnt/efi`, kernel và `/boot/grub` mới sẽ được tạo trên ext4 của Arch; EFI giữ các file khởi động UEFI. Kiểm tra cả Arch và Windows ở mục 7 trước khi bỏ bản sao.

### Chọn một trong ba cách chuẩn bị phân vùng Arch

**Cách A — cài lại trên phân vùng Arch cũ:** Chỉ áp dụng nếu đã lưu bản sao độc lập và ghi root UUID/PARTUUID từ Arch đang chạy ở mục 0. Đối chiếu `lsblk` với UUID, PARTUUID, model ổ, kích thước và loại `ext4`; kiểm tra đây là phân vùng root cũ, không phải ESP, Windows, phân vùng dữ liệu hay một phân vùng Linux khác. Nếu thiếu bất kỳ thông tin nào hoặc không khớp, dừng. Ghi lại tên thiết bị đúng ở phiên USB, ví dụ `/dev/nvme0n1p6`, rồi **bỏ qua Cách B và C**, đến bước format bên dưới. Format sẽ xóa toàn bộ root cũ, bao gồm `/home` nếu chung root.

**Cách C — xóa root Arch cũ rồi chia lại dung lượng:** Làm [hướng dẫn repartition](repartition-arch.md), gồm backup, kiểm tra Windows Boot Manager, xóa đúng root từ USB và tạo root mới. Không áp dụng Cách A rồi xóa tiếp. Sau khi hoàn tất tạo root mới, quay lại đoạn format/mount dưới đây; không làm lại Cách B.

**Cách B — tạo phân vùng Arch mới trong vùng Unallocated:**

Sau khi xác định chính xác ổ, ESP và một vùng trống liên tục, mở `cfdisk` trên **ổ đĩa**, ví dụ:

```bash
cfdisk /dev/nvme0n1
```

Nếu `cfdisk` yêu cầu chọn loại bảng phân vùng mới thay vì hiển thị các phân vùng Windows, bạn có thể đã chọn sai ổ: chọn thoát, không tạo bảng mới. Trong danh sách:

1. Dùng phím mũi tên chọn **Free space** đúng vị trí và dung lượng đã ghi trong Disk Management. Không chọn dòng phân vùng hiện hữu. Nếu không thấy đúng vùng trống, chọn **Quit** và dừng.
2. Chọn **New**, Enter, nhận toàn bộ dung lượng free space bằng Enter. Loại mặc định `Linux filesystem` phù hợp cho root ext4. Ghi lại tên phân vùng mới hiển thị; số của nó có thể không liên tiếp với phân vùng lân cận.
3. Kiểm tra lại toàn bộ bảng, bảo đảm mọi phân vùng cũ vẫn hiện và chỉ có một phân vùng Linux mới. **Không chọn Delete, không tạo bảng GPT mới.** Chọn **Write**, gõ `yes` để ghi; đây là thời điểm thay đổi bảng phân vùng và nếu chọn sai có thể làm mất dữ liệu. Chọn **Quit**. Nếu chưa chắc, chọn Quit trước Write để hủy.

Kiểm tra lại bằng:

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,PARTLABEL,PARTUUID
```

**Format và mount sau Cách A/B/C:** ví dụ nếu phân vùng Arch đã xác định là `/dev/nvme0n1p9`, chỉ format **phân vùng Arch đã chọn và đối chiếu**; không sao chép số `p9` một cách máy móc. Lệnh này xóa dữ liệu trên phân vùng được chỉ định:

```bash
mkfs.ext4 /dev/nvme0n1p9
```

Gắn phân vùng root mới vào `/mnt` và ESP hiện có vào `/mnt/efi`, **không format ESP**:

```bash
mount /dev/nvme0n1p9 /mnt
mount --mkdir /dev/nvme0n1p1 /mnt/efi
lsblk -f
```

Thay cả hai tên theo kết quả thật. Kiểm tra ext4 mới là `/mnt`, ESP FAT32 là `/mnt/efi` và file `/mnt/efi/EFI/Microsoft/Boot/bootmgfw.efi` vẫn có. Dừng nếu sai. ESP được mount tại `/efi`; kernel của Arch nằm trên ext4 ở `/boot`, do đó không cần nhét kernel vào ESP nhỏ.

## 5. Cài hệ thống cơ bản

**Nơi thực hiện: USB Arch.** Cài kernel, firmware, mạng và các công cụ cần để tiếp tục. Có thể mất thời gian tùy mạng:

```bash
pacstrap -K /mnt base linux linux-firmware networkmanager sudo nano git base-devel grub efibootmgr os-prober fuse3
```

Chờ hoàn tất không lỗi. Nếu lỗi tải package, sửa mạng/mirror trước, rồi chạy lại; không chuyển sang bước sau khi `pacstrap` thất bại.

Tạo cấu hình gắn phân vùng khi khởi động và kiểm tra:

```bash
genfstab -U /mnt >> /mnt/etc/fstab
cat /mnt/etc/fstab
```

Phải thấy mục `/` và `/efi` với UUID tương ứng. Không chạy `genfstab >>` lặp lại vì sẽ thêm dòng trùng. Nếu lỡ chạy lại, dùng `nano /mnt/etc/fstab` xóa dòng trùng. Vào môi trường hệ thống mới:

```bash
arch-chroot /mnt
```

**Từ đây đến lệnh `exit` ở mục 7: chạy trong chroot**, vẫn là root, nhưng thao tác lên hệ thống mới.

## 6. Thiết lập giờ, ngôn ngữ, mạng và tài khoản

Dùng múi giờ Việt Nam và đồng bộ đồng hồ phần cứng:

```bash
ln -sf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime
hwclock --systohc
```

Mở cấu hình ngôn ngữ:

```bash
nano /etc/locale.gen
```

Tìm dòng `#en_US.UTF-8 UTF-8`, xóa ký tự `#` đầu dòng. Trong nano, lưu bằng `Ctrl+O`, Enter; thoát bằng `Ctrl+X`. Tạo locale và đặt mặc định:

```bash
locale-gen
printf 'LANG=en_US.UTF-8\n' > /etc/locale.conf
```

Đặt tên máy; `archpc` chỉ là ví dụ, có thể đổi thành tên ngắn gồm chữ thường, số và dấu gạch ngang:

```bash
printf 'archpc\n' > /etc/hostname
systemctl enable NetworkManager
```

Đặt mật khẩu root và tạo tài khoản dùng hàng ngày. Ví dụ dưới dùng tên `an`; bạn có thể chọn tên khác gồm chữ thường không dấu và số. Thay `an` bằng tên đã chọn trong cả hai lệnh:

```bash
passwd
useradd -m -U -G wheel -s /bin/bash an
passwd an
```

`passwd` đầu tiên đặt mật khẩu **root**, còn `passwd an` đặt mật khẩu cho người dùng. `useradd` tạo thư mục home, nhóm chính cùng tên và thêm người dùng vào nhóm `wheel`. Bash được dùng ban đầu vì Zsh có thể chưa được cài. Nếu có lỗi, dừng và kiểm tra trước khi tiếp tục.

Cho nhóm `wheel` quyền dùng sudo bằng trình kiểm tra cú pháp:

```bash
EDITOR=nano visudo
```

Tìm dòng `# %wheel ALL=(ALL:ALL) ALL`, bỏ dấu `#` đầu dòng, lưu `Ctrl+O`, Enter rồi thoát `Ctrl+X`. Nếu `visudo` báo lỗi, chọn sửa lại và không bỏ qua kiểm tra. Sau đó kiểm tra tài khoản, thay `an` nếu bạn chọn tên khác:

```bash
id an
getent passwd an
```

Kết quả `id` cần có nhóm `wheel`; `getent passwd` cho biết thư mục home và shell. Nếu bạn định khôi phục file từ hệ thống cũ, so sánh UID/GID mới với số đã ghi ở mục 0 và kiểm tra quyền sở hữu file sau khi khôi phục. Tên tài khoản giống nhau không đảm bảo UID/GID giống nhau.

Cài microcode cho đúng CPU: xem `lscpu | grep 'Vendor ID'`. Nếu là `GenuineIntel`, chạy `pacman -S intel-ucode`; nếu là `AuthenticAMD`, chạy `pacman -S amd-ucode`. Chỉ chọn gói phù hợp. Kiểm tra `grep '^HOOKS=' /etc/mkinitcpio.conf` có từ `microcode`; nếu thiếu, mở `nano /etc/mkinitcpio.conf` và thêm `microcode` vào trong ngoặc của dòng `HOOKS`, rồi lưu. Tạo lại initramfs:

```bash
mkinitcpio -P
lsinitcpio --early /boot/initramfs-linux.img | grep microcode
```

Lệnh cuối phải liệt kê đường dẫn microcode; nếu không, kiểm tra gói và `HOOKS` trước khi tiếp tục.

## 7. Cài GRUB và khởi động Arch

**Nơi thực hiện: chroot.** Trước hết kiểm tra ESP đang được gắn tại `/efi` và còn file khởi động Windows:

```bash
findmnt /efi
ls /efi/EFI/Microsoft/Boot/bootmgfw.efi
```

Nếu không đúng, dừng. Cài GRUB vào ESP đã mount; lệnh tạo file GRUB và có thể thay đổi thứ tự boot UEFI. Nó không format ESP:

```bash
grub-install --target=x86_64-efi --efi-directory=/efi --bootloader-id=GRUB
```

Nếu báo lỗi hoặc ESP hết chỗ, dừng; không xóa file Windows. Để GRUB tìm Windows Boot Manager, mở:

```bash
nano /etc/default/grub
```

Thêm hoặc sửa thành `GRUB_DISABLE_OS_PROBER=false` (không có `#` ở đầu); lưu `Ctrl+O`, Enter và thoát `Ctrl+X`. Kiểm tra và tạo menu:

```bash
os-prober
grub-mkconfig -o /boot/grub/grub.cfg
```

Kiểm tra output có phát hiện Windows Boot Manager; nếu không, **không xóa/sửa Windows hay format ESP**. GRUB vẫn có thể khởi động Arch; Windows có thể chọn từ boot menu UEFI. Xem [ArchWiki GRUB](https://wiki.archlinux.org/title/GRUB) để xử lý nhận diện. Sau khi cài xong kiểm tra cả hai hệ điều hành; một số firmware đổi thứ tự boot hoặc không hiển thị mục GRUB như dự kiến.

Thoát chroot, tháo filesystem và khởi động lại:

```bash
exit
umount -R /mnt
reboot
```

Tháo USB khi máy khởi động lại. Chọn Arch trong GRUB, đăng nhập kiểm tra; khởi động lại và chọn Windows Boot Manager trong GRUB hoặc boot menu UEFI để xác nhận Windows còn hoạt động. Nếu BitLocker yêu cầu recovery key, dùng khóa đã lưu. Khi đã kiểm tra ổn định, nếu từng tạm ngưng BitLocker thì bật lại bảo vệ trong Windows theo tài liệu Microsoft. Khi chuyển hệ điều hành, tắt hoàn toàn thay vì hibernate.

## 8. Đăng nhập Arch mới, kết nối mạng

**Nơi thực hiện: màn hình chữ của Arch đã cài, không phải USB.** Đăng nhập bằng tên người dùng và mật khẩu vừa tạo, ví dụ `an`. Ethernet thường tự kết nối. Với Wi-Fi, xem danh sách rồi kết nối, thay tên mạng:

```bash
nmcli device wifi list
nmcli device wifi connect "Ten WiFi" --ask
```

Kiểm tra mạng và quyền quản trị:

```bash
ping -c 3 archlinux.org
sudo -v
```

Nếu `sudo -v` thất bại, kiểm tra cấu hình wheel bằng tài khoản root trước khi tiếp tục. Cập nhật toàn hệ thống và cài công cụ cơ bản:

```bash
sudo pacman -Syu
sudo pacman -S --needed git nano
sudo reboot
```

Đăng nhập lại bằng tài khoản thường. Arch là rolling release: đọc [Arch Linux News](https://archlinux.org/news/) trước những lần cập nhật lớn.

## 9. Cài nền JaKooLit/Hyprland

**Nơi thực hiện: Arch mới, đăng nhập tài khoản thường; không chạy script bằng root hoặc `sudo ./install.sh`.** JaKooLit là tác giả bộ cài Hyprland. Bộ cài Arch-Hyprland cài ứng dụng và, nếu chọn, tải dotfiles Hyprland từ dự án khác. Repo hiện tại là lớp cấu hình cá nhân đặt lên nền đó, không phải trình cài Arch hay Hyprland hoàn chỉnh.

Repo hiện đang trỏ đến [JaKooLit/Arch-Hyprland](https://github.com/JaKooLit/Arch-Hyprland). Upstream thông báo dự án chuyển bảo trì sang [LinuxBeginnings](https://github.com/LinuxBeginnings/Arch-Hyprland); các phiên bản/config mới có thể khác repo này. Vì chưa kiểm thử kết hợp mới, lộ trình sau dùng URL repo hiện tại và **không đảm bảo tương thích với bản Arch/Hyprland mới**. Nếu upstream báo không còn hỗ trợ hoặc script thất bại, dừng, đọc thông báo và kiểm tra tài liệu upstream; không tự đổi sang fork rồi giả định tương thích.

Clone repo cá nhân và chạy setup (cần Git, mạng, sudo; `git` đã được cài ở mục 8):

```bash
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles
./setup.sh
```

`setup.sh` có một luồng cài toàn bộ, không có menu chọn nhóm package. Nếu chưa có `~/.config/hypr/hyprland.conf`, script tải và chạy installer JaKooLit trước. Script in đường dẫn installer và log dưới `~/.cache/jakoolit-install.*/Arch-Hyprland`.

Nếu đã có file, script **bỏ qua installer JaKooLit và tiếp tục cài ngay**; chỉ nên chạy khi đã xác nhận đó là cấu hình JaKooLit đang hoạt động. Khi setup đã cài package và áp dụng cấu hình thành công, không cần chạy lại ở mục 10; chuyển đến phần nhóm tùy chọn hoặc mục 11.

Đọc các câu hỏi của installer; dùng phím mũi tên, Space để chọn/bỏ chọn và Enter để xác nhận. Chọn **pre-configured KooL Hyprland dotfiles** (`dots`) vì repo này cần cấu hình nền. Installer JaKooLit cũng có tùy chọn cài và cấu hình trình đăng nhập **SDDM**: nếu Arch mới chưa có trình đăng nhập đồ họa, chọn `sddm` ngay trong menu JaKooLit; không cần cài riêng ở bước khác. Tùy chọn `sddm_theme` là theme bổ sung, có thể chọn nếu muốn. Nếu đã dùng trình đăng nhập khác, xem thông báo của installer trước khi thay đổi; lựa chọn SDDM có thể không được hiện.

Bạn cũng có thể chọn **Zsh with Oh-My-Zsh** và chọn **yay** nếu được hỏi AUR helper. Tên các lựa chọn có thể thay đổi. Với máy hiện tại (RTX 2060 Mobile, kernel `linux`), chọn `nvidia`. Trước khi chạy installer, setup đổi gói `nvidia-dkms` trong bản installer vừa tải thành `nvidia-open`, khớp `pkglist.txt`, và giữ các bước cấu hình NVIDIA của upstream. Nếu cấu trúc danh sách driver upstream thay đổi, setup dừng để kiểm tra. Đây là lựa chọn dành cho máy này; không áp dụng nguyên trạng cho GPU/kernel khác. Installer dùng `sudo`, có thể tải nhiều package và thay đổi audio/config. Nếu lỗi, ghi lại lỗi và dừng.

Nếu setup vừa chạy installer JaKooLit và installer tạo được `hyprland.conf`, setup **dừng sau khi cài nền**, chưa cài package cá nhân hay áp dụng cấu hình của repo. Vì vậy cần đăng nhập và kiểm tra Hyprland, rồi tiếp tục mục 10. Nếu báo không tạo được file hoặc installer lỗi, đọc thông báo và log trong thư mục được in ra; kiểm tra đã chọn `dots`, sau đó xử lý lỗi và chạy lại setup. Khởi động lại theo hướng dẫn installer, chọn phiên Hyprland tại màn hình đăng nhập và đăng nhập. Xác nhận desktop, bàn phím, mạng và terminal hoạt động. Nếu không vào được, xem mục 12.

## 10. Cài công cụ và áp dụng repo này

**Chỉ làm bước chạy setup dưới đây nếu setup đã dừng sau khi cài nền JaKooLit ở mục 9.** Nếu nó đã hoàn tất cài package và áp dụng cấu hình ở mục 9, bỏ qua lần chạy này. Sau khi nền JaKooLit đã hoạt động, mở terminal trong Arch bằng tài khoản thường và dùng lại repo đã clone:

```bash
cd ~/dotfiles
```

Repo có cấu hình màn hình laptop `eDP-1`. Xem tên màn hình bằng `hyprctl monitors` và đọc `hypr/.config/hypr/UserConfigs/LaptopDisplay.conf`; chỉnh file trong repo nếu phần cứng khác. Sao lưu cấu hình JaKooLit và file cá nhân quan trọng ra nơi độc lập.

```bash
./setup.sh
```

Trước khi chạy, đọc `pkglist.txt`: danh sách có `nvidia-open`, `intel-ucode`, kernel và bootloader của máy cũ. Xóa hoặc comment các gói không phù hợp với phần cứng; nếu JaKooLit đã cài driver NVIDIA khác như `nvidia-dkms`, kiểm tra tương thích và giải quyết xung đột driver trước khi cài. Không xác nhận thay thế driver khi chưa hiểu tác động.

Script cập nhật hệ thống, cài toàn bộ package chính thức trong `pkglist.txt` bằng Pacman và kiểm tra rồi cài các dòng `aur/` bằng yay. Script cũng cài các ứng dụng Flatpak trong `packages/flatpak-apps.txt` từ Flathub cho người dùng hiện tại. Sau đó script chuẩn bị Oh My Zsh, hai plugin và theme nếu thiếu, rồi áp dụng cấu hình `zsh`, `nvim`, `hypr`, `fcitx5` qua Stow. Cần mạng và quyền `sudo`; nếu cài package hoặc tải thành phần shell thất bại, script dừng trước khi Stow. Nếu chưa có yay và danh sách có AUR, script tải PKGBUILD yay và dừng để bạn kiểm tra trước khi build. Các gói AUR do cộng đồng duy trì: đọc PKGBUILD và phản hồi các câu hỏi của yay; tên gói có thể thay đổi hoặc build thất bại, khi đó sửa danh sách/lỗi rồi chạy lại.

Script chuyển file trùng và cả `UserConfigs` cũ vào `~/.dotfiles-backup.*`; có thể dừng giữa chừng nếu còn xung đột. Ghi lại đường dẫn backup. Trước khi cập nhật, script dừng nếu `/boot` là EFI FAT và còn dưới 32 MiB; xem mục 0.2 và 4.1 để chuẩn bị khi cài lại. Không dùng `stow --adopt` hay `git checkout` để xử lý xung đột khi chưa hiểu hậu quả.

### Các nhóm tùy chọn

**Nơi thực hiện: terminal của Arch mới, sau khi setup đã cài package.** Tài khoản thông thường đã có thể dùng `sudo` nhờ nhóm `wheel`; chỉ thêm nhóm khác khi cần. Kiểm tra các nhóm hiện tại:

```bash
id
getent group input
getent group docker
```

Nếu một tính năng JaKooLit yêu cầu truy cập thiết bị đầu vào, có thể thêm người dùng hiện tại vào nhóm `input` bằng `sudo usermod -aG input "$USER"`. Nhóm này có thể đọc sự kiện bàn phím và chuột; chỉ thêm khi cần. JaKooLit có thể đã thêm nhóm nếu bạn chọn tùy chọn tương ứng trong installer.

Nếu dùng Docker daemon thông thường và muốn chạy Docker không cần `sudo`, sau khi cài Docker, chạy:

```bash
sudo usermod -aG docker "$USER"
sudo systemctl enable --now docker.service
```

Nhóm `docker` cấp quyền tương đương root cho thành viên; chỉ thêm tài khoản tin cậy. Nếu không dùng Docker, bỏ qua các lệnh này. Sau khi đổi nhóm, đăng xuất toàn bộ phiên và đăng nhập lại, rồi chạy `id` để kiểm tra. Xem [Docker Linux post-installation](https://docs.docker.com/engine/install/linux-postinstall/).

Đăng xuất và đăng nhập lại. Nếu muốn đặt Zsh thành shell đăng nhập:

```bash
chsh -s /bin/zsh
```

Đăng xuất/đăng nhập để áp dụng. Khi gặp lỗi shell, đăng nhập TTY và chạy `chsh -s /bin/bash` để quay về Bash.

## 11. Kiểm tra kết quả

**Nơi thực hiện: terminal của Arch mới.**

```bash
findmnt /
findmnt /efi
systemctl is-active NetworkManager
hyprctl monitors
fcitx5-configtool
nvim
```

`/efi` phải nằm trên phân vùng FAT32 EFI đã xác minh; `/boot` nằm trong phân vùng ext4 của Arch. NetworkManager nên trả về `active`. Trong giao diện Fcitx5, kiểm tra có keyboard và Bamboo, thử nhập tiếng Việt vào ứng dụng; phím chuyển bộ gõ tùy cấu hình Fcitx5. Trong Neovim, chờ LazyVim cài plugin lần đầu, thoát bằng `:qa` rồi Enter. Kiểm tra âm thanh, mạng, màn hình và đăng nhập lại một lần trước khi khôi phục dữ liệu.

Để dùng màn hình ngoài, chạy `hyprctl monitors` trong terminal Hyprland và xác định tên màn hình. Ví dụ dưới dùng `HDMI-A-3` cho màn hình ngoài và `eDP-1` cho laptop; thay bằng tên thực tế:

```bash
# Chiếu giống màn hình laptop:
hyprctl keyword monitor "HDMI-A-3,preferred,auto,1,mirror,eDP-1"

# Hoặc chỉ dùng màn hình ngoài: bật màn hình ngoài và kiểm tra đã có hình trước.
hyprctl keyword monitor "HDMI-A-3,preferred,auto,1"
hyprctl keyword monitor "eDP-1,disable"
```

Trước khi rút HDMI, bật lại laptop bằng `hyprctl keyword monitor "eDP-1,preferred,auto,1"` và xác nhận đã có hình. Các lệnh thay đổi tạm thời; xem [hướng dẫn màn hình ngoài](external-displays.md) để chọn độ phân giải, khôi phục cấu hình và xử lý lỗi.

`packages/explicit-repo.txt`, `explicit-foreign.txt` và `all-foreign.txt` là snapshot để đối chiếu. Riêng `packages/flatpak-apps.txt` được setup dùng để cài ứng dụng Flatpak; `pkglist.txt` quyết định gói Pacman/AUR. Xem [reinstall.md](reinstall.md) và đối chiếu nhu cầu, driver, nguồn package trước khi cài thêm. Giữ bản sao dữ liệu cũ đến khi xác nhận khôi phục đầy đủ.

## 12. Xử lý lỗi thường gặp

- **Không thấy USB trong boot menu / Secure Boot chặn:** kiểm tra lại USB, firmware UEFI, cấu hình Secure Boot và tài liệu máy. Thử tạo lại USB sau khi xác minh ISO.
- **Không có mạng trong USB:** kiểm tra `device list` trong `iwctl`, chọn đúng thiết bị và SSID; thử Ethernet. Trong hệ thống mới dùng `nmcli`, không mặc định cho rằng kết nối trong USB đã được lưu.
- **Không thấy Arch sau reboot:** tháo USB, kiểm tra thứ tự boot UEFI. Có thể boot lại USB để chẩn đoán; xác nhận đúng phân vùng trước khi mount. Kiểm tra thứ tự boot UEFI và mục GRUB/Windows Boot Manager; xem [ArchWiki GRUB](https://wiki.archlinux.org/title/GRUB) và thông báo thực tế, không format lại ESP.
- **Không vào Hyprland / màn hình đen:** dùng `Ctrl+Alt+F2` hoặc F3 để vào TTY, đăng nhập, đọc `journalctl -b -p err` và thông báo của installer. Kiểm tra GPU/driver với tài liệu upstream; không áp driver NVIDIA cho mọi GPU. Nếu nền JaKooLit chưa hoạt động thì chưa chạy overlay.
- **Stow báo conflict:** đọc đường dẫn lỗi và backup do script in ra. Một số file có thể đã được chuyển trước khi script dừng; kiểm tra cả home và backup trước khi khôi phục hoặc chạy lại. Xem [troubleshooting](troubleshooting.md).
- **Bộ gõ hoặc Zsh lỗi:** xác nhận các package, plugin và theme ở mục 10; profile Fcitx5 chỉ cấu hình, không cài engine. `command -v fcitx5 nvim zsh fzf` giúp kiểm tra lệnh.

## Nguồn và giới hạn kiểm chứng

- [Arch installation guide](https://wiki.archlinux.org/title/Installation_guide), [EFI system partition](https://wiki.archlinux.org/title/EFI_system_partition), [dual boot](https://wiki.archlinux.org/title/Dual_boot_with_Windows), [GRUB](https://wiki.archlinux.org/title/GRUB), [iwd](https://wiki.archlinux.org/title/Iwd), [microcode](https://wiki.archlinux.org/title/Microcode).
- [Microsoft Disk Management](https://learn.microsoft.com/windows-server/storage/disk-management/shrink-a-basic-volume), [Microsoft BitLocker](https://learn.microsoft.com/windows/security/operating-system-security/data-protection/bitlocker/operations-guide), [Arch Downloads và checksum/chữ ký](https://archlinux.org/download/), [Microsoft Get-FileHash](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash), [Rufus](https://rufus.ie/).
- [JaKooLit Arch-Hyprland](https://github.com/JaKooLit/Arch-Hyprland), [LinuxBeginnings Arch-Hyprland](https://github.com/LinuxBeginnings/Arch-Hyprland), [Arch package fcitx5-bamboo](https://archlinux.org/packages/extra/x86_64/fcitx5-bamboo/).

Đây là hướng dẫn được đối chiếu tài liệu, **chưa được chạy thử toàn bộ trên máy thật/VM**. Trình cài upstream, tên package, cấu trúc dotfiles, trình đơn firmware và mức hỗ trợ GPU thay đổi theo thời gian; xác nhận hướng dẫn chính thức trước khi thực hiện, đặc biệt nếu máy khác phạm vi ở mục 0.
