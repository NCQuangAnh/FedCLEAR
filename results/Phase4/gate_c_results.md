# Kết quả Gate C (chạy 2026-09-20, T4, 6,40 giờ)

Dữ liệu: `phase4_results.zip`, giải nén ở `extracted/`. 8 job, 5 seed mỗi job, tất cả `rc=0`.

Thiết lập giống Gate B: 10 client — 3 nhiễu (`sym` 40%), 2 độc hại, 5 thật thà. Tín hiệu chấm mỗi round, lấy trung bình round 10–49 cho từng client từng seed, rồi tính AUC.

## 1. Phán quyết theo tiêu chí ghi trước

Xét trên kịch bản trung tâm `P0_disguise` (tấn công nguỵ trang thành nhiễu):

| Tiêu chí | Ngưỡng | DTD | OxfordPets |
|---|---|---|---|
| C1 `s_sem` tách (nhiễu ∪ độc hại) khỏi thật thà | ≥ 0,80 | **0,274 trượt** (và đảo chiều) | **0,954 đạt** |
| C2 `s_conc` tách độc hại khỏi nhiễu | ≥ 0,80 | **0,780 trượt** (thiếu 0,02) | **0,487 trượt** |
| C3 `s_conc` hơn `s_upd` | ≥ +0,10 | **+0,253 đạt** | +0,087 trượt |

**Gate C không đạt trên dataset nào.** Nhưng hai dataset trượt ở **hai tiêu chí khác nhau**, và đó không phải ngẫu nhiên.

## 2. Hai tín hiệu bù trừ nhau, và biến chi phối là mức dataset cần huấn luyện

Bảng AUC đầy đủ cho `P0_disguise`:

| Việc cần làm | DTD (huấn luyện hơn zero-shot **13,83** điểm) | OxfordPets (hơn **2,40** điểm) |
|---|---|---|
| Phát hiện client bất thường: `s_sem`, (nhiễu ∪ độc hại) so với thật thà | 0,274 | **0,954** |
| Phát hiện client bất thường: `s_conc`, nhiễu so với thật thà | 0,384 | **0,973** |
| Phát hiện client bất thường: `s_conc`, độc hại so với thật thà | 0,680 | **0,984** |
| **Tách độc hại khỏi nhiễu: `s_conc`** | **0,780** | 0,487 |

Giá trị trung bình của tín hiệu cho thấy cơ chế:

| Dataset | Vai trò | `s_sem` | `s_conc` |
|---|---|---|---|
| DTD | thật thà | **0,056** | 0,032 |
| DTD | nhiễu | 0,010 | −0,014 |
| DTD | độc hại | 0,020 | **0,125** |
| OxfordPets | thật thà | **−0,082** | 0,001 |
| OxfordPets | nhiễu | 0,087 | 0,030 |
| OxfordPets | độc hại | 0,022 | 0,024 |

**Trên DTD, `s_sem` đo nhầm thứ khác.** Client thật thà có độ trôi ngữ nghĩa **cao nhất** (0,056), vì họ học được nhiều nhất — mà học tốt trên DTD nghĩa là đi xa khỏi cách hiểu gốc của CLIP (zero-shot 41,78 lên 55,61). Nên tín hiệu này đang đo **mức độ học được**, không phải mức độ hỏng. Đó là lý do AUC ra 0,274, tức **đảo chiều**.

**Trên OxfordPets, `s_conc` gần như không có tín hiệu để đo.** Biên độ chỉ 0,02–0,03, nhỏ hơn DTD năm lần, vì zero-shot đã gần trần nên prompt hầu như không di chuyển. Client nhiễu tình cờ tạo ra mức tập trung ngang kẻ tấn công (0,030 so với 0,024), nên AUC rơi về 0,487.

**Quy luật:** dataset càng cần huấn luyện thì `s_sem` càng vô dụng và `s_conc` càng mạnh. Dataset càng gần trần zero-shot thì ngược lại.

Điều đáng chú ý: **biến chi phối này máy chủ tự quan sát được**, vì độ trôi của chính prompt toàn cục so với zero-shot là đại lượng tính được mà không cần nhãn. Nếu quy luật trên đúng, máy chủ biết mình đang ở chế độ nào và dùng tín hiệu tương ứng. Nhưng đây là **suy luận hậu nghiệm**, chưa được kiểm.

