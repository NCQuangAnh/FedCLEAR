"""Build tuong-tac-kich-ban-nhieu.pptx: the server-client interaction figure (noise-only
scenario, K_fixconf) as native, editable PowerPoint shapes.

Coordinates are the ones of tuong-tac-kich-ban-nhieu.html (a 1280 x 720 px canvas); on a
13.333 x 7.5 in slide one px is exactly 9525 EMU and one px of font is 0.75 pt.
"""
import os

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE, MSO_PATTERN_TYPE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tuong-tac-kich-ban-nhieu.pptx")
FONT, MATH = "Arial", "Times New Roman"
INK = "1D1D1F"
ORANGE, BLUE = "E8741A", "2F6FD1"


def E(px):
    return Emu(int(round(px * 9525)))


def rgb(h):
    return RGBColor.from_string(h)


def _line(shape, color, width=1.0, dash=False):
    if color is None:
        shape.line.fill.background()
        return
    shape.line.color.rgb = rgb(color)
    shape.line.width = Pt(width * 0.75)
    if dash:
        shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH


def box(sh, x, y, w, h, fill=None, line=None, lw=1.0, dash=False, radius=None, kind=None):
    k = kind or (MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE)
    s = sh.add_shape(k, E(x), E(y), E(w), E(h))
    if radius and k == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = min(0.5, radius / min(w, h))
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    _line(s, line, lw, dash)
    s.shadow.inherit = False
    s.text_frame.text = ""
    return s


def hatch(s, fore="E07B16", back="FBD7A8"):
    s.fill.patterned()
    s.fill.pattern = MSO_PATTERN_TYPE.WIDE_UPWARD_DIAGONAL
    s.fill.fore_color.rgb = rgb(fore)
    s.fill.back_color.rgb = rgb(back)


def text(sh, x, y, runs, size=13, color=INK, anchor="start", w=None, bold=False):
    """A text box whose BASELINE sits at y, like SVG text. runs: str or [(str, opts)]."""
    if isinstance(runs, str):
        runs = [(runs, {})]
    n = sum(len(r[0]) for r in runs)
    w = w or max(20, n * size * 0.56 + 12)
    left = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
    tb = sh.add_textbox(E(left), E(y - size * 1.02), E(w), E(size * 1.35))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = {"start": PP_ALIGN.LEFT, "middle": PP_ALIGN.CENTER, "end": PP_ALIGN.RIGHT}[anchor]
    for s, o in runs:
        r = p.add_run()
        r.text = s
        f = r.font
        f.name = MATH if o.get("i") else FONT
        f.italic = bool(o.get("i"))
        f.bold = o.get("b", bold)
        f.size = Pt(o.get("size", size) * 0.75)
        f.color.rgb = rgb(o.get("color", color))
    return tb


