# AutoClickTool

Ghi lại thao tác chuột + bàn phím rồi chạy lại tự động — dùng để lặp các thao tác lặp đi lặp lại trên Windows.

## Làm được gì

- **Ghi:** click chuột, kéo-thả, di chuyển chuột, cuộn chuột, gõ phím, phím tắt (Ctrl+C…)
- **Chạy lại:** đúng thời gian đã ghi, số vòng lặp tùy chọn (0 = lặp vô hạn), tốc độ 0.5x / 1x / 2x, nghỉ giữa các vòng
- **Dừng bất cứ lúc nào:** bấm **F11** khi đang chạy, **F12** khi đang ghi, hoặc menu khay hệ thống → Dừng ghi / Dừng chạy
- **3 slot kịch bản có sẵn:** đặt tên + chọn file `.json`, tải lại bằng một nút
- **Lưu / tải kịch bản:** file `.json`, tương thích với kịch bản của bản cũ (chỉ click + phím)
- **Thu xuống khay hệ thống:** đóng / minimize cửa sổ là xuống khay, bấm đúp icon khay để hiện lại
- **Tự cập nhật:** kiểm tra GitHub Releases sau 10 giây rồi mỗi ngày, có nút *Kiểm tra cập nhật*; bản mới chỉ tải về khi bạn bấm đồng ý

## Cách dùng

1. Bấm **Ghi**, thao tác như bình thường, bấm **F12** để dừng ghi.
2. Bấm **Lưu kịch bản mới** để lưu file `.json`, hoặc bấm **▶ Chạy kịch bản** để chạy ngay.
3. Đang chạy bấm **F11** để dừng.

Mẹo: tắt *Ghi di chuyển chuột* nếu chỉ cần click, file kịch bản sẽ gọn hơn (di chuyển chuột được nén: chỉ ghi khi di chuyển ≥ 8px hoặc đã hơn 50ms).

## Cài đặt

Chạy `Install_AutoClickTool.bat` (cài Python 3.11 nếu chưa có + các thư viện `customtkinter pynput pystray pillow`), rồi chạy:

```
python AutoClickTool.pyw
```

Muốn file exe duy nhất, chạy `Build_AutoClickTool.bat` (dùng PyInstaller, file ra ở `dist\AutoClickTool.exe`, kèm zip `AutoClickTool-1.1.5.zip`).

### Build tự động bằng GitHub Actions

PyInstaller chỉ build được cho đúng hệ điều hành nó đang chạy, nên không build exe Windows trên máy Linux được. Repo này có workflow `.github/workflows/build.yml` chạy trên máy Windows của GitHub:

- **Tự động:** mỗi lần push tag `vX.Y.Z` (vd `v1.1.1`), workflow build exe rồi gắn `AutoClickTool.exe` (+ zip) vào release của tag đó.
- **Chạy tay:** vào tab Actions → *Build exe* → *Run workflow*, nhập tag của release cần gắn exe (vd `v1.1.1`), bấm Run.

Nhờ vậy tính năng tự cập nhật trong app luôn tìm thấy file exe trên release.

## Cấu hình

File `AutoClickTool_config.json` nằm cạnh file exe / file `.pyw` (không theo thư mục hiện tại nữa, nên chạy từ shortcut vẫn giữ nguyên slot). Lưu: tên + đường dẫn 3 slot, số vòng, thời gian nghỉ, tốc độ, tùy chọn ghi chuột/cuộn, tự cập nhật. File này chứa đường dẫn trên máy bạn nên không đưa lên GitHub.

## Định dạng kịch bản (.json)

Mỗi hành động là `[tên, dữ liệu, thời gian_giây_tính_từ_lúc_bắt_đầu_ghi]`:

| Hành động | Dữ liệu |
|---|---|
| `key_press` / `key_release` | `"a"`, `"Key.enter"`, `"Key.ctrl_l"` |
| `mouse_down` / `mouse_up` | `[x, y, "Button.left"]` |
| `mouse_move` | `[x, y]` |
| `mouse_scroll` | `[x, y, dx, dy]` |

## Lịch sử

### 1.1.5 (2026-11-23)
- Di chuyển chuột bằng `SendInput` TUYỆT ĐỐI (`MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE`, tọa độ chuẩn hóa 0-65535 theo màn hình ảo) thay cho tương đối. Di chuyển tương đối bị Windows co giãn theo mức tốc độ con trỏ / tăng tốc (Enhance pointer precision) nên điểm click lệch sang trái rất lớn; tuyệt đối thì chính xác tuyệt đối, không phụ thuộc cài đặt chuột. Chỉ khi `SendInput` tuyệt đối lỗi mới rơi về tương đối, rồi về `SetCursorPos`.
- Cửa sổ cao 800 -> 850px: thêm 1 hàng cài đặt ở 1.1.3 ("Chờ trước khi chạy") làm nội dung tràn khỏi cửa sổ cố định 800px, nút "Kiểm tra cập nhật" ở dưới cùng bị đẩy ra ngoài khung hình.

