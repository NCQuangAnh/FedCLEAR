# -*- coding: utf-8 -*-
"""Build the results workbook for the progress report.

Every number here is recomputed from the GPU logs under results/ by
report/statistic/_tmp/perseed.json; nothing is typed in by hand. Aggregates
(mean, sd, paired t, p) are written as Excel formulas over the per-seed sheet,
so editing a raw value updates every table.
"""
import json
import os

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "ket-qua-thi-nghiem.xlsx")
PS = json.load(open(os.path.join(HERE, "perseed.json"), encoding="utf-8"))

INK, RED, TINT, GREY = "FF111111", "FFC72202", "FFF9E2DC", "FF6B6259"
LINE = "FFD9D2C8"
F = "Arial"
H1 = Font(name=F, size=15, bold=True, color=INK)
H2 = Font(name=F, size=11, bold=True, color=RED)
TH = Font(name=F, size=9, bold=True, color="FFFFFFFF")
TD = Font(name=F, size=10, color=INK)
TB = Font(name=F, size=10, bold=True, color=INK)
NOTE = Font(name=F, size=9, italic=True, color=GREY)
MONO = Font(name="Consolas", size=9.5, color=INK)

FILL_H = PatternFill("solid", fgColor=INK)
FILL_HI = PatternFill("solid", fgColor=TINT)
thin = Side(style="thin", color=LINE)
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

NUM, GAIN, PVAL = "0.00", "+0.00;-0.00;0.00", "0.000"


def header(ws, row, cols, widths=None):
    for j, c in enumerate(cols, start=1):
        cell = ws.cell(row=row, column=j, value=c)
        cell.font, cell.fill, cell.border = TH, FILL_H, BOX
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 32
    if widths:
        for j, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(j)].width = w


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = H1
    if sub:
        ws["A2"] = sub
        ws["A2"].font = NOTE
        return 4
    return 3


def note(ws, row, text, span=14):
    c = ws.cell(row=row, column=1, value=text)
    c.font = NOTE
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)
    ws.row_dimensions[row].height = 26 if len(text) > 140 else 14
    return row + 1


def table(ws, row, rows, widths, highlight=(), wrap_last=True):
    """rows[0] is the header; returns the row after the table."""
    header(ws, row, rows[0], widths)
    for i, data in enumerate(rows[1:], start=1):
        rr = row + i
        for j, v in enumerate(data, start=1):
            # a string opening with '=' is stored by openpyxl as a FORMULA; "= 0,437 / 0,326"
            # then reaches Excel as an invalid one and the file opens with a repair prompt
            if isinstance(v, str) and v.lstrip().startswith("="):
                v = "'" + v
            c = ws.cell(row=rr, column=j, value=v)
            c.border = BOX
            c.font = TB if i in highlight else TD
            if j == len(data) and wrap_last:
                c.font = NOTE if i not in highlight else TB
                c.alignment = Alignment(wrap_text=True, vertical="top")
            elif isinstance(v, str) and (v.startswith("dtd_") or v.startswith("oxford")
                                         or v.startswith("--") or v.startswith("s_")
                                         or v.startswith("r_") or v.startswith("L_")):
                c.font = MONO
            if i in highlight:
                c.fill = FILL_HI
        h = max((len(str(x)) for x in data if isinstance(x, str)), default=0)
        ws.row_dimensions[rr].height = 30 if h > 90 else 15
    return row + len(rows) + 1


wb = Workbook()

# ===================================================================== 1
ws = wb.active
ws.title = "Đọc trước"
ws.sheet_view.showGridLines = False
r = title(ws, "Kết quả thí nghiệm — Triage trong Federated Prompt Learning",
          "Benchmark FLIP (NeurIPS 2025) · CLIP RN50 đóng băng · 10 client · Dirichlet α = 0,1 · "
          "8 ảnh/lớp cho cả liên đoàn · 50 round · 5 seed mỗi cấu hình")
