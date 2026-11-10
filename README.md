# HP-skill-revit-VN

Bộ skill tiếng Việt giúp **Claude** làm việc trực tiếp trong **Autodesk Revit 2024** qua MCP (Model Context
Protocol). Bộ skill viết cho kỹ sư kiến trúc nhà phố / nhà ở tại Việt Nam: đơn vị mm, bản vẽ A3 tỷ lệ 1/50,
đánh số KT-01…, bốc khối lượng phần thô ra Excel có công thức.

> Kết nối Revit dùng dự án mã nguồn mở [mcp-servers-for-revit](https://github.com/mcp-servers-for-revit/mcp-servers-for-revit)
> (giấy phép MIT). Repo này chỉ chứa skill và script cài đặt, không chứa bản vẽ, family, template hay file CTB.

## Bộ skill

| Skill | Dùng khi | Nội dung chính |
|---|---|---|
| `hp-revit-quy-uoc` | Trước mọi thao tác Revit | Kiểm tra kết nối, khảo sát dự án, đơn vị, quyền hạn, đặt tên, sao lưu, cách viết mã C# |
| `hp-revit-dung-mo-hinh` | "Dựng mô hình", "chuyển CAD sang Revit" | Trục, Level `TẦNG n`, tường `Tường gạch 110/220`, sàn, cửa, phòng; đầu vào là CAD, lời nói, ảnh hoặc file có sẵn |
| `hp-revit-trien-khai-ban-ve` | "Tạo sheet", "ghi kích thước", "tag phòng" | View 1/50, sheet A3 KT-01…, khung tên tạm, đặt view, dim, tag, thay khung tên hàng loạt |
| `hp-revit-boc-khoi-luong` | "Bốc khối lượng", "xuất Excel" | Tường xây (trừ ô cửa có diễn giải), bê tông + cốp pha, tô trát, lát nền, cửa, diện tích phòng |
| `hp-revit-kiem-tra-mo-hinh` | "Kiểm tra mô hình", "rà lỗi" | Cảnh báo Revit, tường trùng, phòng hở, sai quy ước tên, cửa thiếu kích thước, view sai tỷ lệ |

Quy tắc chung của bộ skill:
- Thông số kỹ thuật bị thiếu (chiều dày tường, cao tầng, kích thước cửa, định mức) thì **hỏi lại**, không tự đoán.
- Claude được tạo / sửa phần tử bằng công cụ MCP. **Xóa phần tử** và **chạy mã C#** thì phải hỏi trước.
- Sao lưu file `.rvt` vào `_backup/YYMMDD/` trước khi sửa. Mô hình lưu ở `02-Mo hinh Revit`, Excel lưu ở `04-Boc tach du toan`.
- Excel dùng công thức, làm tròn 2 số lẻ, tách số liệu gốc (nền vàng) và kết quả tính.

## Cài đặt

### Yêu cầu
- Windows, Autodesk Revit 2020–2026 (bộ skill viết và kiểm tra cho **Revit 2024**).
- Claude Code (hoặc Claude Desktop).
- Python 3 có `openpyxl` (chỉ cần cho xuất Excel khối lượng): `pip install openpyxl`.

### Bước 1 — Cài kết nối Claude ↔ Revit

Đóng Revit, mở PowerShell trong thư mục repo rồi chạy:

```powershell
powershell -ExecutionPolicy Bypass -File .\cai-dat\cai-mcp-revit.ps1 -RevitVersion 2024 -CaiSkill
```

Script sẽ:
1. Tải Node.js 22 bản rời từ nodejs.org (có kiểm tra mã SHA256) vào `%LOCALAPPDATA%\HP-RevitMCP\node22`.
   Dùng Node 22 vì thư viện `better-sqlite3` của server chưa có bản dựng sẵn cho Node mới hơn.
2. Cài server `mcp-server-for-revit@1.0.0` vào `%LOCALAPPDATA%\HP-RevitMCP\server`.
3. Tải plugin Revit đúng phiên bản và chép vào `%APPDATA%\Autodesk\Revit\Addins\<năm>`.
4. Đăng ký MCP server tên `revit` vào `~/.claude.json` (có sao lưu file cũ). Thêm `-ClaudeDesktop` để đăng ký cho Claude Desktop.
5. Có `-CaiSkill` thì chép bộ skill vào `~/.claude/skills`.

### Bước 2 — Bật plugin trong Revit
1. Mở Revit, Revit hỏi plugin lạ thì bấm **Always Load**.
2. Tab **Add-Ins** → panel **Revit MCP Plugin** → **Settings**: tích các lệnh cần dùng → **Save**.
3. Bấm **Revit MCP Switch** để bật kết nối (mỗi lần mở Revit).
4. Khởi động lại Claude Code.

> Plugin dùng **cổng 8080**. Nếu máy có plugin MCP khác cũng dùng cổng 8080 thì tạm tắt plugin đó
> (chuyển file `.addin` của nó ra khỏi thư mục Addins).

### Cài skill theo kiểu plugin của Claude Code (cách khác)

```
/plugin marketplace add HuuPhucGL/HP-skill-revit-VN
/plugin install hp-skill-revit-vn@hp-skill-revit-vn
```

## Cấu trúc repo

```
HP-skill-revit-VN/
├── .claude-plugin/            # khai báo plugin / marketplace cho Claude Code
├── cai-dat/cai-mcp-revit.ps1  # script cài MCP + plugin Revit
└── skills/
    ├── hp-revit-quy-uoc/            SKILL.md + references/csharp-co-ban.md
    ├── hp-revit-dung-mo-hinh/       SKILL.md
    ├── hp-revit-trien-khai-ban-ve/  SKILL.md + references/csharp-ban-ve.md
    ├── hp-revit-boc-khoi-luong/     SKILL.md + references/csharp-khoi-luong.md + scripts/xuat_khoi_luong.py
    └── hp-revit-kiem-tra-mo-hinh/   SKILL.md + references/csharp-kiem-tra.md
```

## Giới hạn hiện tại
- Các đoạn mã C# đã biên dịch được với RevitAPI 2024, nhưng nên chạy thử trên bản sao file trước khi dùng cho dự án thật.
- Plugin MCP chưa có lệnh xuất PDF/DWG, View Template, lưu file. Những việc này làm tay trong Revit.
- Cách tính cốp pha và tô trát là **đề xuất**. Phải duyệt theo định mức của từng dự án.
- Không lấy được khối lượng thép từ mô hình kiến trúc.

## Giấy phép
MIT. Xem [LICENSE](LICENSE).
