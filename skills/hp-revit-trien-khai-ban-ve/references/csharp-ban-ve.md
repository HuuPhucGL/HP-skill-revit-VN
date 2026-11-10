# Mã C# triển khai bản vẽ (Revit 2024)

Thân hàm `Execute(Document document, object[] parameters)`. Đã có Transaction bao ngoài.
Phải hỏi anh Phúc trước khi gửi. Sửa phần "THAM SO" ở đầu mỗi đoạn theo danh mục anh đã duyệt.

---

## 1. Tạo / đổi tên mặt bằng theo Level, tỷ lệ 1/50

```csharp
// THAM SO: ten Level -> ten view
var dsView = new Dictionary<string, string> {
    { "TẦNG 1", "MB TẦNG 1" },
    { "TẦNG 2", "MB TẦNG 2" }
};
int tyLe = 50;

var vft = new FilteredElementCollector(document).OfClass(typeof(ViewFamilyType)).Cast<ViewFamilyType>()
    .First(t => t.ViewFamily == ViewFamily.FloorPlan);
var levels = new FilteredElementCollector(document).OfClass(typeof(Level)).Cast<Level>().ToList();
var plans = new FilteredElementCollector(document).OfClass(typeof(ViewPlan)).Cast<ViewPlan>()
    .Where(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan).ToList();

var ketQua = new List<object>();
foreach (var kv in dsView)
{
    var lv = levels.FirstOrDefault(l => l.Name == kv.Key);
    if (lv == null) { ketQua.Add(new { level = kv.Key, trangThai = "khong co level" }); continue; }
    // Uu tien view mat bang co san cua level (tranh tao trung)
    var v = plans.FirstOrDefault(p => p.Name == kv.Value) ?? plans.FirstOrDefault(p => p.GenLevel != null && p.GenLevel.Id == lv.Id);
    string trangThai = "doi ten";
    if (v == null) { v = ViewPlan.Create(document, vft.Id, lv.Id); trangThai = "tao moi"; }
    if (v.Name != kv.Value) v.Name = kv.Value;
    v.Scale = tyLe;
    ketQua.Add(new { level = kv.Key, view = v.Name, id = v.Id.Value, trangThai });
}
return ketQua;
```

## 2. Đổi tên mặt đứng có sẵn, tỷ lệ 1/50

```csharp
// THAM SO: ten cu -> ten moi (hoi anh mat dung nao ung voi truc nao)
var doiTen = new Dictionary<string, string> {
    { "South", "MẶT ĐỨNG TRỤC 1-5" },
    { "North", "MẶT ĐỨNG TRỤC 5-1" }
};
var ketQua = new List<object>();
foreach (var v in new FilteredElementCollector(document).OfClass(typeof(ViewSection)).Cast<ViewSection>()
    .Where(x => !x.IsTemplate && x.ViewType == ViewType.Elevation))
{
    if (!doiTen.ContainsKey(v.Name)) continue;
    string cu = v.Name;
    v.Name = doiTen[cu];
    v.Scale = 50;
    ketQua.Add(new { cu, moi = v.Name, id = v.Id.Value });
}
return ketQua;
```

## 3. Tạo mặt cắt theo đường cắt 2 điểm (mm)

```csharp
// THAM SO: duong cat (mm), cao do day / dinh vung nhin (mm), chieu sau nhin (mm), ten
double x1 = 0, y1 = 10000, x2 = 5000, y2 = 10000;
double zDuoi = -1000, zTren = 12000, sauNhin = 3000;
string ten = "MẶT CẮT A-A";

Func<double, double> ft = v => UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters);
var p1 = new XYZ(ft(x1), ft(y1), 0); var p2 = new XYZ(ft(x2), ft(y2), 0);
var huong = (p2 - p1).Normalize();          // truc X cua mat cat
var len = XYZ.BasisZ;                        // truc Y = phuong dung
var nhin = huong.CrossProduct(len);          // huong nhin
double nuaDai = p1.DistanceTo(p2) / 2;

var t = Transform.Identity;
t.Origin = (p1 + p2) / 2; t.BasisX = huong; t.BasisY = len; t.BasisZ = nhin;
var box = new BoundingBoxXYZ {
    Transform = t,
    Min = new XYZ(-nuaDai, ft(zDuoi), 0),
    Max = new XYZ(nuaDai, ft(zTren), ft(sauNhin))
};
var vft = new FilteredElementCollector(document).OfClass(typeof(ViewFamilyType)).Cast<ViewFamilyType>()
    .First(x => x.ViewFamily == ViewFamily.Section);
var vs = ViewSection.CreateSection(document, vft.Id, box);
vs.Name = ten; vs.Scale = 50;
return new { id = vs.Id.Value, ten = vs.Name };
```

Mặt cắt nhìn sai phía thì đổi thứ tự hai điểm (x1,y1) ↔ (x2,y2).

## 4. Tag cửa đi và cửa sổ trên view đang mở

