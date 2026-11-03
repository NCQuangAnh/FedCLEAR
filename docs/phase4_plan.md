# Giai đoạn 4: tín hiệu phát hiện và xử lý phân hoá

Cập nhật: 2026-09-19. Tiếp nối Gate A (`results/Phase2/gate_a_results.md`) và Gate B (`results/Phase3/gate_b_results.md`).

## 1. Ba mệnh đề nền, đều đã đo

| # | Mệnh đề | Số liệu |
|---|---|---|
| 1 | Client nhiễu phải **sửa nhãn và giữ lại**, client độc hại phải **loại bỏ** | Gate A: trần của việc loại client nhiễu là −0,2 đến +3,4 điểm, trong khi trần của sửa nhãn là 4,7–13,2 |
| 2 | Gộp model bền vững **không phải lời giải** | Gate B: chỉ 1 trong 4 tổ hợp cho lợi ích đo được, và tổ hợp đó (`median`) đạt được bằng cách **không phân biệt client nào cả** |
| 3 | Luật có phân biệt thì **phân biệt sai đối tượng** | Gate B: `multikrum` loại client nhiễu gấp **17,7 lần** client thật thà, và làm mô hình tệ hơn 1,63 điểm so với không phòng thủ |

Mệnh đề 3 cho biết vì sao phải có tín hiệu mới: **độ lệch của cập nhật** là thứ duy nhất các phòng thủ hiện có nhìn vào, mà nhiễu nhãn cũng sinh ra độ lệch. Muốn tách, phải nhìn vào **hình dạng** của độ lệch chứ không chỉ độ lớn.

## 2. Ba tín hiệu (2026-09-19, đã cài trong `flcore/signals.py`)

Mọi thứ tính **chỉ từ prompt của client**. Server không thấy dữ liệu client, không cần tập sạch, không đụng tập test. Thứ duy nhất dùng thêm là chính CLIP — mà mọi bên đều đã có.

**Mẹo probe:** không gian ảnh và văn bản của CLIP là chung, nên **embedding văn bản của một lớp đóng vai ảnh đại diện của lớp đó**. Server có ngay một tập probe mà không cần một tấm ảnh nào.

| Tín hiệu | Định nghĩa | Kỳ vọng |
|---|---|---|
| `s_sem` | Độ trôi ngữ nghĩa: trung bình cosine giữa embedding lớp của client và embedding zero-shot, trừ đi cùng đại lượng của model toàn cục | Cao ở **cả** client nhiễu lẫn độc hại. Dùng để tách nhóm "có vấn đề" khỏi client thật thà |
| `s_conc` | Độ tập trung: cho probe chạy qua prompt của client, lấy phân phối softmax theo lớp rồi tính khối lượng cột lớn nhất, trừ đi cùng đại lượng của model toàn cục | **Đây là tín hiệu tách nhiễu với độc hại.** Nhiễu đối xứng rải nhãn sai ra nhiều lớp; tấn công có mục tiêu hoặc giả nhiễu dồn hết về một lớp |
| `s_upd` | Chuẩn của hiệu prompt so với model toàn cục, chia cho trung vị của round | Tín hiệu kiểu Krum, giữ lại làm **mốc phải vượt** |

Bật bằng `--log_signals true`. Mỗi round server ghi điểm của từng client kèm **vai trò thật** vào `noise_seed_*.json`, nên đánh giá khả năng tách là đọc thẳng từ file, không phải chạy lại.

Chi phí: mỗi client mỗi round thêm một lượt forward của text encoder trên `n_cls` prompt. Với 47–101 lớp thì không đáng kể so với một round huấn luyện.

## 3. Tiêu chí Gate C (ghi trước khi chạy)

Chạy lại đúng các cấu hình của Gate B nhưng bật `--log_signals true`: `N_control`, `P0_disguise`, `P1_targeted`, `P2_signflip`, trên DTD và OxfordPets, 5 seed. Vai trò: 3 nhiễu, 2 độc hại, 5 thật thà.

Đánh giá trên **các round 10–50** (bỏ giai đoạn khởi động), gộp qua seed. Chỉ số là **AUC** của việc dùng một tín hiệu để xếp hạng client.