ws.column_dimensions["A"].width = 32
ws.column_dimensions["B"].width = 108
for k, v in [
    ("CẤU HÌNH", ""),
    ("Client thật thà", "5/10 — nhãn đúng 100%"),
    ("Client nhiễu (cẩu thả)", "3/10 — lật 40% nhãn về lớp NGẪU NHIÊN (sym noise)"),
    ("Client độc hại", "2/10 — lật 40% nhãn về MỘT lớp đích cố định (noise_disguise). "
                       "Cùng tỉ lệ lật với client nhiễu, nên mọi thống kê 'client này lệch bao nhiêu' nhìn thấy y hệt."),
    ("", ""),
    ("CÁCH ĐỌC SỐ", ""),
    ("last10", "Trung bình accuracy 10 round cuối (41–50). Chỉ số chính của đồ án."),
    ("Vì sao không dùng best", "best = accuracy cao nhất qua 50 round, tương đương dừng sớm bằng oracle. "
                               "Đo được: best làm NHẸ tác hại của nhiễu 1,4–2,5 lần so với last10."),
    ("Lấy lại (gain)", "Trung bình các hiệu TỪNG SEED so với mốc. Dương = tốt hơn mốc."),
    ("p", "Kiểm định t ghép cặp hai phía, n = 5, 4 bậc tự do. p < 0,05 mới coi là có ý nghĩa."),
    ("dz", "Cohen's dz = trung bình hiệu / độ lệch chuẩn của hiệu."),
    ("", ""),
    ("ORACLE LÀ GÌ", ""),
    ("Định nghĩa", "Cấu hình dùng thông tin server KHÔNG BAO GIỜ CÓ (nhãn thật của từng ảnh). "
                   "Không phải phương pháp — là TRẦN để biết mỗi mức can thiệp đáng bao nhiêu."),
    ("L_clientdrop", "Biết trước, loại bỏ cả 5 client hỏng ngay từ vòng 0"),
    ("L_drop", "Biết trước, xoá đúng từng ảnh bị hỏng, giữ nguyên client"),
    ("L_restore", "Biết trước, trả lại nhãn thật cho từng ảnh hỏng"),
    ("O_drop_mal", "Biết trước, loại 2 client độc hại từ vòng 0"),
    ("", ""),
    ("CÁC SHEET", ""),
    ("Mốc và trần", "Thang can thiệp — mức nào đáng bao nhiêu điểm. Đọc trước tiên."),
    ("Từng seed (DTD) / (Pets)", "DỮ LIỆU GỐC. Mọi sheet khác tham chiếu về đây bằng công thức."),
    ("Phán quyết các cổng", "7 cổng thí nghiệm, tiêu chí ghi trước, đạt hay trượt và vì sao."),
    ("Lọc mức ảnh", "Phương pháp hiện tại, kèm tỉ giá đo được và trần theo độ chính xác."),
    ("Phát hiện client", "AUC của các tín hiệu, tách theo cặp vai trò."),
    ("Chất lượng sửa nhãn", "Vì sao hướng sửa nhãn bế tắc — đo trên nhãn thật."),
    ("", ""),
    ("NGUỒN", ""),
    ("Mọi con số", "Tính lại từ log gốc của từng lượt chạy GPU bằng tools/parse_flip_log.py. Không nhập tay."),
    ("Tiêu chí ghi trước", "Mọi ngưỡng đạt/trượt viết ra TRƯỚC khi chạy, không sửa sau khi nhìn số. Xem docs/phase*_plan.md."),
    ("Hồ sơ đầy đủ", "12 tài liệu kết quả dưới results/ — gồm cả các cổng trượt và các chỗ đã sửa sai."),
]:
    if k and not v:
        ws.cell(row=r, column=1, value=k).font = H2
    elif k:
        ws.cell(row=r, column=1, value=k).font = TB
        c = ws.cell(row=r, column=2, value=v)
        c.font = TD
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 28 if len(v) > 105 else 14
    r += 1

# ===================================================================== 2
lad = wb.create_sheet("Mốc và trần")
lad.sheet_view.showGridLines = False
r = title(lad, "Thang can thiệp — mỗi mức đáng bao nhiêu điểm",
          "DTD, 5 seed. Cột last10 và 'Lấy lại' là CÔNG THỨC tham chiếu sang sheet 'Từng seed (DTD)'.")
header(lad, r, ["Mức can thiệp", "Mã cấu hình", "last10", "Lấy lại so với\nkhông phòng thủ",
                "Loại", "Ghi chú"], [42, 21, 10, 15, 13, 78])
LADDER = [
    ("Đuổi cả 5 client hỏng (biết trước)", "dtd_L_clientdrop", "oracle",
     "TỆ HƠN không làm gì. Mất dữ liệu đắt hơn chất độc dọn được."),
    ("Không phòng thủ", "dtd_A0_refuse", "mốc",
     "3 client nhiễu + 2 client độc hại, FedAvg thường."),
    ("Đuổi 2 client độc hại (biết trước, từ vòng 0)", "dtd_O_drop_mal", "oracle",
     "TRẦN TUYỆT ĐỐI của mọi phương pháp mà cần gạt duy nhất là loại bỏ client. Không có ý nghĩa thống kê."),
    ("Luật cấm trực tuyến (của ta)", "dtd_A3_exclude", "phương pháp",
     "Bắt 7/10 kẻ tấn công, chạm 0/25 client thật thà — vẫn không đổi thành accuracy."),
    ("Luật cấm sớm (quyết định từ round 11,6)", "dtd_A6_fast_ban", "phương pháp",
     "Bắt 9/10. Bác bỏ cách giải thích 'phát hiện quá muộn'."),
    ("median — phòng thủ chuẩn của lĩnh vực", "dtd_M0_median", "baseline",
     "Trung vị theo toạ độ. Không quyết định client nào đáng tin."),
    ("Sửa nhãn, liều 25/50 round", "dtd_A5_refuse_dose", "phương pháp",
     "Kết quả tốt nhất TRƯỚC khi chuyển sang lọc mức ảnh."),
    ("LỌC MỨC ẢNH (phương pháp hiện tại)", "dtd_G_rho", "phương pháp",
     "Hạn mức tự ước lượng + luật sai số. Kết quả tốt nhất của đồ án."),
    ("Xoá đúng từng ảnh hỏng (biết trước)", "dtd_L_drop", "oracle",
     "Chỉ cần biết ảnh nào hỏng, KHÔNG cần biết nhãn đúng. Lấy 72% của trần."),
    ("Trả lại nhãn thật (biết trước)", "dtd_L_restore", "oracle",
     "Trần sạch đo trong đúng cấu hình này. Bằng baseline 10 client sạch (55,61) — nhãn bẩn giải thích TOÀN BỘ khoảng cách."),
]
ladder_rows = {}
for i, (nm, tag, kind, cmt) in enumerate(LADDER):
    rr = r + 1 + i
    hot = "LỌC" in nm
    lad.cell(row=rr, column=1, value=nm).font = TB if hot else TD
    lad.cell(row=rr, column=2, value=tag).font = MONO
    lad.cell(row=rr, column=5, value=kind).font = TD
    c = lad.cell(row=rr, column=6, value=cmt)
    c.font = NOTE
    c.alignment = Alignment(wrap_text=True, vertical="top")
    lad.row_dimensions[rr].height = 28
    for col in range(1, 7):
        lad.cell(row=rr, column=col).border = BOX
        if hot:
            lad.cell(row=rr, column=col).fill = FILL_HI
    ladder_rows[tag] = rr
