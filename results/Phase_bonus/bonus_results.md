# Bốn lượt bổ sung (chạy 2026-09-22, T4, 16,5 giờ, 15/15 job `rc=0`)

Dữ liệu: `results/Phase_bonus/`. Bốn phiên song song: `control`, `warmup`, `diag-audit` (quét ngưỡng), `gatef-pets`.

Mọi so sánh ghép cặp theo seed với mốc đã đo trước đó. DTD: `N_control` 52,06, `N_audit` 52,92, `A0_refuse` 47,56. Pets: `N_control` 81,23, `A0_refuse` 75,88.

---

## 1. Kết quả quan trọng nhất: lợi ích **không đến từ việc sửa nhãn cho đúng**

Hai phép đo, đặt cạnh nhau, và chúng nói ngược chiều nhau:

**(a) Bỏ hẳn bước sửa nhãn thì mất lợi ích.** Lượt `N_audit_ownlabels` giữ nguyên mọi thứ — vẫn một epoch phụ, vẫn trả prompt về, vẫn bị kiểm toán gộp — chỉ **không sửa nhãn**:

| | `last10` | So với `N_control` | p |
|---|---|---|---|
| `N_audit` (có sửa nhãn) | 52,92 | **+0,86** | 0,078 |
| `N_audit_ownlabels` (không sửa) | 52,22 | **+0,16** | 0,636 |

Chênh 0,70 điểm. Vậy **việc dùng nhãn của model toàn cục là thứ trả tiền**, không phải epoch phụ, không phải phép gộp.

**(b) Nhưng sửa nhãn cho **đúng hơn** thì không được thêm gì.** Ngưỡng tự tin cải thiện chất lượng nhãn **29 lần** mà accuracy đứng yên:

| Lượt | Tỉ lệ ảnh bị sửa | Chất lượng nhãn (net: vá − phá) | Accuracy so `N_control` |
|---|---|---|---|
| `ownlabels` (đối chứng) | 0% | không sửa gì | +0,16 |
| `conf 0` (`N_audit`) | 100% | **−1481** | **+0,86** |
| `q50` | 51% | −1611 | +0,42 |
| `q75` | 26% | −347 | −0,10 |
| `q90` | 11% | **−51** | **+0,75** |

Từ −1481 lên −51 là cải thiện gần 30 lần về chất lượng nhãn. Accuracy: 0,86 → 0,75. **Không có quan hệ.**

Kết luận buộc phải rút ra:

> Cơ chế đang có lãi **không phải khử nhiễu**. Nó là **sự đồng thuận**: mọi client cùng huấn luyện theo ý kiến của **một người thầy chung**, và điều đó giảm phân kỳ giữa các client dưới phân bố non-IID. **Nhãn đúng hay sai không quan trọng; quan trọng là nhãn đến từ cùng một nguồn.**

Đây là kết quả phản trực giác, có đối chứng sạch, và có **quan hệ liều–đáp ứng bằng không** làm bằng chứng. Nó là phát hiện đáng viết nhất của đồ án.

---

## 2. Ngưỡng tự tin: **thành công ở mức nhãn, thất bại ở mức accuracy**

Ngưỡng làm đúng những gì nó được thiết kế để làm:

| Lượt | Bao phủ | Thầy đúng (chung) | Thầy đúng **trên phần được sửa** |
|---|---|---|---|
| `conf 0` | 100% | 52,5% | 52,5% |
| `q50` | 51% | 56,9% | **74,2%** |
| `q75` | 26% | 57,5% | **84,4%** |
| `q90` | 11% | 57,8% | **91,3%** |

Và trên **client nhiễu** — đúng nhóm cần chữa — nó chuyển sang **net dương**:

| | thầy trên phần được sửa | nhãn của client | fixed | broken | **net** |
|---|---|---|---|---|---|
| `conf 0` | 47,0% | 60,4% | 198 | 355 | −157 |
| `q75` | **76,2%** | 59,9% | 269 | 178 | **+91** |
| `q90` | **87,5%** | 59,9% | 108 | 42 | **+66** |

Thầy đi từ **dốt hơn trò** (47,0 so với 60,4) thành **giỏi hơn hẳn** (87,5 so với 59,9). Cơ chế vận hành chính xác như thiết kế.

**Nhưng accuracy không nhúc nhích** (+0,75 so với +0,86 của bản không ngưỡng). Và client sạch vẫn luôn lỗ: sửa nhãn vốn đã đúng thì `fixed` **luôn bằng 0**, chỉ có thể phá (q90: broken 117, fixed 0).

### Phán quyết Gate G theo tiêu chí ghi trước

| # | Ngưỡng | Kết quả | |
|---|---|---|---|
| **G1** | có ngưỡng hơn không ngưỡng ≥ +1,0 ở ≥ 2/3 mức | **−0,43 / −0,96 / −0,11** — âm cả ba | **TRƯỢT** |
| **G2** | có tấn công, hơn không phòng thủ ≥ +2,0 ở ≥ 1 mức | +1,12 / +1,12 / +1,03 | **TRƯỢT** |

Bản không ngưỡng đạt +1,37 khi có tấn công; **mọi mức ngưỡng đều thấp hơn**.

---

## 3. Warm-up: trượt, và bảng audit nói rõ vì sao

| | `last10` | So với `N_control` | So với `N_audit` |
|---|---|---|---|
| `N_warm5` | 52,07 | +0,01 | −0,85 |
| `N_warm10` | 52,08 | +0,02 | −0,83 |
| `N_warm20` | 51,92 | −0,14 | −1,00 |

Không mức nào khác 0, và cả ba đều **tệ hơn** bản không warm-up.

Lý do nằm ở cột "thầy đúng", tách theo nhóm client:

| Lượt | Thầy đúng trên dữ liệu **client sạch** | Thầy đúng trên dữ liệu **client nhiễu** |
|---|---|---|
| không warm-up | 54,8% | **47,0%** |
| `warm5` | 61,0% | **47,5%** |
| `warm10` | 63,4% | **48,3%** |
| `warm20` | 65,5% | **46,4%** |

Warm-up **làm thầy giỏi lên thật** — nhưng chỉ trên dữ liệu của nhóm đã dạy nó (54,8 → 65,5). Trên dữ liệu của client nhiễu thì **đứng yên** (47,0 → 46,4), tức vẫn **dưới** mức 60,4% của nhãn client.

Cơ chế: Dirichlet α = 0,1 nên mỗi client giữ một tập lớp rất khác nhau. **Nhóm tin cậy chỉ dạy được về những lớp nó có.** Với dữ liệu của người khác nó vẫn mù.

Đây là lý do chặt chẽ hơn "warm-up không hiệu quả": nó **không thể** hiệu quả dưới non-IID mạnh, dù có bao nhiêu vòng đi nữa. Và nó khớp với cảnh báo từ Gate A: mất dữ liệu (7,11 điểm) đắt hơn nhiễu (6,82 điểm) trên DTD.

**Giả định "nhóm client tin cậy" kiểu FLTrust không cứu được bài toán này.**

---

## 4. Liều kiểm toán cũng không phải biến

`N_audit_dose` (25/50 round thay vì 10/50, không tấn công): **52,94**, tức **+0,88** so với `N_control` và **+0,03** so với `N_audit`.

Gấp 2,5 lần liều, được thêm 0,03 điểm. Cùng kết luận với F2 (phía có tấn công: 82% → 94%). **Liều không phải cần gạt.**

---

## 5. Gate F lặp lại trên OxfordPets: cả hai tiêu chí trượt trên 2/2 dataset

| | DTD | **OxfordPets** |
|---|---|---|
| **F1** thiệt hại còn lại sau khi loại trừ (≤ 25% để đạt) | 85% | **82%** |
| | +0,65 ± 1,41 | **+0,96 ± 1,34**, t = 1,60 |
| **F3** `median` + giao thức so `median` (≥ +2,0 để đạt) | −1,62 | **−0,50 ± 2,47** |

Luật loại trừ trực tuyến trên Pets:

| Lượt | Thật thà bị cấm | Nhiễu | Độc hại |
|---|---|---|---|
| `A3_exclude` | **0/25** | 1/15 | 4/10 |
| `M1_median_full` | 1/25 | 0/15 | **7/10** |

Vẫn giữ tính chất tốt: **gần như không cấm oan người thật thà** — khác hẳn `multikrum` ở Gate B (loại client nhiễu gấp 17,7 lần client thật thà). Nhưng bắt đúng người vẫn **không đổi thành accuracy**.

> **"Loại bỏ client là cần gạt sai" giờ có hai dataset chống lưng, cộng với trần oracle ~1 điểm đã đo ở Gate F.**

---

## 6. Bức tranh sau tất cả

| Cần gạt | Trần đo được | Có ý nghĩa thống kê? |
|---|---|---|
| Loại client (mọi biến thể, kể cả oracle từ round 0) | ~+1,0 | **không**, trên 2 dataset |
| Warm-up bằng nhóm tin cậy | ~0,0 | **không** |
| Ngưỡng tự tin cho phần sửa nhãn | ≤ +0,75 | **không**, và thấp hơn bản không ngưỡng |
| Tăng liều kiểm toán | +0,03 | **không** |
| **Sửa nhãn bằng thầy chung** (bất kể thầy đúng hay sai) | **+0,86 / +1,01** | **có trên Pets, p = 0,008** |

Năm cần gạt, bốn cái chết. Cái sống sót lại hoạt động **vì một lý do khác với lý do nó được thiết kế**.

## 7. Luận điểm của bài, sau 7 cổng

1. FPL dưới nhiễu nhãn mong manh hơn benchmark báo, và chỉ số `best` che bớt 1,4–2,5 lần (Gate A).
2. Gộp bền vững hầu như không giúp, và luật nào có quyết định thì **quyết định sai đối tượng** (Gate B).
3. Suy đoán ý đồ từ hình học prompt **phụ thuộc số lớp**, ρ = +0,90 trên 5 dataset, và không hơn baseline ở chỗ baseline mạnh (Gate C).
4. **Nhận diện thì giải được**: kiểm chứng sự tuân thủ tách độc hại khỏi nhiễu ở AUC 0,91–0,99, ổn định qua dataset, luật trực tuyến bắt 4–9/10 với 0–1/25 báo động giả (Gate E, F).
5. **Nhưng nhận diện không phải bài toán.** Loại bỏ client — kể cả hoàn hảo, kể cả tức thì — mua được ~1 điểm và không có ý nghĩa, trên 2 dataset (Gate F).
6. **Và thứ có tác dụng thì có tác dụng vì lý do khác.** Sửa nhãn bằng model toàn cục ăn +0,86/+1,01 trong khi **phá 8,5 nhãn đúng cho mỗi nhãn nó vá**; sửa cho đúng hơn 29 lần không đổi được gì; bỏ hẳn việc sửa thì mất lợi ích. Cái trả tiền là **nguồn chung**, không phải **độ đúng**.

## 8. Việc còn lại

1. Nhân điểm 6 sang OxfordPets: `N_audit_ownlabels` và một mức ngưỡng (~2 giờ). Đây là phát hiện chính, phải có hai dataset.
2. Thêm seed cho `N_audit` trên DTD (p = 0,078) để phát biểu chính đạt p < 0,05 trên cả hai dataset (~1,5 giờ).
3. Dừng thí nghiệm. Viết.
