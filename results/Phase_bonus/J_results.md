# Lượt J, phiên 1–3 (chạy 2026-09-24, T4, 7/7 job `rc=0`)

Dữ liệu: `results/Phase_bonus/J_/{seeds,auto/dtd,auto/pets,score}`.
Tiêu chí của cả ba phiên viết trước khi chạy, ở `gate_j_plan.md`, không sửa sau khi thấy số.

**Tóm tắt: 1 giả thuyết bị bác, 1 phương pháp mới đạt cả hai tiêu chí, 1 chẩn đoán lỗi được xác nhận.**

---

## Phiên 1 — `seeds`: giả thuyết "mềm hơn cứng" **bị bác**

Cấu hình lần này đúng (kiểm `run_index.json`: có đủ `--noise_type sym --noise_rate 0.4
--noisy_client_frac 0.3 --malicious_client_frac 0.2`). Seed 5–9, ghép cặp theo seed.

| Nhánh | `last10` | Lấy lại |
|---|---|---|
| `A0_refuse` | 47,39 ± 1,78 | – |
| `H_soft` | 50,06 ± 1,39 | **+2,67 ± 1,16**, p = 0,0068 |
| `H_band` | 50,42 ± 1,46 | **+3,02 ± 2,40**, p = 0,0482 |

**Hiệu mềm − cứng trên seed mới: −0,36 ± 1,40, p = 0,60. Dấu đã đảo chiều.**

Gộp cả 10 seed:

| | `last10` | So `A0_refuse` |
|---|---|---|
| `H_soft` | 50,41 | **+2,93 ± 1,06**, t = 8,77, p < 0,0001 |
| `H_band` | 50,13 | **+2,66 ± 1,76**, t = 4,78, p = 0,0010 |
| **mềm − cứng** | | **+0,28 ± 1,62, t = 0,54, p = 0,60** |

Tiêu chí ghi trước nói: *"dấu đổi chiều → +0,86 ở n = 5 là nhiễu, phải ghi lại là nhiễu"*
và *"khoảng tin cậy vẫn chứa 0 → ngừng theo hướng này, không thêm seed lần ba"*.
**Cả hai điều kiện đều xảy ra.** Kết luận: trên DTD, hạ trọng số và xoá hẳn **không phân biệt
được**. Con số +0,86 của lượt H là nhiễu lấy mẫu. Không thêm seed nữa.

Điều này **không** làm yếu kết quả trên Pets: ở đó hiệu là 4,33 với p = 0,0057, lớn hơn
độ lệch chuẩn của hiệu trên DTD gấp ba lần. Hai dataset thật sự khác chế độ, chỉ là DTD nằm ở
vùng hai chế độ ngang nhau chứ không phải vùng mềm thắng.

Cả hai nhánh vẫn hơn "không phòng thủ" rất chắc (p < 0,001 ở n = 10). Phần lợi đến từ
**việc có lọc**, không từ **cách lọc**.

---

## Phiên 2 — `auto`: **đạt cả hai tiêu chí**

Máy chủ tự chọn chế độ từ `dis_baseline`, ngưỡng 0,22, hệ số làm trơn 0,3.
Không dùng một nhãn thật nào.

### 2a. DTD

| | `last10` |
|---|---|
| `H_soft` (mềm, ép cứng tay) | 50,75 |
| **`H_auto`** | **50,76** |
| `H_band` (cứng, ép cứng tay) | 49,85 |

Tiêu chí: `|H_auto − H_soft| ≤ 0,5`. Thực tế **0,01**. **ĐẠT.**

Ghép cặp theo seed, hiệu `H_auto − H_soft = +0,01 ± 0,02`. Ba trong năm seed **trùng tới
từng chữ số**. Đúng như mong đợi, vì luật chọn mềm ở 95,6% số vòng.

### 2b. OxfordPets

| | `last10` |
|---|---|
| `H_soft` | 81,18 |
| **`H_auto`** | **85,15** |
| `H_band` | 85,50 |
| zero-shot CLIP | 85,69 |

Tiêu chí: `|H_auto − H_band| ≤ 0,5`. Thực tế **0,35**. **ĐẠT.**

`H_auto − H_soft = +3,97 ± 2,13`, t = 4,16 — nó **tránh được chế độ thua**.
`H_auto − A0_refuse = +9,27 ± 2,89`, t = 7,17.

### Luật chọn đúng như mô phỏng ngoại tuyến dự báo

| | Mô phỏng dự báo chọn cứng | Thực tế chọn cứng | Đổi chế độ |
|---|---|---|---|
| DTD | 11,3% | **4,4%** | 0,4 lần/lượt |
| OxfordPets | 79,1% | **69,6%** | 1,0 lần/lượt |

