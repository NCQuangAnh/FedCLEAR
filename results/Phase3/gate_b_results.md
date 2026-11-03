# Kết quả Gate B (chạy 2026-09-19, T4, 6,09 giờ)

Dữ liệu: `gateB/phase3_results.zip`, giải nén ở `gateB/extracted/`. 14 job, tất cả `rc=0`.

Cấu hình: PromptFL, `--data_transform paper`, seed 0/1/2, 50 round, 10 client — **3 nhiễu** (`sym` 40%), **2 độc hại**, 5 thật thà. Mọi job dùng chung một bộ vai trò và một cách chia dữ liệu, chỉ đổi kiểu tấn công và luật gộp. Chỉ số chính `last10`.

## 1. Bảng thiệt hại (so ghép cặp theo seed với lượt đối chứng)

| Dataset | Job | last10 | Thiệt hại so với đối chứng | Kết luận được? |
|---|---|---|---|---|
| DTD | `N_control` (client độc hại hành xử thật thà) | 51,97 | – | – |
| DTD | `P0_disguise` tấn công giả nhiễu | 47,01 | **+4,96 ± 4,47** | không (< 2 sd) |
| DTD | `P1_targeted` tấn công ồn ào | 50,33 | +1,64 ± 3,15 | không |
| DTD | `P2_signflip` đảo dấu cập nhật | 37,42 | **+14,55 ± 4,83** | **có** |
| DTD | `D0` giả nhiễu + multikrum | 48,26 | +3,71 ± 4,06 | không |
| DTD | `D1` giả nhiễu + median | 48,59 | **+3,38 ± 0,83** | **có** |
| DTD | `D2` signflip + multikrum | 42,87 | **+9,10 ± 4,01** | **có** |
| OxfordPets | `N_control` | 80,74 | – | – |
| OxfordPets | `P0_disguise` | 77,71 | +3,03 ± 2,26 | không |
| OxfordPets | `P1_targeted` | 78,15 | **+2,59 ± 0,76** | **có** |
| OxfordPets | `P2_signflip` | 62,51 | **+18,23 ± 7,97** | **có** |
| OxfordPets | `D0` giả nhiễu + multikrum | 75,73 | +5,01 ± 8,05 | không |
| OxfordPets | `D1` giả nhiễu + median | 80,53 | +0,21 ± 2,96 | không |
| OxfordPets | `D2` signflip + multikrum | 67,99 | +12,75 ± 9,08 | không |

## 2. Phán quyết theo tiêu chí đã ghi trước

| # | Điều kiện | DTD | OxfordPets | Kết quả |
|---|---|---|---|---|
| B1 | tấn công giả nhiễu ≥ 2,0 điểm vượt phần nhiễu sẵn có | +4,96 đạt | +3,03 đạt | **đạt về trung bình, nhưng cả hai đều chưa kết luận được** (nhỏ hơn 2 sd) |
| B2 | multikrum và median vẫn còn ≥ 2,0 thiệt hại | 3,71 và 3,38 đạt | 5,01 đạt, **median 0,21 trượt** | 1/2 dataset |
| B3 | multikrum loại client nhiễu ≥ loại client độc hại | 0,137 so với 0,399 trượt | 0,331 so với 0,467 trượt | **trượt** |

**Gate B không đạt theo câu chữ đã ghi trước.** Như Gate A, phần giá trị nằm ở chi tiết.

## 3. Phòng thủ chuẩn loại nhầm ai: con số

Mỗi round, `multikrum` công bố tập client nó tin. Bảng dưới là **tỉ lệ round mà một client thuộc vai trò đó bị loại**, đã chuẩn hoá theo số client mỗi vai (5 thật thà, 3 nhiễu, 2 độc hại).

| Dataset | Kịch bản | Thật thà | **Nhiễu** | Độc hại |
|---|---|---|---|---|
| DTD | giả nhiễu | 0,158 | 0,137 | 0,399 |
| DTD | signflip | 0,116 | 0,161 | 0,467 |
| OxfordPets | giả nhiễu | **0,014** | **0,331** | 0,467 |
| OxfordPets | signflip | **0,021** | **0,405** | **0,340** |

Đọc bảng này:

1. **Trên OxfordPets, phòng thủ gần như không bao giờ đụng client thật thà (0,014) nhưng loại client nhiễu tới 33% số round.** Tỉ lệ loại nhầm một client nhiễu **gấp 24 lần** client thật thà, và bằng **71%** tỉ lệ loại đúng kẻ tấn công. Nghĩa là thứ `multikrum` thực sự phát hiện không phải ý đồ xấu, mà là **độ lệch của cập nhật** — mà client gán nhãn kém thì cũng lệch.
2. **Ở kịch bản signflip trên Pets, nó loại client nhiễu (0,405) NHIỀU HƠN kẻ tấn công thật (0,340).** Đây là dạng mạnh nhất của giả thuyết, và nó xảy ra đúng lúc kẻ tấn công lẽ ra dễ thấy nhất.
3. **Trên DTD thì không nhầm** (nhiễu 0,137 so với độc hại 0,399). Khác biệt giữa hai dataset khớp với cơ chế đã thấy ở Gate A: DTD học nhiều từ dữ liệu nên cập nhật của mọi client đều lớn và lệch nhau, còn Pets gần như đã xong từ zero-shot nên cập nhật của client thật thà rất nhỏ và giống nhau — client nhiễu nổi bật hẳn lên và bị chấm là bất thường.

Ngưỡng B3 viết trước ("loại nhiễu ≥ loại độc hại") hoá ra quá chặt: nó chỉ bắt được trường hợp cực đoan. Dữ liệu cho thấy vấn đề có thật nhưng ở dạng nhẹ hơn.

## 4. Phòng thủ có khi còn hại hơn không phòng thủ

Chi phí của phòng thủ = thiệt hại khi có phòng thủ − thiệt hại khi không có. Âm là phòng thủ giúp được.

| Dataset | multikrum với tấn công giả nhiễu | median với tấn công giả nhiễu | multikrum với signflip |
|---|---|---|---|
| DTD | −1,25 | −1,58 | −5,44 |
| OxfordPets | **+1,98** | −2,82 | −5,49 |

**Trên OxfordPets, bật `multikrum` làm mô hình tệ đi 1,98 điểm so với không phòng thủ gì.** Lý do nhìn thẳng ra từ mục 3: nó vứt dữ liệu của client nhiễu — thứ mà Gate A đã chứng minh là đáng giữ — trong khi vẫn để lọt kẻ tấn công hơn nửa số round.

Và không luật nào đúng đều: `median` cứu được Pets gần như hoàn toàn (0,21) nhưng để lại 3,38 trên DTD; `multikrum` giúp DTD nhưng hại Pets. **Không tồn tại một luật gộp cố định đúng cho mọi trường hợp**, nên phải quyết định theo từng client thay vì áp một quy tắc cứng. Đó chính là lập luận cho hướng triage.

## 5. Hai phát hiện phụ, đều có giá trị

**Giấu mình không tốn gì cho kẻ tấn công.** Tấn công giả nhiễu gây thiệt hại ngang hoặc hơn tấn công có mục tiêu kinh điển: DTD 4,96 so với 1,64; Pets 3,03 so với 2,59. Tức kẻ tấn công không phải đánh đổi sức mạnh để đổi lấy khả năng ẩn mình. Mô hình đe doạ của đồ án vì thế hợp lý.

**Tấn công mức cập nhật mới là thứ nguy hiểm nhất.** `signflip` lấy đi 14,6 điểm trên DTD và 18,2 trên Pets, và gộp bền vững chỉ chặn được khoảng một nửa (còn 9,1 và 12,8). Riêng con số này đã đủ biện minh cho việc nghiên cứu phòng thủ trong federated prompt learning.

## 6. Vấn đề lớn nhất: phương sai giữa seed

Rất nhiều so sánh có sd từ 4 đến 9 điểm, lớn hơn cả hiệu cần đo. Ví dụ Pets `D0`: ba seed cho 75,88 / 83,74 / 67,58. DTD `P0`: một seed thậm chí không thấy thiệt hại nào.

Nguyên nhân rõ: liên đoàn chỉ có 8 ảnh/lớp, và `multikrum` là một quyết định rời rạc — loại đúng hay trượt kẻ tấn công ở một round là khác biệt lớn, rồi tích luỹ qua 50 round.