## 3. Các phép kiểm đối chứng đều đúng

Lượt `N_control` cho client "độc hại" hành xử thật thà. Nếu tín hiệu đo đúng thứ nó tuyên bố thì AUC tách độc hại khỏi nhiễu phải về mức ngẫu nhiên hoặc đảo chiều — và đúng như vậy: DTD 0,580, OxfordPets 0,080 (đảo chiều, vì lúc này nhóm "độc hại" thực chất là thật thà nên có `s_conc` thấp hơn nhóm nhiễu).

## 4. Tín hiệu bắt rất tốt tấn công mức cập nhật

| Kịch bản | `s_conc` tách độc hại khỏi nhiễu | tách độc hại khỏi thật thà |
|---|---|---|
| `P2_signflip` trên DTD | **0,980** | 0,932 |
| `P2_signflip` trên OxfordPets | **0,807** | 0,940 |

Đảo dấu cập nhật prompt tạo ra méo mó ngữ nghĩa rất tập trung, và tín hiệu bắt được trên **cả hai** dataset. Đây là phần đạt rõ ràng.

Ngược lại, `P1_targeted` (tấn công có mục tiêu kinh điển) không bị bắt (0,553 và 0,187) — hợp lý, vì Gate B đã đo tấn công này yếu nhất (1,64 điểm trên DTD): nó chỉ đụng vào các mẫu của **một lớp nguồn**, mà với 8 ảnh/lớp thì client có rất ít mẫu như vậy, nên gần như không để lại dấu vết.

## 5. Thử các tín hiệu dẫn xuất — không cứu được (hậu nghiệm)

Đã thử chuẩn hoá độ tập trung theo độ lệch (`s_conc / s_upd`), trừ tuyến tính, và nhân với `s_sem`:

| Dataset | `s_conc` | `s_conc/s_upd` | `s_conc − s_upd` | `s_conc × s_sem` |
|---|---|---|---|---|
| DTD `P0_disguise` | 0,780 | 0,787 | 0,773 | 0,687 |
| OxfordPets `P0_disguise` | 0,487 | 0,520 | 0,513 | 0,173 |

Không có biến thể nào vượt ngưỡng. Ghi lại để không ai phải thử lại, và để nói rõ rằng con số 0,780 không phải do chưa tối ưu hoá công thức.

## 6. Việc tiếp theo, và phép kiểm giả thuyết chế độ (ghi trước)

Quy tắc ghi trước cho nhánh "C2 trượt" là: chuyển sang **tín hiệu phản ứng khi sửa nhãn**, vốn dựa vào hành vi chứ không dựa vào cấu trúc nhãn. Sẽ làm ở giai đoạn 5.

Nhưng trước đó, giả thuyết ở mục 2 phải được kiểm trên **một dataset chưa dùng**, nếu không nó chỉ là câu chuyện kể vừa khít hai điểm dữ liệu.

**Phép kiểm:** chạy `N_control` và `P0_disguise` trên **Caltech101**, 5 seed, khoảng 3 giờ T4. Caltech có mức huấn luyện hơn zero-shot là **4,52 điểm**, nằm giữa OxfordPets (2,40) và DTD (13,83).

**Dự đoán ghi trước, trước khi chạy:**

| Đại lượng | Dự đoán cho Caltech101 | Căn cứ |
|---|---|---|
| `s_sem`, (nhiễu ∪ độc hại) so với thật thà | **0,70 – 0,95** | nội suy giữa 0,954 (Pets) và 0,274 (DTD), lệch về phía Pets vì 4,52 gần 2,40 hơn |
| `s_conc`, độc hại so với nhiễu | **0,50 – 0,75** | nội suy giữa 0,487 và 0,780 |
| Dấu của `s_sem` ở nhóm thật thà | âm hoặc gần 0 | vì zero-shot còn tương đối mạnh |

Nếu cả hai rơi đúng khoảng: cơ chế được xác nhận, và luận văn có một **quy luật dự đoán được** chứ không chỉ hai quan sát rời. Nếu trượt ra ngoài: bỏ hẳn cách giải thích theo chế độ, và nói rõ rằng hai dataset chỉ đơn giản hành xử khác nhau vì lý do chưa rõ.

**Không** được sửa khoảng dự đoán sau khi nhìn kết quả.


## 7. Phép kiểm trên Caltech101 (chạy 2026-09-20, 3,14 giờ)