| # | Điều kiện | Ngưỡng |
|---|---|---|
| C1 | `s_sem` tách client **có vấn đề** (nhiễu ∪ độc hại) khỏi client thật thà | AUC ≥ 0,80 trên ít nhất một dataset |
| C2 | `s_conc` tách client **độc hại** khỏi client **nhiễu** | AUC ≥ 0,80 trên ít nhất một dataset |
| C3 | Cả hai tín hiệu ngữ nghĩa phải **hơn** tín hiệu độ lệch | AUC của `s_conc` (tách độc hại với nhiễu) ≥ AUC của `s_upd` cho cùng việc, cách biệt ≥ 0,10 |

**C2 là tiêu chí sống còn.** Nó chính là thứ Gate B chứng minh các phòng thủ hiện có không làm được.

Quy tắc thống kê đã sửa sau Gate B: kết luận theo **kiểm định t ghép cặp p < 0,05 với ≥ 5 seed**, báo kèm trung bình ± sd và Cohen's dz. Với AUC thì so theo từng seed (ghép cặp theo seed).

Quy tắc quyết định, ghi trước:

| Kết quả | Việc làm |
|---|---|
| C1, C2, C3 đều đạt | Dựng bộ triage ba lớp từ hai tín hiệu, sang giai đoạn 5: xử lý phân hoá (sửa nhãn cho nhiễu, loại bỏ độc hại) |
| C2 trượt | Tín hiệu tập trung không đủ. Chuyển sang **tín hiệu phản ứng khi sửa nhãn** (mục 5), vốn không dựa vào cấu trúc nhãn mà dựa vào hành vi |
| C1 trượt nhưng C2 đạt | Bỏ bước lọc "có vấn đề / thật thà", dùng `s_conc` trực tiếp để loại client độc hại |
| C3 trượt | Tín hiệu ngữ nghĩa không hơn được độ lệch. Phải nói thẳng điều này trong luận văn và dồn về tín hiệu phản ứng |

**Không** chỉnh định nghĩa tín hiệu sau khi nhìn kết quả rồi báo như thể đã ghi trước. Nếu sửa, ghi rõ là bản sửa, như đã làm với B3′.

## 4. Kẻ tấn công thích nghi (ghi trước, để phản biện)

`s_conc` bắt việc dồn nhãn về **một** lớp. Kẻ tấn công biết điều đó có thể rải mục tiêu ra `k` lớp. Đây là phản biện hiển nhiên nhất, nên phải tự chạy trước khi bị hỏi:

- thêm `--attack_type noise_disguise_spread --attack_targets k` với k ∈ {1, 2, 4, 8};
- đo `s_conc` và thiệt hại theo k.

Giả thuyết ghi trước: rải mục tiêu làm `s_conc` giảm **nhưng cũng làm thiệt hại giảm**, vì tấn công càng giống nhiễu ngẫu nhiên thì càng chỉ gây hại như nhiễu. Nếu đúng, đó là một **đánh đổi bắt buộc** của kẻ tấn công, và là kết quả đáng giá của luận văn. Nếu sai — tức rải mục tiêu vẫn hại mạnh mà `s_conc` không bắt được — thì tín hiệu này hỏng, và phải nói rõ.

## 5. Tín hiệu thứ hai: phản ứng khi được yêu cầu sửa nhãn (giai đoạn 5)

Server đề nghị một bản sửa nhãn cho những mẫu mà nó nghi sai, rồi quan sát:
- client nhiễu thật thà chấp nhận, và loss cục bộ **giảm đúng như dự đoán**;
- client độc hại hoặc từ chối, hoặc báo loss không khớp với bản sửa.

Khác biệt với Fed-RoSeC (ITASEC 2026): họ **giả định** client độc hại tuân thủ. Khác với zkCor (ICDE 2024): họ **ép** tuân thủ bằng zero-knowledge proof, chứng minh phép tính đúng nhưng không chứng minh dữ liệu trung thực. Ta **phát hiện việc không tuân thủ bằng thống kê**, không giả định và không ép.

## 6. Baseline phải so