def arrow(sh, x1, y1, x2, y2, color, width=2.0, dash=False, head=True):
    c = sh.add_connector(MSO_CONNECTOR.STRAIGHT, E(x1), E(y1), E(x2), E(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width * 0.75)
    if dash:
        c.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    if head:
        ln = c.line._get_or_add_ln()
        t = etree.SubElement(ln, qn("a:tailEnd"))
        t.set("type", "triangle")
        t.set("w", "med")
        t.set("len", "med")
    return c


def num(sh, cx, cy, label, fill, r=11):
    s = box(sh, cx - r, cy - r, 2 * r, 2 * r, fill=fill, kind=MSO_SHAPE.OVAL)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = label
    run.font.name, run.font.bold, run.font.size = FONT, True, Pt(12 * 0.75)
    run.font.color.rgb = rgb("FFFFFF")
    return s


def prompt_strip(sh, x, y):
    g = sh.add_group_shape()
    for k in range(4):
        box(g.shapes, x + 9 * k, y, 9, 11, fill="F6C343", line="8A6D10", lw=0.8)
    g.name = "prompt (4 x 512)"
    return g


def cylinder(sh, x, y, noisy, w=54, h=58):
    g = sh.add_group_shape()
    c = box(g.shapes, x, y, w, h, fill="9CC3F2", line="2A5DA8", lw=1.6, kind=MSO_SHAPE.CAN)
    c.adjustments[0] = 0.28
    if noisy:
        o = box(g.shapes, x, y + h * 0.43, w, h * 0.57, fill="F3A04C", line="2A5DA8", lw=1.6,
                kind=MSO_SHAPE.CAN)
        o.adjustments[0] = 0.28
    return g


def circle(sh, cx, cy, r, kind, faded=False):
    s = box(sh, cx - r, cy - r, 2 * r, 2 * r, kind=MSO_SHAPE.OVAL,
            fill=("9DBDEB" if faded else BLUE) if kind == "ok" else None,
            line=None if kind == "ok" else "C2710C", lw=1.0)
    if kind == "bad":
        hatch(s, *(("F2B98A", "FCEBD8") if faded else ("E07B16", "FBD7A8")))
    return s


def group(sh, name):
    g = sh.add_group_shape()
    g.name = name
    return g.shapes


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = E(1280), E(720)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    S = slide.shapes

    # ---------------- title
    t = group(S, "Tiêu đề")
    text(t, 24, 38, "Một vòng huấn luyện: server và client trao đổi gì?", 23, bold=True)
    text(t, 24, 60, "Kịch bản chỉ có client cẩu thả · 7 client sạch + 3 client cẩu thả "
                    "(40% nhãn sai ngẫu nhiên) · phương pháp K_fixconf", 14, color="555555")

    # ---------------- server panel
    box(S, 20, 76, 840, 196, fill="F2F4F8", line="8A94A6", lw=1.4, dash=True, radius=14)
    g = group(S, "Server: nhãn")
    for k in range(3):
        box(g, 38, 92 + 12 * k, 30, 10, fill="6C7A93", radius=2)
    text(g, 78, 106, "SERVER", 16, bold=True)
    text(g, 78, 124, "không thấy ảnh nào của client", 12.5, color="555555")

    g = group(S, "Server bước 4: gộp prompt")
    box(g, 44, 140, 250, 118, fill="FFFFFF", line="B9C0CC", radius=10)
    num(g, 62, 158, "4", "333333")
    text(g, 80, 163, "Gộp prompt", 14, bold=True)
    for yy in (180, 196, 212):
        prompt_strip(g, 62, yy)
    text(g, 80, 236, "⋮", 11, color="555555", anchor="middle")
    br = box(g, 104, 180, 10, 52, line="555555", lw=1.2, kind=MSO_SHAPE.RIGHT_BRACE)
    arrow(g, 120, 206, 146, 206, "333333", 1.4)
    text(g, 133, 198, "trung", 10.5, color="555555", anchor="middle")
    text(g, 133, 222, "bình", 10.5, color="555555", anchor="middle")
    prompt_strip(g, 152, 200)
    text(g, 206, 204, "prompt", 12, bold=True)
    text(g, 206, 219, "chung mới", 12, bold=True)
    text(g, 62, 250, "10 prompt nhận từ 10 client", 11.5, color="555555")

    g = group(S, "Server: tính mức lệch chuẩn b")
    box(g, 316, 140, 286, 118, fill="FFFFFF", line="B9C0CC", radius=10)
    text(g, 332, 163, [("Tính mức lệch chuẩn ", {"b": True}), ("b", {"i": True, "size": 16})], 14)
    text(g, 336, 185, [("mức lệch ", {}), ("d", {"i": True, "size": 13}), (" của 10 client", {})],
         11.5, color="555555")
    heights = [19, 21, 23, 24, 26, 27, 30, 58, 62, 66]
    for k, hgt in enumerate(heights):
        box(g, 336 + 4 + 17 * k, 244 - hgt, 12, hgt, fill="9CC3F2" if k < 7 else "F3A04C")
    arrow(g, 336, 244, 512, 244, "555555", 1.0, head=False)
    arrow(g, 334, 221, 514, 221, "C0392B", 1.6, dash=True, head=False)
    text(g, 520, 208, [("b", {"i": True, "size": 14}), (" = mức ở", {})], 12, color="C0392B", bold=True)
    text(g, 520, 223, "nhóm thấp", 12, color="C0392B", bold=True)
    text(g, 520, 238, "nhất (25%)", 12, color="C0392B", bold=True)

    arrow(S, 603, 200, 622, 200, "333333", 1.4)

    g = group(S, "Server: ra lệnh lọc")
    box(g, 626, 140, 220, 118, fill="FFFFFF", line="B9C0CC", radius=10)
    text(g, 642, 163, "Ra lệnh lọc", 14, bold=True)
    box(g, 642, 176, 92, 30, fill="DDEFE2", line="2E7D4F", radius=6)
    text(g, 688, 189, "CỨNG", 12, color="1F5F3A", anchor="middle", bold=True, w=90)
    text(g, 688, 201, [("b", {"i": True, "size": 12}), (" < 0.22", {})], 10.5, color="1F5F3A",
         anchor="middle", w=90)
    box(g, 740, 176, 92, 30, fill="FDEBD3", line="C2710C", radius=6)
    text(g, 786, 189, "MỀM", 12, color="8A4F06", anchor="middle", bold=True, w=90)
    text(g, 786, 201, [("b", {"i": True, "size": 12}), (" ≥ 0.22", {})], 10.5, color="8A4F06",
         anchor="middle", w=90)
    text(g, 642, 224, [("b", {"i": True, "size": 13}), (" thấp = mô hình chung đã đủ giỏi", {})],
         11.5, color="444444")
    text(g, 642, 238, "→ cho phép bỏ ảnh / sửa nhãn;", 11.5, color="444444")
    text(g, 642, 252, "ngược lại chỉ giảm trọng số.", 11.5, color="444444")

    # ---------------- wires
    g = group(S, "Dây: gửi xuống (cam) / gửi lên (xanh)")
    arrow(g, 246, 272, 246, 316, ORANGE, 2.6, head=False)
    arrow(g, 53, 316, 791, 316, ORANGE, 2.6, head=False)
    arrow(g, 67, 338, 805, 338, BLUE, 2.6, head=False)
    arrow(g, 624, 338, 624, 280, BLUE, 2.6)
    for k in range(10):
        cx = 60 + 82 * k
        arrow(g, cx - 7, 316, cx - 7, 364, ORANGE, 2.0)
        arrow(g, cx + 7, 370, cx + 7, 344, BLUE, 2.0)

    g = group(S, "Bước 1: gửi xuống")
    box(g, 258, 279, 318, 30, fill="FFF3E8", line=ORANGE, radius=6)
    num(g, 272, 294, "1", ORANGE, r=10)
    text(g, 288, 299, [("Gửi xuống:", {"b": True}), (" prompt chung · mức chuẩn ", {}),
                       ("b", {"i": True, "size": 14}), (" · lệnh", {})], 12.5)
    g = group(S, "Bước 3: gửi lên")
    box(g, 636, 279, 214, 30, fill="EAF1FC", line=BLUE, radius=6)
    num(g, 650, 294, "3", BLUE, r=10)
    text(g, 666, 299, [("Gửi lên:", {"b": True}), (" prompt · mức lệch ", {}),
                       ("d", {"i": True, "size": 14})], 12.5)

    # ---------------- clients panel
    box(S, 20, 370, 840, 226, fill="FFF7EF", line="D9A46C", lw=1.4, dash=True, radius=14)
    noisy = {1, 4, 9}
    for k in range(10):
        cx = 60 + 82 * k
        g = group(S, f"Client C{k + 1}")
        cylinder(g, cx - 27, 410, k in noisy)
        text(g, cx, 490, f"C{k + 1}", 13, anchor="middle", bold=True, w=60)
        text(g, cx, 505, "cẩu thả" if k in noisy else "sạch", 11,
             color="C2710C" if k in noisy else "2A5DA8", anchor="middle", w=70)
    g = group(S, "Bước 2: mỗi client")
    box(g, 40, 522, 800, 62, fill="FFFFFF", line="E3C9A8", radius=8)
    num(g, 58, 542, "2", "333333", r=10)
    text(g, 76, 547, [("Mỗi client:", {"b": True}),
                      (" tự dọn ảnh của mình (xem khung bên phải), rồi học prompt 1 lượt.", {})], 13.5)
    text(g, 76, 570, "Máy nào cũng có sẵn CLIP đóng băng ❄ · chỉ prompt (2.048 số) được học và gửi đi "
                     "· ảnh và nhãn không rời máy.", 12.5, color="444444")

    g = group(S, "Đường phóng to C10")
    arrow(g, 825, 416, 884, 300, "999999", 1.2, dash=True, head=False)
    arrow(g, 825, 462, 884, 580, "999999", 1.2, dash=True, head=False)

    # ---------------- zoom: inside a careless client
    box(S, 884, 76, 376, 520, fill="FFFDF9", line="C2710C", lw=1.6, radius=14)
    g = group(S, "Khung phóng to: tiêu đề")
    num(g, 906, 100, "2", "333333")
    text(g, 924, 105, "Bên trong client cẩu thả C10", 15, bold=True)
    text(g, 902, 126, "cứ 5 vòng chấm lại toàn bộ ảnh; vòng khác học trên bộ đã dọn", 11.5,
         color="666666")

    def step(letter, y):
        gg = group(S, f"Bước con {letter}")
        text(gg, 902, y, letter, 13, color="C2710C", bold=True)
        return gg

    g = step("a", 152)
    text(g, 918, 152, [("Đo ", {}), ("mức lệch", {"b": True}),
                       (": mô hình chung cãi bao nhiêu % nhãn", {})], 13)
    text(g, 918, 170, [("→ ", {}), ("d", {"i": True, "size": 15}), (" = 0.41 ", {}),
                       ("(client sạch chỉ ≈ 0.14)", {"color": "666666", "size": 12})], 13)

    g = step("b", 198)
    text(g, 918, 198, "Tự ước lượng mình bẩn bao nhiêu (ngân sách ρ):", 13)
    box(g, 918, 206, 326, 26, fill="F7F3EC", radius=5)
    text(g, 926, 224, [("ρ", {"i": True}), (" = (", {}), ("d", {"i": True}), (" − ", {}),
                       ("b", {"i": True}), (") / (1 − ", {}), ("b", {"i": True}),
                       (") = (0.41 − 0.14) / 0.86 ≈ ", {}), ("0.31", {"b": True})], 14)
    text(g, 918, 249, "Client sạch: ρ ≤ 0.10 → coi là sạch, không đụng ảnh nào.", 12, color="555555")

    g = step("c", 276)
    text(g, 918, 276, [("Xếp ảnh theo độ ", {}), ("khó học", {"b": True}),
                       (" (loss): top ρ là ảnh nghi", {})], 13)
    lh = [40, 34, 29, 20, 16, 12, 9, 7, 5, 4]
    for k, hgt in enumerate(lh):
        box(g, 920 + 31 * k, 330 - hgt, 22, hgt, fill="F2C9A0" if k < 3 else "E4E4E4")
    arrow(g, 917, 330, 1226, 330, "777777", 1.0, head=False)
    for k in range(10):
        circle(g, 931 + 31 * k, 344, 9, "bad" if k in (0, 1, 3) else "ok")
    box(g, 916, 285, 92, 72, line="C0392B", lw=1.6, dash=True, radius=6)
    text(g, 962, 370, "ảnh nghi (31%)", 11.5, color="C0392B", anchor="middle", bold=True, w=110)
    text(g, 1110, 370, "khó học  →  dễ học", 11.5, color="666666", anchor="middle", w=130)

    g = step("d", 394)
    text(g, 918, 394, [("Xử lý ảnh nghi theo ", {}), ("lệnh của server", {"b": True}), (":", {})], 13)
    box(g, 918, 404, 160, 96, fill="DDEFE2", line="2E7D4F", radius=7)
    text(g, 928, 422, "CỨNG", 12.5, color="1F5F3A", bold=True)
    circle(g, 936, 440, 7, "bad")
    arrow(g, 946, 440, 964, 440, "1F5F3A", 1.4)
    circle(g, 974, 440, 7, "ok")
    text(g, 988, 444, "sửa nhãn", 11.5)
    text(g, 928, 462, "nếu mô hình chung đoán", 10.5, color="333333")
    text(g, 928, 474, "khác và tin ≥ 0.5", 10.5, color="333333")
    circle(g, 936, 490, 7, "bad")
    text(g, 936, 494, "✕", 12, color="C0392B", anchor="middle", bold=True, w=14)
    text(g, 950, 494, "còn lại: tạm bỏ", 11.5)
    box(g, 1086, 404, 158, 96, fill="FDEBD3", line="C2710C", radius=7)
    text(g, 1096, 422, "MỀM", 12.5, color="8A4F06", bold=True)
    circle(g, 1104, 442, 7, "bad", faded=True)
    circle(g, 1124, 442, 7, "bad")
    circle(g, 1144, 442, 7, "ok")
    text(g, 1096, 466, "không bỏ ảnh nào: ảnh càng", 10.5, color="333333")
    text(g, 1096, 479, "nghi thì trọng số càng nhỏ", 10.5, color="333333")
    text(g, 1096, 492, "(tổng phần giảm = ρ)", 10.5, color="333333")

    g = step("e", 526)
    text(g, 918, 526, "Học prompt 1 lượt trên bộ ảnh đã dọn", 13)
    box(g, 918, 538, 70, 42, fill="EAF1FC", line=BLUE, radius=6)
    text(g, 953, 555, "ảnh", 11, anchor="middle", w=68)
    text(g, 953, 569, "đã dọn", 11, anchor="middle", w=68)
    arrow(g, 990, 559, 1010, 559, "333333", 1.3)
    tz = box(g, 1014, 542, 70, 34, fill="E9EEF5", line="6C7A93", kind=MSO_SHAPE.TRAPEZOID)
    tz.rotation = 180
    text(g, 1049, 563, "CLIP ❄", 11, anchor="middle", w=68)
    arrow(g, 1088, 559, 1108, 559, "333333", 1.3)
    text(g, 1116, 554, "so khớp với", 11)
    prompt_strip(g, 1116, 560)
    text(g, 1156, 570, "+ tên lớp", 11)
    text(g, 1014, 592, "chỉ 4 ô vàng (prompt) được cập nhật", 10.5, color="8A4F06")

    # ---------------- timeline
    g = group(S, "Dải thời gian")
    box(g, 20, 608, 300, 34, fill="E3E6EC")
    text(g, 32, 630, [("Vòng 0–4:", {"b": True}), (" chưa có ", {}), ("b", {"i": True, "size": 14}),
                      (" → chưa lọc, chỉ báo ", {}), ("d", {"i": True, "size": 14})], 12.5)
    box(g, 320, 608, 420, 34, fill="CFE0F7")
    text(g, 332, 630, [("Vòng 5, 10, 15, …:", {"b": True}),
                       (" client chấm lại ảnh và lọc theo lệnh mới", {})], 12.5)
    box(g, 740, 608, 520, 34, fill="F9D9B8")
    text(g, 752, 630, [("Mọi vòng (50 vòng):", {"b": True}),
                       (" 1 gửi xuống → 2 học → 3 gửi lên → 4 gộp", {})], 12.5)

    # ---------------- legend
    g = group(S, "Chú thích")
    box(g, 20, 652, 1240, 56, fill="FFFFFF", line="C9CDD4", radius=8)
    arrow(g, 36, 672, 72, 672, ORANGE, 2.4)
    text(g, 80, 676, "gửi xuống", 12)
    arrow(g, 36, 694, 72, 694, BLUE, 2.4)
    text(g, 80, 698, "gửi lên", 12)
    cylinder(g, 172, 664, False, w=28, h=32)
    text(g, 206, 684, "client sạch", 12)
    cylinder(g, 302, 664, True, w=28, h=32)
    text(g, 336, 684, "client cẩu thả (phần cam = nhãn sai)", 12)
    circle(g, 590, 672, 7, "ok")
    text(g, 604, 676, "ảnh đúng nhãn", 12)
    circle(g, 590, 694, 7, "bad")
    text(g, 604, 698, "ảnh nhãn sai", 12)
    prompt_strip(g, 720, 666)
    text(g, 764, 676, "prompt: 4 × 512 số, thứ duy nhất được học", 12)
    text(g, 728, 698, "❄", 13, color="3AA0D8", anchor="middle", w=16)
    text(g, 764, 698, "đóng băng (CLIP không đổi, không gửi đi)", 12)
    text(g, 1060, 676, [("d", {"i": True, "size": 14}), (" mức lệch của client", {})], 12)
    text(g, 1060, 698, [("b", {"i": True, "size": 14}), (" mức lệch chuẩn", {})], 12)

    prs.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