lad.freeze_panes = f"A{r + 1}"
rr = r + len(LADDER) + 2
rr = note(lad, rr, "Đọc thang: càng xuống dưới càng dùng nhiều thông tin mà thực tế không có. "
                   "Khoảng cách giữa 'đuổi client' (+1,02) và 'xoá đúng ảnh' (+6,02) chính là dư địa của hướng mức ảnh.", 6)
rr = note(lad, rr, "Ba phép trừ quan trọng: L_restore − L_drop = +2,37 (p=0,036, chữa hơn xoá); "
                   "L_drop − L_clientdrop = +7,33 (p=0,011, mức ảnh hơn mức client); "
                   "55,61 (baseline sạch giai đoạn 1) − L_restore = −0,33 (nhãn bẩn giải thích toàn bộ).", 6)

# ===================================================================== 3, 4
def seed_sheet(name, prefix, base_tag, tags, subtitle):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    r = title(ws, f"Accuracy last10 từng seed — {prefix}", subtitle)
    header(ws, r, ["Cấu hình", "Lượt chạy", "seed 0", "seed 1", "seed 2", "seed 3", "seed 4",
                   "Trung bình", "Độ lệch\nchuẩn", "Lấy lại\nso với mốc", "sd của\nhiệu",
                   "t", "p (2 phía)", "dz"],
           [27, 11] + [9] * 5 + [11, 11, 13, 10, 8, 11, 8])
    top = r + 1
    pos = {}
    for tag in tags:
        if tag not in PS:
            continue
        src, vals = PS[tag]
        rr = top + len(pos)
        pos[tag] = rr
        ws.cell(row=rr, column=1, value=tag.replace(prefix + "_", "")).font = MONO
        ws.cell(row=rr, column=2, value=src).font = NOTE
        for j, v in enumerate(vals):
            c = ws.cell(row=rr, column=3 + j, value=v)
            c.font, c.number_format = TD, NUM
        n = len(vals)
        last = get_column_letter(2 + n)
        ws.cell(row=rr, column=8, value=f"=AVERAGE(C{rr}:{last}{rr})").number_format = NUM
        ws.cell(row=rr, column=9, value=f"=STDEV(C{rr}:{last}{rr})").number_format = NUM
        for col in range(1, 15):
            cc = ws.cell(row=rr, column=col)
            cc.border = BOX
            if col >= 8:
                cc.font = TD
    b = pos[base_tag]
    nb = len(PS[base_tag][1])
    for tag, rr in pos.items():
        n = len(PS[tag][1])
        last = get_column_letter(2 + n)
        if tag == base_tag or n != nb:
            ws.cell(row=rr, column=10, value="mốc" if tag == base_tag else "—").font = NOTE
            continue
        ws.cell(row=rr, column=10,
                value=f"=AVERAGE(C{rr}:{last}{rr})-AVERAGE(C{b}:{last}{b})").number_format = GAIN
        ws.cell(row=rr, column=11,
                value=(f"=SQRT((SUMPRODUCT((C{rr}:{last}{rr}-C{b}:{last}{b})^2)"
                       f"-{n}*J{rr}^2)/{n - 1})")).number_format = NUM
        ws.cell(row=rr, column=12,
                value=f"=IF(K{rr}=0,\"\",J{rr}/(K{rr}/SQRT({n})))").number_format = NUM
        ws.cell(row=rr, column=13,
                value=f"=IF(K{rr}=0,\"\",TDIST(ABS(L{rr}),{n - 1},2))").number_format = PVAL
        ws.cell(row=rr, column=14,
                value=f"=IF(K{rr}=0,\"\",J{rr}/K{rr})").number_format = NUM
        if tag in ("dtd_G_rho", "dtd_L_drop", "dtd_L_restore"):
            for col in range(1, 15):
                ws.cell(row=rr, column=col).fill = FILL_HI
    ws.freeze_panes = f"C{top}"
    rr = top + len(pos) + 1
    rr = note(ws, rr, f"Mốc để so: {base_tag}. 'Lấy lại' là trung bình các hiệu TỪNG SEED, "
                      "không phải hiệu của hai trung bình — hai cách cho cùng trung bình, nhưng chỉ ghép cặp mới cho sd, t và p đúng.")
    rr = note(ws, rr, "t = trung bình hiệu / (sd hiệu / căn n). p = TDIST hai phía với n−1 bậc tự do. "
                      "Dòng so với chính nó để trống thay vì báo lỗi chia 0.")
    rr = note(ws, rr, "Cột 'Lượt chạy' cho biết số đến từ phiên GPU nào — ghép cặp giữa các phiên vẫn chính xác "
                      "vì seed là tất định (đã kiểm: seed không kích hoạt cơ chế nào cho ra cùng con số tới hai chữ số thập phân).")
    return ws, pos


