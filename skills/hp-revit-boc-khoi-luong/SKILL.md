---
name: hp-revit-boc-khoi-luong
description: Bốc tách khối lượng phần thô từ mô hình Revit 2024 qua MCP cho anh Phúc — tường xây (m², m³, trừ ô cửa có diễn giải), bê tông sàn/dầm/cột và cốp pha, tô trát trong/ngoài/trần, lát nền, thống kê cửa đi/cửa sổ, diện tích phòng — xuất file Excel có công thức, làm tròn 2 số lẻ, lưu vào 04-Boc tach du toan. Dùng khi anh Phúc nói "bốc khối lượng", "tính khối lượng từ Revit", "thống kê tường / bê tông / cửa", "diện tích phòng", "xuất Excel khối lượng", kể cả khi không nhắc tên skill.
---

# Bốc tách khối lượng phần thô từ Revit

Đọc và tuân theo `hp-revit-quy-uoc` trước. Mã C# trích số liệu nằm ở `references/csharp-khoi-luong.md`.
Script lập Excel là `scripts/xuat_khoi_luong.py`.

## Bước 0 — Hỏi trước khi tính

1. **Định mức áp dụng:** dự án dùng định mức nào? Anh chưa có định mức nội bộ. Chưa có câu trả lời thì Excel
   ghi "CHƯA XÁC NHẬN" ở sheet Thong tin, và mọi cách tính cốp pha / tô trát chỉ là đề xuất.
2. **Phạm vi:** cả công trình hay một tầng.
3. **Cấu tạo tường:** loại tường trong mô hình chỉ có lõi gạch, hay có cả lớp trát? Khối lượng xây tính theo
   **dày lõi**. Nếu type có lớp trát, script đã tách lõi qua `day_loi_m`.
4. Tên dự án để ghi lên file và tên file theo `YYMMDD - Tên dự án - Địa chỉ`.

## Bước 1 — Kiểm tra nhanh mô hình

Khối lượng chỉ đúng khi mô hình đúng. Chạy nhanh `hp-revit-kiem-tra-mo-hinh` (ít nhất: tường trùng, phòng
chưa khép kín, cửa thiếu kích thước). Lỗi lớn thì báo anh trước khi bốc.

## Bước 2 — Trích số liệu

1. Hỏi anh, rồi gửi đoạn C# trong `references/csharp-khoi-luong.md` qua `send_code_to_revit`.
   Đoạn mã này chỉ đọc, không sửa mô hình.
2. Lưu nguyên kết quả trả về thành file JSON, ví dụ
   `04-Boc tach du toan/YYMMDD - so lieu Revit.json` (giữ làm số liệu gốc).
3. Mô hình lớn, kết quả bị cắt: chạy lại theo từng tầng (`chiTang = "TẦNG 1"`…), mỗi tầng một file JSON,
   rồi gộp các mảng lại thành một file trước khi xuất Excel.

## Bước 3 — Lập Excel

```bash
python "<thư mục skill>/scripts/xuat_khoi_luong.py" "<file JSON>" "<dự án>/04-Boc tach du toan/YYMMDD - Tên dự án - Địa chỉ - KL phan tho.xlsx" --du-an "Tên dự án" --dinh-muc "Tên định mức anh chọn"
```

Cần Python có thư viện `openpyxl`. Thiếu thì cài bằng `pip install openpyxl`.
Không ghi đè file Excel cũ. Đã có file cùng tên thì đổi ngày ở đầu tên.

File Excel gồm:

| Sheet | Nội dung | Cách tính (công thức trong ô) |
|---|---|---|
| Thong tin | Dự án, file mô hình, định mức, chú giải màu | — |
| Tong hop | Tổng theo hạng mục | SUMIF / COUNTIF về các sheet chi tiết |
| Tuong xay | Từng bức tường | DT = Dài × Cao; trừ ô cửa = Σ(rộng × cao) có diễn giải; KL = DT xây × dày lõi |
| Be tong | Sàn, dầm, cột | Sàn V = DT × dày; dầm V = L×b×h; cột V = b×h×H; cốp pha theo công thức đề xuất |
| Hoan thien | Từng phòng | Lát nền = trát trần = DT phòng; trát tường trong = chu vi × cao − ô cửa |
| Cua | Từng cửa | DT = rộng × cao |

- Ô **nền vàng** là số liệu gốc lấy từ mô hình. Ô không tô nền là công thức. Không nhập số cứng vào ô kết quả.
- Mọi kết quả đều `ROUND(...,2)`.
- Cột "DT Revit / V Revit" để đối chiếu với số Revit tự tính. Lệch nhiều thì xem lại chỗ tường giao nhau.

## Bước 4 — Báo cáo cho anh

Tách rõ ba phần:
1. **Số liệu gốc:** lấy từ mô hình. Ghi số phần tử theo loại.
2. **Kết quả tính:** tổng chính ở sheet Tong hop (xây theo loại tường, bê tông, cốp pha, trát, lát, cửa,
   diện tích phòng theo tầng).
3. **Cần anh duyệt / kiểm tra:**
   - Định mức chưa xác nhận (nếu có).
   - Cách tính cốp pha chưa trừ phần giao dầm, sàn, cột.
   - Trát tường trong lấy theo chu vi phòng × chiều cao phòng (Unbounded Height). Chiều cao phòng khác chiều
     cao trát thực tế thì phải sửa.
   - Dầm, cột thiếu `b`/`h` trong family: V lấy theo Revit, cốp pha để trống.
   - Sàn không đánh dấu kết cấu: có thể là lớp hoàn thiện, không phải sàn BTCT.
   - Cửa thiếu kích thước: phần trừ ghi "kiểm tra".

## Lưu ý

- Phạm vi mặc định là **phần thô**. Hạng mục hoàn thiện (sơn, ốp, trần thạch cao…) chỉ làm khi anh yêu cầu.
- Không tự gán đơn giá. Anh chưa có nguồn đơn giá, cần thì hỏi.
- Khối lượng thép không lấy được từ mô hình kiến trúc. Cần mô hình kết cấu có thép (Rebar) hoặc bảng thống kê
  thép riêng.
