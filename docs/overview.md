# Tổng quan đồ án: FPL-Triage

Phân loại và xử lý phân hoá client nhiễu nhãn với client độc hại trong federated prompt learning.

Cập nhật: 2026-09-19. Tóm tắt ngắn cho người đọc lần đầu: `docs/abstract.md`. Mọi con số dưới đây đều kèm đường dẫn tới lượt chạy sinh ra nó.

## 1. Bối cảnh và bài toán

**Federated prompt learning (FPL).** CLIP được đóng băng hoàn toàn; chỉ một prompt nhỏ (2048 tham số trong thiết lập của đồ án) được huấn luyện và truyền qua lại. Nhờ vậy học liên kết trở nên khả thi ngay cả khi mỗi client chỉ có vài ảnh mỗi lớp. Benchmark chuẩn của lĩnh vực là FLIP (NeurIPS 2025 D&B).

**Hai loại client không đáng tin.**

| | Client nhiễu | Client độc hại |
|---|---|---|
| Ý định | thật thà, gán nhãn kém | cố ý phá hoại |
| Giá trị dữ liệu | dương, chỉ là một phần nhãn sai | **âm** |
| Xử lý đúng | **sửa nhãn, giữ lại** | **loại bỏ** |
| Hành vi khi bị quan sát | không giấu giếm | **cố tình bắt chước client nhiễu** |

Vì cách xử lý đúng của hai loại **ngược nhau**, việc phân biệt không phải chuyện tinh tế học thuật mà là điều kiện cần để làm đúng.

**Vì sao khó.** Mọi phòng thủ hiện có đều xếp hạng client theo **độ lệch của cập nhật** so với số đông. Gán nhãn cẩu thả cũng sinh ra độ lệch. Nên tín hiệu duy nhất mà lĩnh vực đang dùng về bản chất không phân biệt được hai loại.

## 2. Ba mệnh đề nền, đã đo

Thiết lập: RN50, 10 client, Dirichlet α = 0,1, 8 ảnh/lớp cho cả liên đoàn, 50 round. Chỉ số chính là `last10` (trung bình 10 round cuối), lý do ở mục 5. So sánh ghép cặp theo seed, 5–7 seed.

### 2.1 Nhiễu nhãn gây thiệt hại lớn

Nhiễu 40% trên một nửa số client lấy đi **4,7 đến 13,2 điểm** (`results/Phase2/gate_a_results.md`).

Trên hai trong ba dataset, mô hình sau huấn luyện **thấp hơn cả sàn zero-shot** của CLIP: Caltech101 83,84 so với 85,76; OxfordPets 74,91 so với 85,69. Nghĩa là ở mức nhiễu này, **không huấn luyện gì còn tốt hơn**.

### 2.2 Loại bỏ client nhiễu gần như vô ích, và mức vô ích phụ thuộc dataset cần dữ liệu tới đâu

Đo bằng một ORACLE loại đúng mọi client nhiễu — trần tuyệt đối của mọi bộ phát hiện mức client.

| Dataset | Huấn luyện mua được so với zero-shot | ORACLE loại client nhiễu mua lại | Trần của sửa nhãn |
|---|---|---|---|
| DTD | +13,83 | −0,24 đến +1,24 | 6,91–8,40 |
| Caltech101 | +4,52 | +1,36 đến +3,13 | 4,67–6,44 |
| OxfordPets | +2,40 | +4,28 đến +8,81 | 8,64–13,18 |

Quy luật rõ ràng: **dataset càng cần dữ liệu thì loại client càng đắt**. Trên hai dataset mà huấn luyện thực sự có ích, loại bỏ mua lại nhiều nhất 3,1 điểm, trong khi sửa nhãn có trần 4,7–8,4. Chỉ trên OxfordPets — nơi huấn luyện chỉ hơn zero-shot 2,4 điểm, tức dữ liệu gần như không cần thiết — loại bỏ mới đáng.

**Kết luận:** với client nhiễu, hướng đúng là **sửa nhãn và giữ lại**.

### 2.3 Phòng thủ chuẩn phân biệt sai đối tượng

`results/Phase3/gate_b_results.md`. Thiết lập: 3 client nhiễu, 2 client độc hại, 5 thật thà.

**Gộp bền vững không phải lời giải.** Chỉ **1 trong 4** tổ hợp (dataset × luật) cho lợi ích đo được: `median` trên OxfordPets, +3,10 điểm, p = 0,001. Ba tổ hợp còn lại không khác gì không phòng thủ. Và tổ hợp duy nhất có tác dụng ấy lại là luật **không hề quyết định client nào đáng tin** — nó lấy trung vị theo từng toạ độ.

**Luật có quyết định thì quyết định sai.** Tần suất Multi-Krum loại một client, chuẩn hoá theo số client mỗi vai:

| Dataset | Thật thà | Nhiễu | Độc hại |
|---|---|---|---|
| DTD | 0,173 | 0,132 | 0,369 |
| OxfordPets | **0,019** | **0,336** | 0,449 |