Lệch vài điểm phần trăm, nhưng **cùng phía và cách xa nhau**, và không dao động.
Phần lệch là do mô phỏng chạy trên bản ghi của `H_band`/`H_soft`, còn lượt thật thì bộ lọc
đổi chế độ nên quỹ đạo huấn luyện cũng đổi theo — vòng lặp phản hồi mà mô phỏng không có.

### Phải nói cho đúng mức

Đây **chưa phải phép kiểm độc lập**. Ngưỡng 0,22 được khớp trên chính DTD và Pets.
Phiên này chỉ trả lời một câu — *đổi chế độ giữa chừng có tương đương chạy chế độ đó từ đầu
không* — và câu trả lời là **có**. Phép kiểm thật là phiên 4 trên EuroSAT và Caltech101.

Và trên Pets, `H_auto` = 85,15 so với zero-shot 85,69: vẫn là **đạt sàn, chưa vượt**.

---

## Phiên 3 — `score`: chẩn đoán lỗi **được xác nhận**

| Nhánh | `last10` | Ghi chú |
|---|---|---|
| `I_score` (bản hỏng, lượt I) | 49,61 | thua rank −1,14, p = 0,035 |
| `J_score_minmax` (sửa hạn mức) | 50,50 | **+0,89 ± 0,61 so bản hỏng**, t = 3,24 |
| `J_score_robust` (sửa hạn mức + đổi chuẩn hoá) | **50,95** | **+0,45 ± 0,40 so minmax**, t = 2,54 |
| `H_soft` (thang thứ hạng) | 50,75 | mốc phải vượt |

Tách được đóng góp của từng lỗi:

| Lỗi | Nó đáng bao nhiêu điểm |
|---|---|
| Co giãn một chiều (tiêu thiếu 21% hạn mức) | **+0,89** |
| Chuẩn hoá min-max (một ảnh đuôi đặt cả thang) | **+0,45** |
| **Tổng phục hồi** | **+1,34** |

Cộng lại đúng bằng khoảng cách đã mất: 49,61 + 1,34 = 50,95, so với rank 50,75.

**So với thang thứ hạng: +0,20 ± 0,77, t = 0,59 — hoà.**

Kết luận đúng mức: chẩn đoán "đó là lỗi code, không phải ý tưởng sai" **được xác nhận** —
số đo khớp với dự đoán về cả dấu lẫn độ lớn. Nhưng ý tưởng sau khi sửa chỉ **hoà** với thang
thứ hạng, **không thắng**. Nó được cứu khỏi kết luận sai, chứ chưa thành cải tiến.

---

## Điều cả ba phiên cùng nói

Trên DTD, mọi biến thể đều rơi vào 50,1 – 51,0 và lấy lại +2,7 đến +3,2:

| | `last10` |
|---|---|
| `J_score_robust` | 50,95 |
| `H_auto` | 50,76 |
| `H_soft` | 50,75 |
| `H_band` | 49,85 |

Không phân biệt được nhau. Trên Pets thì mềm và cứng chênh 4,33.

**Cách lọc chỉ quan trọng ở nơi bộ lọc đủ chính xác để lựa chọn có ý nghĩa.** Ở DTD, độ chính
xác 66% nằm sát ngưỡng hoà vốn 57,3%, nên mọi cách tiêu hạn mức đều cho kết quả gần như nhau.
Ở Pets, độ chính xác 85% thì cách tiêu hạn mức quyết định 4 điểm.

Đây là lý do luật chọn chế độ tự động có giá trị: nó **không cần biết mình đang ở dataset nào**,
và ở nơi lựa chọn không quan trọng thì nó cũng không gây hại.

---

## Việc tiếp theo

| # | Việc | Vì sao |
|---|---|---|
| 1 | **Phiên 4a/4b — `gate_j_regime` trên EuroSAT rồi Caltech101** | Phép kiểm độc lập duy nhất. Ngưỡng 0,22 mới chỉ khớp trên hai điểm |
| 2 | Food101 | Nằm đúng ranh giới (baseline ~0,25). Đắt (~20 giờ) nhưng là phép kiểm sắc nhất |
| 3 | Đo lại độ chính xác bộ lọc dưới `auto` | Mô hình tỉ giá dự đoán auto phải đạt độ chính xác ít nhất bằng nhánh thắng ở mỗi dataset; chưa kiểm |

**Không làm:** thêm seed cho mềm-vs-cứng trên DTD (đã bác, đúng theo tiêu chí ghi trước);
thang điểm thật như một cải tiến riêng (hoà, không thắng).
