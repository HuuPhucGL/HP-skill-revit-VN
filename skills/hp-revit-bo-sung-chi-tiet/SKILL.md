---
name: hp-revit-bo-sung-chi-tiet
description: Bổ sung chi tiết cho mô hình Revit nhà phố / nhà ở của anh Phúc sau khi đã dựng khối (tường, sàn, cửa) — cột, dầm, cầu thang, mái, lan can, trần, vật liệu hoàn thiện, ghi chú chữ, nét chi tiết, bảng thống kê cửa / phòng / vật liệu, mặt cắt và chi tiết cấu tạo — để đủ nội dung ra hồ sơ. Dùng khi anh Phúc nói "bổ sung chi tiết", "làm cầu thang", "dựng mái", "đặt cột dầm", "lan can", "bảng thống kê cửa", "bảng phòng", "ghi chú", "chi tiết cấu tạo", "làm đầy đủ hồ sơ", kể cả khi không nhắc tên skill.
---

# Bổ sung chi tiết cho mô hình Revit

Đọc `hp-revit-quy-uoc` trước (đơn vị mm, quyền hạn, sao lưu). Skill này nằm **giữa** `hp-revit-dung-mo-hinh`
(dựng khối) và `hp-revit-trien-khai-ban-ve` + `hp-revit-xuat-ho-so-pdf` (ra hồ sơ).
Phạm vi của anh: kiến trúc nhà phố, nhà ở. Phần kết cấu thép, móng: chỉ làm khi anh yêu cầu và đưa số liệu.

## Nguyên tắc

- Thiếu thông số (kích thước cột, bậc thang, độ dốc mái, chiều cao lan can, vật liệu): **hỏi anh, không tự đoán**.
  Số liệu theo quy chuẩn (chiều cao lan can, bậc thang...) chỉ nêu khi anh yêu cầu và ghi "cần kiểm tra
  tiêu chuẩn hiện hành".
- Mỗi lần chạy mã C# phải hỏi anh trước (quy ước mục 4). Mọi đoạn mã dưới đây là **mẫu**, chạy thử trên
  **bản sao** của file trước.
- Thiếu family (cột, dầm, lan can, tag...) thì liệt kê để anh nạp file `.rfa`. Không tự tạo family mới.
- Làm lần lượt từng nhóm, mỗi nhóm xong thì kiểm tra bằng ảnh chụp view và đếm phần tử.

## Danh mục bổ sung (đề xuất thứ tự, anh duyệt)

| # | Nhóm | Cách làm | Hỏi anh những gì |
|---|---|---|---|
| 1 | Cột | Mã C# `NewFamilyInstance(XYZ, symbol, level, StructuralType.Column)` hoặc công cụ MCP point-based với `OST_Columns` / `OST_StructuralColumns` | Vị trí (theo giao trục), kích thước, tầng bắt đầu / kết thúc |
| 2 | Dầm | Mã C# `NewFamilyInstance(Curve, symbol, level, StructuralType.Beam)` hoặc `create_structural_framing_system` | Tiết diện, cao độ đáy / đỉnh dầm |
| 3 | Cầu thang | Công cụ MCP chưa có. Dùng mã C# với `StairsEditScope` (cầu thang theo run) hoặc dựng tạm bằng sàn bậc | Chiều cao tầng, bề rộng vế, số bậc, kích thước bậc (rộng × cao), vị trí |
| 4 | Mái | Mã C# `NewFootPrintRoof(CurveArray, level, roofType, out ModelCurveArray)`, đặt `DefinesSlope` và độ dốc | Kiểu mái (bằng / dốc), độ dốc, chiều dày, mép đua |
| 5 | Lan can, ban công | Mã C# `Railing.Create` hoặc công cụ line-based `OST_Railings` | Chiều cao, kiểu, vị trí |
| 6 | Trần | Mã C# `Ceiling.Create` (2022 trở lên) hoặc công cụ surface-based | Cao độ trần theo phòng, loại trần |
| 7 | Vật liệu / lớp hoàn thiện | Đổi type tường / sàn có lớp cấu tạo (tô trát, ốp lát) hoặc `Parameter` Material | Cấu tạo lớp, dày từng lớp (đối chiếu với bốc khối lượng) |
| 8 | Ghi chú chữ | Mã C# `TextNote.Create(doc, viewId, XYZ, text, textTypeId)` | Nội dung, font Unicode (Arial / Times New Roman) |
| 9 | Nét chi tiết, hatch | Mã C# `doc.Create.NewDetailCurve(view, line)`; hatch bằng Filled Region | Chi tiết nào, tỷ lệ |
| 10 | Bảng thống kê cửa / phòng / vật liệu | Mã C# `ViewSchedule.CreateSchedule(doc, categoryId)` rồi `AddField` | Cột cần hiện, thứ tự, tên bảng |
| 11 | Mặt cắt, mặt đứng | Xem `hp-revit-trien-khai-ban-ve` (mục 2) | Vị trí đường cắt, hướng nhìn |

## Quy trình

1. Khảo sát: `analyze_model_statistics`, `get_available_family_types` cho các nhóm cần (`OST_Columns`,
   `OST_StructuralColumns`, `OST_StructuralFraming`, `OST_Stairs`, `OST_Roofs`, `OST_Railings`, `OST_Ceilings`).
   Lập bảng "có / thiếu" cho anh.
2. Đề xuất danh mục nhóm sẽ làm + bảng thông số còn thiếu. Chờ anh trả lời.
3. Sao lưu file `.rvt` vào `_backup/YYMMDD/` (quy ước mục 7).
4. Làm từng nhóm theo bảng. Sau mỗi nhóm: chụp ảnh view (`revit_screenshot` nếu có MCP `hp-revit`, hoặc xem
   `get_current_view_info`), đếm lại số phần tử, báo anh những gì đã tạo (kèm Id).
5. Chạy `hp-revit-kiem-tra-mo-hinh` để rà cảnh báo trước khi ra hồ sơ.
6. Chuyển sang `hp-revit-trien-khai-ban-ve`.

## Báo cáo

Liệt kê: nhóm đã làm (số lượng theo tầng), nhóm bỏ qua và lý do (thiếu family / thiếu số liệu), số liệu đề
xuất cần anh duyệt, cảnh báo còn lại. Tách rõ **số liệu anh cung cấp** và **số liệu đề xuất**.