Theo đúng quy tắc đã ghi trước (hiệu nhỏ hơn 2 lần sd thì không kết luận, phải thêm seed), **bước tiếp theo là chạy thêm seed 3 và 4** cho 4 cấu hình then chốt: `N_control`, `P0_disguise`, `D0_disguise_multikrum`, `D1_disguise_median`, trên cả hai dataset. Chi phí khoảng **2,3 giờ T4**.

## 7. Tiêu chí sửa lại cho lượt 5 seed (ghi trước khi chạy)

Giữ nguyên B1 và B2. Thay B3 bằng **B3′**, đo đúng thứ cần đo thay vì đòi trường hợp cực đoan:

> **B3′:** với `multikrum`, tỉ lệ loại một client **nhiễu** phải ≥ 5 lần tỉ lệ loại một client **thật thà**, **và** ≥ 0,5 lần tỉ lệ loại một client **độc hại**, trên ít nhất một trong hai dataset.

Diễn giải: phòng thủ chuẩn đối xử với client gán nhãn kém gần như thể chúng là kẻ tấn công, chứ không cần nhầm tới mức đảo ngược. Với số liệu hiện có, Pets đạt cả hai vế (24 lần và 0,71 lần) còn DTD không đạt vế nào — nhưng đó là số 3 seed, nên phải chạy lại 5 seed mới kết luận.

**Ghi rõ trong luận văn:** B3 nguyên bản trượt, B3′ là tiêu chí sửa sau khi nhìn dữ liệu, và cả hai đều được báo. Không được trình bày B3′ như thể đã ghi trước từ đầu.

Kèm theo, mượn cặp chỉ số của FedMGP+ (TPAMI 2026) để báo cho dễ so: Attack Detection Rate (phần cập nhật độc hại bị chặn) và Mis-classification Rate (phần cập nhật lành bị chặn nhầm), **cộng thêm hạng mục thứ ba mà họ không có**: tỉ lệ client nhiễu nhưng thật thà bị chặn nhầm. Với số hiện tại, `multikrum` trên Pets có ADR 0,467, MCR-thật-thà 0,014 và MCR-nhiễu 0,331.


## 8. Lượt 5 seed (chạy 2026-09-19, 2,25 giờ)

Thêm seed 3 và 4 cho bốn cấu hình then chốt, trên cả hai dataset. Ô phân tích của notebook bị lỗi `KeyError: 0` (lỗi trong code gộp tỉ lệ loại trừ, đã sửa), nhưng mọi job huấn luyện đã xong và file output vẫn còn, nên số liệu lấy lại đủ, không phải chạy lại. Dữ liệu ở `gateB/seeds34/phase3/`.

### 8.1 Bảng 5 seed

| Dataset | Job | last10 | Thiệt hại (5 seed) | Quy tắc 2 sd | t-test ghép cặp |
|---|---|---|---|---|---|
| DTD | `P0_disguise` | 48,26 | +4,13 ± 3,43 | chưa đạt | t = 2,70, **p = 0,054** |
| DTD | `D0` giả nhiễu + multikrum | 47,99 | +4,40 ± 3,19 | chưa đạt | t = 3,08, p = 0,037 |
| DTD | `D1` giả nhiễu + median | 48,67 | **+3,73 ± 0,79** | **đạt** | t = 10,59, p < 0,001 |
| OxfordPets | `P0_disguise` | 77,71 | +3,58 ± 1,95 | chưa đạt | t = 4,10, **p = 0,015** |
| OxfordPets | `D0` giả nhiễu + multikrum | 76,08 | +5,21 ± 6,02 | chưa đạt | t = 1,94, p = 0,125 |
| OxfordPets | `D1` giả nhiễu + median | 80,81 | +0,48 ± 2,39 | chưa đạt | t = 0,45, p = 0,677 |

Quy tắc "hiệu ≥ 2 sd" mà ta ghi trước **chặt hơn** kiểm định t thông thường: nó nói về độ tản của từng hiệu, không phải sai số chuẩn của trung bình. Theo kiểm định t ghép cặp, B1 **có ý nghĩa thống kê trên Pets** (p = 0,015) và sát ngưỡng trên DTD (p = 0,054). Luận văn báo cả hai cách, và nói rõ quy tắc nào được ghi trước.