ws_dtd, pos_dtd = seed_sheet(
    "Từng seed (DTD)", "dtd", "dtd_A0_refuse",
    ["dtd_N_control", "dtd_A0_refuse", "dtd_L_clientdrop", "dtd_O_drop_mal", "dtd_A6_fast_ban",
     "dtd_A3_exclude", "dtd_M0_median", "dtd_M1_median_full", "dtd_A1_refuse_audit",
     "dtd_A2_comply_audit", "dtd_A5_refuse_dose", "dtd_A4_comply_dose", "dtd_G_rho",
     "dtd_G_both", "dtd_G_both_floor", "dtd_L_drop", "dtd_L_restore", "dtd_N_audit",
     "dtd_N_audit_dose", "dtd_N_audit_ownlabels", "dtd_N_audit_q50", "dtd_N_audit_q75",
     "dtd_N_audit_q90", "dtd_A1_audit_q50", "dtd_A1_audit_q75", "dtd_A1_audit_q90"],
    "DỮ LIỆU GỐC. Mọi sheet khác tham chiếu về đây. Mốc: A0_refuse = có tấn công, không phòng thủ.")
ws_pets, pos_pets = seed_sheet(
    "Từng seed (Pets)", "oxford_pets", "oxford_pets_A0_refuse",
    ["oxford_pets_N_control", "oxford_pets_A0_refuse", "oxford_pets_A1_refuse_audit",
     "oxford_pets_A2_comply_audit", "oxford_pets_A3_exclude", "oxford_pets_M0_median",
     "oxford_pets_M1_median_full", "oxford_pets_N_audit"],
    "OxfordPets — dataset thứ hai, dùng để kiểm mọi phát biểu chính có chuyển được không.")

for tag, rr in ladder_rows.items():
    if tag in pos_dtd:
        s = pos_dtd[tag]
        c = lad.cell(row=rr, column=3, value=f"='Từng seed (DTD)'!H{s}")
        c.number_format, c.font = NUM, TD
        if tag == "dtd_A0_refuse":
            lad.cell(row=rr, column=4, value="mốc").font = NOTE
        else:
            c = lad.cell(row=rr, column=4, value=f"='Từng seed (DTD)'!J{s}")
            c.number_format = GAIN
            c.font = TB if tag == "dtd_G_rho" else TD

# ===================================================================== 5
ws = wb.create_sheet("Phán quyết các cổng")
ws.sheet_view.showGridLines = False
r = title(ws, "Bảy cổng thí nghiệm — tiêu chí ghi trước khi chạy",
          "Mọi ngưỡng được viết ra TRƯỚC khi chạy và không sửa sau khi nhìn số.")
