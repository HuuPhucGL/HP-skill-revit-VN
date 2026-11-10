---
name: hp-revit-trien-khai-ban-ve
description: Triển khai bản vẽ kiến trúc trong Revit 2024 qua MCP cho anh Phúc — tạo view mặt bằng / mặt đứng / mặt cắt tỷ lệ 1/50, tạo sheet A3 đánh số KT-01, KT-02…, đặt khung tên (tạm dùng khung A3 có sẵn trong file, đánh dấu TẠM), đặt view lên sheet, ghi kích thước (dim), tag tường / phòng / cửa, tô màu theo tham số. Dùng khi anh Phúc nói "triển khai bản vẽ", "tạo sheet", "dàn trang", "đặt view lên sheet", "ghi kích thước", "tag phòng", "đánh số bản vẽ", "thay khung tên", kể cả khi không nhắc tên skill.
---

# Triển khai bản vẽ kiến trúc trong Revit

Đọc và tuân theo `hp-revit-quy-uoc` trước. Mã C# cho view và sheet nằm ở `references/csharp-ban-ve.md`.
Mọi đoạn C# đều phải hỏi anh trước khi chạy. Khi đã liệt kê đủ các đoạn cho một bộ bản vẽ, có thể gộp vào
một lần hỏi.

## Quy chuẩn trình bày (anh Phúc)

- Khổ **A3**, tỷ lệ view **1/50**, số hiệu sheet **KT-01, KT-02…** theo thứ tự anh duyệt.
- Font chữ Unicode (Arial hoặc Times New Roman), không dùng font VNI/TCVN3. Text type trong file dùng font
  khác thì báo anh.
- **Khung tên:** anh chưa có family khung tên Revit. Tạm dùng khung tên A3 có sẵn trong file và ghi
  `TAM - thay khung ten GH.A3` vào tham số **Comments** của khung tên, để sau này lọc ra thay hàng loạt.
  File không có khung A3 nào thì dừng lại hỏi anh: nạp file `.rfa` anh chỉ định, hay tạo sheet không có khung
  tên. Không tự vẽ khung tên.

## Bước 1 — Lập danh mục bản vẽ

Đề xuất danh mục rồi chờ anh duyệt, ví dụ nhà phố 3 tầng:

| Số hiệu | Tên sheet | View |
|---|---|---|
| KT-01 | MẶT BẰNG TẦNG 1 | MB TẦNG 1 |
| KT-02 | MẶT BẰNG TẦNG 2 | MB TẦNG 2 |
| KT-03 | MẶT BẰNG TẦNG 3 | MB TẦNG 3 |
| KT-04 | MẶT BẰNG MÁI | MB TẦNG MÁI |
| KT-05 | MẶT ĐỨNG TRỤC A-C | MẶT ĐỨNG TRỤC A-C |
| KT-06 | MẶT CẮT A-A | MẶT CẮT A-A |

Đây là đề xuất. Số lượng, thứ tự và tên do anh quyết.

## Bước 2 — Tạo view

1. Mặt bằng: mã C# mục 1 tạo `ViewPlan` cho từng Level, đặt tên theo danh mục, tỷ lệ 1/50.
   View đã có thì chỉ đổi tên và tỷ lệ, không tạo trùng.
2. Mặt đứng: template mặc định có sẵn 4 mặt đứng (East/North/South/West). Dùng mã C# mục 2 để đổi tên
   và đặt tỷ lệ.
3. Mặt cắt: mã C# mục 3 tạo mặt cắt theo đường cắt anh chỉ định (2 điểm, mm) và chiều sâu nhìn.

## Bước 3 — Chú thích trên từng view

Mở view cần chú thích (anh mở trong Revit, hoặc hỏi anh mở) vì các công cụ tag và dim chạy trên **view
đang mở**. Kiểm tra bằng `get_current_view_info` trước khi chú thích.

- Tag phòng: `tag_all_rooms`. Tag tường: `tag_all_walls`.
- Tag cửa đi / cửa sổ: mã C# mục 4. File phải có family tag cửa. Chưa có thì báo anh.
- Kích thước: `create_dimensions` với `elementIds` là các tường hoặc trục cần dim, `linePoint` là vị trí
  đường dim (mm). Thứ tự đề xuất: dim tổng ngoài cùng, dim trục, dim chi tiết tường và cửa. Trên mặt bằng
  1/50, các đường dim cách nhau khoảng 8–10 mm trên giấy, tức 400–500 mm ngoài mô hình (đề xuất).
- Kiểm tra trực quan: `color_elements` theo `Type Name` để soát loại tường. Đây chỉ là đổi màu tạm trên view.
  Báo anh, và trả lại màu bằng `operate_element` với action `SetColor` hoặc Visibility/Graphics nếu cần.

## Bước 4 — Tạo sheet và đặt view

1. Mã C# mục 5: tìm khung tên A3, tạo sheet theo danh mục, ghi Comments TẠM, đặt view vào giữa khung.
2. View đã nằm trên sheet khác thì không đặt được. Mã sẽ báo, hỏi anh xử lý.
3. Viewport tràn khổ A3 ở tỷ lệ 1/50 thì báo anh. Không tự đổi tỷ lệ vì anh in 1/50.

## Bước 5 — Thay khung tên chính thức (khi anh đã có family GH.A3 cho Revit)

Mã C# mục 6: tìm mọi khung tên có Comments bắt đầu bằng `TAM`, đổi sang type khung tên mới, xóa ghi chú TẠM.

## Bước 6 — Báo cáo

Liệt kê: view đã tạo / đổi tên, sheet đã tạo (số hiệu, tên, khung tên đang dùng, có TẠM hay không), chú thích
đã đặt, phần còn thiếu (thiếu tag family, view tràn khổ…). Nhắc anh kiểm tra bản in thử ở A3 bằng file CTB
của anh, rồi lưu file.

## Ngoài phạm vi MCP hiện tại

Plugin chưa có lệnh xuất PDF/DWG và chưa áp dụng View Template. Anh làm tay trong Revit
(File → Export / Print). Muốn dùng mã C# thì phải hỏi riêng, vì `PrintManager` và `Export` không chạy được
bên trong Transaction mà plugin mở sẵn.
