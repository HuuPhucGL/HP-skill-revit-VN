---
name: hp-revit-kiem-tra-mo-hinh
description: Kiểm tra mô hình Revit 2024 qua MCP cho anh Phúc — đọc cảnh báo Revit (Warnings), tìm tường trùng / chồng nhau, phòng chưa khép kín hoặc chưa đặt, phần tử sai Level, tên Level / loại tường / sheet sai quy ước (TẦNG n, Tường gạch 110/220, KT-01), cửa thiếu kích thước, thống kê mô hình, tô màu đánh dấu lỗi để anh xem. Dùng khi anh Phúc nói "kiểm tra mô hình", "rà lỗi Revit", "check model", "mô hình có lỗi gì", "trước khi bốc khối lượng / trước khi in", kể cả khi không nhắc tên skill.
---

# Kiểm tra mô hình Revit

Đọc và tuân theo `hp-revit-quy-uoc` trước. Mã C# kiểm tra nằm ở `references/csharp-kiem-tra.md`.
Skill này **chỉ đọc và đánh dấu**: không tự sửa, không tự xóa. Sửa gì thì liệt kê để anh chọn. Xóa thì
luôn hỏi trước.

## Bước 1 — Thống kê tổng quan (công cụ MCP, làm luôn)

- `analyze_model_statistics`: số phần tử theo loại, theo Level. Chú ý phần tử nằm trên Level lạ.
- `export_room_data` với `includeUnplacedRooms: true`, `includeNotEnclosedRooms: true`: phòng chưa đặt,
  phòng chưa khép kín (diện tích 0).

## Bước 2 — Kiểm tra sâu (mã C#, hỏi anh một lần cho cả đoạn)

Đoạn C# "Kiểm tra tổng hợp" trả về:

| Mục | Phát hiện |
|---|---|
| `canhBao` | Cảnh báo Revit gom theo nội dung, kèm Id phần tử (tường chồng, phòng trùng, phần tử trùng vị trí…) |
| `tuongTrung` | Cặp tường cùng tầng, song song, chồng lên nhau trên một đoạn |
| `levelSaiTen` | Level không theo mẫu `TẦNG n` / `TẦNG MÁI` |
| `tuongSaiTen` | Loại tường đang dùng không theo mẫu `Tường gạch N` |
| `tuongLechDay` | Loại tường tên `Tường gạch N` nhưng chiều dày lõi khác N mm |
| `sheetSaiSo` | Sheet không theo mẫu `KT-nn` |
| `cuaThieuKichThuoc` | Cửa đi / cửa sổ không đọc được rộng hoặc cao |
| `khungTenTam` | Sheet còn dùng khung tên TẠM |
| `viewSaiTyLe` | Mặt bằng / mặt đứng / mặt cắt có tỷ lệ khác 1/50 |

## Bước 3 — Đánh dấu cho anh xem

Đánh dấu trên **view đang mở** (đây là đổi hiển thị, không đổi mô hình, nên làm luôn rồi báo):
- `operate_element` với action `Highlight` (tô đỏ) hoặc `Isolate` cho các Id lỗi.
- Xem xong: `operate_element` với action `ResetIsolate`. Trả màu bằng `SetColor` hoặc nhờ anh dùng
  Visibility/Graphics → Reset.

## Bước 4 — Báo cáo

Lập bảng theo mức độ:

| Mức | Ví dụ | Ảnh hưởng |
|---|---|---|
| **Nghiêm trọng** | Tường trùng, phòng chưa khép kín, cửa thiếu kích thước | Sai khối lượng |
| **Cần sửa** | Tên Level / loại tường / sheet sai quy ước, view sai tỷ lệ | Sai hồ sơ, khó lọc |
| **Lưu ý** | Khung tên TẠM, cảnh báo nhẹ của Revit | Cần xử lý trước khi phát hành |

Mỗi dòng ghi: Id phần tử, tầng, mô tả, cách sửa đề xuất. Cuối báo cáo hỏi anh muốn sửa mục nào:
- Đổi tên, đổi type, chỉnh tham số: là thao tác "sửa", được làm luôn sau khi anh chọn mục.
- Xóa tường trùng hay phòng thừa: phải hỏi riêng, liệt kê từng Id.

## Lưu ý

- Danh sách cảnh báo Revit có thể rất dài. Chỉ in 10 nhóm nhiều nhất, phần còn lại ghi số lượng.
- Tường trùng mà khác loại (ví dụ lớp ốp đặt sát tường gạch) có thể là cố ý. Hỏi anh, đừng kết luận lỗi.