| Baseline | Nguồn | Vì sao |
|---|---|---|
| `multikrum`, `median`, `trimmed_mean` | đã cài | Phòng thủ chuẩn, đã đo ở Gate B |
| Bộ phát hiện của **FedPN** | IEEE TBD 2025 | Cùng dùng CLIP, chấm client bằng độ chính xác của prototype toàn cục trên dữ liệu cục bộ. **Không thể** tách nhiễu với độc hại vì cả hai đều cho điểm thấp — đây là baseline công bằng nhất |
| "Clean probability = sigmoid(hiệu loss) + EMA" | FedDR-LoRA, ICML 2026 | Baseline mức mẫu rất rẻ |
| ORACLE triage | tự dựng | Trần: biết trước vai trò thật, sửa nhãn client nhiễu và loại client độc hại |

Cặp chỉ số báo cáo, mượn của FedMGP+ (TPAMI 2026) và **thêm hạng mục thứ ba mà họ không có**: Attack Detection Rate, Mis-classification Rate trên client thật thà, và **Mis-classification Rate trên client nhiễu**.

## 7. Việc còn lại

1. ~~Ba tín hiệu, tính từ prompt, ghi kèm vai trò thật~~ — xong 2026-09-19 (`flcore/signals.py`, cờ `--log_signals`).
2. ~~Kiểm trên CPU~~ — xong 2026-09-19. Dữ liệu giả 6 lớp, 4 client (1 độc hại `noise_disguise`, 2 nhiễu, 1 thật thà), 4 round. Tín hiệu ghi đúng kèm vai trò thật, và lưu cả vào `noise_seed_*.json`.

Dù dữ liệu giả và chỉ 4 round, `s_conc` đã tách đúng hướng: client độc hại đạt +0,067 / +0,045 / +0,038 ở round 1–3, trong khi ba client còn lại đều ≤ 0,02. `s_upd` cũng bắt được client độc hại nhưng đồng thời chấm cao một client nhiễu — đúng hành vi đã đo ở Gate B.

Một điểm cần biết: ở **round cuối**, lịch cosine đưa learning rate về 0 nên mọi client trả về đúng prompt toàn cục và mọi tín hiệu bằng 0. Ô phân tích đã bỏ qua những round như vậy.

3. ~~Notebook `kaggle/phase4_gate_c.ipynb` và ô phân tích AUC~~ — xong.
4. ~~Chạy Gate C~~ — xong 2026-09-20, 6,40 giờ, 8 job × 5 seed. Kết quả: `results/Phase4/gate_c_results.md`.

**Gate C không đạt trên dataset nào** — nhưng hai dataset trượt ở **hai tiêu chí khác nhau**, và lý do có cấu trúc:

| | DTD (huấn luyện hơn zero-shot 13,83) | OxfordPets (hơn 2,40) |
|---|---|---|
| C1 `s_sem` phát hiện client bất thường | 0,274 — **đảo chiều** | **0,954** |
| C2 `s_conc` tách độc hại khỏi nhiễu | **0,780** (thiếu 0,02) | 0,487 |
| C3 hơn `s_upd` | +0,253 đạt | +0,087 trượt |

Cơ chế: trên DTD, client thật thà học được nhiều nên trôi xa zero-shot nhất — `s_sem` đang đo **mức học được**, không phải mức hỏng. Trên Pets, prompt gần như không di chuyển nên `s_conc` không có gì để đo, và client nhiễu tình cờ tập trung ngang kẻ tấn công.

Phần đạt rõ: tấn công mức cập nhật (`signflip`) bị `s_conc` bắt trên **cả hai** dataset (0,980 và 0,807).

5. **Kiểm giả thuyết chế độ trên dataset chưa dùng.** Caltech101 có mức huấn luyện hơn zero-shot 4,52, nằm giữa hai dataset đã chạy. Dự đoán **ghi trước**: `s_sem` ∈ [0,70; 0,95], `s_conc` ∈ [0,50; 0,75]. Notebook đã đặt `MODE = "gate_c_regime"`, ~3 giờ, và tự in ra "as predicted" hay "OUTSIDE the predicted range".

6. Theo quy tắc ghi trước cho nhánh C2 trượt: sang **tín hiệu phản ứng khi sửa nhãn** (mục 5), không phụ thuộc chế độ.