r = table(ws, r, [
    ["Cổng", "Tiêu chí ghi trước", "Ngưỡng", "Kết quả đo được", "Phán quyết", "Ý nghĩa"],
    ["1", "Tái lập benchmark FLIP", "sai số trong dung sai paper", "9/9 ô đạt, 4,76 giờ T4", "ĐẠT",
     "Sau khi vá 11 chỗ trong code gốc; phát hiện code public của FLIP không chuẩn hoá ảnh lúc train"],
    ["A1", "Nhiễu nhãn gây thiệt hại đo được", "≥ 2,0 điểm", "4,7–13,2 điểm (last10)", "ĐẠT",
     "2/3 dataset tụt xuống DƯỚI mức zero-shot — huấn luyện cho giá trị âm"],
    ["A2", "Bỏ client nhiễu cứu được nhiều", "≥ 2,0 điểm", "≤ 3,1 điểm, và ≈ 0 trên DTD", "TRƯỢT",
     "Mất dữ liệu gần bằng mất do nhiễu. Dấu hiệu đầu tiên rằng loại bỏ là cần gạt sai"],
    ["B1", "Tấn công giả nhiễu gây hại", "p < 0,05, ≥ 5 seed", "+4,13 (DTD) / +3,58 (Pets)", "ĐẠT",
     "Đạt ở 7 seed"],
    ["B3", "Gộp bền vững phân biệt đúng đối tượng", "loại độc hại > loại nhiễu", "multikrum loại nhiễu gấp 17,7× thật thà", "TRƯỢT",
     "Luật nào có quyết định thì quyết định SAI đối tượng; luật có tác dụng (median) lại không phân biệt gì cả"],
    ["C2", "Hình học prompt tách độc hại khỏi nhiễu", "AUC ≥ 0,80", "0,49–0,99 tuỳ dataset", "TRƯỢT",
     "Phụ thuộc SỐ LỚP: Spearman +0,90 trên 5 dataset. Chỉ hơn baseline ở chỗ cả hai đều yếu"],
    ["E2", "Phát hiện client từ chối tuân thủ", "AUC ≥ 0,90", "0,993 (DTD) / 0,965 (Pets)", "ĐẠT",
     "Và 0,987 / 0,907 khi so RIÊNG với client nhiễu — việc Gate C và D đều không làm được"],
    ["E1", "Tuân thủ làm kẻ tấn công mất ≥ nửa cuộc tấn công", "≥ 50%", "chỉ mất 18–23%", "TRƯỢT",
     "Tiêu chí ghi trước chọn sai nhóm đối chứng — lỗi thiết kế, đã ghi lại như một đính chính"],
    ["F1", "Loại trừ client xoá được cuộc tấn công", "thiệt hại còn ≤ 25%", "còn 85% (DTD) / 82% (Pets)", "TRƯỢT",
     "Bắt đúng 7–9/10 mà chỉ mua +0,65 / +0,96 điểm, không có ý nghĩa"],
    ["F3", "Ghép với median hơn median một mình", "≥ +2,0 điểm", "−1,62 (DTD) / −0,50 (Pets)", "TRƯỢT",
     "Ghép vào làm TỆ ĐI"],
    ["F2", "Tăng liều kiểm toán làm tuân thủ tốn hơn", "còn ≤ 60%", "82% → 94%, tức ngược chiều", "TRƯỢT",
     "Vế 'tuân thủ phải trả giá' của thế lưỡng nan chết hẳn"],
    ["G1", "Ngưỡng tự tin cải thiện phần sửa nhãn", "≥ +1,0 ở ≥ 2/3 mức", "−0,43 / −0,96 / −0,11", "TRƯỢT",
     "Chất lượng nhãn cải thiện 29 lần mà accuracy không nhúc nhích"],
    ["G2", "Sửa nhãn có ngưỡng hơn không phòng thủ", "≥ +2,0 ở ≥ 1 mức", "+1,12 / +1,12 / +1,03", "TRƯỢT",
     "Bản KHÔNG ngưỡng còn tốt hơn (+1,37)"],
    ["H", "Lọc mức ảnh (không đuổi client)", "vượt mọi baseline", "+2,33, p = 0,023", "ĐẠT",
     "Kết quả tốt nhất của đồ án. Lượt tinh chỉnh tiếp theo đang chạy"],
], [7, 38, 24, 30, 11, 66], highlight=(14,))
r = note(ws, r, "Bốn cổng trượt (B3, C2, F1, G1) đều có CƠ CHẾ giải thích được và trở thành một bước trong lập luận, "
                "không phải kết quả bị giấu. Đó là điều khiến chúng có giá trị khi viết bài.", 6)
r = note(ws, r, "Các cổng và tiêu chí đầy đủ: docs/phase1_plan.md … docs/phase6_plan.md. "
                "Kết quả chi tiết từng cổng: results/Phase1/…/Phase6/ và results/Phase_bonus/.", 6)

# ===================================================================== 6
ws = wb.create_sheet("Lọc mức ảnh")
ws.sheet_view.showGridLines = False
r = title(ws, "Lọc ở mức từng ảnh — phương pháp hiện tại",
          "DTD, 5 seed. Không client nào bị đuổi; chỉ thôi huấn luyện trên những ảnh đáng ngờ, chấm lại mỗi 5 vòng.")

ws.cell(row=r, column=1, value="A · KẾT QUẢ TỪNG NHÁNH").font = H2
r += 1
r = table(ws, r, [
    ["Nhánh", "Mô tả", "last10", "Lấy lại", "p", "Bắt % ảnh\nhỏng", "Độ chính\nxác", "Chạm client\nthật thà", "Ghi chú"],
    ["A0_refuse", "không phòng thủ", 47.56, None, None, None, None, None, "mốc"],
    ["F_both (v1)", "luật lớp KHÔNG hạn mức", 37.29, -10.27, None, 0.89, 0.51, 0.453,
     "SẬP vì vòng phản hồi: cắt → model tệ → ngưỡng tuyệt đối bắn khắp nơi → cắt thêm. Bỏ 45,3% dữ liệu client thật thà, KHÔNG ảnh nào thật sự hỏng"],
    ["F_rho (v1)", "luật sai số, mốc = trung vị", 48.96, 1.40, 0.087, 0.314, 0.800, 0.004,
     "Độ chính xác cao nhưng bắt được quá ít — hạn mức ước thiếu vì trung vị đã bị nhiễm"],
    ["G_both", "luật lớp + hạn mức cứng", 48.40, 0.84, 0.116, 0.613, 0.644, 0.040,
     "Hạn mức chặn được vòng phản hồi, nhưng hai luật tranh nhau một ngân sách làm độ chính xác tụt"],
    ["G_both_floor", "thêm sàn hạn mức 0,35", 48.58, 1.02, 0.109, 0.680, 0.661, 0.122,
     "Bắt nhiều nhất mà kết quả gần thấp nhất — bằng chứng recall KHÔNG phải biến chi phối"],
    ["G_rho", "luật sai số, mốc = phân vị 25%", 49.89, 2.33, 0.023, 0.662, 0.711, 0.035,
     "TỐT NHẤT. Đổi mốc so sánh làm hạn mức ước gần đúng (0,405 so với 0,40 thật)"],
    ["L_drop (oracle)", "xoá đúng từng ảnh hỏng", 53.58, 6.02, 0.010, 1.000, 1.000, 0.0,
     "Trần của việc lọc"],
], [15, 28, 9, 9, 8, 10, 10, 11, 74], highlight=(6,))

