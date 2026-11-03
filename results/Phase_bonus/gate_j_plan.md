# Kế hoạch lượt J — ghi TRƯỚC khi chạy (2026-09-23)

Ba mục ưu tiên rút ra từ `I_results.md`. Tiêu chí dưới đây viết trước, không sửa sau khi thấy số.

---

## Mục 1 — chạy lại `seeds` (lỗi đã sửa)

**Vì sao.** Lượt `gate_i_seeds` trước đó vô hiệu: nhánh gọi `PLAN.append(...)` trực tiếp
thay vì `job(...)`, nên `base()` không chạy và toàn bộ cấu hình nhiễu/tấn công bị mất.
Đã sửa, và đã thêm bước kiểm tra in ra danh sách tham số thật cho cả 16 MODE.

**Chạy.** `MODE = "gate_i_seeds"`, `DATASETS = ["dtd"]`, seed 5–9.
Ba job: `H_soft_s5`, `H_band_s5`, `A0_refuse_s5`. Khoảng 4 giờ.

**Câu hỏi.** Trên DTD, hạ trọng số có thật sự hơn xoá hẳn không? Ở n = 5 hiệu là
+0,86 ± 2,07 (p = 0,40). Gộp 10 seed sẽ thu hẹp khoảng đó khoảng √2 lần.

**Tiêu chí.**

| Kết quả | Đọc là |
|---|---|
| `H_soft` − `H_band` > 0 với p < 0,05 ở n = 10 | mềm thắng trên DTD, khẳng định được |
| khoảng tin cậy vẫn chứa 0 | hiệu quá nhỏ để đo ở quy mô này; **ngừng theo hướng này**, không thêm seed lần ba |
| dấu đổi chiều | +0,86 ở n = 5 là nhiễu, phải ghi lại là nhiễu |

---

## Mục 2 — để máy chủ **tự chọn** chế độ

**Vấn đề.** Không chế độ nào thắng ở mọi nơi:

| Dataset | Độ chính xác bộ lọc | Mềm | Cứng | Ai thắng |
|---|---|---|---|---|
| DTD | 65,7% | +3,19 | +2,29 | mềm, +0,86 (p = 0,40) |
| OxfordPets | 85,3% | +5,29 | +9,62 | **cứng, +4,33 (p = 0,0057)** |

Chế độ đúng là hàm của **độ chính xác**. Nhưng độ chính xác cần nhãn thật để đo, mà máy chủ
không có nhãn thật. Cần một đại lượng thay thế **máy chủ quan sát được**.

**Đại lượng chọn: `dis_baseline`.** Phân vị thấp của mức bất đồng giữa các client và mô hình
toàn cục — tức **tỉ lệ sai của chính người thầy** trên nhóm client sạch nhất mà nó thấy.
Máy chủ đã tính sẵn đại lượng này cho việc khác, nên **không tốn thêm một byte truyền tin nào**.

**Hiệu chỉnh ngoại tuyến, 0 giờ GPU** (`tools/simulate_filter_mode.py`, chạy trên 460 vòng
probe đã ghi của lượt H_ và I_):

| | `dis_baseline` trung bình | Độ chính xác thật |
|---|---|---|
| DTD | 0,344 | 65,7% |
| OxfordPets | 0,135 | 85,3% |

Tương quan gộp r = **−0,533**; hồi quy `precision ≈ 0,868 − 0,470 · baseline`.
Ngưỡng **0,22** rơi vào vùng trống giữa hai dataset.

Phát lại luật trên dữ liệu cũ:

| | Chọn CỨNG | Số lần đổi chế độ mỗi lượt |
|---|---|---|
| DTD | 11,3% số vòng | 0,8 |
| OxfordPets | 79,1% số vòng | 1,0 |

Đúng chế độ đã thắng trên từng dataset, và **không dao động** (đổi đúng một lần, lúc đầu).

**Hệ số làm trơn** của trung bình động cũng chọn ngoại tuyến. Thử cả bốn mức trên đúng bộ
dữ liệu đó:

| Hệ số | DTD chọn cứng | Pets chọn cứng | Đổi chế độ/lượt | Số lần đổi khi baseline dao động 0,10↔0,40 |
|---|---|---|---|---|
| 0,5 | 17,0% | 82,6% | 1,0 | **29** |
| 0,4 | 16,1% | 81,7% | 1,0 | 3 |
| **0,3** | **11,3%** | **79,1%** | **0,8** | **1** |
| 0,2 | 8,3% | 73,9% | 0,9 | 1 |

