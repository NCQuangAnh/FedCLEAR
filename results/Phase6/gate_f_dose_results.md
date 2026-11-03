# Gate F, lượt liều và chẩn đoán (chạy 2026-09-22, T4, 5,52 giờ)

Dữ liệu: `results/Phase6/dtd_dosed/`. **4/4 job `rc=0`**, DTD, 5 seed. Mọi so sánh ghép cặp theo seed với `N_control` và `A0_refuse` của phiên Gate F.

## 1. Bảng đầy đủ, mọi thứ đã đo trên DTD

| Job | `last10` | Thiệt hại so `N_control` | p | Giữ lại bao nhiêu % thiệt hại |
|---|---|---|---|---|
| `N_control` không tấn công, không luật | 52,06 ± 0,74 | – | | |
| `N_audit` sửa nhãn, không tấn công | **52,92 ± 1,05** | **−0,86** (lãi) | 0,078 | |
| `A0_refuse` có tấn công, không phòng thủ | 47,56 ± 2,91 | +4,50 ± 2,47 | 0,015 | 100% |
| `A3_exclude` loại trừ, cấm từ ~round 18 | 48,21 ± 2,66 | +3,85 ± 2,15 | 0,016 | 85% |
| **`A6_fast_ban`** loại trừ nhanh, cấm từ ~round 11,6 | 48,63 ± 1,69 | +3,43 ± 1,15 | 0,003 | **76%** |
| **`O_drop_mal`** **loại trừ hoàn hảo từ round 0** | 48,57 ± 2,02 | +3,49 ± 1,42 | 0,005 | **77%** |
| `A1_refuse_audit` sửa nhãn liều 10/50 | 48,93 ± 3,11 | +3,13 ± 2,54 | 0,051 | 70% |
| `M0_median` phòng thủ chuẩn của lĩnh vực | 49,01 ± 1,87 | +3,05 ± 1,17 | 0,004 | 68% |
| **`A5_refuse_dose`** **sửa nhãn liều 25/50** | **49,11 ± 3,13** | **+2,95 ± 2,64** | 0,067 | **65%** |
| `A4_comply_dose` như trên, kẻ tấn công tuân thủ | 49,29 ± 1,78 | +2,77 ± 1,53 | 0,016 | 62% |

## 2. Câu hỏi quan trọng nhất đã có câu trả lời: **trần của việc loại trừ là ~1 điểm**

`O_drop_mal` là oracle: server **biết chính xác** ai là kẻ tấn công và loại họ **ngay từ round 0**. Không bộ phát hiện nào có thể làm tốt hơn thế.

| Cách loại trừ | Mua được so với không phòng thủ | p |
|---|---|---|
| Luật của ta, cấm từ ~round 18 | +0,65 ± 1,41 | 0,358 |
| Luật của ta, cấm từ ~round 11,6 (bắt 9/10) | +1,08 ± 1,51 | 0,185 |
| **Oracle, hoàn hảo, từ round 0** | **+1,02 ± 1,20** | **0,131** |

Ba con số **nằm trong sai số của nhau**, và **không con số nào có ý nghĩa thống kê**.

Đây là kết quả dứt khoát, và nó bác bỏ cả hai cách bào chữa cho F1:

- **"Bộ phát hiện chưa đủ tốt"** — sai. `A6_fast_ban` bắt **9/10** kẻ tấn công, cấm oan **0/25** client thật thà, sớm hơn 6 round, và mua thêm được 0,43 điểm, nằm trong nhiễu.
- **"Phát hiện quá muộn"** — sai. Oracle loại từ round 0 cũng chỉ mua được 1,02 điểm.

> **Trần tuyệt đối của mọi phương pháp mà cần gạt duy nhất là loại client ra khỏi phép gộp, trên cấu hình này, là khoảng 1 điểm trên 4,50 điểm thiệt hại — và ngay cả cái trần đó cũng không đạt ý nghĩa thống kê ở n = 5.**

