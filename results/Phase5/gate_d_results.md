# Kết quả Gate D (chạy 2026-09-20, T4, 7,03 giờ)

Dữ liệu: `phase5_results.zip`, giải nén ở `extracted/`. **5 trên 6 job** hoàn thành — `caltech101_P0_disguise` bị chặn bởi ngân sách 9 giờ. DTD và OxfordPets đủ cả hai cấu hình, Caltech chỉ có lượt đối chứng.

Thiết lập: 3 client nhiễu, 2 độc hại, 5 thật thà, `sym` 40%, tấn công `noise_disguise`, probe mỗi 5 round, kẻ tấn công `mimic`, 5 seed.

## 1. Phán quyết: **Gate D trượt cả ba tiêu chí**

| Tiêu chí | Ngưỡng | Kết quả |
|---|---|---|
| D1 `r_align` tách độc hại khỏi nhiễu, AUC ≥ 0,80 trên ≥ 2/3 dataset | | **0,013 (DTD), 0,107 (Pets)** — trượt |
| D2 AUC ≥ 0,75 trên OxfordPets | | **0,107** — trượt |
| D3 hơn `s_upd` ≥ 0,10 | | không áp dụng được vì D1 trượt |

Theo **điểm dừng đã cam kết** ở `docs/phase5_plan.md` mục 5: D1 trượt thì **dừng thêm tín hiệu mới và bắt đầu viết luận văn**.

## 2. Nhưng tín hiệu không hề yếu — nó ngược dấu

AUC dưới 0,5 nghĩa là tín hiệu tách được, chỉ là theo chiều ngược với dự đoán. Giá trị trung bình của `r_align`:

| Dataset | Lượt | Thật thà | Nhiễu | **Độc hại** |
|---|---|---|---|---|
| DTD | tấn công | +0,563 | +0,554 | **+0,302** |
| DTD | đối chứng | +0,566 | +0,586 | **+0,359** |
| OxfordPets | tấn công | +0,794 | +0,558 | **+0,361** |
| OxfordPets | đối chứng | +0,803 | +0,548 | **+0,706** |
| Caltech101 | đối chứng | +0,613 | +0,471 | **+0,418** |

Mình **dự đoán client từ chối sửa sẽ có `r_align` cao** — vì nó vẫn đi tiếp hướng cũ. Thực tế **ngược lại: thấp nhất bảng**.

Và tách khỏi client **thật thà** thì gần như hoàn hảo, chỉ là ngược dấu:

| Dataset | Lượt | AUC(độc hại / thật thà) | Đổi dấu thành |
|---|---|---|---|
| DTD | tấn công | 0,004 | **0,996** |
| DTD | đối chứng | 0,064 | **0,936** |
| OxfordPets | tấn công | 0,000 | **1,000** |
| OxfordPets | đối chứng | 0,180 | 0,820 |
| Caltech101 | đối chứng | 0,044 | **0,956** |

**Không được coi đây là đạt.** Tiêu chí ghi trước nói `r_align` phải **cao** ở client độc hại. Nó thấp. Đảo dấu sau khi nhìn dữ liệu rồi tuyên bố thắng chính là thứ kỷ luật của đồ án tồn tại để ngăn. Con số được báo cáo như **một quan sát**, và cơ chế đằng sau **chưa được xác lập**.

## 3. Lỗi thiết kế của chính mình: lượt đối chứng không phải đối chứng

`probe_comply` được đặt bằng `not is_malicious(client)`, **không quan tâm có cấu hình tấn công hay không**. Nghĩa là trong lượt đối chứng — nơi lẽ ra client độc hại phải hành xử hoàn toàn thật thà — chúng **vẫn từ chối bản sửa nhãn**.

Hậu quả: thí nghiệm **trộn lẫn hai thứ**:
- từ chối tuân thủ probe;
- dữ liệu bị đầu độc.

Nên không thể nói `r_align` đang phát hiện cái nào. Bằng chứng của sự trộn lẫn nằm ngay trong bảng: trên OxfordPets, cùng là client từ chối, lượt đối chứng cho +0,706 còn lượt có tấn công cho +0,361. Chênh 0,345 đó **chỉ có thể đến từ dữ liệu bị đầu độc**, nhưng thiết kế hiện tại không tách được phần nào của phần nào.

**Đây là lỗi của mình, không phải của dữ liệu.** Đã sửa: một client vai trò độc hại giờ **tuân thủ khi không có tấn công nào được cấu hình**.

## 4. Một lượt duy nhất còn nên chạy, và vì sao nó không vi phạm điểm dừng

Điểm dừng cấm **thêm tín hiệu mới**. Sửa một thí nghiệm có thiết kế sai **không phải** thêm tín hiệu — đó là làm cho kết quả âm trở nên đọc được.

Một luận văn báo cáo kết quả âm thì kết quả âm đó phải **đúng**. Hiện tại nó mơ hồ: không biết "probe không hoạt động" hay "probe phát hiện việc từ chối, nhưng từ chối không phải dấu hiệu đáng tin của ý đồ xấu trong bối cảnh này". Hai câu đó dẫn tới hai phần kết luận khác hẳn nhau.

**Lượt sửa lỗi:** chỉ lượt đối chứng, DTD và OxfordPets, 5 seed, khoảng **2,2 giờ**. Notebook đã đặt `MODE = "gate_d_control"`.

**Dự đoán ghi trước:** nếu `r_align` thấp là do **từ chối**, thì khi client vai trò độc hại tuân thủ, `r_align` của chúng phải **ngang client thật thà** (≈ +0,56 trên DTD, ≈ +0,79 trên Pets) và AUC so với thật thà phải về quanh **0,5**. Nếu nó **vẫn thấp**, thì `r_align` đang đo một thứ gắn với cách gán vai trò chứ không phải hành vi, và cả tín hiệu này lẫn kết quả âm đều phải viết lại.

Sau lượt đó: **viết luận văn**, dù kết quả ra sao.

## 5. Còn thiếu

`caltech101_P0_disguise` chưa chạy vì hết ngân sách. Không ảnh hưởng phán quyết — D1 đã trượt trên cả hai dataset có đủ dữ liệu, và Caltech chỉ có thể làm dataset thứ ba. Nếu sau này muốn bảng đầy đủ cho luận văn thì chạy riêng job đó, khoảng 2,7 giờ.
