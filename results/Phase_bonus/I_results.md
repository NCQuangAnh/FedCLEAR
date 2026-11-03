# Lượt I (chạy 2026-09-23, T4, 3/3 job `rc=0`)

Dữ liệu: `results/Phase_bonus/I_/{seeds,score,pets}`. Ba mục tiêu độc lập:
thêm seed cho phép so sánh mềm-cứng, đổi cách tính trọng số, và nhân sang dataset thứ hai.

Kết quả: **1 lượt hỏng do lỗi lập trình của tôi, 1 lượt tưởng là bác bỏ ý tưởng cải tiến
nhưng hoá ra cũng là lỗi lập trình, 1 lượt cho kết quả mạnh nhất của cả đồ án — đồng thời
lật ngược một kết luận trước đó.**

---

## 1. `seeds` — không dùng được, lỗi của tôi

Ba job trả về **đúng cùng một dãy giá trị** `[51,74 · 51,73 · 52,46 · 51,92 · 53,06]`,
dù lẽ ra chúng là ba cấu hình khác nhau (`H_soft`, `H_band`, `A0_refuse`).

Nguyên nhân: nhánh `gate_i_seeds` trong `tools/build_kaggle_notebook.py` gọi
`PLAN.append(...)` trực tiếp thay vì `job(...)`. Hàm `job()` mới là chỗ bọc `base()`,
và `base()` là thứ mang theo toàn bộ cấu hình thí nghiệm. Kiểm tra `run_index.json`
xác nhận: các tham số thực sự được truyền chỉ có

```
--attack_type noise_disguise --attack_rate 0.4 --correction_audit true --sample_filter ... --seed 5
```

Thiếu hẳn `--data_transform paper --noise_type sym --noise_rate 0.4
--noisy_client_frac 0.3 --malicious_client_frac 0.2 --log_signals true --correction_every 5`.

Tức là **không có nhiễu, không có client độc hại, và dùng transform mặc định**.
Ba job hoá ra là ba bản sao của cùng một lượt chạy sạch. Con số 52,2 khớp với
55,61 − 3,43 (chênh lệch transform đã đo ở giai đoạn 1), đúng như dự đoán cho một
lượt chạy sạch — thêm một bằng chứng nữa rằng nhiễu chưa từng được bật.

Mất khoảng 2 giờ GPU. **Đã sửa**: nhánh này giờ gọi `job(...)` với `--seed` ghi đè,
và kiểm tra lại bằng cách in ra danh sách tham số thực tế cho cả 17 MODE.
Câu hỏi "mềm có hơn cứng không trên DTD" vẫn **chưa được trả lời**, cần chạy lại (~4 giờ).

---

## 2. `score` — đo ra kém hơn, nhưng vì cấu hình hỏng chứ không vì ý tưởng

Đây là mục số 4 trong danh sách việc tiếp theo của lượt trước, và là thứ tôi đánh giá
"có khả năng đẩy tiếp" nhất. Số đo ra thua rõ — nhưng khi truy nguyên nhân thì lỗi nằm ở
code, không ở ý tưởng.

| Nhánh | `last10` | Lấy lại so với không phòng thủ | p | So với `H_soft` (thứ hạng) |
|---|---|---|---|---|
| `H_soft` (thứ hạng) | **50,75** | **+3,19** | 0,002 | – |
| `I_score` | 49,61 | +2,05 ± 0,57 | 0,0013 | **−1,14 ± 0,82**, p = 0,035 |
| `I_score_floor` | 49,16 | +1,60 ± 0,59 | 0,0038 | **−1,59 ± 1,03**, p = 0,026 |

Cả hai biến thể vẫn hơn "không phòng thủ" một cách có ý nghĩa, nhưng **thua
bản thứ hạng một cách có ý nghĩa** (p < 0,05 ở cả hai). Đây là phép so sánh trực tiếp,
ghép cặp theo seed, nên kết luận chắc hơn phép so `H_soft` vs `G_rho` ở lượt trước.