Lý do đã nêu ở `gate_f_results.md` mục 5, giờ được chứng minh chứ không còn là suy luận: kẻ tấn công `noise_disguise` **vẫn giữ 60% nhãn đúng**, và hai client là 20% dữ liệu của federation ở mức 8 ảnh/lớp. Vứt nó đi là vứt cả phần tốt. Đúng phép đánh đổi Gate A đã đo cho client nhiễu.

## 3. F2 trượt, và trượt theo hướng bất ngờ

| Liều kiểm toán | Kẻ tấn công tuân thủ giữ lại bao nhiêu % thiệt hại |
|---|---|
| 10/50 round (Gate E) | 82% |
| **25/50 round** | **94%** |

Ngưỡng ghi trước là ≤ 60%. `A4` − `A5` = **+0,18 ± 1,65**, t = 0,24, **p = 0,823**. Tăng liều gấp 2,5 lần **không** làm việc tuân thủ tốn kém hơn; nếu có thì hướng còn ngược lại.

**Vế "tuân thủ phải trả giá" của thế lưỡng nan chính thức chết.** Cộng với E1 và F1, khung "thế lưỡng nan của kẻ tấn công" không còn gì đứng được.

## 4. Nhưng cùng lượt đó lại cho **kết quả phòng thủ tốt nhất toàn đồ án**

`A5_refuse_dose` — sửa nhãn ở liều 25/50, **không loại ai, không nhận diện ai**:

| So với | Chênh | p |
|---|---|---|
| `A0_refuse` không phòng thủ | **+1,56 ± 1,21** | **0,045** |
| `A1_refuse_audit` liều 10/50 | +0,19 ± 2,31 | 0,86 |
| `M0_median` phòng thủ chuẩn | +0,10 | – |

**+1,56 với p = 0,045 là kết quả phòng thủ có ý nghĩa thống kê đầu tiên của đồ án.** Nó hoà với `median`, nhưng khác `median` ở một điểm quyết định: **nó không cần có kẻ địch mới có lãi** (`N_audit` +0,86 khi không ai tấn công), trong khi `median` là luật gộp chống kẻ địch thuần tuý (Gate B: chỉ +0,40 trên DTD).

Cảnh báo cần thiết: chênh so với liều 10/50 chỉ +0,19 và hoàn toàn nằm trong nhiễu. Không được nói "tăng liều thì tốt hơn" — chỉ được nói **"ở liều 25/50, hiệu ứng đủ lớn so với sai số để đạt p < 0,05, còn ở liều 10/50 thì chưa (p = 0,051)"**. Hai câu đó khác nhau.

## 5. Bức tranh sau ba cổng

| Cần gạt | Trần đo được | Có ý nghĩa? |
|---|---|---|
| **Loại client** (mọi biến thể, kể cả oracle) | **~+1,0** | **không** |
| Gộp bền vững `median` | +1,45 | có, p = 0,004 so với `N_control`; so với `A0` chưa đo ghép cặp |
| **Sửa nhãn** (không nhận diện ai) | **+1,56** | **có, p = 0,045** |
| Sửa nhãn khi **không có kẻ địch** | +0,86 / +1,01 | Pets p = 0,008 |

> Nhận diện giải được nhưng vô dụng. Cần gạt duy nhất có tác dụng là **sửa nhãn**, và nó hoạt động **mà không cần biết ai xấu**.

## 6. Việc còn lại

1. **Gate G** (`MODE = "gate_g"`, ~6,6 giờ): ngưỡng tự tin cho phần sửa nhãn — thứ duy nhất chưa thử, và phiên bản hiện tại là bản ngây thơ nhất (ghi đè **mọi** nhãn bằng `argmax` của một model chỉ đúng ~52% trên DTD). Tiêu chí ở `gate_g_plan.md`.
2. **Bổ sung vào Gate G**: `N_audit` ở liều 25/50 **chưa từng đo**. Nếu sửa nhãn là một luật gộp chứ không phải phòng thủ thì liều cao phải giúp cả khi không có kẻ địch. Đây là phép kiểm rẻ và trực tiếp nhất cho luận điểm chính.
3. Nhân sang OxfordPets để mọi phát biểu có hai dataset.
4. Dừng. Viết.
