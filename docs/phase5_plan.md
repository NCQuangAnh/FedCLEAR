# Giai đoạn 5: tín hiệu phản ứng khi được yêu cầu sửa nhãn

Cập nhật: 2026-09-20. Tiếp nối Gate C (`results/Phase4/gate_c_results.md`).

## 1. Vì sao cần trục khác

Gate C cho thấy giới hạn của việc **đọc hình học của prompt**:

| Vấn đề đo được ở Gate C | Hệ quả |
|---|---|
| `s_sem` đảo chiều trên DTD | tín hiệu đang đo **mức học được**, không phải mức hỏng |
| `s_conc` sập trên OxfordPets | prompt gần như không di chuyển thì không có gì để đọc |
| Trên Caltech, `s_upd` kiểu Krum gần bằng `s_conc` | tín hiệu ngữ nghĩa **không hơn baseline ở chỗ nó hoạt động** |

Điểm chung: prompt cho biết client **đã học gì**, không cho biết client **có cố ý hay không**. Hai client có thể trôi giống hệt nhau vì hai lý do ngược nhau.

Tín hiệu phản ứng đi theo trục khác hẳn: thay vì **đo**, nó **hỏi**.

## 2. Cơ chế

Cứ mỗi `--correction_every` round, client làm thêm một lượt huấn luyện trong đó nhãn của chính nó bị thay bằng **dự đoán của model toàn cục**, rồi gửi về prompt sau lượt đó cùng hai con số loss.

Vì sao kẻ tấn công không thể làm theo: **bản sửa đến từ model toàn cục, mà model toàn cục không chia sẻ lớp đích của kẻ tấn công**. Làm theo nghĩa là xoá chính cuộc tấn công của mình. Nên nó buộc phải hoặc từ chối, hoặc báo một con số mà prompt gửi kèm không chứng minh được.

Ba tín hiệu, tính ở server:

| Tín hiệu | Đo gì |
|---|---|
| `r_gain` | mức giảm loss mà client **tự báo**. Một mình nó không kiểm chứng được |
| `r_align` | lượt sửa nhãn đi **cùng hướng** với cập nhật mà client đang được gộp trong round này tới đâu |
| `r_conc_drop`, `r_kl_drop` | độ tập trung giảm bao nhiêu sau khi sửa. Là **hiệu của cùng một client giữa hai trạng thái**, nên sàn 1/C — thứ làm `s_conc` không so được giữa các dataset — phần lớn triệt tiêu |

**Điểm mấu chốt về tính kiểm chứng được:** mốc so sánh của `r_align` là **cập nhật đang được gộp**, thứ server đã có sẵn. Không phải một vật thứ hai do client gửi. Bản đầu tiên mình viết so hai prompt **đều do client gửi** — kẻ tấn công điều khiển được cả hai vế, nên vô dụng. Đã sửa, và ghi lại ở đây vì đó là bài học thiết kế.

Cách đọc:

| Loại client | `r_gain` | `r_align` | `r_gain × r_align` |
|---|---|---|---|
| Thật thà, nhãn sạch | thấp — nhãn vốn đã khớp model | cao — lượt sửa chỉ đi tiếp hướng cũ | thấp |
| Thật thà, nhãn nhiễu | cao — được sửa thì lợi thật | thấp — đổi hướng rõ rệt | thấp |
| **Độc hại** | **cao (tự báo)** | **cao — vẫn đi hướng cũ vì không thực sự sửa** | **cao** |

## 3. Kẻ tấn công, hai mức

Cài sẵn cả hai bằng `--attack_lie`:

| | Cách làm | Mức khó |
|---|---|---|
| `big` | bịa một mức giảm lớn | dễ, bắt được bằng riêng con số |
| **`mimic`** (mặc định) | **chạy lượt sửa một cách riêng tư, lấy đúng mức giảm mà nó sẽ đạt được nếu thật thà, rồi huấn luyện lại trên nhãn của chính mình và gửi prompt đó đi** | khó: con số báo cáo không còn chứa thông tin, chỉ còn prompt tố cáo nó |

Mặc định là `mimic`, tức **luôn đánh giá trước kẻ tấn công mạnh hơn**.

## 4. Lỗ hổng còn lại, ghi trước để không bị hỏi bất ngờ

Prompt của lượt probe **không được gộp** vào model toàn cục. Nên về nguyên tắc kẻ tấn công có thể **bịa luôn cả prompt probe** (gửi một prompt trông như đã sửa) mà không mất gì, vì cuộc tấn công của nó nằm ở cập nhật chính.

Cách chặn, sẽ thử ở giai đoạn 5b: **kiểm toán ngẫu nhiên** — với xác suất *p*, server lấy chính prompt probe làm đóng góp của client trong round đó. Khi ấy bịa prompt probe **có giá**: bịa thành "đã sửa" thì mất cuộc tấn công mỗi lần bị kiểm toán.

Đây cũng là chỗ khác biệt rõ với hai bài gần nhất: Fed-RoSeC **giả định** client độc hại tuân thủ; zkCor **ép** tuân thủ bằng zero-knowledge proof, chứng minh phép tính đúng nhưng không chứng minh dữ liệu trung thực. Ở đây việc tuân thủ **có giá**, và việc không tuân thủ **để lại dấu vết thống kê**.