Dữ liệu: `caltech/`. Hai job, 5 seed, `rc=0`.

| Đại lượng | Dự đoán ghi trước | Thực tế | |
|---|---|---|---|
| `s_sem`, client bất thường so với thật thà | [0,70; 0,95] | **0,938** | **đúng dự đoán** |
| `s_conc`, độc hại so với nhiễu | [0,50; 0,75] | **0,987** | **ra ngoài, cao hơn hẳn** |
| Dấu `s_sem` của client thật thà | âm hoặc gần 0 | −0,043 | đúng dự đoán |

**Giả thuyết chế độ bị bác một nửa.** Phần `s_sem` đúng: nó hoạt động khi zero-shot còn tương đối mạnh và đảo chiều khi dataset cần học nhiều. Phần `s_conc` sai hẳn: Caltech không nằm giữa hai dataset kia mà **cao hơn cả hai**.

Bảng đầy đủ ba dataset, kịch bản `P0_disguise`:

| Dataset | Số lớp | Huấn luyện hơn zero-shot | `s_sem` | **`s_conc`** | `s_upd` | Chênh so với `s_upd` |
|---|---|---|---|---|---|---|
| Caltech101 | **102** | 4,52 | 0,938 | **0,987** | 0,933 | +0,053 |
| DTD | **47** | 13,83 | 0,274 | **0,780** | 0,527 | +0,253 |
| OxfordPets | **37** | 2,40 | 0,954 | **0,487** | 0,400 | +0,087 |

Sắp theo `s_conc` thì thứ tự là 0,987 > 0,780 > 0,487, **khớp chính xác thứ tự số lớp** 102 > 47 > 37, và **không khớp** thứ tự mức huấn luyện 4,52 < 13,83 > 2,40.

Cách giải thích hợp lý: độ tập trung được đo bằng khối lượng cột lớn nhất trong phân phối probe. Khi có 102 lớp, mức nền là 1/102 nên một lớp đích bị dồn về sẽ nổi bật; khi chỉ có 37 lớp, mức nền là 1/37 và nhiễu ngẫu nhiên cũng dễ tạo ra mức tập trung tương đương.

**Nhưng đây lại là suy luận hậu nghiệm**, và tệ hơn: trên ba dataset này, **số lớp và mức huấn luyện bị trộn lẫn** (Pets vừa ít lớp vừa ít cần học). Không được dừng ở đây.

## 8. Thí nghiệm phân định (ghi trước khi chạy)

Cần hai dataset phá được sự trộn lẫn đó:

| Dataset | Số lớp | Mức huấn luyện hơn zero-shot | Góc nào |
|---|---|---|---|
| **EuroSAT** | **10** | lớn (zero-shot RN50 rất thấp) | ít lớp, cần học nhiều |
| **Food101** | **101** | nhỏ (zero-shot đã mạnh) | nhiều lớp, cần học ít |

Hai giả thuyết cho **dự đoán ngược nhau**, nên một lượt chạy là đủ phân định:

| | EuroSAT | Food101 |
|---|---|---|
| Nếu **số lớp** chi phối | `s_conc` thấp, ≤ 0,65 | `s_conc` cao, ≥ 0,85 |
| Nếu **mức huấn luyện** chi phối | `s_conc` cao, ≥ 0,75 | `s_conc` thấp, ≤ 0,65 |

Notebook đã đặt `MODE = "gate_c_confound"`, `DATASETS = ["eurosat", "food101"]`, 2 job mỗi dataset, 5 seed, khoảng **4,8 giờ**, và tự in ra giả thuyết nào được ủng hộ.

Nếu cả hai đều bị mâu thuẫn thì bỏ cả hai cách giải thích, và báo cáo đơn giản rằng khả năng tách phụ thuộc dataset theo cách chưa giải thích được.

## 9. Phán quyết Gate C sau khi có Caltech101

Tiêu chí ghi trước là "AUC ≥ 0,80 **trên ít nhất một dataset**". Với ba dataset trong tay:

| Tiêu chí | Kết quả | Trên dataset nào |
|---|---|---|
| C1 `s_sem` ≥ 0,80 | **đạt** | Caltech101 (0,938), OxfordPets (0,954) |
| C2 `s_conc` ≥ 0,80 | **đạt** | Caltech101 (0,987) |
| C3 hơn `s_upd` ≥ 0,10 | đạt trên DTD (+0,253); trượt trên hai dataset kia | |

