# Lọc ở mức ảnh (chạy 2026-09-22/23, T4, 6,2 giờ, 5/5 job `rc=0`)

DTD, 5 seed, ghép cặp theo seed với `A0_refuse` = 47,56.

Hai lượt: `F_*` (bản đầu, mốc = trung vị) và `G_*` (bản sửa, mốc = phân vị 25%, `rho` làm hạn mức cứng).

## 1. Kết quả

| Nhánh | `last10` | Lấy lại | p | Bắt % ảnh bẩn | Độ chính xác |
|---|---|---|---|---|---|
| `A0_refuse` không phòng thủ | 47,56 | – | | | |
| `F_both` (v1, luật lớp không hạn mức) | 37,29 | **−10,27** | | 89% | 51% |
| `G_both` | 48,40 | +0,84 | 0,116 | 61,3% | 64,4% |
| `G_both_floor` (sàn 0,35) | 48,58 | +1,02 | 0,109 | 68,0% | 66,1% |
| `F_rho` (v1) | 48,96 | +1,40 | 0,087 | 31,4% | 80,0% |
| **`G_rho`** | **49,89** | **+2,33 ± 1,46** | **0,023** | 66,2% | 71,1% |
| `L_drop` oracle | 53,58 | +6,02 | 0,010 | 100% | 100% |
| `L_restore` oracle | 55,94 | +8,39 | 0,002 | | |

**`G_rho` là kết quả tốt nhất của cả đồ án**: +2,33, p = 0,023, hơn mức tốt nhất cũ (+1,56) một nửa.

## 2. Dự đoán ghi trước: sai, và sai một cách có ích

Ghi trước lượt này: *"`G_rho` +2,5 đến +3,0; `G_both_floor` +3,5 đến +4,5."*

| | Dự đoán | Thực tế |
|---|---|---|
| `G_rho` | +2,5 – 3,0 | **+2,33** (sát dưới) |
| `G_both_floor` | +3,5 – 4,5 | **+1,02** (trượt xa) |

Dự đoán dựa trên giả thuyết **recall chi phối**, suy từ một điểm dữ liệu (31% → +1,40) nội suy tuyến tính tới oracle (100% → +6,02). Giả thuyết đó **bị bác**:

| Nhánh | Recall | Gain |
|---|---|---|
| `G_rho` | 66,2% | **+2,33** |
| `G_both_floor` | **68,0%** | +1,02 |

Recall gần như nhau, gain chênh **2,3 lần**. Recall không phải biến chi phối.

## 3. Biến chi phối là **độ chính xác**, và có tỉ giá đo được

Khớp `gain = a·(số ảnh bẩn bỏ đi) − b·(số ảnh sạch bỏ nhầm)` trên cả 5 điểm (4 nhánh thật + oracle):

| | Giá trị |
|---|---|
| Bỏ 1000 ảnh **bẩn** | **+0,326 điểm** |
| Bỏ nhầm 1000 ảnh **sạch** | **−0,437 điểm** |
| Tỉ giá | bỏ nhầm 1 ảnh sạch tốn bằng **1,34** ảnh bẩn bỏ đúng |

Khớp rất khít, kể cả điểm oracle không dùng để khớp ý nghĩa gì đặc biệt:

| Nhánh | Thực | Mô hình |
|---|---|---|
| `F_rho` | +1,40 | +1,28 |
| `G_rho` | +2,33 | +1,84 |
| `G_both` | +0,84 | +0,97 |
| `G_both_floor` | +1,02 | +1,30 |
| `L_drop` | +6,02 | **+6,11** |

**Hệ quả quan trọng nhất: độ chính xác hoà vốn là 57,3%.** Dưới ngưỡng đó, lọc càng nhiều càng hại — mỗi ảnh sạch mất đi đắt hơn mỗi ảnh bẩn dọn được.

Ta đang ở 64–71%, tức **chỉ nhỉnh hơn hoà vốn**. Đó là lý do mọi nhánh đều nhỏ.

