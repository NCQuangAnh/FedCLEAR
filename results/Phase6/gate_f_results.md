# Kết quả Gate F (chạy 2026-09-21, T4, 5,46 giờ)

Dữ liệu: `results/Phase6/GateF/`. **5/5 job `rc=0`**, DTD, 5 seed. `MODE = "gate_f"` (F1 và F3).

## 1. Phán quyết theo tiêu chí ghi trước

| # | Tiêu chí | Ngưỡng | Kết quả | |
|---|---|---|---|---|
| **F1** | Loại trừ kẻ từ chối xoá được cuộc tấn công | thiệt hại còn ≤ 25% | **còn 85%** | **TRƯỢT** |
| **F3** | `median` + kiểm toán + loại trừ hơn `median` một mình | ≥ +2,0 điểm | **−1,62** | **TRƯỢT** |
| F2 | Liều kiểm toán 25/50 round | ≤ 60% | chưa chạy | – |

Không sửa ngưỡng sau khi nhìn số.

## 2. Bảng accuracy

| Job | `last10` | Thiệt hại so với `N_control` | t (n=5) | p |
|---|---|---|---|---|
| `N_control` | 52,06 ± 0,74 | – | | |
| `A0_refuse` (không phòng thủ) | 47,56 ± 2,91 | +4,50 ± 2,47 | 4,08 | **0,015** |
| `A3_exclude` (kiểm toán + loại trừ) | 48,21 ± 2,66 | +3,85 ± 2,15 | 4,00 | **0,016** |
| `M0_median` | 49,01 ± 1,87 | +3,05 ± 1,17 | 5,81 | **0,004** |
| `M1_median_full` (median + kiểm toán + loại trừ) | 47,39 ± 3,43 | +4,67 ± 2,83 | 3,69 | **0,021** |

**F1:** `A3` − `A0` = **+0,65 ± 1,41**, t = 1,04, **p = 0,358**. Loại trừ mua được 0,65 điểm trên 4,50 điểm thiệt hại, và không phân biệt được với 0.

**F3:** `M1` − `M0` = **−1,62 ± 2,29**, t = −1,58, p = 0,189. Ghép giao thức vào `median` làm **tệ đi**.

## 3. Bộ phát hiện chạy đúng như hiệu chỉnh — vấn đề không nằm ở đó

Luật loại trừ trực tuyến (`mad`, k = 2,0, floor = 0,12, patience = 3) đã hiệu chỉnh ngoại tuyến trên bản ghi Gate E. Kết quả **trên GPU, trong vòng lặp thật**, nơi mỗi lệnh cấm làm đổi bản gộp và do đó đổi `r_align` của mọi client còn lại — thứ mà mô phỏng ngoại tuyến không tái hiện được:

| Lượt | Thật thà bị cấm | Nhiễu bị cấm | **Độc hại bị cấm** |
|---|---|---|---|
| `dtd_A3_exclude` | **0/25** | **0/15** | **7/10** |
| `dtd_M1_median_full` | 1/25 | 1/15 | **9/10** |

Mô phỏng ngoại tuyến dự đoán 7/10 và 0/25 cho đúng cấu hình đó. **Thực tế khớp chính xác.** Vòng phản hồi không phá luật.

Đặt cạnh Gate B thì chênh lệch rất rõ: `multikrum` trên OxfordPets loại client nhiễu **gấp 17,7 lần** client thật thà và làm mô hình tệ hơn 1,63 điểm; luật này loại **7–9 trong 10 kẻ tấn công** và chạm vào **0–1 trong 25** client thật thà.

**Nhận diện không phải nút thắt. Nút thắt là phản ứng.**

Thời điểm cấm, từng seed của `A3_exclude`:

| seed | client bị cấm | round cấm | vai trò |
|---|---|---|---|
| 0 | [6] | 30 | độc hại |
| 1 | [2, 6] | 10, 30 | độc hại, độc hại |
| 2 | [3, 9] | 10, 10 | độc hại, độc hại |
| 3 | [] | – | (không cấm ai) |
| 4 | [3, 4] | 10, 10 | độc hại, độc hại |

## 4. Vì sao loại trừ không giúp: thiệt hại **tăng dần**, mà loại trừ chỉ chặn phần sau

Thiệt hại theo round (trung bình 5 seed):

| round | 5 | 10 | 15 | 20 | 25 | 30 | 35 | 40 | 45 | 49 |
|---|---|---|---|---|---|---|---|---|---|---|
| `A0_refuse` | +3,44 | +2,12 | +2,13 | +3,17 | +3,05 | +3,64 | +4,12 | +4,86 | +5,05 | +4,49 |
| `A3_exclude` | +4,93 | +1,23 | +2,09 | +2,57 | +2,22 | +2,19 | +3,16 | +2,19 | +3,56 | +4,10 |

Cuộc tấn công **cộng dồn**: từ +2,1 ở round 10 lên +5,0 ở round 45. Loại trừ giữ thiệt hại thấp hơn ở khúc giữa (round 25–45: 2,19–3,56 so với 3,05–5,05), nhưng tới `last10` thì khoảng cách teo lại còn 0,65 và biến động seed nuốt hết.

Quyết định cấm sớm nhất rơi vào **round 10**, vì probe chạy mỗi 5 round và `patience = 3`. Kẻ tấn công được 10 round miễn phí, và ở một seed thì không bị cấm lần nào.