**Phải nói thẳng hai điều khi viết luận văn:**

1. Caltech101 được chạy cho **mục đích khác** (kiểm giả thuyết chế độ), rồi mới dùng để xét lại Gate C. Tiêu chí "ít nhất một dataset" càng dễ đạt khi càng thêm dataset. Vì vậy phát biểu trung thực không phải "Gate C đạt", mà là: **tín hiệu hoạt động trên một số dataset và không hoạt động trên số khác, và biến chi phối thì chưa biết chắc.**
2. Trên dataset mà `s_conc` xuất sắc nhất (Caltech, 0,987), tín hiệu độ lệch kiểu Krum **cũng gần như xuất sắc** (0,933). Chỗ duy nhất tín hiệu ngữ nghĩa hơn hẳn độ lệch là DTD (+0,253), mà ở đó cả hai đều chưa đạt 0,80. Nói gọn: **tín hiệu của ta hơn baseline đúng ở chỗ cả hai đều yếu, và không hơn ở chỗ cả hai đều mạnh.**

Điểm 2 là giới hạn thật, và nó củng cố đúng lý do đã ghi trước cho nhánh C2: cần một tín hiệu **không dựa vào cấu trúc nhãn**, tức tín hiệu phản ứng khi được yêu cầu sửa nhãn.


## 10. Hai biến thể không phụ thuộc số lớp (thêm 2026-09-20, trước lượt phân định)

Nghi vấn ở mục 7 là `s_conc` có sàn 1/C nên không so được giữa các dataset khác số lớp. Nếu đúng thì đó là **lỗi định nghĩa, sửa được**, chứ không phải giới hạn của ý tưởng. Đã thêm hai biến thể bỏ sàn đó, tính từ đúng vector khối lượng cột đang có:

| Tín hiệu | Định nghĩa | Ý nghĩa |
|---|---|---|
| `s_conc_n` | khối lượng cột lớn nhất **nhân số lớp** | 1,0 là mức đều; giá trị 3,0 nghĩa là lớp đó hút gấp ba mức đều, bất kể dataset có bao nhiêu lớp |
| `s_conc_kl` | khoảng cách KL từ phân phối khối lượng cột tới phân phối đều | nhạy cả khi tấn công dồn về **vài** lớp chứ không chỉ một |

Cả hai đều trừ đi giá trị của model toàn cục như `s_conc`, và được ghi cùng chỗ. Ô phân tích báo AUC của cả ba, nên lượt phân định trả lời **hai câu một lúc**:

1. Biến nào chi phối `s_conc` — số lớp hay mức huấn luyện (mục 8);
2. Chuẩn hoá theo số lớp có **sửa được** vấn đề không.

Nếu `s_conc_n` hoặc `s_conc_kl` cho AUC ổn định trên cả EuroSAT (10 lớp) lẫn Food101 (101 lớp), thì hạn chế ở mục 9 biến mất và tín hiệu dùng được không phụ thuộc dataset. Nếu vẫn dao động như `s_conc` thì vấn đề nằm ở bản chất tín hiệu, không phải ở thang đo.

`s_conc_kl` còn có ích riêng: nó là tín hiệu duy nhất bắt được kẻ tấn công **rải mục tiêu ra vài lớp** — đúng kịch bản kẻ tấn công thích nghi đã ghi trước ở `docs/phase4_plan.md` mục 4.


## 11. Lượt phân định lần 1 hỏng vì nguồn dữ liệu, không phải vì khoa học (2026-09-20)

Lượt EuroSAT + Food101 chết ở ô chuẩn bị dữ liệu:

```
wget -q -O /tmp/eurosat.zip http://madm.dfki.de/files/sentinel/EuroSAT.zip
CalledProcessError: ... returned non-zero exit status 4
```

Ba vấn đề, đã sửa cả ba:

