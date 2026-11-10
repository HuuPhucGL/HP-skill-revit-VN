# -*- coding: utf-8 -*-
"""
Ten script : xuat_khoi_luong.py
Cong dung  : Doc file JSON so lieu trich tu Revit (doan C# trong references/csharp-khoi-luong.md)
             va lap file Excel boc khoi luong phan tho, co cong thuc, lam tron 2 so le.
Cach dung  : python xuat_khoi_luong.py <du_lieu.json> <ket_qua.xlsx> [--du-an "Ten du an"] [--dinh-muc "..."]
Ngay viet  : 2026-11-10
Ghi chu    : - So lieu goc (kich thuoc lay tu mo hinh) nhap dang so, to nen vang nhat.
             - Moi ket qua deu la cong thuc Excel, khong nhap so cung.
             - Cach tinh cop pha, trat la DE XUAT, can anh Phuc duyet theo dinh muc du an.
"""
import argparse
import json
import sys
from collections import OrderedDict

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

FONT = "Times New Roman"
F_THUONG = Font(name=FONT, size=11)
F_DAM = Font(name=FONT, size=11, bold=True)
F_TIEU_DE = Font(name=FONT, size=14, bold=True)
F_GHI_CHU = Font(name=FONT, size=10, italic=True, color="7F7F7F")
NEN_GOC = PatternFill("solid", fgColor="FFF2CC")      # so lieu goc tu mo hinh
NEN_DAU = PatternFill("solid", fgColor="D9E1F2")      # dong tieu de cot
NEN_TONG = PatternFill("solid", fgColor="E2EFDA")     # dong tong
VIEN = Border(*(Side(style="thin", color="A6A6A6"),) * 4)
CAN_GIUA = Alignment(horizontal="center", vertical="center", wrap_text=True)
CAN_TRAI = Alignment(horizontal="left", vertical="center", wrap_text=True)
SO = "#,##0.00"


def so(x):
    """Doi gia tri ve so thuc, None giu nguyen."""
    if x is None or x == "":
        return None
    try:
        return round(float(x), 4)
    except (TypeError, ValueError):
        return None


def ghi_dau_bang(ws, hang, cot_list, rong=None):
    for i, ten in enumerate(cot_list, start=1):
        c = ws.cell(row=hang, column=i, value=ten)
        c.font, c.fill, c.alignment, c.border = F_DAM, NEN_DAU, CAN_GIUA, VIEN
        if rong:
            ws.column_dimensions[get_column_letter(i)].width = rong[i - 1]
    ws.row_dimensions[hang].height = 45
    ws.freeze_panes = ws.cell(row=hang + 1, column=1)


def o(ws, hang, cot, gia_tri, goc=False, dinh_dang=None, trai=False):
    c = ws.cell(row=hang, column=cot, value=gia_tri)
    c.font, c.border = F_THUONG, VIEN
    c.alignment = CAN_TRAI if trai else CAN_GIUA
    if goc:
        c.fill = NEN_GOC
    if dinh_dang:
        c.number_format = dinh_dang
    return c


def dong_tong(ws, hang, nhan, cac_cot, tu, den, so_cot):
    for cc in range(1, so_cot + 1):
        c = ws.cell(row=hang, column=cc)
        c.fill, c.border, c.font = NEN_TONG, VIEN, F_DAM
    ws.cell(row=hang, column=2, value=nhan).alignment = CAN_TRAI
    for cc in cac_cot:
        L = get_column_letter(cc)
        c = ws.cell(row=hang, column=cc, value=f"=ROUND(SUM({L}{tu}:{L}{den}),2)" if den >= tu else 0)
        c.number_format, c.alignment = SO, CAN_GIUA


def cong_thuc_tru(lo):
    """Tao cong thuc tru o cua: =ROUND(0.9*2.2+1.2*1.5,2) va dong dien giai."""
    phan, giai = [], []
    for x in lo:
        r, c = so(x.get("rong_m")), so(x.get("cao_m"))
        if r and c:
            phan.append(f"{r:g}*{c:g}")
            giai.append(f"{x.get('ten', '')} {r:g}x{c:g}")
        else:
            giai.append(f"{x.get('ten', '')} (thieu kich thuoc - kiem tra)")
    return (f"=ROUND({'+'.join(phan)},2)" if phan else 0), "; ".join(giai)