## 5. Kết quả khó chịu nhất: thêm loại trừ vào lượt đã kiểm toán làm **tệ đi**

`A3_exclude` khác `A1_refuse_audit` của Gate E **đúng một thứ**: bật loại trừ. Ghép theo seed:

| seed | 0 | 1 | 2 | 3 | 4 | trung bình |
|---|---|---|---|---|---|---|
| `A1_refuse_audit` (Gate E) | 44,06 | 52,67 | 49,04 | **49,00** | 49,88 | 48,93 |
| `A3_exclude` (Gate F) | 43,76 | 50,88 | 48,27 | **49,00** | 49,14 | 48,21 |
| chênh | −0,30 | −1,79 | −0,77 | **0,00** | −0,74 | **−0,72** |

Âm ở 4/5 seed. Seed 3 là seed **không cấm ai**, và hai lượt ra **đúng cùng một con số tới hai chữ số thập phân** — xác nhận rằng ghép cặp theo seed giữa các phiên là chính xác tuyệt đối, chứ không phải giả định.

Cách giải thích khớp với mọi thứ đã đo: **loại bỏ một client thì mất luôn dữ liệu của nó.** Kẻ tấn công `noise_disguise` lật 40% nhãn, tức 60% nhãn còn đúng; trong cấu hình 8 ảnh/lớp, Dirichlet α = 0,1, hai client là 20% dữ liệu của cả federation. Gate A đã đo đúng phép đánh đổi này cho client nhiễu: bỏ họ đi chỉ mua được ≤ 3,1 điểm, vì mất dữ liệu gần bằng mất do nhiễu. Kẻ tấn công nguỵ trang thành client nhiễu thì **cũng đáng giá xấp xỉ một client nhiễu**.

## 6. Điều này khớp với cả bốn cổng trước, và nó là luận điểm của bài

| Cổng | Đo gì | Kết luận |
|---|---|---|
| A | Bỏ client nhiễu | mua ≤ 3,1 điểm; sửa nhãn mới là hướng đúng |
| B | Gộp bền vững (bản chất là loại trừ) | có tác dụng ở 1/4 tổ hợp, và loại nhầm đối tượng |
| C | Suy đoán ý đồ từ hình học prompt | phụ thuộc số lớp, không hơn baseline ở chỗ baseline mạnh |
| E | Kiểm chứng sự tuân thủ | **phát hiện được**, AUC 0,91–0,99; và bản thân việc sửa nhãn **có lãi** +0,86/+1,01 |
| **F** | **Loại trừ kẻ tấn công đã nhận diện đúng** | **+0,65, không có ý nghĩa** |

> Trong federated prompt learning few-shot, **loại bỏ client không phải cần gạt có tác dụng** — không với client nhiễu, không với client độc hại, không khi làm bằng luật gộp bền vững, và không ngay cả khi nhận diện gần như hoàn hảo. Thứ có tác dụng là **thay cập nhật của client bằng một cập nhật huấn luyện dưới nhãn của model toàn cục**, và thứ đó có lãi ngay cả khi không có kẻ địch nào.
>
> Nhận diện giải được. Nhận diện không phải bài toán.

**Khung "thế lưỡng nan của kẻ tấn công" như một cơ chế phòng thủ coi như chết.** E1 trượt, F1 trượt, F3 trượt. Không tìm cách cứu nó nữa. Phần còn sống là (a) bộ phát hiện sự từ chối, và (b) phát hiện rằng gộp có sửa nhãn tự nó là một luật gộp tốt hơn.

## 7. Hai lượt chẩn đoán cuối, rồi chốt

Ghi trước, **không phải để cứu F1** mà để giải thích nó đủ chắc cho phần thảo luận. Cả hai nằm trong `MODE = "gate_f_dose"`, khoảng 6,8 giờ, DTD:

| Job | Hỏi gì | Đọc kết quả thế nào |
|---|---|---|
| `O_drop_mal` | Loại trừ **hoàn hảo, từ round 0** mua được bao nhiêu? Đây là **trần tuyệt đối** của mọi phương pháp mà cần gạt duy nhất là vứt client đi | Nếu thiệt hại còn ≥ 3,0 (so với +4,50): loại trừ là **sai về nguyên tắc**, và mục 5–6 được chứng minh. Nếu về gần 0: loại trừ đúng, và luật của ta chỉ **quá chậm** |
| `A6_fast_ban` | Cùng luật, probe mỗi 2 round, `patience = 2`, quyết định đầu ở **round 4** thay vì round 10 | Nếu tốt hơn `A3_exclude` rõ rệt thì độ trễ là nguyên nhân; nếu không thì không phải |
| `A5_refuse_dose`, `A4_comply_dose` | F2 như đã ghi trước: liều 25/50 round | ngưỡng ≤ 60% |

Hai job F2 vẫn chạy vì đó là tiêu chí đã ghi trước của Gate F và phải được đo, dù khung lưỡng nan đã chết — liều kiểm toán còn là biến của **luật gộp có sửa nhãn**, thứ đang sống.

**Sau lượt này thì dừng thí nghiệm mới và viết.** Phương án lui ở `docs/phase6_plan.md` mục 5 là đích thật, nhưng với luận điểm mạnh hơn bản ghi ở đó: không phải "chúng tôi đo nhiễu nhãn trong FPL", mà "**nhận diện giải được, phản ứng thì không — và cần gạt mà cả lĩnh vực đang dùng là cần gạt sai**".