Trên OxfordPets, client nhiễu bị loại với tần suất **gấp 17,7 lần** client thật thà, bằng 75% tần suất loại đúng kẻ tấn công. Hậu quả đo được: bật Multi-Krum làm mô hình **tệ hơn 1,63 điểm so với không phòng thủ gì**, vì nó vứt đúng thứ dữ liệu mà mục 2.2 chứng minh là đáng giữ.

**Tấn công nguỵ trang không tốn gì để ẩn mình.** Tấn công giả làm nhiễu — lật đúng tỉ lệ như một client nhiễu thật, nhưng dồn mọi nhãn bị lật về một lớp đích — gây thiệt hại **+3,62 điểm trên DTD** (p = 0,019) và **+3,51 trên OxfordPets** (p = 0,001), 7 seed. Tức ngang hoặc hơn tấn công có mục tiêu kinh điển vốn ồn ào và dễ thấy.

## 3. Phương pháp đề xuất

**Phân loại ba lớp, xử lý phân hoá:** thật thà thì giữ nguyên, nhiễu thì sửa nhãn rồi giữ lại, độc hại thì loại bỏ.

**Ràng buộc tự đặt, và là điểm khác biệt:** máy chủ **không xem dữ liệu client**, **không có tập dữ liệu sạch**, **không đụng tập test**. Ràng buộc này không tuỳ tiện — ba bài cạnh tranh gần nhất (RFedLR NeurIPS 2025, FedMGP+ TPAMI 2026, và FedPN theo cách khác) đều phải mượn một tập dữ liệu sạch đặt ở máy chủ.

**Mẹo probe.** CLIP biểu diễn ảnh và chữ trong cùng một không gian, nên **embedding văn bản của một lớp đóng vai ảnh đại diện của lớp đó**. Máy chủ có ngay tập dữ liệu thử mà không cần một tấm ảnh nào, và không cần ai tin tưởng ai.

**Ba tín hiệu, tính chỉ từ prompt client gửi lên** (`flip/flcore/signals.py`):

| Tín hiệu | Đo cái gì | Kỳ vọng |
|---|---|---|
| `s_sem` | prompt kéo khái niệm các lớp ra xa cách hiểu gốc của CLIP bao nhiêu | cao ở **cả** nhiễu lẫn độc hại |
| `s_conc` | phần trôi đó **dồn vào một lớp** hay **rải ra nhiều lớp** | **tín hiệu tách hai loại** |
| `s_upd` | độ lệch của cập nhật, kiểu Krum | mốc phải vượt |

Lý lẽ đằng sau `s_conc`: gán nhãn cẩu thả thì sai **lung tung**, còn tấn công thì phải **dồn** về lớp mà kẻ tấn công muốn — nếu rải đều ra thì đã thành nhiễu chứ không còn là tấn công có mục tiêu.

**Phản biện hiển nhiên nhất đã được ghi trước để tự kiểm:** kẻ tấn công có thể rải mục tiêu ra `k` lớp. Giả thuyết ghi trước là việc đó làm `s_conc` giảm **nhưng đồng thời làm thiệt hại giảm**, tức kẻ tấn công bị buộc vào một đánh đổi. Nếu sai thì tín hiệu hỏng, và sẽ nói thẳng (`docs/phase4_plan.md` mục 4).

**Tín hiệu thứ hai, giai đoạn sau:** phản ứng khi được yêu cầu sửa nhãn. Máy chủ đề nghị một bản sửa; client nhiễu thật thà chấp nhận và loss giảm đúng dự đoán, client độc hại thì không. Khác Fed-RoSeC ở chỗ họ **giả định** client độc hại tuân thủ; khác zkCor ở chỗ họ **ép** tuân thủ bằng mật mã, chứng minh phép tính đúng nhưng không chứng minh dữ liệu trung thực.

## 4. Vị trí so với các bài liên quan, và những gì **không** được tuyên bố

Sáu bài gần nhất đã đọc full text (`docs/literature/phase0c_full_text_notes.md`).

| Bài | Trùng chỗ nào | Khác chỗ nào |
|---|---|---|
| FLIP (NeurIPS 2025) | benchmark nền, code gốc | không có nhiễu, không có tấn công. Mục Limitations của họ **tự nêu** khoảng trống này |
| FedPN (IEEE TBD 2025) | CLIP + FL + nhiễu nhãn, cũng sửa nhãn thay vì loại client | mô hình huấn luyện là ResNet thường, CLIP chỉ dùng làm encoder ảnh, **không dùng text encoder**, không few-shot, **không có client độc hại** |
| RFedLR (NeurIPS 2025) | FL + PEFT + nhiễu nhãn | LoRA trên ViT ImageNet-21K, không CLIP, không client độc hại, **cần tập proxy sạch ở server** |
| FedDR-LoRA (ICML 2026) | như trên, mạnh hơn | như trên. Ý "hai nhánh sạch/nhiễu" của họ là thứ đồ án **cố ý tránh** để không thành bản port |
| FedMGP+ (TPAMI 2026) | prompt + client độc hại | ViT không phải CLIP, **không có nhiễu nhãn**, client độc hại chỉ là dữ liệu ngẫu nhiên, **cần tập thay thế sạch ở server** |
| zkCor (ICDE 2024) | sửa nhãn + client không trung thực | bài mật mã; ép tuân thủ bằng ZKP thay vì phát hiện |