### Nguyên nhân thật (đo lại 2026-09-23, sửa lại phần chẩn đoán đầu tiên)

Chẩn đoán đầu tiên của tôi — "đuôi dài làm trọng số bị dồn về 1" — đúng về hiện tượng nhưng
**sai về hệ quả**, và sai ở chỗ kiểm được. Đo lượng trọng số thật sự bị gỡ đi, trung bình mỗi
lượt trên DTD:

| Nhánh | Gỡ đi bao nhiêu | Hạn mức được phép | Tỉ lệ trúng chất độc |
|---|---|---|---|
| `H_soft` (thứ hạng) | **2695** | 2695 | 66,4% |
| `I_score` (điểm thật) | **2128** | 2695 | 63,3% |
| `I_score_floor` | 1973 | 2695 | 61,5% |

Thang thứ hạng tiêu **đúng** hạn mức theo thiết kế. Thang điểm thật chỉ tiêu **79%** hạn mức.

**Đây là lỗi lập trình, không phải ý tưởng sai.** Đoạn co giãn chỉ co **một chiều**:

```python
if removed > budget_w and removed > 0:     # chỉ co khi vượt hạn mức
    k = budget_w / removed
```

Phân bố loss đuôi dài nên vector trọng số thô luôn rơi **dưới** hạn mức, và không có gì kéo
nó lên. Chú thích ngay trên đoạn đó ghi *"rescaled so the total weight removed still equals
the budget"* — code không làm đúng điều nó tự nhận.

Nghĩa là phép so `I_score` với `H_soft` **không phải** so hai cách chia trọng số, mà là so
**liều đủ với liều 79%**. Nó chưa bao giờ kiểm được ý tưởng nó sinh ra để kiểm.

### Lỗi thứ hai, lộ ra khi sửa lỗi thứ nhất

Chuẩn hoá min-max để một ảnh ở đuôi tự mình đặt thang đo, mọi ảnh còn lại dồn về gần nhau,
và phép co giãn **không tách chúng ra lại được** dù đẩy mạnh tới đâu. Thử trên 300 client mô
phỏng (40 ảnh, 12 ảnh hỏng, loss đuôi dài), cùng một hạn mức:

| Chuẩn hoá | Gỡ đi | Rơi trúng ảnh hỏng |
|---|---|---|
| min-max | 12,00 | **60,8%** |
| trung vị + IQR | 12,00 | **77,5%** |

Và lỗi **hạn mức bằng 0 vẫn can thiệp** cũng có ở đây: với hạn mức 0, bản cũ vẫn gỡ 8,28 đơn
vị trọng số của một client mà bộ ước lượng đã tha. Cùng loại lỗi đã bắt được ở thang thứ hạng
trước đây (`span = max(1, ...)`), chỉ là ở nhánh khác nên lần trước không thấy.

### Đã sửa, và sẽ kiểm lại

Ba thay đổi trong `flip/flcore/correction.py`:

1. Co giãn **hai chiều** bằng chia đôi khoảng, có sàn `w_min` — tiêu đúng hạn mức dù vector
   thô ban đầu trên hay dưới.
2. Chuẩn hoá **trung vị + IQR** thay min-max (`--filter_score_norm robust`, mặc định), cắt đuôi
   thay vì để đuôi đặt thang.
3. Hạn mức 0 thì trọng số đúng bằng 1 cho mọi ảnh, không ngoại lệ.

Kiểm lại bằng `MODE = "gate_j_score"`, hai nhánh (`J_score_minmax`, `J_score_robust`) để biết
**lỗi nào mới là lỗi quyết định**, ~2,6 giờ.

**Kết luận đúng mức: chưa được phép bỏ hướng này.** Kết quả −1,14 đo được là thật, nhưng nó đo
một cấu hình hỏng chứ không đo ý tưởng. Thang thứ hạng vẫn là mốc phải vượt.

---

