---
name: hp-revit-dung-mo-hinh
description: Dựng mô hình kiến trúc nhà phố / nhà ở trong Revit 2024 qua MCP cho anh Phúc — lưới trục, Level "TẦNG n", tường "Tường gạch 110/220", sàn, cửa đi, cửa sổ, phòng — từ bản vẽ CAD 2D đã link, từ kích thước anh nói bằng lời, từ ảnh/phác tay, hoặc bổ sung vào file Revit có sẵn. Dùng khi anh Phúc nói "dựng mô hình", "dựng tường", "dựng nhà 5x20", "chuyển CAD sang Revit", "đặt cửa", "tạo level", "tạo trục", "tạo phòng", kể cả khi không nhắc tên skill.
---

# Dựng mô hình kiến trúc trong Revit

Đọc và tuân theo skill `hp-revit-quy-uoc` trước (kết nối, đơn vị mm, quyền hạn, đặt tên, sao lưu).
Mã C# mẫu nằm ở `../hp-revit-quy-uoc/references/csharp-co-ban.md`.

## Bước 0 — Xác định đầu vào và chốt thông số

Anh có thể đưa một trong bốn loại đầu vào:

| Đầu vào | Cách đọc |
|---|---|
| **Bản vẽ CAD 2D (.dwg)** | Nhờ anh link vào Revit: Insert → Link CAD, Positioning "Auto - Origin to Origin", Import units "millimeter", chọn đúng Level. Sau đó đọc layer bằng mã C# mục 4 và lấy nét tường bằng mục 5 |
| **Kích thước bằng lời** | Ghi lại thành bảng thông số (bên dưới), đọc lại cho anh xác nhận |
| **Ảnh / phác tay** | Đọc ảnh, chép mọi kích thước ghi trên ảnh vào bảng. Chỗ nào mờ, thiếu hay tổng các đoạn không khớp kích thước tổng thì liệt kê để hỏi, không tự điền |
| **File Revit có sẵn** | Khảo sát (quy ước mục 2), sao lưu file trước khi sửa (quy ước mục 7) |

Trước khi dựng, phải có **bảng thông số** được anh xác nhận:

```
Kích thước tổng thể: rộng ___ m × sâu ___ m
Lưới trục: trục chữ (A, B, …) khoảng cách ___ ; trục số (1, 2, …) khoảng cách ___
Tầng: TẦNG 1 ±0.000 | TẦNG 2 +___ | … | TẦNG MÁI +___
Tường: Tường gạch ___ (bao che) | Tường gạch ___ (ngăn) — lớp trát có trong type không?
Sàn: loại ___, dày ___ mm
Cửa: ký hiệu, rộng × cao, cao độ bậu cửa sổ
Phòng: tên, tầng
```

Mục nào trống thì hỏi. Không tự đoán chiều dày tường, chiều cao tầng, kích thước cửa.

## Bước 1 — Lưới trục và Level

1. Level: đổi tên Level có sẵn thành `TẦNG 1`, `TẦNG 2`… (mã C# mục 2, nhớ hỏi trước khi chạy).
   Tầng còn thiếu thì tạo bằng `create_level` với `name` và `elevation` (mm).
2. Lưới trục: `create_grid`.
   - Khoảng cách đều: dùng `xCount`, `xSpacing`, `yCount`, `ySpacing`.
   - Khoảng cách không đều (thường gặp ở nhà phố): tạo từng nhóm khoảng cách đều, hoặc viết mã C#
     `Grid.Create(document, Line.CreateBound(p0, p1))` rồi đặt `grid.Name`.
   - Quy ước: trục chữ A, B, C theo một phương, trục số 1, 2, 3 theo phương còn lại. Hỏi anh phương nào là
     trục chữ nếu bản vẽ CAD chưa thể hiện.

## Bước 2 — Loại tường

1. `get_available_family_types` với `["OST_Walls"]`.
2. Chưa có `Tường gạch 110` / `Tường gạch 220` thì tạo bằng mã C# mục 3 với chiều dày anh đã cho.
3. Ghi lại `typeId` của từng loại để dùng ở bước sau.

## Bước 3 — Dựng tường

Dùng `create_line_based_element`, gửi **một lô cho mỗi tầng**:

```json
{ "data": [
  { "category": "OST_Walls", "typeId": 123456,
    "locationLine": { "p0": {"x":0,"y":0,"z":0}, "p1": {"x":5000,"y":0,"z":0} },
    "thickness": 220, "height": 3600, "baseLevel": 0, "baseOffset": 0 }
] }
```

- Tọa độ là **tim tường** (mm). Từ CAD: tim = trung điểm hai nét song song, chiều dày = khoảng cách hai nét.
  Khoảng cách đó không khớp loại tường nào thì báo anh, không làm tròn.
- `baseLevel` là cao độ của Level đặt chân tường (mm), `height` là chiều cao tường, thường bằng chiều cao tầng.
- Chu vi khép kín: điểm cuối của bức này trùng điểm đầu bức sau, để sau này tạo phòng được.
- Dựng xong: `get_current_view_elements` với `["OST_Walls"]` để đếm, so với số tường dự kiến.

## Bước 4 — Sàn

`create_surface_based_element` với `category: "OST_Floors"`, `typeId` loại sàn, `boundary.outerLoop` là
các đoạn khép kín, tối thiểu 3 đoạn, nối tiếp nhau. Biên sàn lấy theo mép ngoài tường bao hoặc theo CAD.
Chiều dày sàn lấy theo type. Không có type đúng chiều dày thì hỏi anh.

## Bước 5 — Cửa đi, cửa sổ

1. `get_available_family_types` với `["OST_Doors","OST_Windows"]` để lấy type.
   Thiếu kích thước cần thì báo anh: nạp family hoặc nhân bản type (mã C#, phải hỏi).
2. `create_point_based_element`: `locationPoint` nằm trên tim tường chủ, `hostWallId` là Id tường chủ.
   Cửa sổ: `baseOffset` là cao độ bậu cửa so với Level (lấy từ anh).
3. Kiểm tra vị trí cửa nằm trong chiều dài tường, cách đầu tường đủ chỗ cho khuôn cửa.
4. Hướng mở sai thì đặt lại với `facingFlipped: true`. Xóa cửa đặt sai là thao tác xóa nên phải hỏi anh trước.

## Bước 6 — Phòng

`create_room` với `name`, `number`, `location` là một điểm nằm hẳn trong vùng tường khép kín, `levelId`.
Sau đó `export_room_data` với `includeNotEnclosedRooms: true` để thấy phòng nào chưa khép kín.
Phòng chưa khép kín thì tìm chỗ tường hở rồi sửa, không xóa phòng khi chưa hỏi.

## Bước 7 — Kiểm tra và báo cáo

1. Chạy nhanh skill `hp-revit-kiem-tra-mo-hinh` (cảnh báo Revit, phòng hở, tên sai quy ước).
2. Báo cáo theo quy ước mục 9: số tường / sàn / cửa / phòng theo tầng, phần chưa dựng, số liệu đề xuất.
3. Nhắc anh lưu file vào `02-Mo hinh Revit`.

## Lưu ý

- Chưa có template riêng: dùng type có sẵn trong file. Thiếu type thì hỏi, không tự tạo family mới.
- Đơn vị luôn là mm. Kích thước anh đọc theo m thì đổi sang mm rồi nhắc lại.
- Dựng tầng trên: chép lô tường tầng dưới, đổi `baseLevel` rồi chỉnh theo mặt bằng tầng đó. Không giả định
  các tầng giống nhau khi anh chưa nói.