```csharp
var view = document.ActiveView;
var daTag = new HashSet<long>(new FilteredElementCollector(document, view.Id).OfClass(typeof(IndependentTag))
    .Cast<IndependentTag>().SelectMany(t => t.GetTaggedLocalElementIds()).Select(id => id.Value));
var cua = new FilteredElementCollector(document, view.Id).WherePasses(new LogicalOrFilter(
        new ElementCategoryFilter(BuiltInCategory.OST_Doors), new ElementCategoryFilter(BuiltInCategory.OST_Windows)))
    .WhereElementIsNotElementType().Cast<FamilyInstance>().ToList();
int dem = 0; var loi = new List<string>();
foreach (var c in cua)
{
    if (daTag.Contains(c.Id.Value)) continue;          // da co tag thi bo qua
    var lp = c.Location as LocationPoint;
    if (lp == null) continue;
    try {
        IndependentTag.Create(document, view.Id, new Reference(c), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, lp.Point);
        dem++;
    } catch (Exception ex) { loi.Add(c.Id.Value + ": " + ex.Message); }
}
return new { view = view.Name, soCua = cua.Count, daTagMoi = dem, loi };
```

Lỗi "no tag loaded" nghĩa là file chưa có family tag cửa. Báo anh nạp tag (Insert → Load Family →
Annotations → Door Tag / Window Tag).

## 5. Tạo sheet A3, khung tên TẠM, đặt view vào giữa

```csharp
// THAM SO: so hieu, ten sheet, ten view dat len
var ds = new List<Tuple<string, string, string>> {
    Tuple.Create("KT-01", "MẶT BẰNG TẦNG 1", "MB TẦNG 1"),
    Tuple.Create("KT-02", "MẶT BẰNG TẦNG 2", "MB TẦNG 2")
};
string ghiChuTam = "TAM - thay khung ten GH.A3";

// Tim khung ten A3 co trong file
var tb = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_TitleBlocks)
    .WhereElementIsElementType().Cast<FamilySymbol>()
    .FirstOrDefault(s => (s.FamilyName + " " + s.Name).ToUpper().Contains("A3"));
if (tb == null) return new { loi = "Khong co khung ten A3 trong file. Hoi anh Phuc nap file .rfa hay tao sheet khong khung ten." };

var sheetCo = new FilteredElementCollector(document).OfClass(typeof(ViewSheet)).Cast<ViewSheet>().ToList();
var views = new FilteredElementCollector(document).OfClass(typeof(View)).Cast<View>().Where(v => !v.IsTemplate).ToList();
var ketQua = new List<object>();
foreach (var d in ds)
{
    if (sheetCo.Any(s => s.SheetNumber == d.Item1)) { ketQua.Add(new { so = d.Item1, trangThai = "so hieu da ton tai, bo qua" }); continue; }
    var sh = ViewSheet.Create(document, tb.Id);
    sh.SheetNumber = d.Item1; sh.Name = d.Item2;

    // Danh dau khung ten TAM vao Comments
    var tbInst = new FilteredElementCollector(document, sh.Id).OfCategory(BuiltInCategory.OST_TitleBlocks)
        .WhereElementIsNotElementType().FirstElement();
    if (tbInst != null) tbInst.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)?.Set(ghiChuTam);

    // Dat view vao giua khung ten
    var v = views.FirstOrDefault(x => x.Name == d.Item3);
    string vp = "khong tim thay view";
    if (v != null)
    {
        if (!Viewport.CanAddViewToSheet(document, sh.Id, v.Id)) vp = "view da nam tren sheet khac";
        else
        {
            document.Regenerate();
            var bb = tbInst != null ? tbInst.get_BoundingBox(sh) : null;
            var tam = bb != null ? (bb.Min + bb.Max) / 2 : XYZ.Zero;
            Viewport.Create(document, sh.Id, v.Id, new XYZ(tam.X, tam.Y, 0));
            vp = "da dat";
        }
    }
    ketQua.Add(new { so = sh.SheetNumber, ten = sh.Name, khungTen = tb.FamilyName + " : " + tb.Name, view = d.Item3, viewport = vp, id = sh.Id.Value });
}
return ketQua;
```

## 6. Thay khung tên TẠM bằng khung tên chính thức

```csharp
// THAM SO: ten family khung ten moi (sau khi anh da nap vao file)
string familyMoi = "GH.A3";
var moi = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_TitleBlocks)
    .WhereElementIsElementType().Cast<FamilySymbol>().FirstOrDefault(s => s.FamilyName == familyMoi);
if (moi == null) return new { loi = "Chua nap family " + familyMoi };
if (!moi.IsActive) moi.Activate();

var doi = new List<object>();
foreach (var inst in new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_TitleBlocks)
    .WhereElementIsNotElementType().Cast<FamilyInstance>())
{
    var p = inst.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS);
    if (p == null || p.AsString() == null || !p.AsString().StartsWith("TAM")) continue;
    inst.ChangeTypeId(moi.Id);
    p.Set("");
    var sh = document.GetElement(inst.OwnerViewId) as ViewSheet;
    doi.Add(new { sheet = sh != null ? sh.SheetNumber : "?", id = inst.Id.Value });
}
return new { daThay = doi.Count, doi };
```
