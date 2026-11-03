"""Add slide 3 to tuong-tac-kich-ban-nhieu.pptx: round 0 at the server, plain federated
learning vs federated prompt learning (noise-only scenario). Slides 1-2 are left untouched;
the colours follow the user's slide 2 (theme accent1 navy, accent6 peach, accent4 purple).

Run once: it refuses to add a second copy if the deck already has 3 slides.
"""
import os
import random

import make_tuong_tac_pptx as H
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "tuong-tac-kich-ban-nhieu.pptx")
H.FONT = "Calibri"
NAVY, PEACH, PEACH_T, PURP, PURP_T = "1E3048", "FDE9D9", "984807", "CCC1DA", "3F3151"
box, text, arrow, group, strip = H.box, H.text, H.arrow, H.group, H.prompt_strip


def server_icon(sh, x, y):
    g = group(sh, "Server")
    text(g, x + 23, y - 6, "Server", 13, anchor="middle", w=60)
    for k in range(3):
        box(g, x, y + 22 * k, 46, 19, fill="FFFFFF", line=NAVY, lw=2)
    H.box(g, x + 35, y + 6, 6, 6, fill="C00000", kind=MSO_SHAPE.OVAL)


def clients(sh, x0, y, name):
    g = group(sh, name)
    arrow(g, x0 + 23, y - 6, x0 + 23 + 54 * 9, y - 6, "5B87C0", 1.2, head=False)
    for k in range(10):
        x = x0 + 54 * k
        noisy = k in (3, 6, 9)
        arrow(g, x + 23, y - 6, x + 23, y, "5B87C0", 1.2, head=False)
        b = box(g, x, y, 46, 40, fill=PURP if noisy else PEACH, line=NAVY, lw=1.6, radius=8)
        text(g, x + 23, y + 26, f"C{k + 1}", 13, color=PURP_T if noisy else PEACH_T,
             anchor="middle", w=44)
    return g