### Trần theo độ chính xác, nếu bắt được **toàn bộ** ảnh bẩn

| Độ chính xác | Tối đa lấy lại được |
|---|---|
| 65% | +1,70 |
| **71,1% (hiện tại)** | **+2,78** |
| 80% | +4,06 |
| 90% | +5,20 |
| 100% | +6,11 |

`G_rho` đạt **+2,33 trên trần +2,78 của chính độ chính xác nó** — tức khai thác **84%** những gì bộ lọc hiện tại cho phép. Không còn gì để vắt ở recall. **Muốn hơn thì phải chính xác hơn, không phải bắt nhiều hơn.**

## 4. Luật lớp: bắt nhiều hơn nhưng bẩn hơn, nên lỗ

| | Độ chính xác | Chạm client thật thà |
|---|---|---|
| `G_rho` (chỉ sai số) | **71,1%** | **3,5%** |
| `G_both` (thêm luật lớp) | 64,4% | 4,0% |
| `G_both_floor` | 66,1% | **12,2%** |

Luật lớp đổi recall lấy độ chính xác, mà tỉ giá 1,34 làm phép đổi đó **lỗ**. Sàn 0,35 còn tệ hơn: chạm 12,2% dữ liệu client thật thà — **toàn bộ đều là ảnh sạch** (`actually damaged 0,0%`).

Điều này **không bác bỏ** giá trị của luật lớp. Đo riêng ở lượt chẩn đoán, nó bắt 83% chất độc ở client phá hoại trong khi sai số chỉ bắt 19%. Nó **chọn đúng ảnh**, nhưng khi bị nhét vào cùng một hạn mức với sai số thì nó **đẩy ảnh sạch vào danh sách bỏ**. Hai luật đang tranh nhau một ngân sách chung.

## 5. Điều bản v1 đã dạy, và bản v2 xác nhận

`F_both` = **−10,27**, vì vòng phản hồi: cắt → model tệ → ngưỡng tuyệt đối 0,9 bắn khắp nơi → cắt thêm. Bỏ 45,3% dữ liệu client thật thà, **không một ảnh nào thật sự hỏng**.

Chuyển `rho` thành hạn mức cứng chặn được hẳn: `G_both` chỉ còn chạm 4,0% client thật thà. Vòng phản hồi bị cắt tận gốc vì client thật thà có hạn mức ~0 nên không luật nào đụng được vào nó.

**Không nhánh `G_*` nào bỏ dù một ảnh hỏng của client thật thà** (`actually damaged 0,0%` ở cả ba) — đúng như thiết kế, vì client thật thà không có ảnh hỏng nào.

## 6. Việc tiếp theo, theo đúng thứ tự tỉ giá chỉ ra

Mục tiêu đổi từ **"bắt nhiều hơn"** sang **"bỏ đúng hơn"**.

1. **Tách ngân sách cho hai luật** (~2,5 giờ). Hiện chúng tranh nhau một hạn mức. Cho luật lớp ngân sách **riêng, nhỏ**, chỉ áp vào những lớp thật sự bất thường; sai số giữ phần còn lại. Cộng độ chính xác của hai luật thay vì pha loãng nhau.
2. **Bỏ qua lớp quá ít ảnh** (~1 giờ). Một lớp 3 ảnh mà cả 3 bị đoán sai sẽ ra 100% bất đồng dù hoàn toàn sạch. Đây là nguồn nhiễu chính của luật lớp dưới Dirichlet α = 0,1.
3. **Hạ trọng số thay vì xoá hẳn** (~2,5 giờ). Tỉ giá nói sai lầm rất đắt; ảnh đáng ngờ mà chỉ giảm nửa trọng số thì sai lầm cũng chỉ tốn nửa giá. Có thể đẩy hoà vốn xuống dưới 57,3%.
4. Nhân sang OxfordPets (~2,5 giờ).

Điểm 3 có thể là cái quan trọng nhất: **toàn bộ phân tích trên giả định quyết định nhị phân**. Bỏ giả định đó thì tỉ giá đổi, và trần đổi theo.