| Vấn đề | Sửa |
|---|---|
| Host `madm.dfki.de` mà `docs/DATASETS.md` của FLIP trỏ tới đã **chết** | Chuyển sang Zenodo 7711810, kho lưu trữ của chính nhóm tác giả EuroSAT. Tên file là **`EuroSAT_RGB.zip`** (94,7 MB) chứ không phải `EuroSAT.zip`. Đã tải về kiểm: đúng 10 thư mục lớp, bố cục `EuroSAT_RGB/<lớp>/`, nên phải đổi tên thành `2750/` cho khớp FLIP |
| `wget` treo **47 phút** rồi mới báo lỗi, đốt sạch nửa giờ GPU | Thêm hàm `fetch()` với `--timeout=30 --tries=2` và **danh sách mirror**: chết host nào thì bỏ qua trong vài giây |
| Một dataset hỏng làm **chết cả phiên** | Vòng chuẩn bị dữ liệu giờ bắt lỗi từng dataset: cái nào hỏng thì in `SKIPPED` rồi chạy tiếp với phần còn lại |

Và một phát hiện nhờ đi kiểm chủ động: **đường dẫn Food101 trong `docs/DATASETS.md` của FLIP cũng 404**. Lượt chạy đó chắc chắn sẽ chết tiếp ở bước sau dù EuroSAT có tải được. Đã thay bằng hai mirror còn sống (ETH Zürich đường dẫn mới, và bản mirror của fast.ai trên S3).

Ghi lại vì đây là điểm đáng nói trong luận văn: **tài liệu dữ liệu của một benchmark NeurIPS 2025 đã có hai liên kết hỏng chỉ sau mười tháng.** Cùng loại vấn đề với việc code public của họ không chuẩn hoá ảnh lúc train — bản công bố không phải bản chạy được.

## 12. Lượt phân định lần 2: EuroSAT xong, Food101 thiếu đúng ô quyết định (2026-09-21)

Dữ liệu: `results/Phase4/food101-eurosat/`. Ba job chạy xong `rc=0`, tổng **7,52 giờ**.

| Job | Thời gian | `last10` |
|---|---|---|
| `eurosat_N_control` | 22,0 phút | 58,48 ± 2,26 |
| `eurosat_P0_disguise` | 22,9 phút | 52,63 ± 4,55 |
| `food101_N_control` | **406,2 phút** | 74,93 ± 0,61 |
| `food101_P0_disguise` | **không chạy** | – |

**Job quan trọng nhất của cả thí nghiệm đã không chạy.** Bảng ước lượng thời gian đặt Food101 ở 32,0 giây/round; thực tế là **95,6 giây/round**, gấp ba. Một mình `food101_N_control` ăn 6,77 giờ trên ngân sách 6,0 giờ, nên bộ canh ngân sách bỏ qua job còn lại — nó làm đúng việc của nó, chỉ là ước lượng sai. Đã sửa bảng theo số đo thật (EuroSAT 5,2; Food101 96,0) để lỗi này không lặp lại.

### 12.1. Phán quyết theo đúng quy tắc ghi trước, cho nhánh EuroSAT

`s_conc` tách độc hại khỏi nhiễu trên `eurosat_P0_disguise` = **0,593**.

| Giả thuyết | Dự đoán cho EuroSAT | Kết quả |
|---|---|---|
| **Số lớp** chi phối | ≤ 0,65 | **được ủng hộ** |
| **Mức huấn luyện** chi phối | ≥ 0,75 | **bị mâu thuẫn** |

Nhưng **không được đọc con số này là một chiến thắng**, vì ba lý do phải nói rõ:

**1. Nhánh EuroSAT không cung cấp thông tin.** Lượt đối chứng `eurosat_N_control` cho thấy trên EuroSAT **không tín hiệu nào tách được gì**, kể cả baseline:

| Tín hiệu | nhiễu so với thật thà (đối chứng) |
|---|---|
| `s_conc` | 0,440 |
| `s_conc_kl` | 0,445 |
| `s_sem` | 0,467 |
| `s_upd` (baseline Krum) | 0,400 |

Tất cả đều ở hoặc **dưới** mức ngẫu nhiên. Một giả thuyết mà dự đoán của nó là "tín hiệu sẽ yếu" thì không thể được xác nhận bởi một dataset nơi **mọi thứ** đều yếu. Kết quả 0,593 tương thích với giả thuyết số lớp, nhưng cũng tương thích hoàn toàn với "EuroSAT không phát hiện được gì bất kể cơ chế nào".

**2. Trật tự theo số lớp đã bị phá.** Mục 7 nhận xét thứ tự `s_conc` khớp chính xác thứ tự số lớp. Thêm điểm thứ tư thì không còn khớp:

