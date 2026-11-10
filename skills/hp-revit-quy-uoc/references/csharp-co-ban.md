# Mã C# cơ bản cho `send_code_to_revit` (Revit 2024)

Mọi đoạn dưới đây là **thân hàm** `Execute(Document document, object[] parameters)`.
Gửi nguyên văn qua tham số `code`. Trước khi gửi phải hỏi anh Phúc (quy ước mục 4).

Nhắc lại khuôn mẫu của plugin:
- Đã có `using System; System.Linq; System.Collections.Generic; Autodesk.Revit.DB; Autodesk.Revit.UI;`
- Đã có Transaction bao ngoài. Không mở Transaction mới.
- Phải `return` một giá trị. Kết quả được đổi sang JSON.

Các đoạn mã là mẫu. Lần đầu dùng trên một file nên chạy thử trên bản sao.
Gặp lỗi biên dịch thì đọc thông báo `Line N: ...`, sửa đúng dòng đó rồi gửi lại.

---

## 1. Khảo sát dự án (chỉ đọc)

```csharp
// Doi don vi noi bo (feet) sang mm
Func<double, double> mm = v => Math.Round(UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters), 1);

// Danh sach Level sap theo cao do
var levels = new FilteredElementCollector(document).OfClass(typeof(Level)).Cast<Level>()
    .OrderBy(l => l.Elevation)
    .Select(l => new { id = l.Id.Value, ten = l.Name, caoDo_mm = mm(l.Elevation) })
    .ToList();

// Loai tuong co ban
var wallTypes = new FilteredElementCollector(document).OfClass(typeof(WallType)).Cast<WallType>()
    .Where(t => t.Kind == WallKind.Basic)
    .Select(t => new { id = t.Id.Value, ten = t.Name, day_mm = mm(t.Width) })
    .ToList();

// Khung ten co trong file
var titleBlocks = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_TitleBlocks)
    .WhereElementIsElementType().Cast<FamilySymbol>()
    .Select(s => new { id = s.Id.Value, family = s.FamilyName, ten = s.Name })
    .ToList();

// Ban ve CAD da link/import
var cad = new FilteredElementCollector(document).OfClass(typeof(ImportInstance)).Cast<ImportInstance>()
    .Select(i => new { id = i.Id.Value, ten = i.Category != null ? i.Category.Name : "", laLink = i.IsLinked })
    .ToList();

var don_vi_do_dai = document.GetUnits().GetFormatOptions(SpecTypeId.Length).GetUnitTypeId().TypeId;

return new {
    file = document.PathName,
    tieuDe = document.Title,
    donViDoDai = don_vi_do_dai,
    levels, wallTypes, titleBlocks, cad,
    soView = new FilteredElementCollector(document).OfClass(typeof(View)).Cast<View>().Count(v => !v.IsTemplate),
    soSheet = new FilteredElementCollector(document).OfClass(typeof(ViewSheet)).GetElementCount()
};
```

## 2. Đổi tên và cao độ Level theo quy ước "TẦNG n"

Truyền danh sách đã thống nhất với anh. Ví dụ đổi `Level 1` → `TẦNG 1` (±0), `Level 2` → `TẦNG 2` (+3600).

```csharp
// Danh sach doi ten: tenCu -> (tenMoi, caoDo_mm). Sua theo yeu cau anh Phuc truoc khi chay.
var doiTen = new List<Tuple<string, string, double>> {
    Tuple.Create("Level 1", "TẦNG 1", 0.0),
    Tuple.Create("Level 2", "TẦNG 2", 3600.0)
};
var ketQua = new List<object>();
var levels = new FilteredElementCollector(document).OfClass(typeof(Level)).Cast<Level>().ToList();
foreach (var d in doiTen)
{
    var lv = levels.FirstOrDefault(l => l.Name == d.Item1);
    if (lv == null) { ketQua.Add(new { tenCu = d.Item1, trangThai = "khong tim thay" }); continue; }
    lv.Name = d.Item2;
    lv.Elevation = UnitUtils.ConvertToInternalUnits(d.Item3, UnitTypeId.Millimeters);
    ketQua.Add(new { tenCu = d.Item1, tenMoi = d.Item2, caoDo_mm = d.Item3, id = lv.Id.Value });
}
return ketQua;
```

