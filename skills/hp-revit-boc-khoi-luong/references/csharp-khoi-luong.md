# Mã C# trích số liệu khối lượng (Revit 2024, chỉ đọc)

Một đoạn duy nhất, không sửa mô hình, trả về JSON đúng định dạng mà `scripts/xuat_khoi_luong.py` đọc.
Phải hỏi anh Phúc trước khi gửi (mã C#). Mô hình lớn có thể trả về nhiều dữ liệu: chạy theo từng tầng bằng
cách điền `chiTang`.

```csharp
// THAM SO: de trong = ca cong trinh; hoac ten 1 tang, vi du "TẦNG 1"
string chiTang = "";

Func<double, double> m = v => UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Meters);
Func<double, double> m2 = v => UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.SquareMeters);
Func<double, double> m3 = v => UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.CubicMeters);
Func<double, double> r = v => Math.Round(v, 4);

// Doc tham so dang chieu dai (m): thu instance truoc, roi den type; theo BuiltInParameter hoac theo ten
Func<Element, BuiltInParameter[], string[], double?> layDai = (e, bips, tens) => {
    var nguon = new List<Element> { e };
    var t = e.Document.GetElement(e.GetTypeId());
    if (t != null) nguon.Add(t);
    foreach (var x in nguon) {
        foreach (var b in bips) { var p = x.get_Parameter(b); if (p != null && p.HasValue && p.StorageType == StorageType.Double && p.AsDouble() > 0) return r(m(p.AsDouble())); }
        foreach (var ten in tens) { var p = x.LookupParameter(ten); if (p != null && p.HasValue && p.StorageType == StorageType.Double && p.AsDouble() > 0) return r(m(p.AsDouble())); }
    }
    return null;
};
Func<Element, BuiltInParameter, double?> layGT = (e, b) => {
    var p = e.get_Parameter(b);
    return (p != null && p.HasValue && p.StorageType == StorageType.Double) ? (double?)p.AsDouble() : null;
};
Func<Element, string> tenTang = e => {
    var lv = e.LevelId != ElementId.InvalidElementId ? document.GetElement(e.LevelId) as Level : null;
    if (lv == null) { var p = e.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT) ?? e.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM) ?? e.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM) ?? e.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM); if (p != null) lv = document.GetElement(p.AsElementId()) as Level; }
    return lv != null ? lv.Name : "(khong ro)";
};
Func<Element, bool> dungTang = e => chiTang == "" || tenTang(e) == chiTang;
Func<BuiltInCategory, List<Element>> layLoai = c => new FilteredElementCollector(document).OfCategory(c).WhereElementIsNotElementType().Where(dungTang).ToList();

var BIP_RONG = new[] { BuiltInParameter.DOOR_WIDTH, BuiltInParameter.WINDOW_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM, BuiltInParameter.FAMILY_ROUGH_WIDTH_PARAM };
var BIP_CAO = new[] { BuiltInParameter.DOOR_HEIGHT, BuiltInParameter.WINDOW_HEIGHT, BuiltInParameter.FAMILY_HEIGHT_PARAM, BuiltInParameter.FAMILY_ROUGH_HEIGHT_PARAM };
var phase = document.Phases.Cast<Phase>().LastOrDefault();

// ---- Cua di, cua so (kem phong hai ben de tru trat) ----
var cua = new List<object>();
foreach (var e in layLoai(BuiltInCategory.OST_Doors).Concat(layLoai(BuiltInCategory.OST_Windows)).OfType<FamilyInstance>())
{
    var phong = new List<long>();
    try { if (phase != null) { var a = e.get_FromRoom(phase); var b = e.get_ToRoom(phase); if (a != null) phong.Add(a.Id.Value); if (b != null && (a == null || b.Id != a.Id)) phong.Add(b.Id.Value); } } catch { }
    cua.Add(new {
        id = e.Id.Value,
        nhom = e.Category.Id.Value == (long)BuiltInCategory.OST_Doors ? "Cua di" : "Cua so",
        loai = e.Symbol.FamilyName + " : " + e.Symbol.Name,
        tang = tenTang(e),
        rong_m = layDai(e, BIP_RONG, new[] { "Width", "Rộng" }),
        cao_m = layDai(e, BIP_CAO, new[] { "Height", "Cao" }),
        hostId = e.Host != null ? e.Host.Id.Value : -1,
        phong
    });
}

// ---- Tuong ----
var tuong = new List<object>();
foreach (var w in layLoai(BuiltInCategory.OST_Walls).OfType<Wall>())
{
    var wt = w.WallType;
    if (wt.Kind != WallKind.Basic) continue;            // bo qua curtain / stacked
    var cs = wt.GetCompoundStructure();
    double dayLoi = 0;
    if (cs != null)
        foreach (var l in cs.GetLayers())
            if (l.Function == MaterialFunctionAssignment.Structure || l.Function == MaterialFunctionAssignment.Substrate) dayLoi += l.Width;
    var lo = new List<object>();
    foreach (var id in w.FindInserts(true, false, false, false))
    {
        var ins = document.GetElement(id);
        if (ins is FamilyInstance fi)
            lo.Add(new { id = id.Value, loai = fi.Category.Id.Value == (long)BuiltInCategory.OST_Doors ? "Cua di" : "Cua so", ten = fi.Symbol.Name,
                         rong_m = layDai(fi, BIP_RONG, new[] { "Width", "Rộng" }), cao_m = layDai(fi, BIP_CAO, new[] { "Height", "Cao" }) });
        else if (ins is Opening op && op.IsRectBoundary)
        {
            var a = op.BoundaryRect[0]; var b = op.BoundaryRect[1];
            lo.Add(new { id = id.Value, loai = "Lo mo", ten = "Opening", rong_m = (double?)r(m(new XYZ(a.X, a.Y, 0).DistanceTo(new XYZ(b.X, b.Y, 0)))), cao_m = (double?)r(m(Math.Abs(b.Z - a.Z))) });
        }
    }
    tuong.Add(new {
        id = w.Id.Value, loai = wt.Name, tang = tenTang(w),
        chucNang = wt.Function == WallFunction.Exterior ? "Ngoai" : "Trong",
        dai_m = r(m(layGT(w, BuiltInParameter.CURVE_ELEM_LENGTH) ?? 0)),
        cao_m = r(m(layGT(w, BuiltInParameter.WALL_USER_HEIGHT_PARAM) ?? 0)),
        day_m = r(m(wt.Width)), day_loi_m = r(m(dayLoi > 0 ? dayLoi : wt.Width)),
        dt_revit_m2 = r(m2(layGT(w, BuiltInParameter.HOST_AREA_COMPUTED) ?? 0)),
        v_revit_m3 = r(m3(layGT(w, BuiltInParameter.HOST_VOLUME_COMPUTED) ?? 0)),
        lo
    });
}

// ---- San ----
var san = layLoai(BuiltInCategory.OST_Floors).Select(f => (object)new {
    id = f.Id.Value, loai = document.GetElement(f.GetTypeId()).Name, tang = tenTang(f),
    ketCau = (f.get_Parameter(BuiltInParameter.FLOOR_PARAM_IS_STRUCTURAL)?.AsInteger() ?? 0) == 1,
    dt_m2 = r(m2(layGT(f, BuiltInParameter.HOST_AREA_COMPUTED) ?? 0)),
    day_m = r(m(layGT(document.GetElement(f.GetTypeId()), BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM) ?? layGT(f, BuiltInParameter.FLOOR_ATTR_THICKNESS_PARAM) ?? 0)),
    chu_vi_m = r(m(layGT(f, BuiltInParameter.HOST_PERIMETER_COMPUTED) ?? 0)),
    v_revit_m3 = r(m3(layGT(f, BuiltInParameter.HOST_VOLUME_COMPUTED) ?? 0))
}).ToList();

// ---- Dam, cot (b, h lay theo ten tham so family; thieu thi de null) ----
var tenB = new[] { "b", "B", "Width", "Rộng" }; var tenH = new[] { "h", "H", "Height", "Depth", "Cao" };
var dam = layLoai(BuiltInCategory.OST_StructuralFraming).Select(e => (object)new {
    id = e.Id.Value, loai = document.GetElement(e.GetTypeId()).Name, tang = tenTang(e),
    dai_m = r(m(layGT(e, BuiltInParameter.STRUCTURAL_FRAME_CUT_LENGTH) ?? 0)),
    b_m = layDai(e, new BuiltInParameter[0], tenB), h_m = layDai(e, new BuiltInParameter[0], tenH),
    v_revit_m3 = r(m3(layGT(e, BuiltInParameter.HOST_VOLUME_COMPUTED) ?? 0))
}).ToList();
var cot = layLoai(BuiltInCategory.OST_StructuralColumns).Select(e => {
    var bb = e.get_BoundingBox(null);
    return (object)new {
        id = e.Id.Value, loai = document.GetElement(e.GetTypeId()).Name, tang = tenTang(e),
        cao_m = bb != null ? r(m(bb.Max.Z - bb.Min.Z)) : 0,
        b_m = layDai(e, new BuiltInParameter[0], tenB), h_m = layDai(e, new BuiltInParameter[0], tenH),
        v_revit_m3 = r(m3(layGT(e, BuiltInParameter.HOST_VOLUME_COMPUTED) ?? 0))
    };
}).ToList();

// ---- Phong ----
var phongDs = layLoai(BuiltInCategory.OST_Rooms).OfType<Autodesk.Revit.DB.Architecture.Room>().Where(p => p.Area > 0).Select(p => (object)new {
    id = p.Id.Value, so = p.Number, ten = p.get_Parameter(BuiltInParameter.ROOM_NAME)?.AsString() ?? "",
    tang = p.Level != null ? p.Level.Name : "(khong ro)",
    dt_m2 = r(m2(p.Area)), chu_vi_m = r(m(p.Perimeter)), cao_m = r(m(p.UnboundedHeight))
}).ToList();

return new {
    file = document.PathName, tieuDe = document.Title, chiTang,
    ngayXuat = DateTime.Now.ToString("yyyy-MM-dd HH:mm"),
    tuong, san, dam, cot, phong = phongDs, cua
};
```

Ghi chú:
- Chiều dài tường lấy theo tim tường. Ở góc giao nhau có thể tính trùng. Cột "DT Revit" trong Excel dùng để đối chiếu.
- `b`, `h` của dầm và cột lấy theo tên tham số trong family. Family đặt tên khác thì thêm tên vào `tenB` / `tenH`.
- Phòng hai bên cửa lấy theo phase cuối cùng của dự án.