Chọn **0,3**: cùng đáp án ở chỗ đo được, ổn định hơn hẳn ở chỗ không đo được.
Cột cuối là trường hợp bệnh lý dựng thủ công, không phải dữ liệu thật — nhưng một luật có thể
dao động 29 lần trong 30 vòng thì không nên để nguyên chỉ vì dữ liệu hiện có chưa bắt nó.

**Chạy.** `MODE = "gate_j_auto"`, một job `H_auto` trên DTD rồi trên OxfordPets.
Khoảng 2,6 giờ cho cả hai.

**Đây là phép kiểm nhất quán, KHÔNG phải phép kiểm độc lập** — ngưỡng 0,22 được khớp
trên chính hai dataset này. Nó chỉ trả lời một câu: *đổi chế độ giữa chừng có giống chạy
chế độ đó từ vòng 0 không?* Đó là rủi ro thật, và là lý do nhánh này tồn tại.

**Tiêu chí.**

| Kết quả | Đọc là |
|---|---|
| DTD `H_auto` trong khoảng ±0,5 của `H_soft` (50,75) **và** Pets `H_auto` trong ±0,5 của `H_band` (85,50) | đạt; sang mục 3 |
| lệch quá 0,5 ở một trong hai | chuyển chế độ giữa chừng **không** tương đương; phải quyết một lần ở vòng probe đầu rồi khoá |
| rơi về phía chế độ thua | luật hỏng ở mức cơ chế, dừng hướng này |

---

## Mục 3 — phép kiểm **thật**: dataset chưa từng thấy

Ngưỡng 0,22 khớp trên **đúng hai điểm**. Phải kiểm trên dataset thứ ba.

**Bốn nhánh** — kiểm một luật *chọn lựa* thì phải chạy cả hai thứ nó chọn giữa, cộng chính nó:
`A0_refuse` (mốc không phòng thủ, hai dataset này chưa có), `H_soft`, `H_band`, `H_auto`.

**Dự đoán vị trí, suy từ độ chính xác sạch của PromptFL** (tức trần của người thầy, vốn là
thứ `dis_baseline` đo):

| Dataset | Số lớp | PromptFL sạch | `dis_baseline` dự kiến | Chế độ dự kiến |
|---|---|---|---|---|
| **EuroSAT** | 10 | thấp | cao, > 0,22 | **MỀM** |
| **Caltech101** | 102 | 90,9 | thấp, < 0,22 | **CỨNG** |

**Chạy.** `MODE = "gate_j_regime"`, một dataset mỗi phiên.
EuroSAT ~1,5 giờ ở 5 seed (5,2 giây/vòng). Caltech101 ~11,6 giờ ở 5 seed
(20,6 giây/vòng) — nên để `TIMES = 3` hoặc `BUDGET_HOURS = 12`.

**Tiêu chí.**

| Kết quả | Đọc là |
|---|---|
| `H_auto` bám nhánh **thắng** trên cả hai dataset | luật chọn chế độ đứng vững; đây là đóng góp riêng, viết được vào paper |
| bám nhánh thắng ở 1/2 | ngưỡng phụ thuộc dataset, chưa phải luật; phải tìm đại lượng khác |
| bám nhánh **thua** | luật bị bác; ghi lại và dừng |

### Điều phải nói trước, vì nó là điểm yếu thật

`dis_baseline` dự báo độ chính xác **giữa các dataset** (r = −0,53) nhưng **gần như không dự báo
trong cùng một dataset**: trên DTD, những vòng luật gọi "cứng" lại có độ chính xác **thấp hơn**
(0,618 so với 0,665). Nghĩa là nó là **bộ nhận diện chế độ ở mức dataset**, không phải bộ ước
lượng độ chính xác ở mức vòng. Điều đó đủ cho việc đang cần — chọn chế độ vốn là câu hỏi mức
dataset — nhưng phải phát biểu đúng như vậy, không được nói quá.

Và toàn bộ luật khớp trên **hai điểm dữ liệu**. Mục 3 chính là thứ quyết định nó là quy luật
hay là trùng hợp.

---

## Không làm trong lượt này

| Việc | Vì sao hoãn |
|---|---|
| Food101 | Là dataset **đúng giữa ranh giới** (PromptFL sạch ~76 → baseline ~0,25), nên là phép kiểm sắc nhất. Nhưng 96 giây/vòng → ~20 giờ cho 4 nhánh. Để sau EuroSAT và Caltech |
| Trọng số theo điểm thật | Đã bác ở lượt I (−1,14, p = 0,035) |
| Luật lớp | Đã thua ba lần liên tiếp |
| Quét mức nhiễm 10/40/80% | Là câu hỏi "điều kiện áp dụng", chỉ đáng hỏi sau khi luật chọn chế độ đứng vững |