Tạo Level mới thì dùng công cụ MCP `create_level` (không cần C#).

## 3. Tạo loại tường "Tường gạch N" (chỉ lõi gạch)

Chiều dày phải lấy từ anh, không tự đoán. Đoạn mã nhân bản một loại tường Basic có sẵn rồi đặt một lớp lõi.

```csharp
// Tham so: ten loai tuong va chieu day loi (mm) — lay tu anh Phuc
string tenMoi = "Tường gạch 110";
double day_mm = 110;

var tatCa = new FilteredElementCollector(document).OfClass(typeof(WallType)).Cast<WallType>().ToList();
var daCo = tatCa.FirstOrDefault(t => t.Name == tenMoi);
if (daCo != null) return new { trangThai = "da co san", id = daCo.Id.Value };

var goc = tatCa.First(t => t.Kind == WallKind.Basic);
var moi = (WallType)goc.Duplicate(tenMoi);

// Mot lop loi gach, vat lieu de trong (anh gan sau neu can)
var lop = new List<CompoundStructureLayer> {
    new CompoundStructureLayer(UnitUtils.ConvertToInternalUnits(day_mm, UnitTypeId.Millimeters),
        MaterialFunctionAssignment.Structure, ElementId.InvalidElementId)
};
moi.SetCompoundStructure(CompoundStructure.CreateSimpleCompoundStructure(lop));
return new { trangThai = "da tao", id = moi.Id.Value, ten = tenMoi, day_mm };
```

Tường có lớp trát trong type: hỏi anh chiều dày từng lớp, thêm `CompoundStructureLayer` với
`MaterialFunctionAssignment.Finish1` hoặc `Finish2` ở hai bên lớp lõi. Khi bốc khối lượng phải tách
lõi gạch và lớp trát.

## 4. Đọc layer của bản vẽ CAD đã link/import (chỉ đọc)

```csharp
// Liet ke layer va so doan net trong moi ban ve CAD
var ketQua = new List<object>();
foreach (var imp in new FilteredElementCollector(document).OfClass(typeof(ImportInstance)).Cast<ImportInstance>())
{
    var demLayer = new Dictionary<string, int>();
    var geo = imp.get_Geometry(new Options());
    if (geo == null) continue;
    foreach (var gi in geo.OfType<GeometryInstance>())
        foreach (var obj in gi.GetInstanceGeometry())
        {
            var gs = document.GetElement(obj.GraphicsStyleId) as GraphicsStyle;
            string layer = gs != null && gs.GraphicsStyleCategory != null ? gs.GraphicsStyleCategory.Name : "(khong ro)";
            demLayer[layer] = demLayer.ContainsKey(layer) ? demLayer[layer] + 1 : 1;
        }
    ketQua.Add(new { id = imp.Id.Value, layers = demLayer.OrderByDescending(k => k.Value).Select(k => new { layer = k.Key, soDoan = k.Value }) });
}
return ketQua;
```

## 5. Lấy các đoạn thẳng trên một layer CAD, tọa độ mm (chỉ đọc)

Dùng để dựng tường từ mặt bằng CAD: hai nét song song cách nhau đúng chiều dày tường là một bức tường,
tim tường nằm giữa hai nét.

```csharp
// Ten layer chua net tuong — hoi anh Phuc (vi du "KT-TUONG")
string tenLayer = "KT-TUONG";
Func<double, double> mm = v => Math.Round(UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters), 1);
var doan = new List<object>();
foreach (var imp in new FilteredElementCollector(document).OfClass(typeof(ImportInstance)).Cast<ImportInstance>())
{
    var geo = imp.get_Geometry(new Options());
    if (geo == null) continue;
    foreach (var gi in geo.OfType<GeometryInstance>())
        foreach (var obj in gi.GetInstanceGeometry())
        {
            var gs = document.GetElement(obj.GraphicsStyleId) as GraphicsStyle;
            if (gs == null || gs.GraphicsStyleCategory == null || gs.GraphicsStyleCategory.Name != tenLayer) continue;
            if (obj is Line ln)
                doan.Add(new { x1 = mm(ln.GetEndPoint(0).X), y1 = mm(ln.GetEndPoint(0).Y), x2 = mm(ln.GetEndPoint(1).X), y2 = mm(ln.GetEndPoint(1).Y) });
            else if (obj is PolyLine pl)
            {
                var p = pl.GetCoordinates();
                for (int i = 0; i < p.Count - 1; i++)
                    doan.Add(new { x1 = mm(p[i].X), y1 = mm(p[i].Y), x2 = mm(p[i + 1].X), y2 = mm(p[i + 1].Y) });
            }
        }
}
return new { layer = tenLayer, soDoan = doan.Count, doan };
```

Lưu ý: tọa độ trả về là tọa độ trong Revit sau khi đặt CAD. Nếu khi link anh chọn "Auto - Origin to Origin"
thì gốc CAD trùng gốc Revit.