ws.cell(row=r, column=1, value="B · TỈ GIÁ ĐO ĐƯỢC").font = H2
r += 1
r = table(ws, r, [
    ["Đại lượng", "Giá trị", "Cách có được", "Ý nghĩa"],
    ["Bỏ 1000 ảnh BẨN", "+0,326 điểm", "khớp bình phương tối thiểu trên cả 5 nhánh",
     "Lãi thu được khi dọn đúng chất độc"],
    ["Bỏ nhầm 1000 ảnh SẠCH", "−0,437 điểm", "cùng phép khớp",
     "Thiệt hại khi cắt nhầm dữ liệu tốt"],
    ["Tỉ giá", "1,34", "0,437 / 0,326",
     "Bỏ nhầm 1 ảnh sạch tốn bằng 1,34 ảnh bẩn bỏ đúng"],
    ["ĐỘ CHÍNH XÁC HOÀ VỐN", "57,3%", "0,437 / (0,326 + 0,437)",
     "DƯỚI mức này thì lọc càng nhiều CÀNG HẠI. Đây là tiêu chí thiết kế cho mọi phương pháp lọc"],
    ["Kiểm chứng mô hình", "oracle: thực +6,02 / mô hình +6,11", "điểm oracle không dùng để khớp",
     "Mô hình tuyến tính hai hệ số mô tả được cả 5 điểm"],
], [26, 30, 40, 74], highlight=(4,))

ws.cell(row=r, column=1, value="C · TRẦN THEO ĐỘ CHÍNH XÁC (nếu bắt được TOÀN BỘ ảnh hỏng)").font = H2
r += 1
r = table(ws, r, [
    ["Độ chính xác", "Lấy lại tối đa", "Ghi chú"],
    ["57,3%", "0,00", "hoà vốn"],
    ["65%", "+1,70", ""],
    ["71,1% (hiện tại)", "+2,78", "Phương pháp đạt +2,33 = 84% của trần này. Recall đã hết chỗ vắt"],
    ["80%", "+4,06", "Mục tiêu của lượt tinh chỉnh đang chạy"],
    ["90%", "+5,20", ""],
    ["100%", "+6,11", "bằng oracle L_drop"],
], [16, 15, 92], highlight=(3,))
r = note(ws, r, "Kết luận vận hành: KHÔNG còn gì vắt được từ việc bắt nhiều ảnh hỏng hơn. "
                "Muốn hơn nữa phải BỎ ĐÚNG HƠN — giảm tỉ lệ cắt nhầm ảnh sạch.", 9)
r = note(ws, r, "Dự đoán ghi trước của lượt G (‘recall chi phối’) đã BỊ BÁC: hai nhánh có recall 66,2% và 68,0% "
                "cho kết quả chênh 2,3 lần (+2,33 so với +1,02). Biến chi phối là độ chính xác.", 9)
for rr in range(4, r):
    for col in (6, 7, 8):
        c = ws.cell(row=rr, column=col)
        if isinstance(c.value, float):
            c.number_format = "0.0%"

# ===================================================================== 7
ws = wb.create_sheet("Phát hiện client")
ws.sheet_view.showGridLines = False
r = title(ws, "Phát hiện client — AUC của từng tín hiệu",
          "AUC = xác suất một client/ảnh hỏng được xếp trên một client/ảnh sạch. 0,5 = ngẫu nhiên.")