### 1.1.4 (2026-11-23)
- Sửa thật sự việc Paint không vẽ được nét cong. Đọc source pynput 1.8.2 mới biết: trên Windows, `Controller.move(dx, dy)` chỉ là `self.position = vị trí hiện tại + (dx, dy)`, tức là `SetCursorPos` — chỉ đổi vị trí con trỏ hiển thị, không đưa sự kiện kéo vào hàng đợi nhập. Vì vậy 1.1.2 tưởng đã sửa bằng `mouse.move` nhưng thực ra không đổi gì trên Windows. PowerPoint vẫn quét chọn được vì nó chỉ cần điểm đầu/cuối (hình chữ nhật chọn theo vị trí con trỏ), còn Paint cần từng điểm giữa như sự kiện nhập thật để vẽ nét. Nay lúc chạy gửi di chuyển chuột bằng `SendInput` thật qua `ctypes` (`MOUSEEVENTF_MOVE` tương đối), như cách pynput gửi nhấn/nhả chuột; chỉ khi không phải Windows hoặc `SendInput` lỗi mới rơi về `SetCursorPos`.

### 1.1.3 (2026-11-23)
- Thêm thời gian chờ trước khi chạy (mặc định 3 giây, chỉnh được ở mục "Chờ trước khi chạy"). Nguyên nhân: bấm Chạy thì app ẩn đi ngay và chạy luôn, nhưng lúc đó chưa có cửa sổ nào được chọn (Paint chưa phải cửa sổ trước) nên thao tác rơi vào hư không — chuột thì vẫn đi theo đường cong nhưng không vẽ được gì. Nay sau khi ẩn app sẽ chờ 3 giây (ngắt được bằng F11) để bạn bấm vào cửa sổ cần thao tác (vd Paint) rồi macro mới chạy.

### 1.1.2 (2026-11-23)
- Sửa thật sự lỗi vẽ nét cong thành nét thẳng trong Paint. File `test.json` của Bạch chứng minh lúc ghi đã đúng: 1 lần kéo dài 2,02 giây, 112 điểm di chuyển, đường đi 1340px nhưng điểm đầu-cuối chỉ cách nhau 30px. Lỗi nằm ở lúc chạy: `_play_one` dùng `mouse_ctrl.position` để di chuyển chuột — trên Windows pynput cài này bằng `SetCursorPos`, chỉ đổi vị trí con trỏ hiển thị chứ không đưa sự kiện kéo vào hàng đợi của ứng dụng, nên Paint chỉ thấy nhấn xuống ở điểm đầu và nhả ra ở điểm cuối rồi nối thẳng 2 điểm. Nay lúc chạy ghi nhớ vị trí cuối, di chuyển bằng `mouse_ctrl.move(dx, dy)` tương đối (pynput cài bằng `SendInput`) nên mỗi bước đều là sự kiện nhập thật, Paint vẽ được nét cong. Chỉ lần định vị đầu tiên của mỗi vòng mới dùng `position` để dịch chuyển nhanh.

### 1.1.1 (2026-11-23)
- Sửa lỗi vẽ nét cong thành nét thẳng trong Paint: `on_move`/`on_scroll` gọi `BooleanVar.get()` của Tkinter ngay trong thread của pynput — Tkinter chỉ cho đọc biến từ luồng UI chính nên pynput ngừng gọi `on_move`, chỉ còn lại `mouse_down`/`mouse_up` (2 đầu mút) nên Paint nối thành đường thẳng. Nay đọc tùy chọn ghi ở luồng UI trước khi ghi, lưu vào biến bool thường, listener chỉ đọc biến thường đó; bọc mọi callback listener trong `try/except` để một lỗi không giết listener. Dừng ghi giờ hiện số lượng từng loại: di chuyển / click / cuộn / phím, để kiểm tra ngay là đã ghi được điểm di chuyển chưa.

### 1.1.0 (2026-11-23)
- Ghi di chuyển chuột + cuộn chuột (có bật/tắt, nén move)
- Dừng chạy (F11) ngắt được ngay, kể cả khi đang nghỉ giữa các sự kiện
- Sửa lỗi kẹt app: delay âm / số vòng không hợp lệ / file kịch bản lỗi không còn làm cửa sổ biến mất
- Config lưu cạnh file exe, lưu cả số vòng / delay / tốc độ / tùy chọn ghi / tự cập nhật
- Thêm mô tả hướng dẫn trong app, hiện tray icon trong lúc ghi/chạy
- Tự cập nhật qua GitHub Releases (kiểm tra sau 10 giây rồi mỗi ngày, nút Kiểm tra cập nhật)
- Số vòng 0 = lặp vô hạn, tốc độ phát 0.5x / 1x / 2x, khai DPI-aware
- Sửa: icon taskbar không còn bị mất do GC, phím Ctrl+chữ lấy đúng chữ cái từ phím vật lý