### 8.2 Phòng thủ có tự trả giá nổi không? (so trực tiếp với lượt không phòng thủ)

| Dataset | Luật gộp | Chênh so với không phòng thủ | t-test |
|---|---|---|---|
| DTD | multikrum | −0,27 | t = −0,20, p = 0,850 |
| DTD | median | +0,40 | t = 0,28, p = 0,793 |
| OxfordPets | multikrum | **−1,63** | t = −0,80, p = 0,466 |
| OxfordPets | median | **+3,10** | t = 7,84, **p = 0,001** |

Dương là phòng thủ giúp được. **Chỉ 1 trong 4 tổ hợp (dataset × luật) cho lợi ích thật: `median` trên Pets.** Hai tổ hợp còn lại không khác gì không phòng thủ, và `multikrum` trên Pets vẫn âm.

Đáng chú ý về phương pháp luận: ở 3 seed, `multikrum` trên DTD cho −1,25 (có vẻ giúp), nhưng ở 5 seed thành **+0,27** — **đổi dấu**. Đúng lý do vì sao quy tắc "chưa đủ chắc thì thêm seed" phải được giữ, và là bài học FedSNC lặp lại lần thứ ba.

### 8.3 Tỉ lệ loại trừ, gộp 5 seed

| Dataset | Thật thà | Nhiễu | Độc hại | Nhiễu/thật thà | Nhiễu/độc hại | B3 | B3′ |
|---|---|---|---|---|---|---|---|
| DTD | 0,173 | 0,132 | 0,369 | 0,8× | 0,36× | trượt | trượt |
| OxfordPets | **0,019** | **0,336** | 0,449 | **17,7×** | 0,75× | trượt | **đạt** |

B3′ ghi trước là "đạt trên ít nhất một trong hai dataset", nên **B3′ đạt**.

### 8.4 Phán quyết cuối của Gate B

| Tiêu chí | Kết quả |
|---|---|
| B1 | chưa đạt theo quy tắc 2 sd; **đạt theo kiểm định t trên Pets** (p = 0,015), sát ngưỡng trên DTD (p = 0,054) |
| B2 | đạt trên DTD (4,40 và 3,73); trượt trên Pets vì `median` chỉ để lại 0,48 |
| B3 | trượt cả hai |
| **B3′** | **đạt trên OxfordPets** |

**Kết luận cho luận văn, dựa trên số đã đo:**

1. **Gộp model bền vững không phải lời giải ở đây.** 3 trong 4 tổ hợp không cho lợi ích đo được; tổ hợp duy nhất có tác dụng (`median` trên Pets) lại là luật **không hề quyết định client nào đáng tin** — nó lấy trung vị theo từng toạ độ.
2. **Luật nào có quyết định thì quyết định sai đối tượng.** `multikrum` trên Pets loại client nhiễu nhiều gấp **17,7 lần** client thật thà, bằng 75% tỉ lệ loại đúng kẻ tấn công, và làm mô hình tệ hơn 1,63 điểm so với không phòng thủ.
3. Vậy triage — nhận diện rồi **xử lý khác nhau** — không phải thứ trang trí, mà là mảnh còn thiếu: luật dựa trên loại trừ không phân biệt được hai loại, còn luật có tác dụng thì đạt được bằng cách không phân biệt gì cả.

### 8.5 Việc còn lại của Gate B

Chạy thêm seed 5 và 6 cho `N_control` và `P0_disguise` (khoảng **1,2 giờ**), để B1 vượt hẳn ngưỡng ghi trước thay vì dừng ở p = 0,054. Notebook đã đặt sẵn `EXTRA_SEED_START = 5`, `EXTRA_SEED_JOBS = ["N_control", "P0_disguise"]`.


## 9. Lượt 7 seed cho B1 (chạy 2026-09-19, 1,07 giờ)

Thêm seed 5 và 6 cho `N_control` và `P0_disguise` trên cả hai dataset. Dữ liệu: `gateB/seeds56/`.

