# Giai đoạn 6: đổi khung bài toán — từ suy đoán ý đồ sang kiểm chứng sự tuân thủ

Cập nhật: 2026-09-20. Sau Gate C và Gate D.

## 1. Vì sao đổi khung, và đây không phải là bỏ cuộc

Gate C và Gate D đều trượt. Nhưng đọc kỹ thì cả hai trượt **cùng một lý do**, và lý do đó chỉ ra lối đi.

| Cổng | Hỏi gì | Kết quả |
|---|---|---|
| C | Nhìn prompt có đoán được ý đồ không? | Phụ thuộc dataset. `s_sem` đảo chiều khi dataset cần học nhiều; `s_conc` sập khi prompt ít di chuyển. Và ở chỗ nó mạnh thì baseline cũng mạnh |
| D | Nhìn phản ứng có đoán được ý đồ không? | Trượt tiêu chí, vì tiêu chí hỏi "tách độc hại khỏi nhiễu" |

**Ý đồ không quan sát được.** Một client cẩu thả và một kẻ tấn công có thể gửi lên thứ giống hệt nhau. Mọi nỗ lực suy ra ý đồ từ vật phẩm client gửi đều đang cố đọc một thứ không có trong dữ liệu.

Nhưng số liệu Gate D chứa một đại lượng **quan sát được rất rõ**, chỉ là mình đã hỏi sai câu nên không nhìn thấy:

| Dataset | Lượt | AUC tách **client từ chối** khỏi **client tuân thủ** |
|---|---|---|
| DTD | có tấn công | **0,993** |
| OxfordPets | có tấn công | **0,960** |
| DTD | đối chứng | 0,945 |
| Caltech101 | đối chứng | 0,870 |

Không phụ thuộc chế độ dataset như Gate C. Đây là tín hiệu mạnh nhất toàn đồ án.

**Đổi khung:**

> Không thể nhìn thứ client gửi lên để biết nó cẩu thả hay cố ý. Nhưng có thể **yêu cầu nó làm một việc mà chỉ kẻ tấn công mới có lý do từ chối**, rồi phát hiện sự từ chối. Bài toán chuyển từ **suy đoán ý đồ** (không đặt đúng) sang **kiểm chứng sự tuân thủ với một giao thức do server ra** (đặt đúng và kiểm được).

## 2. Cơ chế: kiểm toán ngẫu nhiên biến quan sát thành phương pháp

Chỉ phát hiện từ chối thì chưa đủ, vì kẻ tấn công có thể **bịa prompt probe** cho giống đã tuân thủ — prompt probe vốn không được gộp nên bịa không tốn gì.

Vá lỗ đó bằng một dòng: **với xác suất `p`, server lấy chính prompt probe làm đóng góp của client round đó** (`--probe_audit_prob`).

Khi ấy kẻ tấn công kẹt trong thế lưỡng nan không lối thoát:

| Lựa chọn | Hậu quả |
|---|---|
| **Tuân thủ thật** | Bản sửa đến từ model toàn cục, vốn không chia sẻ lớp đích của kẻ tấn công → **mất cuộc tấn công** mỗi lần bị kiểm toán |
| **Từ chối** | Bị phát hiện ở AUC 0,96–0,99 |
| **Bịa prompt probe cho giống đã sửa** | Prompt bịa đó **bị gộp thật** khi kiểm toán → cũng mất cuộc tấn công |

Client thật thà không mất gì ở cả ba nhánh: bản sửa từ model toàn cục gần với nhãn thật của họ, nên prompt probe của họ cũng tốt ngang prompt thường.

**Khác biệt với hai bài gần nhất:**

| | Cách xử lý việc tuân thủ | Chi phí |
|---|---|---|
| Fed-RoSeC (ITASEC 2026) | **Giả định** client độc hại tuân thủ | — (giả định không kiểm được) |
| zkCor (ICDE 2024) | **Ép** tuân thủ bằng zero-knowledge proof | Rất đắt, và chỉ chứng minh phép tính đúng chứ không chứng minh dữ liệu trung thực |
| **Đây** | **Làm cho tuân thủ có giá và không tuân thủ để lại dấu vết** | Một lượt huấn luyện thêm mỗi vài round |

## 3. Tiêu chí Gate E (ghi trước khi chạy)

Cấu hình: 3 nhiễu, 2 độc hại, 5 thật thà, `sym` 40%, `noise_disguise`, 5 seed, `--correction_every 5`, `--probe_audit_prob 1.0`. Dataset: DTD, OxfordPets, Caltech101.

| # | Điều kiện | Ngưỡng | Ý nghĩa |
|---|---|---|---|
| **E1** | **Thế lưỡng nan có thật.** Kẻ tấn công **tuân thủ** mất ít nhất **một nửa** thiệt hại nó gây được so với khi từ chối | ≥ 50% trên ≥ 2/3 dataset, ghép cặp theo seed, t-test p < 0,05 | Nếu trượt: tuân thủ không tốn gì cho kẻ tấn công, cả khung sụp |
| **E2** | **Từ chối phát hiện được.** AUC(−`r_align`) tách client từ chối khỏi client tuân thủ | ≥ 0,90 trên ≥ 2/3 dataset | Đã có 0,96–0,99 ở Gate D, nhưng phải xác nhận với đối chứng đã sửa |
| **E3** | **Giao thức có lợi thật.** Accuracy cuối (`last10`) của giao thức đầy đủ hơn luật gộp cố định tốt nhất | ≥ 2,0 điểm trên ≥ 2/3 dataset | Đây là điều duy nhất hội đồng và reviewer thực sự quan tâm |