# ----------------------------------------------------------------------------
def sheet_thong_tin(wb, du_lieu, du_an, dinh_muc):
    ws = wb.active
    ws.title = "Thong tin"
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 90
    ws["A1"] = "BẢNG BỐC TÁCH KHỐI LƯỢNG PHẦN THÔ (TRÍCH TỪ MÔ HÌNH REVIT)"
    ws["A1"].font = F_TIEU_DE
    dong = [
        ("Dự án", du_an or du_lieu.get("tieuDe", "")),
        ("File mô hình", du_lieu.get("file", "")),
        ("Phạm vi tầng", du_lieu.get("chiTang") or "Toàn công trình"),
        ("Ngày trích số liệu", du_lieu.get("ngayXuat", "")),
        ("Định mức áp dụng", dinh_muc or "CHƯA XÁC NHẬN - cần anh Phúc chọn định mức trước khi lập dự toán"),
        ("Đơn vị", "m, m², m³; làm tròn 2 số lẻ bằng hàm ROUND"),
        ("Ô nền vàng", "Số liệu gốc lấy từ mô hình Revit"),
        ("Ô không tô nền", "Công thức Excel"),
        ("Cốp pha, tô trát", "Cách tính là ĐỀ XUẤT (ghi ở từng sheet), cần anh duyệt theo định mức dự án"),
        ("Chiều dài tường", "Theo tim tường. Ở góc giao có thể tính trùng. Đối chiếu cột 'DT Revit'"),
    ]
    for i, (k, v) in enumerate(dong, start=3):
        ws.cell(row=i, column=1, value=k).font = F_DAM
        c = ws.cell(row=i, column=2, value=v)
        c.font, c.alignment = F_THUONG, CAN_TRAI
    ws["A5"].fill = NEN_GOC