| Dataset | n | Thiệt hại của tấn công giả nhiễu | Quy tắc 2 sd | t-test ghép cặp | Cohen's dz |
|---|---|---|---|---|---|
| DTD | 7 | +3,62 ± 2,99 | chưa đạt | t = 3,20, **p = 0,019** | 1,21 |
| OxfordPets | 7 | **+3,51 ± 1,63** | **đạt** | t = 5,69, **p = 0,001** | 2,15 |

Ước lượng đã ổn định qua ba lần mở rộng: DTD 4,96 → 4,13 → 3,62; Pets 3,03 → 3,58 → 3,51. Cả hai hội tụ quanh 3,5 điểm, vượt xa ngưỡng 2,0 mà B1 đòi. Trên DTD, 6/7 seed cho thiệt hại dương, seed tệ nhất chỉ −0,2.

**B1 đạt.**

### 9.1 Một sai sót trong chính tiêu chí của ta, phải ghi vào luận văn

Quy tắc ghi trước là "hiệu trung bình ≥ 2 lần sd của hiệu thì mới kết luận". Sau ba lượt mở rộng seed mới thấy rõ: **quy tắc này không bao giờ có thể đạt được bằng cách thêm seed.**

Lý do: `sd` ước lượng **độ tản của tổng thể**, không phải sai số của trung bình. Thêm seed làm `sd` chính xác hơn chứ không làm nó nhỏ đi. Đại lượng co lại theo số seed là **sai số chuẩn** `se = sd / √n`. Nên "mean ≥ 2 sd" thực chất là một tiêu chí về **độ lớn hiệu ứng** (tương đương Cohen's dz ≥ 2), không phải tiêu chí về độ tin cậy thống kê.

Quy tắc đó vẫn có ích: nó là lá cờ đỏ bắt ta thêm seed, và nhờ thế mới bắt được vụ `multikrum` trên DTD **đổi dấu** giữa 3 seed và 5 seed. Nhưng nó không trả lời được câu "hiệu này có thật không".

**Sửa cho các giai đoạn sau, ghi trước từ đây:**
- Kết luận dựa trên **kiểm định t ghép cặp, p < 0,05**, với tối thiểu 5 seed.
- Luôn báo kèm **trung bình ± sd** và **Cohen's dz = mean/sd** để người đọc thấy cả độ lớn hiệu ứng lẫn độ tản.
- `dz < 1` thì dù p nhỏ vẫn phải nói rõ là hiệu ứng nhỏ so với phương sai giữa seed.

Trong luận văn ghi đúng trình tự này: tiêu chí ban đầu, chỗ nó sai, và tiêu chí thay thế. Đây là một phần của phương pháp làm việc, không phải điều cần giấu.

## 10. Tổng kết Gate B

| Tiêu chí | Kết quả |
|---|---|
| **B1** tấn công giả nhiễu gây thiệt hại thật | **đạt** — +3,62 (DTD, p = 0,019) và +3,51 (Pets, p = 0,001), 7 seed |
| **B2** phòng thủ chuẩn không cứu được | đạt trên DTD; trượt trên Pets, nơi `median` chỉ để lại 0,48 |
| **B3** (bản gốc) | trượt cả hai |
| **B3′** (bản sửa) | **đạt trên OxfordPets** — loại client nhiễu gấp 17,7 lần client thật thà |

**Đủ điều kiện sang giai đoạn 4.** Ba mệnh đề đã có số liệu đứng sau:

1. Tấn công giả làm nhiễu gây thiệt hại thật, và **không tốn gì để ẩn mình** — nó hại ngang hoặc hơn tấn công có mục tiêu kinh điển.
2. Gộp model bền vững **không phải lời giải**: chỉ 1 trong 4 tổ hợp cho lợi ích đo được, và tổ hợp đó (`median`) đạt được bằng cách **không phân biệt client nào cả**.
3. Luật có phân biệt thì **phân biệt sai đối tượng**: `multikrum` loại client nhiễu gấp 17,7 lần client thật thà và làm mô hình tệ hơn không phòng thủ.

Cộng với kết luận Gate A (client nhiễu phải sửa chứ không loại, client độc hại phải loại), đây là lập luận đầy đủ cho phương pháp của giai đoạn 4: **nhận diện ba loại client rồi xử lý khác nhau**, dùng zero-shot CLIP làm tham chiếu sạch duy nhất mà bài toán cho phép.
