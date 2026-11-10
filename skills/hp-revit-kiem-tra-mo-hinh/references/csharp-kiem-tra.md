# Mã C# kiểm tra tổng hợp (Revit 2024, chỉ đọc)

Thân hàm `Execute(Document document, object[] parameters)`. Không sửa mô hình. Phải hỏi anh trước khi gửi.

Trong thân hàm không viết được `using`, nên mã dưới đây gọi đầy đủ `System.Text.RegularExpressions.Regex`.

```csharp
Func<double, double> mm = v => Math.Round(UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters), 1);
Func<string, string, bool> khop = (s, mau) => System.Text.RegularExpressions.Regex.IsMatch(s ?? "", mau);

// ---- 1. Canh bao Revit, gom theo noi dung ----
var canhBao = document.GetWarnings()
    .GroupBy(w => w.GetDescriptionText())
    .OrderByDescending(g => g.Count())
    .Select(g => new { noiDung = g.Key, soLan = g.Count(),
        idMau = g.SelectMany(w => w.GetFailingElements()).Select(id => id.Value).Distinct().Take(20) })
    .ToList();

// ---- 2. Tuong trung / chong nhau (cung tang, song song, sat nhau, co doan chung) ----
var walls = new FilteredElementCollector(document).OfClass(typeof(Wall)).Cast<Wall>()
    .Where(w => w.Location is LocationCurve lc && lc.Curve is Line).ToList();
var tuongTrung = new List<object>();
for (int i = 0; i < walls.Count; i++)
    for (int j = i + 1; j < walls.Count; j++)
    {
        var a = walls[i]; var b = walls[j];
        if (a.LevelId != b.LevelId) continue;
        var la = (Line)((LocationCurve)a.Location).Curve; var lb = (Line)((LocationCurve)b.Location).Curve;
        if (la.Direction.CrossProduct(lb.Direction).GetLength() > 0.01) continue;      // khong song song
        var a0 = la.GetEndPoint(0); var a1 = la.GetEndPoint(1);
        var b0 = new XYZ(lb.GetEndPoint(0).X, lb.GetEndPoint(0).Y, a0.Z);
        var b1 = new XYZ(lb.GetEndPoint(1).X, lb.GetEndPoint(1).Y, a0.Z);
        var vo = Line.CreateUnbound(a0, la.Direction);
        double kc = vo.Distance(b0);                                                     // khoang cach 2 tim
        if (kc > (a.Width + b.Width) / 2 - 1e-6) continue;                               // khong cham nhau
        double ta0 = 0, ta1 = la.Length;
        double tb0 = (b0 - a0).DotProduct(la.Direction), tb1 = (b1 - a0).DotProduct(la.Direction);
        double chung = Math.Min(ta1, Math.Max(tb0, tb1)) - Math.Max(ta0, Math.Min(tb0, tb1));
        if (chung <= UnitUtils.ConvertToInternalUnits(10, UnitTypeId.Millimeters)) continue; // chi cham dau
        tuongTrung.Add(new { idA = a.Id.Value, loaiA = a.WallType.Name, idB = b.Id.Value, loaiB = b.WallType.Name,
            tang = document.GetElement(a.LevelId)?.Name, doanChung_mm = mm(chung), khoangCachTim_mm = mm(kc) });
    }

// ---- 3. Ten Level ----
var levelSaiTen = new FilteredElementCollector(document).OfClass(typeof(Level)).Cast<Level>()
    .Where(l => !khop(l.Name, @"^TẦNG (\d+|MÁI)$"))
    .Select(l => new { id = l.Id.Value, ten = l.Name, caoDo_mm = mm(l.Elevation) }).ToList();

// ---- 4. Loai tuong dang dung: sai ten / lech chieu day ----
var loaiDung = walls.Select(w => w.WallType).Where(t => t.Kind == WallKind.Basic)
    .GroupBy(t => t.Id.Value).Select(g => g.First()).ToList();
var tuongSaiTen = new List<object>(); var tuongLechDay = new List<object>();
foreach (var t in loaiDung)
{
    var mt = System.Text.RegularExpressions.Regex.Match(t.Name, @"^Tường gạch (\d+)");
    if (!mt.Success) { tuongSaiTen.Add(new { id = t.Id.Value, ten = t.Name, day_mm = mm(t.Width) }); continue; }
    double loi = 0;
    var cs = t.GetCompoundStructure();
    if (cs != null) foreach (var l in cs.GetLayers())
        if (l.Function == MaterialFunctionAssignment.Structure || l.Function == MaterialFunctionAssignment.Substrate) loi += l.Width;
    double loiMm = mm(loi > 0 ? loi : t.Width);
    if (Math.Abs(loiMm - double.Parse(mt.Groups[1].Value)) > 0.5)
        tuongLechDay.Add(new { id = t.Id.Value, ten = t.Name, dayLoiThucTe_mm = loiMm });
}

// ---- 5. Sheet sai so hieu ----
var sheetSaiSo = new FilteredElementCollector(document).OfClass(typeof(ViewSheet)).Cast<ViewSheet>()
    .Where(s => !s.IsPlaceholder && !khop(s.SheetNumber, @"^KT-\d{2,}$"))
    .Select(s => new { id = s.Id.Value, so = s.SheetNumber, ten = s.Name }).ToList();

// ---- 6. Cua thieu kich thuoc ----
var bipR = new[] { BuiltInParameter.DOOR_WIDTH, BuiltInParameter.WINDOW_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM };
var bipC = new[] { BuiltInParameter.DOOR_HEIGHT, BuiltInParameter.WINDOW_HEIGHT, BuiltInParameter.FAMILY_HEIGHT_PARAM };
Func<Element, BuiltInParameter[], bool> coGT = (e, bips) => {
    foreach (var x in new[] { e, document.GetElement(e.GetTypeId()) })
        if (x != null) foreach (var b in bips) { var p = x.get_Parameter(b); if (p != null && p.HasValue && p.AsDouble() > 0) return true; }
    return false;
};
var cuaThieuKichThuoc = new FilteredElementCollector(document).WherePasses(new LogicalOrFilter(
        new ElementCategoryFilter(BuiltInCategory.OST_Doors), new ElementCategoryFilter(BuiltInCategory.OST_Windows)))
    .WhereElementIsNotElementType().Cast<FamilyInstance>()
    .Where(e => !coGT(e, bipR) || !coGT(e, bipC))
    .Select(e => new { id = e.Id.Value, loai = e.Symbol.FamilyName + " : " + e.Symbol.Name }).ToList();

// ---- 7. Khung ten TAM ----
var khungTenTam = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_TitleBlocks)
    .WhereElementIsNotElementType()
    .Where(e => (e.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)?.AsString() ?? "").StartsWith("TAM"))
    .Select(e => (document.GetElement(e.OwnerViewId) as ViewSheet)?.SheetNumber ?? "?").ToList();

// ---- 8. View sai ty le (mat bang, mat dung, mat cat) ----
var viewSaiTyLe = new FilteredElementCollector(document).OfClass(typeof(View)).Cast<View>()
    .Where(v => !v.IsTemplate && (v.ViewType == ViewType.FloorPlan || v.ViewType == ViewType.Elevation || v.ViewType == ViewType.Section) && v.Scale != 50)
    .Select(v => new { id = v.Id.Value, ten = v.Name, tyLe = "1/" + v.Scale }).ToList();

return new {
    tongCanhBao = canhBao.Sum(c => c.soLan), canhBao = canhBao.Take(10), soNhomCanhBao = canhBao.Count,
    tuongTrung, levelSaiTen, tuongSaiTen, tuongLechDay, sheetSaiSo, cuaThieuKichThuoc, khungTenTam, viewSaiTyLe
};
```

Ghi chú:
- Mẫu tên Level là `TẦNG 1`, `TẦNG 2`, `TẦNG MÁI`. Anh dùng thêm tầng lửng, tum… thì sửa biểu thức
  `^TẦNG (\d+|MÁI)$`, ví dụ `^TẦNG (\d+|MÁI|LỬNG|TUM)$`.
- Tường cong không được kiểm tra trùng (chỉ xét tường thẳng).