**Ba điều không được viết trong luận văn:**
- không viết "đầu tiên dùng CLIP cho FL nhiễu nhãn" — FedPN đã nhận;
- không viết "đầu tiên tách client nhiễu với client độc hại trong FL" — MUD-HoG, Fed-RoSeC và vài bài khác đã làm ở FL thường;
- không viết "đầu tiên làm FL + PEFT + nhiễu nhãn" — RFedLR đã nhận.

**Điều được phép tuyên bố:** chưa có bài nào nghiên cứu nhiễu nhãn trong **federated prompt learning trên mô hình thị giác–ngôn ngữ**, và chưa có bài nào tách client nhiễu với client độc hại trong bối cảnh đó. Mức trùng ước lượng 50–55%.

## 5. Kỷ luật đánh giá

Đây là phần đồ án cố ý làm chặt, vì lần làm trước (cải tiến FedSNC) đổ vỡ đúng vì thiếu nó.

**Ghi tiêu chí trước khi chạy.** Mỗi giai đoạn có một cổng với ngưỡng số và **quy tắc quyết định cho mọi nhánh kết quả**, viết trước khi nhìn dữ liệu. Gate A không đạt, Gate B đạt 2/3 — và cả hai lần, phần giá trị nằm ở lý do trượt.

**`last10` là chỉ số chính, không phải `best`.** Lĩnh vực này báo độ chính xác **cao nhất qua 50 round**, tức chọn đỉnh **trên tập test**. Khi có nhiễu, mô hình đạt đỉnh sớm rồi trượt dài vì học thuộc nhãn sai, nên chỉ số ấy **làm nhẹ thiệt hại đi 1,4 đến 2,5 lần**. Muốn dừng đúng đỉnh thì phải có tập validation sạch — thứ mà một liên đoàn có nhiễu không hề có. Đây là một đóng góp phương pháp luận độc lập với phương pháp đề xuất.

**Luôn có sàn zero-shot.** Một "phòng thủ" tầm thường là không huấn luyện gì, và nó **thắng baseline trên 2/3 dataset**. Mọi phương pháp phải được so với mốc này.

**Thống kê.** Kết luận theo **kiểm định t ghép cặp, p < 0,05, tối thiểu 5 seed**, luôn báo kèm trung bình ± sd và Cohen's dz. Quy tắc ban đầu ("hiệu ≥ 2 sd") đã bị **phát hiện là sai mục đích** và được thay: `sd` đo độ tản của tổng thể nên không co lại khi thêm seed; đại lượng co lại là sai số chuẩn. Luận văn ghi cả quy tắc cũ, chỗ nó sai, và quy tắc thay thế.

Kỷ luật này đã bắt được hai lỗi thật: một lượt 3 seed cho thấy Multi-Krum trên DTD có vẻ giúp (−1,25), nhưng ở 5 seed thì **đổi dấu** (+0,27); và bản public của FLIP **không chuẩn hoá ảnh lúc huấn luyện** trong khi lúc kiểm tra thì có, khiến mọi con số thấp hơn paper 1,3–4,3 điểm cho tới khi sửa.

## 6. Tiến độ

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| 0, 0b, 0c | Literature review, kiểm novelty, đọc full text 6 bài gần nhất | Xong |
| 1 | Dựng pipeline trên FLIP, tái lập baseline | **Xong.** 9/9 ô đạt tiêu chí ghi trước, 4,76 giờ T4 |
| 2 | Gate A: đo dư địa của nhiễu nhãn | **Xong.** 5,14 giờ, 3 dataset |
| 3 | Gate B: tấn công nguỵ trang và phòng thủ chuẩn | **Xong.** 9,4 giờ, B1 đạt, B3′ đạt |
| 4 | Gate C: ba tín hiệu phát hiện | **Đã cài, kiểm CPU đạt.** Chờ chạy, ~5,8 giờ |
| 5 | Xử lý phân hoá, tín hiệu phản ứng khi sửa nhãn | Chưa |

Tổng thời gian GPU đã dùng: khoảng 19 giờ T4.

## 7. Đọc tiếp

| Muốn biết | Đọc |
|---|---|
| Tóm tắt ngắn, cả tiếng Việt và tiếng Anh | `docs/abstract.md` |
| Vì sao chọn hướng này, trùng bao nhiêu với bài đã có | `docs/literature/` |
| Tiêu chí và kế hoạch từng giai đoạn | `docs/phase1_plan.md` … `phase4_plan.md` |
| Số liệu đầy đủ | `results/Phase1/phase1_results.md`, `results/Phase2/gate_a_results.md`, `results/Phase3/gate_b_results.md` |
| Đã sửa gì so với code FLIP gốc | `docs/flip_patches.md` |
