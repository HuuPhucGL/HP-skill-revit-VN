---
name: hp-revit-xuat-ho-so-pdf
description: Ra hồ sơ PDF từ mô hình Revit nhà phố / nhà ở của anh Phúc — rà đủ bản vẽ, đặt sheet A3 KT-01…, view tỷ lệ 1/50, kiểm tra khung tên và chữ Unicode, xuất PDF gộp một file hoặc từng sheet vào thư mục 03-PDF xuat ban, đặt tên theo YYMMDD, kiểm lại file đã ra. Dùng khi anh Phúc nói "xuất PDF", "ra hồ sơ", "in bản vẽ", "xuất hồ sơ gửi chủ nhà", "gộp PDF", "bộ bản vẽ PDF", kể cả khi không nhắc tên skill.
---

# Ra hồ sơ PDF từ Revit

Đọc `hp-revit-quy-uoc` trước. Skill này là bước **cuối** sau `hp-revit-dung-mo-hinh`,
`hp-revit-bo-sung-chi-tiet`, `hp-revit-trien-khai-ban-ve`, `hp-revit-kiem-tra-mo-hinh`.

## Công cụ

Xuất PDF cần MCP **`hp-revit`** của bộ [HP-MCP-Revit-vn](https://github.com/HuuPhucGL/HP-MCP-Revit-vn)
(công cụ `revit_list_sheets`, `revit_create_sheet`, `revit_place_view`, `revit_set_view_scale`,
`revit_export_pdf`). Bộ `mcp-servers-for-revit` (MCP `revit`) **không** có lệnh xuất PDF.

- `revit_export_pdf` chạy từ **Revit 2022 trở lên**. Revit 2017–2021: không xuất qua API được; hướng dẫn anh
  tự In → chọn máy in PDF với danh sách sheet đã lập.
- Chỉ **Revit 2024** đã được kiểm chứng; các bản khác ghi "cần kiểm tra".
- Chưa có MCP `hp-revit`: hướng dẫn anh cài (README của HP-MCP-Revit-vn), hoặc xuất tay: File → Export → PDF.

## Quy chuẩn hồ sơ (anh Phúc)

- Khổ **A3**, view **1/50**, số hiệu **KT-01, KT-02…** theo thứ tự anh duyệt. Font Unicode (Arial / Times New Roman).
- Thư mục: `03-PDF xuat ban` của dự án. Tên file: `YYMMDD - Tên dự án - Địa chỉ` (thêm ` - KT` nếu chỉ phần kiến trúc).
- **Không ghi đè** PDF cũ: bản mới đổi ngày ở đầu tên (hoặc thêm hậu tố `v2`).
- Khung tên: dùng khung tên có sẵn trong file (đánh dấu TẠM theo `hp-revit-trien-khai-ban-ve`) cho tới khi anh có
  family khung tên chính thức. Không tự vẽ khung tên.
- Dự án mới: **hỏi** anh xuất gộp một file hay từng sheet.
- Màu / độ dày nét ra PDF phụ thuộc cấu hình Revit của anh; file CTB riêng của anh dùng khi in từ AutoCAD, **không áp dụng tự động** cho PDF xuất từ Revit. Báo anh điều này, đừng hứa "in đúng CTB".

## Quy trình

1. **Rà hồ sơ.** `revit_list_sheets` và `revit_list_views`. Đối chiếu danh mục bản vẽ anh đã duyệt
   (`hp-revit-trien-khai-ban-ve` bước 1). Lập bảng: sheet có / thiếu, view chưa lên sheet, tỷ lệ view khác 1/50.
2. **Bổ sung sheet thiếu.** `revit_create_sheet(number, name, titleblock)`, `revit_place_view(sheet, view)`,
   `revit_set_view_scale(view, 50)`. Hỏi anh trước khi đổi tỷ lệ view đã có. Viewport tràn khung A3 thì báo
   anh, không tự đổi tỷ lệ.
3. **Kiểm tra mô hình.** Chạy `hp-revit-kiem-tra-mo-hinh`; còn cảnh báo nghiêm trọng thì báo anh trước khi xuất.
4. **Chốt thông số xuất** và đọc lại cho anh xác nhận:
   thư mục đích, tên file, danh sách sheet (hoặc tất cả), gộp / tách.
5. **Xuất.** `revit_export_pdf(folder, file_name, sheet_numbers, combine)`. Công cụ từ chối nếu file đã tồn tại.
6. **Kiểm chứng file đã ra** (không tin lời báo "thành công"): kiểm tra file tồn tại, dung lượng > 0,
   mở bằng skill `pdf` đếm số trang = số sheet, xem thử một vài trang (khổ A3, chữ có dấu hiển thị đúng,
   không tràn khung).
7. **Báo cáo.** Đường dẫn file, số trang, danh sách sheet, phần còn thiếu / TẠM, những mục "cần kiểm tra".
   Nhắc anh in thử một tờ A3 để soát nét trước khi gửi hồ sơ.

## Ngoài phạm vi

Xuất DWG, ký số, đóng dấu: làm tay. Hồ sơ đi thẩm duyệt phải đối chiếu quy định hiện hành của cơ quan duyệt
(cần kiểm tra, không ghi số hiệu tiêu chuẩn từ trí nhớ).