def build():
    prs = Presentation(DECK)
    if len(prs.slides) >= 3:
        raise SystemExit("deck already has 3 slides; not adding another")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    S = slide.shapes

    t = group(S, "Tiêu đề")
    text(t, 40, 50, "Vòng 0 tại server: Federated Learning thường vs Federated Prompt Learning", 25,
         bold=True)
    text(t, 40, 76, "Kịch bản chỉ có client cẩu thả (7 sạch + 3 cẩu thả) · server tạo gì, gửi gì, "
                    "và mô hình xuất phát từ đâu", 14, color="555555")

    # column headers + divider
    g = group(S, "Tiêu đề cột")
    box(g, 40, 96, 560, 34, fill="E7E9EE", radius=8)
    text(g, 320, 119, "Federated Learning thường  (vd: ResNet-50 học từ đầu)", 15, bold=True,
         anchor="middle", w=550)
    box(g, 680, 96, 560, 34, fill="FBE3CF", line="E8741A", radius=8)
    text(g, 960, 119, "Federated Prompt Learning — đề tài  (CLIP + CoOp)", 15, bold=True,
         color="8A4F06", anchor="middle", w=550)
    arrow(S, 640, 96, 640, 556, "B9C0CC", 1.4, dash=True, head=False)

    # ---------------- server row, FL
    server_icon(S, 50, 172)
    g = group(S, "FL: server khởi tạo")
    box(g, 120, 146, 480, 180, fill="FFFFFF", line="B9C0CC", radius=10)
    text(g, 136, 172, "Khởi tạo TOÀN BỘ mạng bằng số ngẫu nhiên", 15, bold=True)
    rnd = random.Random(0)
    shades = ["9CC3F2", "6FA3E3", "C9DEF8", "4F81BD", "B3CFF0"]
    for r in range(6):
        for c in range(20):
            box(g, 136 + 14 * c, 186 + 14 * r, 12, 12, fill=rnd.choice(shades))
    text(g, 432, 222, "~25 triệu số", 22, bold=True, color="2A5DA8")
    text(g, 432, 244, "(mọi trọng số của ResNet-50)", 12, color="666666")
    text(g, 136, 290, "Mô hình chưa biết gì: đoán như bốc thăm", 13.5)
    text(g, 136, 310, "(Pets có 37 lớp → đúng ≈ 3%)", 12.5, color="666666")

    # ---------------- server row, FPL
    server_icon(S, 690, 172)
    g = group(S, "FPL: server khởi tạo")
    box(g, 760, 146, 480, 180, fill="FFFFFF", line="B9C0CC", radius=10)
    text(g, 776, 172, "Chỉ khởi tạo prompt bằng số ngẫu nhiên", 15, bold=True)
    for k in range(4):
        b = box(g, 776 + 30 * k, 188, 28, 28, fill="F6C343", line="8A6D10", lw=1)
        text(g, 790 + 30 * k, 207, f"V{k + 1}", 11, anchor="middle", w=26, color="5C4708")
    text(g, 900, 208, "+ “tên lớp”", 13)
    text(g, 776, 236, "4 × 512 = 2.048 số", 15, bold=True, color="8A4F06")
    text(g, 776, 254, "ngẫu nhiên, độ lệch 0,02", 12, color="666666")
    box(g, 1008, 182, 218, 74, fill="E9EEF5", line="6C7A93", radius=8)
    text(g, 1018, 204, "CLIP đã huấn luyện sẵn ❄", 13.5, bold=True)
    text(g, 1018, 224, "~100 triệu số · đóng băng", 12)
    text(g, 1018, 244, "mọi client tải sẵn 1 lần", 12, color="555555")
    text(g, 776, 290, "Mô hình đã biết nhìn ảnh và đọc chữ:", 13.5)
    text(g, 776, 310, "chỉ còn học cách “đặt câu hỏi” cho đúng", 12.5, color="666666")

    # ---------------- what goes down, FL
    g = group(S, "FL: gửi xuống")
    arrow(g, 360, 330, 360, 448, "E8741A", 13)
    box(g, 384, 352, 216, 60, fill="FFF3E8", line="E8741A", radius=6)
    text(g, 394, 374, "Gửi xuống mỗi client:", 12.5, bold=True)
    text(g, 394, 396, "cả mạng ≈ 25 triệu số", 14, color="B5530A", bold=True)
    box(g, 50, 346, 290, 76, fill="F2F4F8", radius=6)
    text(g, 60, 366, "Vòng 0 ở FL thường:", 12.5, bold=True)
    text(g, 60, 386, "• không có bước lọc nhãn", 12)
    text(g, 60, 404, "• client học trên mọi ảnh, kể cả nhãn sai", 12)

    # ---------------- what goes down, FPL
    g = group(S, "FPL: gửi xuống")
    arrow(g, 1000, 330, 1000, 448, "E8741A", 2.5)
    box(g, 1016, 340, 224, 98, fill="FFF3E8", line="E8741A", radius=6)
    text(g, 1026, 360, "Gửi xuống mỗi client:", 12.5, bold=True)
    text(g, 1026, 381, "chỉ 2.048 số prompt", 14, color="B5530A", bold=True)
    text(g, 1026, 401, [("mức chuẩn ", {}), ("b", {"i": True, "size": 14}), (": chưa có", {})], 12)
    text(g, 1026, 420, "lệnh lọc: MỀM (mặc định)", 12)
    box(g, 690, 340, 296, 98, fill="F2F4F8", radius=6)
    text(g, 700, 360, "Vòng 0 ở kịch bản client cẩu thả:", 12.5, bold=True)
    text(g, 700, 380, [("• chưa có ", {}), ("b", {"i": True, "size": 14}),
                       (" → ngân sách lọc = 0, chưa lọc", {})], 12)
    text(g, 700, 399, [("• client học mọi ảnh, chỉ báo lên ", {}), ("d", {"i": True, "size": 14})], 12)
    text(g, 700, 418, "• lọc thật bắt đầu từ vòng 5", 12)

    # ---------------- clients
    clients(S, 50, 462, "FL: 10 client")
    clients(S, 690, 462, "FPL: 10 client")
    g = group(S, "Chú thích client")
    text(g, 50, 524, "Mỗi client giữ cả mạng và chỉnh MỌI trọng số", 12.5, color="444444")
    text(g, 690, 524, "Mỗi client: CLIP ❄ + prompt, chỉ chỉnh 2.048 số", 12.5, color="444444")

    # ---------------- key difference
    g = group(S, "Khác biệt cốt lõi")
    box(g, 40, 568, 1200, 78, fill="FBF3EA", line="E3C9A8", radius=10)
    text(g, 60, 596, "Khác biệt cốt lõi", 15, bold=True, color="8A4F06")
    text(g, 60, 620, "FL thường học cả mạng từ số 0. FPL giữ nguyên CLIP đã giỏi sẵn và chỉ học "
                     "2.048 số “câu hỏi”.", 14)
    text(g, 60, 638, "Cả hai đều gửi số qua mạng, nhưng FPL gửi ít hơn rất nhiều và xuất phát từ "
                     "một mô hình đã biết nhìn.", 12.5, color="555555")
    text(g, 1220, 606, "≈ 12.500×", 30, bold=True, color="B5530A", anchor="end", w=200)
    text(g, 1220, 630, "ít số hơn mỗi lần gửi", 12, color="666666", anchor="end", w=200)

    # ---------------- legend
    g = group(S, "Chú thích")
    box(g, 40, 664, 22, 18, fill=PEACH, line=NAVY, lw=1.4, radius=4)
    text(g, 70, 678, "client sạch", 12)
    box(g, 160, 664, 22, 18, fill=PURP, line=NAVY, lw=1.4, radius=4)
    text(g, 190, 678, "client cẩu thả (40% nhãn sai)", 12)
    strip(g, 400, 667)
    text(g, 444, 678, "prompt (thứ duy nhất được học ở FPL)", 12)
    text(g, 720, 678, "❄ đóng băng: không đổi, không gửi đi", 12)
    text(g, 990, 678, "Số liệu ≈: ResNet-50 25,6 tr. tham số; CLIP RN50 ≈ 102 tr.", 11, color="777777")

    prs.save(DECK)
    print("slides now:", len(prs.slides))


if __name__ == "__main__":
    build()