def sheet_tuong(wb, tuong):
    ws = wb.create_sheet("Tuong xay")
    cot = ["STT", "Tầng", "Loại tường", "Id Revit", "Chức năng", "Dài (m)", "Cao (m)", "Dày lõi (m)",
           "DT toàn bộ (m²)\n= Dài × Cao", "DT trừ ô cửa (m²)", "Diễn giải phần trừ", "DT xây (m²)\n= toàn bộ − trừ",
           "KL xây (m³)\n= DT xây × Dày", "Trát ngoài 1 mặt (m²)\n(tường Ngoài)", "DT Revit (đối chiếu)",
           "V Revit (đối chiếu)"]
    ghi_dau_bang(ws, 1, cot, [5, 10, 22, 10, 9, 9, 9, 9, 13, 12, 38, 13, 13, 14, 11, 11])
    ds = sorted(tuong, key=lambda x: (str(x.get("tang")), str(x.get("loai"))))
    h = 2
    for i, t in enumerate(ds, start=1):
        o(ws, h, 1, i)
        o(ws, h, 2, t.get("tang"), goc=True)
        o(ws, h, 3, t.get("loai"), goc=True, trai=True)
        o(ws, h, 4, t.get("id"), goc=True)
        o(ws, h, 5, t.get("chucNang"), goc=True)
        o(ws, h, 6, so(t.get("dai_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 7, so(t.get("cao_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 8, so(t.get("day_loi_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 9, f"=ROUND(F{h}*G{h},2)", dinh_dang=SO)
        ct, giai = cong_thuc_tru(t.get("lo") or [])
        o(ws, h, 10, ct, dinh_dang=SO)
        o(ws, h, 11, giai, trai=True)
        o(ws, h, 12, f"=ROUND(I{h}-J{h},2)", dinh_dang=SO)
        o(ws, h, 13, f"=ROUND(L{h}*H{h},2)", dinh_dang=SO)
        o(ws, h, 14, f'=IF(E{h}="Ngoai",L{h},0)', dinh_dang=SO)
        o(ws, h, 15, so(t.get("dt_revit_m2")), goc=True, dinh_dang=SO)
        o(ws, h, 16, so(t.get("v_revit_m3")), goc=True, dinh_dang=SO)
        h += 1
    dong_tong(ws, h, "TỔNG", [9, 10, 12, 13, 14, 15, 16], 2, h - 1, len(cot))
    return h - 1


def sheet_be_tong(wb, san, dam, cot):
    ws = wb.create_sheet("Be tong")
    ten_cot = ["STT", "Cấu kiện", "Loại", "Id Revit", "Tầng", "Dài / DT (m | m²)", "b / Dày (m)", "h (m)",
               "Cao cột (m)", "V bê tông (m³)", "Cốp pha (m²)\n(ĐỀ XUẤT)", "Diễn giải", "V Revit (đối chiếu)"]
    ghi_dau_bang(ws, 1, ten_cot, [5, 9, 24, 10, 10, 12, 10, 9, 9, 12, 13, 46, 12])
    h, stt = 2, 1

    def chung(loai_ck, x):
        nonlocal stt
        o(ws, h, 1, stt)
        o(ws, h, 2, loai_ck)
        o(ws, h, 3, x.get("loai"), goc=True, trai=True)
        o(ws, h, 4, x.get("id"), goc=True)
        o(ws, h, 5, x.get("tang"), goc=True)
        o(ws, h, 13, so(x.get("v_revit_m3")), goc=True, dinh_dang=SO)
        stt += 1

    for x in sorted(san, key=lambda a: str(a.get("tang"))):
        chung("Sàn", x)
        o(ws, h, 6, so(x.get("dt_m2")), goc=True, dinh_dang="0.000")
        o(ws, h, 7, so(x.get("day_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 10, f"=ROUND(F{h}*G{h},2)", dinh_dang=SO)
        o(ws, h, 11, f"=ROUND(F{h},2)", dinh_dang=SO)
        ghi = "V = DT × dày. Cốp pha đáy sàn = DT sàn, chưa trừ phần dầm/cột chiếm chỗ"
        if not x.get("ketCau"):
            ghi += ". LƯU Ý: sàn không đánh dấu kết cấu, kiểm tra có phải lớp hoàn thiện"
        o(ws, h, 12, ghi, trai=True)
        h += 1
    for x in sorted(dam, key=lambda a: str(a.get("tang"))):
        chung("Dầm", x)
        o(ws, h, 6, so(x.get("dai_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 7, so(x.get("b_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 8, so(x.get("h_m")), goc=True, dinh_dang="0.000")
        if so(x.get("b_m")) and so(x.get("h_m")):
            o(ws, h, 10, f"=ROUND(F{h}*G{h}*H{h},2)", dinh_dang=SO)
            o(ws, h, 11, f"=ROUND(F{h}*(G{h}+2*H{h}),2)", dinh_dang=SO)
            o(ws, h, 12, "V = L × b × h. Cốp pha = L × (b + 2h), chưa trừ phần sàn gối lên dầm", trai=True)
        else:
            o(ws, h, 10, f"=ROUND(M{h},2)", dinh_dang=SO)
            o(ws, h, 11, None)
            o(ws, h, 12, "THIẾU b/h trong family: V lấy theo Revit, cốp pha cần nhập tay", trai=True)
        h += 1
    for x in sorted(cot, key=lambda a: str(a.get("tang"))):
        chung("Cột", x)
        o(ws, h, 7, so(x.get("b_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 8, so(x.get("h_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 9, so(x.get("cao_m")), goc=True, dinh_dang="0.000")
        if so(x.get("b_m")) and so(x.get("h_m")):
            o(ws, h, 10, f"=ROUND(G{h}*H{h}*I{h},2)", dinh_dang=SO)
            o(ws, h, 11, f"=ROUND(2*(G{h}+H{h})*I{h},2)", dinh_dang=SO)
            o(ws, h, 12, "V = b × h × H. Cốp pha = 2(b + h) × H, chưa trừ phần dầm/sàn giao", trai=True)
        else:
            o(ws, h, 10, f"=ROUND(M{h},2)", dinh_dang=SO)
            o(ws, h, 11, None)
            o(ws, h, 12, "THIẾU b/h trong family: V lấy theo Revit, cốp pha cần nhập tay", trai=True)
        h += 1
    dong_tong(ws, h, "TỔNG", [10, 11, 13], 2, h - 1, len(ten_cot))
    return h - 1


def sheet_hoan_thien(wb, phong, cua):
    ws = wb.create_sheet("Hoan thien")
    ten_cot = ["STT", "Số phòng", "Tên phòng", "Tầng", "DT sàn (m²)", "Chu vi (m)", "Cao (m)",
               "Lát nền (m²)\n= DT", "Trát trần (m²)\n= DT", "Trát tường trong\ntoàn bộ (m²)\n= Chu vi × Cao",
               "Trừ ô cửa (m²)", "Diễn giải phần trừ", "Trát tường trong\n(m²)"]
    ghi_dau_bang(ws, 1, ten_cot, [5, 9, 20, 10, 11, 10, 9, 11, 11, 14, 11, 40, 13])
    theo_phong = {}
    for c in cua:
        for pid in c.get("phong") or []:
            theo_phong.setdefault(pid, []).append({"ten": c.get("loai", "").split(" : ")[-1],
                                                   "rong_m": c.get("rong_m"), "cao_m": c.get("cao_m")})
    h = 2
    for i, p in enumerate(sorted(phong, key=lambda a: (str(a.get("tang")), str(a.get("so")))), start=1):
        o(ws, h, 1, i)
        o(ws, h, 2, p.get("so"), goc=True)
        o(ws, h, 3, p.get("ten"), goc=True, trai=True)
        o(ws, h, 4, p.get("tang"), goc=True)
        o(ws, h, 5, so(p.get("dt_m2")), goc=True, dinh_dang="0.000")
        o(ws, h, 6, so(p.get("chu_vi_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 7, so(p.get("cao_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 8, f"=ROUND(E{h},2)", dinh_dang=SO)
        o(ws, h, 9, f"=ROUND(E{h},2)", dinh_dang=SO)
        o(ws, h, 10, f"=ROUND(F{h}*G{h},2)", dinh_dang=SO)
        ct, giai = cong_thuc_tru(theo_phong.get(p.get("id"), []))
        o(ws, h, 11, ct, dinh_dang=SO)
        o(ws, h, 12, giai, trai=True)
        o(ws, h, 13, f"=ROUND(J{h}-K{h},2)", dinh_dang=SO)
        h += 1
    dong_tong(ws, h, "TỔNG", [5, 8, 9, 10, 11, 13], 2, h - 1, len(ten_cot))
    g = ws.cell(row=h + 2, column=2, value="Ghi chú: cao trát lấy theo chiều cao phòng trong Revit (Unbounded Height). "
                                         "Trát trần = DT phòng, lát nền = DT phòng: ĐỀ XUẤT, cần anh duyệt.")
    g.font = F_GHI_CHU
    return h - 1


def sheet_cua(wb, cua):
    ws = wb.create_sheet("Cua")
    ten_cot = ["STT", "Nhóm", "Loại cửa", "Tầng", "Id Revit", "Rộng (m)", "Cao (m)", "DT 1 cửa (m²)"]
    ghi_dau_bang(ws, 1, ten_cot, [5, 9, 34, 10, 10, 9, 9, 12])
    h = 2
    for i, c in enumerate(sorted(cua, key=lambda a: (a.get("nhom", ""), a.get("loai", ""), str(a.get("tang")))), start=1):
        o(ws, h, 1, i)
        o(ws, h, 2, c.get("nhom"), goc=True)
        o(ws, h, 3, c.get("loai"), goc=True, trai=True)
        o(ws, h, 4, c.get("tang"), goc=True)
        o(ws, h, 5, c.get("id"), goc=True)
        o(ws, h, 6, so(c.get("rong_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 7, so(c.get("cao_m")), goc=True, dinh_dang="0.000")
        o(ws, h, 8, f"=ROUND(F{h}*G{h},2)", dinh_dang=SO)
        h += 1
    return h - 1


def sheet_tong_hop(wb, tuong, cua, phong, cuoi):
    ws = wb.create_sheet("Tong hop", 1)
    ws["A1"] = "TỔNG HỢP KHỐI LƯỢNG PHẦN THÔ"
    ws["A1"].font = F_TIEU_DE
    ghi_dau_bang(ws, 3, ["STT", "Hạng mục", "Đơn vị", "Khối lượng", "Cách lấy số"], [6, 46, 9, 14, 60])
    ws.freeze_panes = None
    h, stt = 4, 1

    def dong(ten, dv, ct, cach):
        nonlocal h, stt
        o(ws, h, 1, stt)
        o(ws, h, 2, ten, trai=True)
        o(ws, h, 3, dv)
        o(ws, h, 4, ct, dinh_dang=SO)
        o(ws, h, 5, cach, trai=True)
        h += 1
        stt += 1

    nt = cuoi["tuong"]
    for loai in OrderedDict.fromkeys(sorted(str(t.get("loai")) for t in tuong)):
        dong(f"Xây {loai}", "m³", f"=ROUND(SUMIF('Tuong xay'!C2:C{nt},\"{loai}\",'Tuong xay'!M2:M{nt}),2)",
             "Tổng cột KL xây theo loại tường (đã trừ ô cửa)")
        dong(f"Diện tích xây {loai}", "m²", f"=ROUND(SUMIF('Tuong xay'!C2:C{nt},\"{loai}\",'Tuong xay'!L2:L{nt}),2)",
             "Tổng cột DT xây theo loại tường")
    nb = cuoi["be_tong"]
    for ck in ["Sàn", "Dầm", "Cột"]:
        dong(f"Bê tông {ck.lower()}", "m³", f"=ROUND(SUMIF('Be tong'!B2:B{nb},\"{ck}\",'Be tong'!J2:J{nb}),2)",
             f"Tổng V bê tông cấu kiện {ck.lower()}")
        dong(f"Cốp pha {ck.lower()} (đề xuất)", "m²", f"=ROUND(SUMIF('Be tong'!B2:B{nb},\"{ck}\",'Be tong'!K2:K{nb}),2)",
             "Theo cách tính đề xuất ở sheet Be tong, cần anh duyệt")
    nh = cuoi["hoan_thien"]
    dong("Trát tường trong", "m²", f"=ROUND(SUM('Hoan thien'!M2:M{nh}),2)", "Chu vi phòng × cao − ô cửa (đề xuất)")
    dong("Trát tường ngoài", "m²", f"=ROUND(SUM('Tuong xay'!N2:N{nt}),2)", "DT xây 1 mặt của tường chức năng Ngoài")
    dong("Trát trần", "m²", f"=ROUND(SUM('Hoan thien'!I2:I{nh}),2)", "Bằng DT phòng (đề xuất)")
    dong("Lát nền", "m²", f"=ROUND(SUM('Hoan thien'!H2:H{nh}),2)", "Bằng DT phòng (đề xuất)")
    nc = cuoi["cua"]
    for nhom, ten in [("Cua di", "Cửa đi"), ("Cua so", "Cửa sổ")]:
        dong(f"{ten} - số bộ", "bộ", f"=COUNTIF(Cua!B2:B{nc},\"{nhom}\")", "Đếm theo sheet Cua")
        dong(f"{ten} - diện tích", "m²", f"=ROUND(SUMIF(Cua!B2:B{nc},\"{nhom}\",Cua!H2:H{nc}),2)", "Rộng × cao từng cửa")
    for tang in OrderedDict.fromkeys(sorted(str(p.get("tang")) for p in phong)):
        dong(f"Diện tích phòng {tang}", "m²", f"=ROUND(SUMIF('Hoan thien'!D2:D{nh},\"{tang}\",'Hoan thien'!E2:E{nh}),2)",
             "Tổng DT phòng của tầng (lấy từ Room)")


def main():
    ap = argparse.ArgumentParser(description="Lap Excel boc khoi luong tu JSON trich tu Revit")
    ap.add_argument("json_vao")
    ap.add_argument("xlsx_ra")
    ap.add_argument("--du-an", default="")
    ap.add_argument("--dinh-muc", default="")
    a = ap.parse_args()

    with open(a.json_vao, encoding="utf-8-sig") as f:
        du_lieu = json.load(f)
    # Ket qua send_code_to_revit co the la chuoi JSON long trong JSON
    if isinstance(du_lieu, dict) and isinstance(du_lieu.get("result"), str):
        du_lieu = json.loads(du_lieu["result"])
    if isinstance(du_lieu, str):
        du_lieu = json.loads(du_lieu)

    tuong, san, dam, cot = (du_lieu.get(k) or [] for k in ("tuong", "san", "dam", "cot"))
    phong, cua = du_lieu.get("phong") or [], du_lieu.get("cua") or []

    wb = Workbook()
    sheet_thong_tin(wb, du_lieu, a.du_an, a.dinh_muc)
    cuoi = {
        "tuong": max(sheet_tuong(wb, tuong), 2),
        "be_tong": max(sheet_be_tong(wb, san, dam, cot), 2),
        "hoan_thien": max(sheet_hoan_thien(wb, phong, cua), 2),
        "cua": max(sheet_cua(wb, cua), 2),
    }
    sheet_tong_hop(wb, tuong, cua, phong, cuoi)
    for ws in wb.worksheets:
        ws.page_setup.paperSize = ws.PAPERSIZE_A3
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToHeight = 0
    wb.save(a.xlsx_ra)
    print(f"Da ghi: {a.xlsx_ra}")
    print(f"Tuong: {len(tuong)} | San: {len(san)} | Dam: {len(dam)} | Cot: {len(cot)} | Phong: {len(phong)} | Cua: {len(cua)}")


if __name__ == "__main__":
    sys.exit(main())