## 5. Tiêu chí Gate D (ghi trước khi chạy)

Cấu hình như Gate C: 3 nhiễu, 2 độc hại, 5 thật thà, `sym` 40%, tấn công `noise_disguise`, 5 seed, `--correction_every 5`, `--attack_lie mimic`. Dataset: DTD, Caltech101, OxfordPets.

| # | Điều kiện | Ngưỡng |
|---|---|---|
| D1 | `r_align` tách client độc hại khỏi client nhiễu | AUC ≥ 0,80 **trên ít nhất 2 trong 3 dataset** |
| D2 | Hoạt động cả ở nơi mọi thứ khác đều hỏng | AUC ≥ 0,75 trên **OxfordPets** |
| D3 | Hơn hẳn tín hiệu độ lệch | AUC(`r_align`) − AUC(`s_upd`) ≥ 0,10 ở những dataset D1 đạt |

**Ngưỡng "ít nhất 2 trong 3" là cố ý chặt hơn Gate C.** Gate C dùng "ít nhất 1 dataset" và điều đó hoá ra quá dễ: thêm dataset là thêm cơ hội đạt. Đây là **sửa tiêu chí sau khi thấy điểm yếu**, và ghi rõ như vậy, y như đã làm với B3′.

Thống kê theo quy tắc đã sửa sau Gate B: kiểm định t ghép cặp p < 0,05 với ≥ 5 seed, báo kèm trung bình ± sd và Cohen's dz.

Quy tắc quyết định, ghi trước:

| Kết quả | Việc làm |
|---|---|
| D1, D2, D3 đạt | Dựng bộ triage ba lớp dùng `r_align` làm tín hiệu chính, sang giai đoạn 6: xử lý phân hoá và đo lợi ích cuối cùng bằng accuracy |
| D1 đạt, D2 trượt | Giữ tín hiệu nhưng ghi rõ **điều kiện áp dụng**: không dùng được khi zero-shot đã gần trần |
| D1 trượt | **Dừng thêm tín hiệu mới.** Viết luận văn theo hướng nghiên cứu thực nghiệm: bốn phát hiện đã đo cộng một kết quả âm có cơ chế giải thích rõ ràng |

Dòng cuối là **điểm dừng đã cam kết**. Thêm tín hiệu thứ tư rồi thứ năm cho tới khi có cái khớp số liệu chính là cái bẫy đã giết vòng cải tiến FedSNC.

## 6. Chi phí

Mỗi round có probe tốn thêm hai lượt huấn luyện trên dữ liệu cục bộ (rất nhỏ, vài chục ảnh) cộng một lượt forward lấy nhãn đề xuất. Với `--correction_every 5` thì tăng khoảng 8% thời gian client.

## 7. Trạng thái

1. ~~`flcore/correction.py`: probe, ba tín hiệu, hai mức kẻ tấn công~~ — xong 2026-09-20.
2. ~~Chạy được trong vòng đời client (client giải phóng model cuối round nên probe phải nằm trong `local_train`)~~ — xong.
3. ~~Kiểm trên CPU~~ — xong: probe chạy, ghi đúng vai trò, và sau khi sửa mốc so sánh thì client độc hại có `r_align` cao nhất ở cả hai round probe. Dữ liệu giả 6 lớp nên **chỉ đủ nói đường ống thông**, không nói gì về khả năng tách.
4. ~~Notebook giai đoạn 5 và ô phân tích AUC~~ — xong.
5. ~~Chạy Gate D~~ — xong 2026-09-20, 7,03 giờ, 5/6 job. **Trượt cả ba tiêu chí.** Kết quả: `results/Phase5/gate_d_results.md`.

`r_align` của client độc hại là **thấp nhất** chứ không phải cao nhất như dự đoán (DTD 0,302 so với 0,563 ở client thật thà). Tách khỏi client thật thà thì gần như hoàn hảo nhưng **ngược dấu** (AUC 0,004 và 0,000, tức 0,996 và 1,000 nếu đảo). Không được coi là đạt: tiêu chí ghi trước nói phải **cao**.

Và một lỗi thiết kế của chính mình: `probe_comply` không xét việc có cấu hình tấn công hay không, nên trong **lượt đối chứng** client vai trò độc hại **vẫn từ chối bản sửa**. Thí nghiệm vì thế trộn lẫn "từ chối tuân thủ" với "dữ liệu bị đầu độc", và không nói được `r_align` đang phát hiện cái nào. Đã sửa trong `server_base.py`.

6. Chạy lại **lượt đối chứng đã sửa** (`MODE = "gate_d_control"`, DTD + OxfordPets, ~2,2 giờ) với dự đoán ghi trước ở mục 4 của file kết quả. Sửa một thiết kế sai không phải là thêm tín hiệu mới, nên không vi phạm điểm dừng: một kết quả âm được báo cáo thì phải là kết quả âm **đúng**.

7. Sau đó: **viết luận văn**, dù kết quả ra sao.
