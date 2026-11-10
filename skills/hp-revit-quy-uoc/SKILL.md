---
name: hp-revit-quy-uoc
description: Quy ước nền và cách kết nối Claude với Revit 2024 qua MCP (mcp-servers-for-revit) cho anh Phúc — kiểm tra kết nối, khảo sát dự án, đơn vị mm, tên Level/tường, quyền hạn (hỏi trước khi xóa hoặc chạy C#), sao lưu và nơi lưu file .rvt. Dùng skill này TRƯỚC mọi thao tác Revit, khi anh Phúc nói "mở Revit", "kết nối Revit", "Claude không thấy Revit", "khảo sát file Revit", hoặc khi một skill hp-revit-* khác yêu cầu đọc quy ước.
---

# Quy ước nền khi làm việc với Revit

Skill này là luật chung cho cả bộ HP-skill-revit-VN. Các skill khác (dựng mô hình, triển khai bản vẽ,
bốc khối lượng, kiểm tra mô hình) đều tuân theo các mục dưới đây.

## 1. Kết nối Claude ↔ Revit

Chuỗi kết nối: Claude → MCP server `revit` (Node, chạy trên máy) → cổng 8080 → plugin trong Revit 2024.

Trước khi thao tác, kiểm tra kết nối bằng `get_current_view_info` (chỉ đọc, không bật hộp thoại).
Không dùng `say_hello` để kiểm tra vì nó bật hộp thoại trong Revit, anh phải bấm tắt.

Nếu báo lỗi `connect to revit client failed`, hướng dẫn anh lần lượt:
1. Mở Revit 2024 và mở một file dự án (không phải file family).
2. Tab **Add-Ins** → panel **Revit MCP Plugin** → bấm **Revit MCP Switch** để bật dịch vụ.
3. Lần đầu: bấm **Settings**, tích chọn các lệnh cần dùng, bấm **Save**.
4. Nếu vẫn lỗi: có thể plugin khác đang chiếm cổng 8080 (ví dụ plugin "Revit AI MCP Bridge" cũ).
   Báo anh, không tự tắt plugin khác.
5. Nếu Claude không có công cụ `revit` nào: khởi động lại Claude (cấu hình MCP chỉ nạp khi mở phiên mới).

## 2. Khảo sát trước khi làm

Mỗi phiên làm việc với một file, chạy khảo sát một lần rồi mới dựng hay sửa:
- `get_current_view_info`: view đang mở.
- `analyze_model_statistics`: số phần tử, level, view, sheet.
- `get_available_family_types` với `["OST_Walls","OST_Floors","OST_Doors","OST_Windows","OST_TitleBlocks"]`:
  loại có sẵn.
- Đoạn C# "Khảo sát dự án" trong `references/csharp-co-ban.md`: đường dẫn file, đơn vị, danh sách Level kèm
  cao độ. Đây là mã C# nên phải hỏi anh trước khi chạy (mục 4).

Tóm tắt kết quả cho anh ngắn gọn: file nào, bao nhiêu tầng, thiếu loại tường/cửa/khung tên nào.

## 3. Đơn vị và hệ tọa độ

- Mọi công cụ MCP nhận **mm**. Nhận số từ anh bằng m thì đổi sang mm và nhắc lại để anh kiểm.
- Trong mã C#, Revit lưu nội bộ bằng **feet**. Luôn đổi bằng
  `UnitUtils.ConvertToInternalUnits(giaTri, UnitTypeId.Millimeters)` và đổi ngược bằng
  `UnitUtils.ConvertFromInternalUnits(...)`. Không tự nhân hay chia 304.8 rải rác trong code.
- Gốc tọa độ (0,0) đặt tại giao trục đầu tiên (A-1), trục X theo chiều ngang nhà, trục Y theo chiều sâu.
  Với dự án mới, xác nhận với anh trước khi dựng.
- Cao độ ±0.000 là mặt sàn hoàn thiện TẦNG 1.

## 4. Quyền hạn (anh Phúc đã chọn)

| Thao tác | Cách làm |
|---|---|
| Đọc, truy vấn, thống kê | Làm luôn |
| Tạo / sửa phần tử bằng công cụ MCP (tường, sàn, cửa, level, trục, phòng, dim, tag, tô màu) | Làm luôn, xong báo lại đã tạo gì (kèm Id) |
| **Xóa phần tử** (`delete_element`, `operate_element` với action `Delete`) | **Dừng hỏi.** Liệt kê Id, loại, tầng và lý do, chờ anh đồng ý |
| **Chạy mã C#** (`send_code_to_revit`) | **Dừng hỏi.** Tóm tắt đoạn mã làm gì (đọc hay sửa, sửa cái gì). Một lần hỏi có thể gộp nhiều đoạn mã của cùng một việc nếu đã liệt kê rõ |

- Mỗi lệnh MCP là một Transaction riêng: anh bấm `Ctrl+Z` trong Revit để hoàn tác từng bước.
- Dựng nhiều phần tử thì gửi theo lô (mảng `data`) để gọn số bước Undo.

## 5. Thông tin bắt buộc phải hỏi, không tự đoán

Chiều dày tường, cấu tạo lớp trát, chiều cao tầng, cao độ, chiều dày sàn, tiết diện dầm/cột, kích thước cửa,
vật liệu, định mức áp dụng. Thiếu thì hỏi. Có số đề xuất thì ghi rõ "đề xuất", tách khỏi số liệu gốc.

## 6. Quy ước đặt tên

- **Level:** `TẦNG 1`, `TẦNG 2`, …, `TẦNG MÁI` (có dấu, chữ in hoa).
- **Loại tường:** `Tường gạch 110`, `Tường gạch 220` (số = chiều dày lõi gạch, mm).
  Tường có thêm lớp trát trong type thì hỏi anh cách đặt tên, ví dụ `Tường gạch 110 + trát 15x2`.
- **Sheet:** số hiệu `KT-01`, `KT-02`…, khổ A3, tỷ lệ view 1/50.
- **View:** đề xuất `MB TẦNG 1`, `MẶT ĐỨNG TRỤC 1-5`, `MẶT CẮT A-A`. Lần đầu dự án hỏi anh duyệt.
- Dữ liệu đặt tên khác (phòng, cửa) theo bản vẽ CAD của anh; chưa có thì hỏi.

## 7. Lưu file và sao lưu

Thư mục dự án `YYMMDD - Tên dự án - Địa chỉ`:
- `02-Mo hinh Revit`: file `.rvt`, tên `YYMMDD - Tên dự án - Địa chỉ.rvt`.
- `04-Boc tach du toan`: file Excel khối lượng.
- `_backup/YYMMDD/`: bản gốc trước khi sửa.

Quy tắc:
- **Trước khi sửa một file .rvt có sẵn**: lấy đường dẫn file (đoạn mã khảo sát), chép bản gốc vào
  `_backup/YYMMDD/` của dự án bằng lệnh chép file trên máy. Chưa có thư mục thì tạo.
- Không ghi đè, không xóa file gốc. Lưu bản mới bằng cách đổi ngày ở đầu tên file.
- MCP không tự lưu file được (mã C# chạy trong Transaction nên không gọi được `SaveAs`). Khi xong việc, nhắc
  anh bấm Save hoặc Save As vào `02-Mo hinh Revit`.
- Dự án mới: đề xuất template `C:\ProgramData\Autodesk\RVT 2024\Templates\English\DefaultMetric.rte`
  (đơn vị mm), vì anh chưa có template riêng.
- Không xóa file hay thư mục khi chưa hỏi anh.

## 8. Viết mã C# cho `send_code_to_revit`

Xem `references/csharp-co-ban.md`. Tóm tắt:
- Đoạn mã được chèn vào thân hàm `public static object Execute(Document document, object[] parameters)`.
  Biến tài liệu tên là `document` (không phải `doc`). Đã có sẵn `using System; System.Linq;
  System.Collections.Generic; Autodesk.Revit.DB; Autodesk.Revit.UI;`.
- Bắt buộc `return` một đối tượng (kiểu ẩn danh hoặc List) để Claude đọc kết quả dạng JSON.
- Đoạn mã đã nằm sẵn trong một Transaction. **Không** tự mở `new Transaction(...)`.
- Revit 2024: dùng `ElementId.Value` (kiểu long), không dùng `IntegerValue`.
- Chú thích code bằng tiếng Việt. Trả về số đã đổi sang mm, m, m², m³.

## 9. Báo cáo sau mỗi việc

Kết thúc mỗi việc, báo anh:
1. Đã tạo / sửa gì (số lượng, loại, tầng, Id chính).
2. Phần nào chưa làm hoặc chưa kiểm được, lý do.
3. Số liệu nào là đề xuất, cần anh duyệt.
4. Nhắc lưu file nếu mô hình đã thay đổi.