| Dataset | Số lớp | `s_conc` (P0_disguise) |
|---|---|---|
| Caltech101 | 102 | 0,987 |
| DTD | 47 | 0,780 |
| OxfordPets | 37 | 0,487 |
| **EuroSAT** | **10** | **0,593** |

EuroSAT có **ít lớp nhất** nhưng lại cao hơn OxfordPets. Cơ chế "sàn 1/C" dự đoán EuroSAT phải thấp nhất, và nó không thấp nhất. Vậy ngưỡng ghi trước thì đạt, còn **lập luận cơ chế sinh ra ngưỡng đó thì không**.

**3. Ô phân định thật sự vẫn trống.** Food101 là ô duy nhất mà hai giả thuyết dự đoán ngược nhau ở **hai phía khác nhau của thang đo** (≥ 0,85 so với ≤ 0,65). EuroSAT chỉ phân biệt được "thấp" với "cao", mà "thấp" là kết quả mặc định khi dataset không cho tín hiệu nào.

**Kết luận trung thực tại thời điểm này: chưa phân định được.** Không sửa dự đoán, không tuyên bố giả thuyết số lớp thắng.

### 12.2. Hai biến thể không phụ thuộc số lớp: một cái sai về toán, một cái không đủ

| Tín hiệu | EuroSAT `N_control` | EuroSAT `P0_disguise` |
|---|---|---|
| `s_conc` | 0,440 | 0,593 |
| `s_conc_n` (× số lớp) | 0,440 | 0,593 |
| `s_conc_kl` (KL tới phân phối đều) | 0,487 | 0,667 |

**`s_conc_n` không bao giờ có thể khác `s_conc`, và đó là lỗi thiết kế của tôi.** Nhân mọi client trong cùng một dataset với cùng hằng số `C` là một phép biến đổi đơn điệu, mà AUC chỉ phụ thuộc thứ hạng. Hai cột đầu **bắt buộc** bằng nhau về mặt toán học. Mục 10 đề ra `s_conc_n` để sửa vấn đề so sánh **giữa các dataset**, nhưng mọi AUC trong đồ án đều tính **trong một dataset**, nên chuẩn hoá đó không bao giờ xuất hiện trong con số. Nó chỉ có ích nếu server dùng một ngưỡng tuyệt đối dùng chung cho nhiều dataset — điều chưa bao giờ nằm trong thiết kế. Ghi lại để không ai (kể cả tôi) đọc hai cột giống nhau như một sự trùng hợp.

`s_conc_kl` **là** một thống kê khác thật, không phải biến đổi đơn điệu, và nó có nhích: +0,074 trên lượt tấn công, +0,047 trên đối chứng. Đúng chiều nhưng quá nhỏ, và 0,667 vẫn xa ngưỡng 0,80.

Một lỗi phần mềm liên quan: ô phân tích trong notebook chỉ nạp ba khoá `s_sem`, `s_conc`, `s_upd`, nên AUC của hai biến thể in ra `NaN` trong `phase4_gate_c.json`. Dữ liệu thô vẫn đủ trong `noise_seed_*.json`, nên các số ở trên được tính lại tại máy, **không tốn thêm giờ GPU**. Ô phân tích đã được sửa để nạp cả năm khoá.

### 12.3. Phát hiện ngoài dự kiến: Food101 là chế độ ngược hẳn EuroSAT

Lượt đối chứng Food101 không trả lời câu hỏi phân định, nhưng nó nói một điều mạnh:

| Tín hiệu | nhiễu so với thật thà, Food101 `N_control` |
|---|---|
| `s_upd` (baseline Krum) | **1,000** |
| `s_sem` | 0,955 |
| `s_conc_kl` | 0,923 |
| `s_conc` | 0,888 |

Trên Food101, client nhiễu tách khỏi client thật thà **hoàn hảo** — và tách hoàn hảo bằng **baseline độ lệch**, chứ không cần tín hiệu nào của ta. Đây đúng là điều mục 9 đã nói: *tín hiệu của ta chỉ hơn baseline ở chỗ cả hai đều yếu*. Food101 là ví dụ cực đoan nhất: baseline đạt 1,000, nên **không còn chỗ nào để hơn**.

Đặt cạnh EuroSAT thì thành một cặp đối xứng, và cặp này là kết quả đáng viết:

| | EuroSAT | Food101 |
|---|---|---|
| Phát hiện client nhiễu (đối chứng) | 0,40 – 0,47, **dưới ngẫu nhiên** | 0,89 – 1,00, **gần hoàn hảo** |
| Thiệt hại do tấn công giả nhiễu | **+5,85 ± 5,75 điểm** (t = 2,28, dz = 1,02, n = 5) | chưa đo |
| Chỗ cho một tín hiệu mới | không có, vì không gì phát hiện được | không có, vì baseline đã 1,000 |

**Thiệt hại 5,85 điểm trên EuroSAT là lớn nhất trong bốn dataset** (DTD +4,13, OxfordPets +3,58 ở Gate B) — và nó rơi đúng vào dataset **khó phát hiện nhất**. Độ nguy hiểm và độ dễ phát hiện đi ngược chiều nhau. Với n = 5 thì t = 2,28 chưa qua ngưỡng p < 0,05, nên đây là quan sát cần thêm seed chứ chưa phải kết luận.

### 12.4. Việc tiếp theo

1. **Chạy lại đúng một job**: `food101_P0_disguise`, 5 seed, khoảng **6,8 giờ**. Notebook đã đặt `MODE = "gate_c_confound_food"`, `BUDGET_HOURS = 8.5`, và bộ lọc `ONLY` để chỉ chạy job đó. Dự đoán **giữ nguyên như mục 8**, không sửa: số lớp chi phối thì `s_conc` ≥ 0,85; mức huấn luyện chi phối thì ≤ 0,65.
2. Lượt đó chạy kèm **ZS-CLIP cho EuroSAT và Food101** (vài phút mỗi cái). Trục "mức huấn luyện" của giả thuyết chưa bao giờ được đo trên hai dataset này — vẫn đang dựa vào mô tả thiết kế chứ không phải số đo của chính mình. Không thể kiểm một giả thuyết bằng một trục chưa đo.
3. Nếu Food101 ra ≥ 0,85: giả thuyết số lớp thắng ở mức ngưỡng, nhưng phải báo cáo kèm việc trật tự bốn dataset không đơn điệu (mục 12.1, điểm 2).
4. Nếu Food101 ra ≤ 0,65: cả hai giả thuyết đều bị mâu thuẫn ở ít nhất một nhánh, và theo đúng quy tắc ghi trước ở mục 8, **bỏ cả hai cách giải thích** và báo cáo rằng khả năng tách phụ thuộc dataset theo cách chưa giải thích được.
5. Dù kết quả nào, phần này vào luận văn với tư cách **kết quả âm có cơ chế**, là bước 4 trong mạch lập luận của `docs/phase6_plan.md` mục 4, chứ không phải một thất bại cần giấu.

## 13. Ô phân định đã chạy: giả thuyết số lớp thắng (2026-09-21, 6,73 giờ)

Dữ liệu: `results/Phase4/food101-eurosat/food_run/`. Ba job `rc=0`: `food101_P0_disguise` (401,0 phút, 5 seed) cùng ZS-CLIP cho cả hai dataset.

### 13.1. Phán quyết

`s_conc` tách độc hại khỏi nhiễu trên Food101 = **0,933**.

| Giả thuyết | Dự đoán ghi trước cho Food101 | Kết quả |
|---|---|---|
| **Số lớp** chi phối | ≥ 0,85 | **được ủng hộ** |
| **Mức huấn luyện** chi phối | ≤ 0,65 | **bị mâu thuẫn** |

Cộng với nhánh EuroSAT ở mục 12 (0,593 ≤ 0,65, cũng ủng hộ số lớp), **cả hai nhánh của thí nghiệm phân định đều chỉ về cùng một phía**. Đây là kết luận theo đúng quy tắc ghi trước, không sửa ngưỡng sau khi nhìn số.

### 13.2. Trục "mức huấn luyện" giờ đã được đo, không còn phải đoán

ZS-CLIP RN50 chạy tại chỗ: **EuroSAT 26,11%**, **Food101 78,05%**. Đặt cạnh `last10` của lượt `N_control` (có nhiễu):

| Dataset | Số lớp | ZS-CLIP | `last10` có nhiễu | Chênh | `s_conc` độc hại/nhiễu | `s_upd` cùng việc |
|---|---|---|---|---|---|---|
| Caltech101 | 102 | 85,76 | – | +4,52 (sạch, GĐ1) | **0,987** | 0,933 |
| **Food101** | **101** | **78,05** | 74,93 | **−3,12** | **0,933** | **0,947** |
| DTD | 47 | 41,78 | – | +13,83 (sạch, GĐ1) | 0,780 | 0,527 |
| OxfordPets | 37 | 85,69 | – | +2,40 (sạch, GĐ1) | 0,487 | 0,400 |
| EuroSAT | 10 | **26,11** | 58,48 | **+32,37** | 0,593 | 0,407 |