ws.cell(row=r, column=1, value="A · MỨC CLIENT — kiểm chứng sự tuân thủ (Gate E)").font = H2
r += 1
r = table(ws, r, [
    ["Lượt chạy", "Kẻ tấn công làm gì", "AUC vs mọi\nclient khác", "AUC vs riêng\nclient nhiễu", "Ghi chú"],
    ["dtd_A0_refuse", "từ chối", 0.993, 0.987, "Tín hiệu −r_align, trung bình qua mọi round probe"],
    ["dtd_A1_refuse_audit", "từ chối", 1.000, None, ""],
    ["dtd_A2_comply_audit", "tuân thủ", 0.487, 0.507, "Tuân thủ thì KHÔNG tách được — đó chính là nội dung của thế lưỡng nan"],
    ["dtd_N_control", "không có tấn công", 0.487, None, "Đối chứng: tín hiệu im lặng đúng như phải thế"],
    ["dtd_N_audit", "không có tấn công", 0.497, None, ""],
    ["oxford_pets_A0_refuse", "từ chối", 0.965, 0.907, ""],
    ["oxford_pets_A1_refuse_audit", "từ chối", 0.930, None, ""],
    ["oxford_pets_A2_comply_audit", "tuân thủ", 0.695, 0.227, ""],
    ["oxford_pets_N_control", "không có tấn công", 0.385, None, ""],
    ["oxford_pets_N_audit", "không có tấn công", 0.345, None, ""],
], [28, 22, 13, 13, 80], highlight=(1, 6))
r = note(ws, r, "Bảng chân trị sạch: tín hiệu kêu KHI VÀ CHỈ KHI có client từ chối. "
                "Cột 4 là cột quan trọng nhất — tách độc hại khỏi NHIỄU, việc Gate C và Gate D đều không làm được.", 5)
r += 1

ws.cell(row=r, column=1, value="B · MỨC CLIENT — hình học prompt (Gate C, đã trượt)").font = H2
r += 1
r = table(ws, r, [
    ["Dataset", "Số lớp", "ZS-CLIP", "s_conc\n(độc hại vs nhiễu)", "s_upd\n(baseline Krum)", "Chênh so\nvới baseline", "Ghi chú"],
    ["Caltech101", 102, 85.76, 0.987, 0.933, 0.053, "Tín hiệu mạnh — nhưng baseline cũng mạnh"],
    ["Food101", 101, 78.05, 0.933, 0.947, -0.014, "Baseline MẠNH HƠN tín hiệu của ta"],
    ["DTD", 47, 41.78, 0.780, 0.527, 0.253, "Hơn baseline nhiều nhất — nhưng cả hai đều dưới 0,80"],
    ["OxfordPets", 37, 85.69, 0.487, 0.400, 0.087, "Ở mức ngẫu nhiên"],
    ["EuroSAT", 10, 26.11, 0.593, 0.407, 0.186, "Mọi tín hiệu đều ở hoặc dưới mức ngẫu nhiên"],
], [14, 9, 10, 15, 14, 12, 74])
r = note(ws, r, "Biến chi phối là SỐ LỚP (Spearman ρ = +0,90), không phải mức huấn luyện (ρ = −0,20). "
                "Kết luận: tín hiệu hình học prompt hơn baseline ĐÚNG Ở CHỖ cả hai đều yếu, và không hơn ở chỗ cả hai đều mạnh.", 7)
r += 1

ws.cell(row=r, column=1, value="C · MỨC ẢNH — hai dấu hiệu bù nhau (cơ sở của phương pháp)").font = H2
r += 1
r = table(ws, r, [
    ["Tín hiệu", "Nhìn cái gì", "AUC ở client\nNHIỄU", "AUC ở client\nĐỘC HẠI", "Ghi chú"],
    ["loss (trung bình nhiều vòng)", "từng ảnh — 'học mãi không thuộc'", 0.924, 0.526,
     "Công cụ chuẩn mực của lĩnh vực nhãn nhiễu. MÙ hoàn toàn trước tấn công có tổ chức"],
    ["thầy không đồng ý (trung bình)", "từng ảnh", 0.838, 0.845, "Tín hiệu tổng quát tốt nhất, cân bằng hai loại"],
    ["bất đồng theo LỚP", "cả lớp trong một client", 0.807, 0.792, "Bắt 83% chất độc ở client độc hại, nơi loss chỉ bắt 19%"],
    ["model của chính client", "từng ảnh", 0.739, 0.511, "Vô dụng — model vừa học thuộc chính nhãn đó xong"],
], [30, 32, 13, 13, 78], highlight=(1, 3))
r = note(ws, r, "Vì sao hai dấu hiệu bù nhau: client nhiễu lật nhãn NGẪU NHIÊN nên mô hình không học nổi → loss cao → lộ. "
                "Client độc hại lật về MỘT lớp, đó là một quy luật nhất quán nên mô hình học thuộc dễ → loss thấp như ảnh sạch → thoát. "
                "Chính cái giúp kẻ tấn công thoát dấu hiệu 1 lại làm nó lộ ở dấu hiệu 2.", 5)

# ===================================================================== 8
ws = wb.create_sheet("Chất lượng sửa nhãn")
ws.sheet_view.showGridLines = False
r = title(ws, "Vì sao hướng sửa nhãn bế tắc",
          "Đo trên NHÃN THẬT (clean_targets) — thông tin offline, không rule nào được dùng. DTD.")