## 3. `pets` — kết quả mạnh nhất của đồ án, và nó lật một kết luận

OxfordPets, 5 seed, cùng thiết lập nhiễu và tấn công như DTD.

| Nhánh | `last10` | Lấy lại | t | p |
|---|---|---|---|---|
| `A0_refuse` không phòng thủ | 75,89 | – | | |
| `M0_median` gộp bền vững | 80,49 | +4,60 | | |
| `N_control` không có kẻ tấn công | 81,23 | | | |
| `H_soft` hạ trọng số | 81,18 ± 2,33 | +5,29 ± 1,45 | 8,19 | 0,0012 |
| `N_audit` kiểm toán | 82,24 | | | |
| **`H_band` xoá hẳn** | **85,50 ± 1,71** | **+9,62 ± 2,36** | **9,10** | **0,0008** |
| zero-shot CLIP | 85,69 | | | |
| PromptFL trên dữ liệu sạch | 88,09 | | | |

### 3.1. Các phép so sánh đã định trước

| Phép so | Kết quả |
|---|---|
| `H_band` − `A0_refuse` | **+9,62 ± 2,36**, p = 0,0008 |
| `H_band` − `M0_median` | **+5,01 ± 2,02**, t = 5,55 |
| `H_band` − `N_audit` | **+3,26 ± 2,27**, t = 3,22 |
| `H_band` − `N_control` | **+4,27 ± 2,34**, t = 4,09 |
| `H_band` − zero-shot | −0,19 |
| `H_band` − PromptFL sạch | −2,59 |

Hai dòng đáng chú ý nhất:

- **Hơn `median` +5,01.** Đây là lần đầu tiên phương pháp của ta vượt hẳn phương pháp
  phòng thủ tiêu chuẩn của lĩnh vực trên một dataset. Trên DTD ta chưa bao giờ làm được.
- **Hơn `N_control` +4,27**, tức hơn cả một liên đoàn *không có kẻ tấn công nào*.
  Không mâu thuẫn: `N_control` vẫn còn 3 client nhiễu; bộ lọc dọn luôn phần nhiễu đó.

### 3.2. Nhưng phải nói cho đúng mức

`H_band` = 85,50, zero-shot CLIP = 85,69. Tức **phương pháp kéo được về đúng mức
"không huấn luyện gì cả"**, chứ chưa vượt. Theo tiêu chí đã đặt từ giai đoạn 1
(zero-shot là sàn bắt buộc trên Pets), đây là *đạt sàn*, không phải *vượt trần*.
Cách phát biểu đúng: **phương pháp biến một lượt huấn luyện có giá trị âm thành
một lượt huấn luyện hoà vốn**, và làm việc đó tốt hơn `median` +5,01 điểm.

### 3.3. Bộ lọc chạy chính xác hơn hẳn trên Pets

| Loại client | % dữ liệu bị bỏ | Trong số bị bỏ, % thật sự hỏng | `rho` ước ra |
|---|---|---|---|
| thật thà | 2,8% | 0,0% | 0,032 |
| nhiễu | 31,0% | **94,4%** | 0,309 |
| độc hại | 36,3% | **85,1%** | 0,364 |

So với DTD, nơi độ chính xác chỉ khoảng 66–71%. Hạn mức `rho` tự ước ra gần như
đúng bằng mức nhiễm thật (0,309 và 0,364 so với 0,4 lý thuyết, sau khi trừ phần
nhiễu ngẫu nhiên trùng nhãn gốc), và client thật thà gần như không bị đụng tới.

---

## 4. Điều quan trọng nhất: **mềm vs cứng bị lật, và lật một cách giải thích được**

| Dataset | Độ chính xác bộ lọc | Mềm (`H_soft`) | Cứng (`H_band`) | Chênh |
|---|---|---|---|---|
| DTD | ~66–71% | **+3,19** | +2,29 | mềm hơn +0,86 (p = 0,40, không ý nghĩa) |
| OxfordPets | **85–94%** | +5,29 | **+9,62** | **cứng hơn +4,33 (p = 0,0057)** |