Hai trục, năm điểm, hạng Spearman:

| Trục | ρ với `s_conc` |
|---|---|
| **Số lớp** | **+0,90** |
| Mức huấn luyện | **−0,20** |

Food101 là điểm đắt giá nhất: nó có **101 lớp nhưng huấn luyện dưới nhiễu còn tệ hơn zero-shot 3,12 điểm** — mức huấn luyện thấp nhất trong năm dataset. Giả thuyết mức huấn luyện dự đoán nó phải thấp nhất; nó ra 0,933, gần cao nhất. Trục đó hỏng dứt khoát.

Trật tự theo số lớp gần đơn điệu, chỉ sai một chỗ: EuroSAT (10 lớp, 0,593) vẫn cao hơn OxfordPets (37 lớp, 0,487). Như mục 12.1 đã ghi, EuroSAT là dataset không tín hiệu nào tách được gì, nên điểm đó có sai số lớn. Không được lấp liếm chỗ này: **quy luật là "gần đơn điệu theo số lớp", không phải "đơn điệu".**

### 13.3. Và Food101 xác nhận lại đúng giới hạn đã biết

`s_upd`, baseline độ lệch kiểu Krum, đạt **0,947** trên cùng việc — **cao hơn** `s_conc` 0,933. Chênh lệch so với baseline trên cả năm dataset:

| Dataset | `s_conc` | `s_upd` | Chênh |
|---|---|---|---|
| Food101 | 0,933 | 0,947 | **−0,014** |
| Caltech101 | 0,987 | 0,933 | +0,053 |
| OxfordPets | 0,487 | 0,400 | +0,087 |
| EuroSAT | 0,593 | 0,407 | +0,186 |
| DTD | 0,780 | 0,527 | **+0,253** |

Hai chỗ chênh lớn nhất (DTD +0,253, EuroSAT +0,186) là hai chỗ `s_conc` **dưới 0,80**, tức tín hiệu không dùng được dù có hơn baseline. Hai chỗ `s_conc` mạnh nhất (Caltech 0,987, Food101 0,933) là hai chỗ baseline **cũng mạnh** và Food101 thì baseline còn mạnh hơn. Phát biểu ở mục 9 giờ có năm dataset chống lưng, không còn là nhận xét từ ba điểm:

> **Tín hiệu hình học prompt hơn baseline đúng ở chỗ cả hai đều yếu, và không hơn ở chỗ cả hai đều mạnh.**

### 13.4. Gate C: chốt

| Tiêu chí | Kết quả |
|---|---|
| C1 `s_sem` ≥ 0,80 | đạt trên Caltech101 (0,938), OxfordPets (0,954) |
| C2 `s_conc` ≥ 0,80 | đạt trên Caltech101 (0,987), Food101 (0,933) |
| C3 hơn `s_upd` ≥ 0,10 | đạt trên DTD (+0,253), EuroSAT (+0,186) — **không chỗ nào trùng với C2** |

C1 và C2 đạt trên một số dataset, C3 đạt trên các dataset khác, và **không dataset nào đạt cả ba**. Biến chi phối đã tìm ra (số lớp), nên đây là **kết quả âm có cơ chế** chứ không phải kết quả âm mù mờ:

> Độ tập trung đo bằng khối lượng cột lớn nhất có sàn 1/C. Nhiều lớp thì lớp bị dồn nổi bật; ít lớp thì nhiễu ngẫu nhiên cũng tạo được mức tập trung tương đương. Nhưng đúng những dataset nhiều lớp đó cũng là nơi cập nhật của kẻ tấn công lệch xa nhất về hình học, nên baseline Krum bắt được không kém. Tín hiệu ngữ nghĩa **không thêm thông tin** so với thứ đã đo được bằng khoảng cách thuần tuý.

Đây là bước 4 trong mạch lập luận `docs/phase6_plan.md` mục 4, và giờ nó có đủ 5 dataset cùng một lời giải thích kiểm được. Không cần chạy thêm gì cho Gate C.