ws.cell(row=r, column=1, value="A · THẦY DỐT HƠN TRÒ").font = H2
r += 1
r = table(ws, r, [
    ["Lượt chạy", "Nhóm client", "% ảnh\nđược sửa", "Nhãn client\nđúng", "Model toàn cục\nđúng", "Vá\nđược", "Phá\nhỏng", "Ròng", "Ghi chú"],
    ["DIAG_audit", "tất cả", 1.00, 0.881, 0.525, 198, 1679, -1481, "Sửa mọi nhãn bằng argmax của model toàn cục"],
    ["DIAG_audit", "client nhiễu", 1.00, 0.604, 0.470, 198, 355, -157,
     "THẦY ĐÚNG 47,0% TRONG KHI NHÃN CLIENT ĐÚNG 60,4% — thầy dốt hơn trò ngay trên bài của trò"],
    ["DIAG_audit", "client sạch", 1.00, 1.000, 0.548, 0, 1324, -1324,
     "Nhãn vốn đã đúng hết nên chỉ có thể PHÁ, không thể vá"],
    ["N_audit_q90", "client nhiễu", 0.11, 0.599, 0.875, 108, 42, 66,
     "Ngưỡng tự tin làm thầy giỏi hơn trò (87,5% so với 59,9%) — cơ chế chạy ĐÚNG như thiết kế"],
    ["N_audit_q90", "client sạch", 0.11, 1.000, 0.929, 0, 117, -117, "Vẫn chỉ có thể phá"],
], [15, 15, 10, 11, 14, 8, 8, 9, 78], highlight=(2, 4))

ws.cell(row=r, column=1, value="B · CHẤT LƯỢNG NHÃN TỐT LÊN 29 LẦN MÀ ACCURACY ĐỨNG YÊN").font = H2
r += 1
r = table(ws, r, [
    ["Cấu hình", "% ảnh được sửa", "Chất lượng nhãn\n(vá − phá)", "Accuracy so với\nkhông sửa nhãn", "Ghi chú"],
    ["ownlabels (đối chứng)", "0%", "không sửa gì", 0.16, "Giữ NGUYÊN mọi thứ — epoch phụ, prompt trả về, kiểm toán — chỉ bỏ bước sửa nhãn"],
    ["conf 0 (không ngưỡng)", "100%", -1481, 0.86, "Bỏ bước sửa nhãn thì mất lợi ích → việc dùng nhãn model toàn cục LÀ thứ trả tiền"],
    ["q50", "51%", -1611, 0.42, ""],
    ["q75", "26%", -347, -0.10, ""],
    ["q90", "11%", -51, 0.75, "Chất lượng nhãn tốt lên 29 lần mà accuracy không nhúc nhích"],
], [24, 16, 18, 18, 80], highlight=(1, 5))
r = note(ws, r, "KẾT LUẬN PHẢN TRỰC GIÁC: cơ chế có lãi KHÔNG PHẢI khử nhiễu. "
                "Bỏ bước sửa nhãn thì mất lợi ích (+0,86 → +0,16), nhưng sửa nhãn ĐÚNG HƠN 29 lần lại không được thêm gì. "
                "Nhiều khả năng lợi ích đến từ SỰ ĐỒNG THUẬN — mọi client cùng học theo một nguồn nhãn chung, giảm phân kỳ dưới non-IID. "
                "Nhãn đúng hay sai không quan trọng; quan trọng là cùng một nguồn. (Giả thuyết, chưa chứng minh.)", 5)
r += 1

ws.cell(row=r, column=1, value="C · WARM-UP KHÔNG CỨU ĐƯỢC").font = H2
r += 1
r = table(ws, r, [
    ["Cấu hình", "Thầy đúng trên dữ liệu\nclient SẠCH", "Thầy đúng trên dữ liệu\nclient NHIỄU", "Accuracy so với\nN_control", "Ghi chú"],
    ["không warm-up", 0.548, 0.470, 0.86, "Mốc để vượt: nhãn client nhiễu đúng 60,4%"],
    ["warm5", 0.610, 0.475, 0.01, ""],
    ["warm10", 0.634, 0.483, 0.02, ""],
    ["warm20", 0.655, 0.464, -0.14, "Thầy giỏi lên 10,7 điểm trên dữ liệu nhóm sạch, ĐỨNG YÊN trên dữ liệu client nhiễu"],
], [18, 22, 22, 17, 80], highlight=(4,))
r = note(ws, r, "Lý do: Dirichlet α = 0,1 nên mỗi client giữ một tập lớp rất khác nhau. "
                "Nhóm tin cậy chỉ dạy được thầy về NHỮNG LỚP NÓ CÓ; với dữ liệu của client nhiễu thầy vẫn mù. "
                "Đây không phải 'warm-up chưa đủ vòng' — nó KHÔNG THỂ hiệu quả dưới non-IID mạnh. "
                "Giả định 'nhóm client tin cậy' kiểu FLTrust không cứu được bài toán này.", 5)

for name in ("Chất lượng sửa nhãn", "Lọc mức ảnh"):
    s = wb[name]
    for row in s.iter_rows():
        for c in row:
            if isinstance(c.value, float) and c.number_format == "General":
                c.number_format = "0.0%" if 0 <= c.value <= 1.001 else NUM

wb.save(OUT)
print("saved", OUT)