**E1 là tiêu chí sống còn**, và nó là câu hỏi mình chưa từng đo: *tuân thủ có thực sự xoá được cuộc tấn công không?*

Quy tắc quyết định:

| Kết quả | Việc làm |
|---|---|
| E1, E2, E3 đạt | Có bài. Viết paper quanh khung "kiểm chứng tuân thủ", dùng Gate A–D làm phần động cơ và phần kết quả âm |
| E1 đạt, E3 trượt | Cơ chế đúng nhưng chưa thành lợi ích. Dò `p` và tần suất probe, rồi đo lại một lần |
| **E1 trượt** | Khung sụp. Quay về **bài đo đạc** (mục 5), và đó là điểm dừng thật sự |

## 4. Vì sao đây là bài mạnh hơn bài cũ

Bài cũ: "chúng tôi đề xuất một tín hiệu phát hiện client độc hại". Yếu, vì tín hiệu phụ thuộc dataset và không hơn baseline ở chỗ baseline mạnh.

Bài mới: **"ý đồ không quan sát được, nên đừng suy đoán nó — hãy thiết kế giao thức sao cho kẻ tấn công phải tự lộ diện."** Mạch bài:

1. FPL dưới nhiễu nhãn mong manh hơn benchmark báo (Gate A, cộng phát hiện về chỉ số).
2. Client nhiễu và độc hại cần xử lý **ngược nhau** (Gate A).
3. Phòng thủ hiện có không tách được, và **phân biệt sai đối tượng** (Gate B).
4. Suy đoán ý đồ từ hình học prompt **không đáng tin** — kết quả âm có cơ chế (Gate C).
5. **Vì vậy** đổi câu hỏi: kiểm chứng tuân thủ thay vì suy đoán ý đồ (Gate D, E).
6. Kiểm toán ngẫu nhiên đóng nốt lỗ hổng bịa prompt.
7. Đo lợi ích cuối bằng accuracy, so với mọi baseline.

Kết quả âm ở bước 4 **trở thành một phần cần thiết của lập luận** chứ không còn là thất bại. Đó là dấu hiệu của một bài viết chắc.

## 5. Phương án lui, nếu E1 trượt

Bài đo đạc, nhắm **NeurIPS Datasets & Benchmarks** — đúng chỗ FLIP đã đăng:

- nghiên cứu hệ thống đầu tiên về nhiễu nhãn trong federated prompt learning trên VLM;
- chỉ số `best` mà cả lĩnh vực dùng làm nhẹ tác hại 1,4–2,5 lần, và 2/3 dataset tụt dưới zero-shot;
- trần của loại bỏ so với trần của sửa nhãn: hai cách xử lý ngược nhau;
- gộp bền vững chỉ có tác dụng ở 1/4 tổ hợp, và có khi còn hại hơn không phòng thủ;
- hai kết quả âm có cơ chế về việc phát hiện.

Không có phương pháp, nhưng đủ chất cho một bài benchmark/analysis.

## 6. Việc cần làm

1. ~~Cơ chế kiểm toán (`--probe_audit_prob`) và kẻ tấn công biết tuân thủ (`--attack_probe_comply`)~~ — xong 2026-09-20.
2. ~~Kiểm trên CPU.~~
3. ~~Notebook giai đoạn 6.~~
4. ~~Chạy Gate E.~~ — xong 2026-09-21, 10,88 giờ, 10/10 job. Kết quả ở `results/Phase6/gate_e_results.md`.

## 7. Gate E đã chạy: E2 đạt, E1 và E3 trượt, và quy tắc quyết định ở mục 3 cần đọc lại cho đúng

| Tiêu chí | Kết quả |
|---|---|
| E1 (tuân thủ mất ≥ 50% thiệt hại) | **trượt**: giữ 57% / 62%; và ở tương phản sạch `A2` − `A1` thì giữ tới 82% / 77% |
| E2 (từ chối phát hiện được, AUC ≥ 0,90) | **đạt**: 0,993 / 0,965, và **0,987 / 0,907 khi so riêng với client nhiễu** |
| E3 (hơn luật gộp cố định tốt nhất ≥ 2,0 điểm) | **trượt**: +0,81 trên DTD, **−2,90** trên Pets |

Quy tắc ghi trước ở mục 3 nói "**E1 trượt → khung sụp → quay về bài đo đạc**". Không áp dụng quy tắc đó ngay, và đây là lý do, ghi ra để người đọc tự phán xét thay vì phải tin:

1. **Tiêu chí E1 chọn sai nhóm đối chứng.** Tương phản `A2` so với `A0` đổi hai thứ cùng lúc (kiểm toán bật/tắt *và* tuân thủ/từ chối). Lỗi thiết kế của phần ghi trước, không phải phát hiện hậu nghiệm.
2. **Tiêu chí E1 trộn cơ chế với liều lượng.** Cơ chế chỉ xoá tấn công ở round bị kiểm toán, mà cấu hình chỉ kiểm toán 10 trong 50 round. Xoá 18–23% bằng 20% số round là gần đúng tỉ lệ. Liều lượng chưa bao giờ được đăng ký như một biến.
3. **Giao thức mà E3 so sánh chưa từng tồn tại.** Cả 5 cấu hình Gate E đều **vẫn gộp** client đã bị bắt quả tang từ chối. Bộ phát hiện đạt AUC 0,91–0,99 rồi bị bỏ không dùng.

Điểm 3 là điểm quyết định: E1 và E3 chưa được kiểm, chứ không phải đã bị bác. Gate F kiểm chúng. Nếu Gate F trượt thì **lúc đó** mới áp dụng phương án lui ở mục 5, và lúc đó nó là điểm dừng thật.

Thêm một kết quả không nằm trong kế hoạch, và nó đổi tính chất của đóng góp: **kiểm toán có lãi ròng**. Federation có nhiễu, không có kẻ địch nào, vẫn tốt lên **0,86 điểm (DTD, p = 0,078)** và **1,01 điểm (Pets, p = 0,008)** khi bật kiểm toán. Vì nhãn của model toàn cục sạch hơn nhãn của client nhiễu, nên thay đóng góp bằng prompt huấn luyện dưới nhãn đó là một bước **khử nhiễu**. Cơ chế này không chỉ là phòng thủ; nó là một **luật gộp có sửa nhãn**.

## 8. Việc còn lại

1. ~~Luật loại trừ trên nhãn "từ chối" (`--refusal_rule`)~~ — xong 2026-09-21.
2. ~~Chạy Gate F, `MODE = "gate_f"`~~ — xong 2026-09-21, 5,46 giờ, 5/5 job trên DTD. **F1 và F3 đều trượt.** `results/Phase6/gate_f_results.md`.
3. `MODE = "gate_f_dose"`: F2 cộng hai lượt chẩn đoán (`O_drop_mal`, `A6_fast_ban`), ~6,8 giờ.

## 9. Gate F trượt, và lần này áp dụng quy tắc dừng

| Tiêu chí | Kết quả |
|---|---|
| F1 (loại trừ xoá được tấn công, còn ≤ 25%) | **trượt**: còn **85%**, chênh +0,65 ± 1,41, p = 0,358 |
| F3 (ghép với `median`, ≥ +2,0 điểm) | **trượt**: **−1,62**, ghép vào làm tệ đi |

Ở mục 7 tôi đã **không** áp dụng quy tắc "E1 trượt → khung sụp", với lý do E1 chọn sai nhóm đối chứng và giao thức đầy đủ chưa từng tồn tại. Lý do đó đã được kiểm: giao thức đầy đủ giờ tồn tại, bộ phát hiện chạy đúng như hiệu chỉnh (cấm 7–9 trong 10 kẻ tấn công, chạm 0–1 trong 25 client thật thà), **và nó vẫn không mua được accuracy**. Không có lý do thứ hai để hoãn.

**Khung "thế lưỡng nan của kẻ tấn công" như một cơ chế phòng thủ: chết.** Không cứu nữa.

Nhưng phương án lui ở mục 5 giờ mạnh hơn bản viết ban đầu, vì Gate E và Gate F đã thêm hai thứ mà bản đó chưa có:

1. **Nhận diện giải được.** Sự tuân thủ với một yêu cầu do server ra thì quan sát được, kể cả khi ý đồ thì không: AUC 0,91–0,99 tách độc hại khỏi **nhiễu**, ổn định qua dataset, và luật trực tuyến đạt 7–9/10 với 0–1/25 báo động giả.
2. **Loại bỏ client là cần gạt sai** — không với client nhiễu (Gate A, ≤ 3,1 điểm), không với client độc hại (Gate F, +0,65 không ý nghĩa), không bằng luật gộp bền vững (Gate B, 1/4 tổ hợp). Thứ có tác dụng là **thay cập nhật bằng bản huấn luyện dưới nhãn của model toàn cục**, và nó có lãi +0,86/+1,01 **ngay cả khi không có kẻ địch**.

Luận điểm của bài không còn là "chúng tôi đo nhiễu nhãn trong federated prompt learning", mà là **"nhận diện giải được, phản ứng thì không, và cần gạt mà cả lĩnh vực đang dùng là cần gạt sai"**.

## 10. Việc còn lại trước khi viết

1. `MODE = "gate_f_dose"` trên DTD (~6,8 giờ): F2, cộng `O_drop_mal` (trần tuyệt đối của loại trừ) và `A6_fast_ban` (độ trễ có phải nguyên nhân không).
2. Nhân bản cổng E và F sang **OxfordPets** để mọi phát biểu có ít nhất hai dataset.
3. Dừng thí nghiệm mới. Viết.
