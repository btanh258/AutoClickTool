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

Muốn file exe duy nhất, chạy `Build_AutoClickTool.bat` (dùng PyInstaller, file ra ở `dist\AutoClickTool.exe`, kèm zip `AutoClickTool-1.1.1.zip`).

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
