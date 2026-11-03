# Hạ trọng số thay vì xoá (chạy 2026-09-23, T4, 5,26 giờ, 4/4 job `rc=0`)

Dữ liệu: `results/Phase_bonus/H_/`. DTD, 5 seed, ghép cặp theo seed với `A0_refuse` = 47,56.

## 1. Kết quả

| Nhánh | Nội dung | `last10` | Lấy lại | p |
|---|---|---|---|---|
| `A0_refuse` | không phòng thủ | 47,56 | – | |
| `G_rho` | mốc cũ tốt nhất (xoá hẳn) | 49,89 | +2,33 ± 1,46 | 0,023 |
| `H_band` | + ngưỡng miễn trừ client sạch | 49,85 | +2,29 ± 0,91 | **0,005** |
| `H_split` | + túi ngân sách riêng + lớp ≥ 5 ảnh | 49,77 | +2,22 ± 1,52 | 0,031 |
| `H_full` | hạ trọng số + túi riêng | 50,20 | +2,64 ± 1,37 | 0,013 |
| **`H_soft`** | **hạ trọng số** | **50,75** | **+3,19 ± 1,00** | **0,002** |
| `L_drop` oracle | xoá đúng từng ảnh hỏng | 53,58 | +6,02 | 0,010 |

**`H_soft` là kết quả tốt nhất của cả đồ án**: +3,19, p = 0,002 — lấy được **53% của trần** `L_drop`.

Tiến trình: +1,56 (kiểm toán) → +2,33 (lọc xoá hẳn) → **+3,19 (lọc hạ trọng số)**.

## 2. Điều quan trọng nhất: thắng **mà bỏ ít hơn**

| Nhánh | Tổng lượng bỏ | Bắt được % chất độc | Độ chính xác | Lấy lại |
|---|---|---|---|---|
| `H_band` (xoá hẳn) | 19.033 | 66,8% | 65,8% | +2,29 |
| **`H_soft`** | **13.477** | **47,8%** | 66,4% | **+3,19** |

`H_soft` bỏ **ít hơn 29%**, bắt được **ít hơn 19 điểm phần trăm** chất độc, độ chính xác **ngang nhau** — mà accuracy **cao hơn 0,90 điểm**.

Không giải thích được bằng "bắt nhiều hơn" hay "bỏ đúng hơn". Chỉ còn một cách giải thích: **giá của một quyết định sai đã giảm.**

### Kiểm bằng mô hình tỉ giá cũ

Mô hình khớp từ lượt trước: bỏ 1000 ảnh bẩn = +0,326; bỏ nhầm 1000 ảnh sạch = −0,437.

Áp vào `H_soft` (8.954 đơn vị bẩn, 4.523 đơn vị sạch):

```
dự đoán = 0,326 × 8,954 − 0,437 × 4,523 = +0,94
thực tế = +3,19
```

Lệch **3,4 lần**. Mô hình cũ **không còn mô tả được** chế độ hạ trọng số — đúng như đã ghi trước: *"toàn bộ phân tích trên giả định quyết định nhị phân; bỏ giả định đó thì tỉ giá đổi."*

Giải hệ ngược với giả thiết phần lãi giữ nguyên: hệ số phạt cho ảnh sạch bị hạ oan rơi từ **−0,437 xuống khoảng 0** — tức **hạ nửa trọng số một ảnh sạch gần như không tốn gì**, trong khi xoá hẳn nó thì tốn 1,34 lần phần lãi của một ảnh bẩn.

## 3. Hai thứ phụ nhưng đáng giữ

**Ngưỡng miễn trừ client sạch** (`H_band`): accuracy **không đổi** (+2,29 so với +2,33 của `G_rho`, chênh −0,04, p = 0,93), nhưng

| | Chạm client thật thà | sd của hiệu |
|---|---|---|
| `G_rho` | 3,5% | ±1,46 |
| `H_band` | **2,7%** | **±0,91** |

Không mua thêm điểm, nhưng **giảm dao động giữa các seed 38%**, nên p từ 0,023 xuống 0,005. Đáng giữ vì lý do độ tin cậy, không vì lý do accuracy.

**Mọi nhánh đều không bỏ một ảnh hỏng nào của client thật thà** (`0,0%` ở cả bốn) — đúng thiết kế, vì client thật thà không có ảnh hỏng.

## 4. Luật lớp: vẫn không đáng

| | Lấy lại |
|---|---|
| `H_soft` (chỉ sai số) | **+3,19** |
| `H_full` (thêm luật lớp, túi riêng) | +2,64 |
| `G_rho` (chỉ sai số, xoá hẳn) | +2,33 |
| `H_split` (thêm luật lớp, xoá hẳn) | +2,22 |

Thêm luật lớp làm **giảm** kết quả ở cả hai chế độ (−0,55 khi mềm, −0,11 khi cứng). Tách túi ngân sách riêng **không cứu được**.

Đây là lần thứ ba luật lớp thất bại ở mức accuracy dù nó **nhận diện tốt** (bắt 83% chất độc ở client độc hại, nơi luật sai số chỉ bắt 19%). Kết luận phải rút: **nó chọn đúng ảnh nhưng chọn kèm quá nhiều ảnh sạch cùng lớp**, và tỉ giá không cho phép phép đổi đó — kể cả khi tỉ giá đã mềm đi.

## 5. Điều phải nói cho đúng mức

So trực tiếp `H_soft` với `G_rho`: **+0,86 ± 2,07, p = 0,40** — **không có ý nghĩa thống kê**.

Phát biểu đúng là:

- Cả hai đều hơn "không phòng thủ" một cách có ý nghĩa.
- `H_soft` có **con số tuyệt đối cao nhất** và **khoảng tin cậy chặt nhất** so với mốc (p = 0,002 so với 0,023).
- Nhưng **chưa chứng minh được** hạ trọng số hơn xoá hẳn, vì phép so trực tiếp giữa hai nhánh có sai số quá rộng ở n = 5.

Muốn khẳng định thì cần **thêm seed** cho đúng hai nhánh này, không cần ý tưởng mới. Khoảng 2,7 giờ cho 5 seed nữa mỗi nhánh.

## 6. Việc tiếp theo

| # | Việc | Vì sao | Giờ |
|---|---|---|---|
| 1 | Thêm seed 5–9 cho `H_soft` và `G_rho` | Biến "+0,86 chưa chắc" thành kết luận | ~2,7 |
| 2 | Nhân `H_soft` sang OxfordPets | Phát hiện chính cần 2 dataset | ~1,4 |
| 3 | Quét mức nhiễm 10% / 40% / 80% | Điều kiện áp dụng | ~5,0 |
| 4 | Trọng số theo **điểm thật** thay vì thứ hạng | Thang hiện tại ép ảnh đáng ngờ ngang nhau thành trọng số cách đều; dùng điểm thật rồi co lại cho khớp hạn mức thì trung thực hơn | ~1,4 |

Điểm 4 là thứ có khả năng đẩy tiếp: cơ chế hiện tại chứng minh được **hướng đúng**, nhưng nó là bản thô nhất của hướng đó.