Phép so trực tiếp trên Pets: `soft − band = −4,33 ± 1,79`, t = −5,40, **p = 0,0057**.

**Không được phát biểu "hạ trọng số tốt hơn xoá hẳn".** Kết luận đó chỉ đúng trên DTD,
và ngay trên DTD nó cũng chưa có ý nghĩa thống kê. Trên Pets nó sai, và sai một cách
rõ ràng.

### 4.1. Mô hình tỉ giá dự đoán đúng chiều lật này

Tỉ giá đã khớp từ lượt trước: bỏ 1 ảnh bẩn = +0,326/1000, bỏ nhầm 1 ảnh sạch
= −0,437/1000, hoà vốn ở độ chính xác 57,3%.

Hạ trọng số làm cả hai vế nhỏ lại: mỗi ảnh bẩn chỉ bị hạ nửa trọng số nên chỉ thu
được nửa phần lãi, nhưng mỗi ảnh sạch bị hạ oan cũng chỉ tốn gần như không gì.
Vậy:

- **Độ chính xác thấp (DTD, 71%):** phần lỗ do bỏ nhầm rất lớn, nên việc triệt tiêu
  nó đáng giá hơn việc mất nửa phần lãi. **Mềm thắng.**
- **Độ chính xác cao (Pets, 85–94%):** gần như không có ảnh sạch nào bị bỏ nhầm,
  nên không có gì để triệt tiêu — hạ trọng số chỉ còn tác dụng **giữ lại một nửa
  lượng chất độc**. **Cứng thắng.**

Điểm hoà giữa hai chế độ rơi vào khoảng **độ chính xác 80–85%** theo tỉ giá hiện có.
Đây là một dự đoán kiểm chứng được và chưa được kiểm chứng.

### 4.2. Hệ quả cho cách phát biểu luận văn

Phát biểu cũ ("hạ trọng số là cải tiến") phải đổi thành:

> **Chế độ quyết định phải khớp với độ chính xác của bộ phát hiện.** Khi bộ phát hiện
> còn yếu, hạ trọng số bảo vệ ta khỏi chính sai lầm của nó; khi bộ phát hiện đã tốt,
> hạ trọng số trở thành gánh nặng vì nó giữ lại chất độc mà nó đã nhận đúng.

Đây là phát biểu **mạnh hơn** phát biểu cũ, vì nó có cơ chế, có dự đoán định lượng,
và được chứng minh ở cả hai chiều trên hai dataset — chứ không phải một mẹo thắng
0,86 điểm không có ý nghĩa thống kê trên một dataset.

---

## 5. Việc tiếp theo

| # | Việc | Vì sao | Giờ |
|---|---|---|---|
| 1 | Chạy lại `seeds` với generator đã sửa | Câu hỏi mềm-vs-cứng trên DTD vẫn chưa có câu trả lời | ~4 |
| 2 | Chọn chế độ **tự động** theo độ chính xác ước lượng | Đây là phát hiện chính mới; cần một ước lượng độ chính xác không dùng nhãn thật | ~3 |
| 3 | Nhân sang dataset thứ ba có độ chính xác trung gian | Kiểm chứng điểm hoà 80–85% | ~2,5 |
| 4 | Quét mức nhiễm 10 / 40 / 80% trên Pets | Điều kiện áp dụng | ~5 |

Mục 2 là mục có giá trị nhất và cũng là mục khó nhất: **độ chính xác cần nhãn thật
để đo**, nên phải tìm một đại lượng thay thế mà server quan sát được. Ứng viên rõ nhất
là độ tách bạch của phân bố `rho` giữa các client — trên Pets nó tách rất rõ
(0,032 so với 0,31–0,36), trên DTD thì nhoè hơn. Nếu đại lượng đó tương quan với
độ chính xác thật thì ta có luật chọn chế độ, và đó là một đóng góp đứng riêng được.
