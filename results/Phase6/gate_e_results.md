# Kết quả Gate E (chạy 2026-09-21, T4, 10,88 giờ)

Dữ liệu: `results/Phase6/extracted/`. **10/10 job `rc=0`**, 5 cấu hình × 2 dataset (DTD, OxfordPets) × 5 seed.
Cấu hình: 3 client nhiễu (`sym` 40%), 2 độc hại (`noise_disguise` 40%), 5 thật thà; `--correction_every 5`, `--probe_audit_prob 1.0`, tức **10 trong 50 round** bị kiểm toán.

## 1. Phán quyết theo tiêu chí ghi trước

| # | Tiêu chí | Ngưỡng | Kết quả | |
|---|---|---|---|---|
| **E1** | Kẻ tấn công **tuân thủ** mất ≥ một nửa thiệt hại so với khi **từ chối** | ≥ 50% trên ≥ 2/3 dataset | DTD giữ **57%**, Pets giữ **62%** | **TRƯỢT** |
| **E2** | Từ chối phát hiện được, AUC(−`r_align`) | ≥ 0,90 | DTD **0,993**, Pets **0,965** | **ĐẠT** |
| **E3** | Giao thức đầy đủ hơn luật gộp cố định tốt nhất | ≥ 2,0 điểm | DTD +0,81, Pets **−2,90** | **TRƯỢT** |

Không sửa ngưỡng, không đổi cách tính sau khi nhìn số.

## 2. Bảng accuracy đầy đủ

| Dataset | Cấu hình | `last10` | Thiệt hại so với `N_control` | t (n=5) | p |
|---|---|---|---|---|---|
| DTD | `N_control` | 52,06 ± 0,74 | – | | |
| DTD | `N_audit` (sạch + kiểm toán) | **52,92 ± 1,05** | **−0,86** (kiểm toán *giúp*) | −2,36 | 0,078 |
| DTD | `A0_refuse` | 47,56 ± 2,91 | +4,50 ± 2,47 | 4,08 | **0,015** |
| DTD | `A1_refuse_audit` | 48,93 ± 3,11 | +3,13 ± 2,54 | 2,76 | 0,051 |
| DTD | `A2_comply_audit` | 49,48 ± 2,61 | +2,58 ± 2,27 | 2,54 | 0,064 |
| OxfordPets | `N_control` | 81,23 ± 1,21 | – | | |
| OxfordPets | `N_audit` | **82,24 ± 1,23** | **−1,01** (kiểm toán *giúp*) | −4,87 | **0,008** |
| OxfordPets | `A0_refuse` | 75,88 ± 2,74 | +5,35 ± 2,56 | 4,67 | **0,010** |
| OxfordPets | `A1_refuse_audit` | 76,89 ± 3,53 | +4,34 ± 3,31 | 2,94 | **0,043** |
| OxfordPets | `A2_comply_audit` | 77,91 ± 3,09 | +3,32 ± 2,28 | 3,26 | **0,031** |

## 3. E1 trượt, và trượt tệ hơn con số 57%/62% trông có vẻ

Tương phản E1 ghi trước là `A2_comply_audit` so với `A0_refuse`. **Tương phản đó đổi hai thứ cùng lúc**: kiểm toán bật/tắt, *và* tuân thủ/từ chối. Nó không đo riêng được thế lưỡng nan. Tách ra:

| Tương phản | Đo cái gì | DTD | OxfordPets |
|---|---|---|---|
| `A1` − `A0` | **kiểm toán một mình**, kẻ tấn công vẫn từ chối | +1,37 ± 1,71 (t = 1,80) | +1,01 ± 0,85 (t = 2,66) |
| `A2` − `A1` | **tuân thủ một mình**, kiểm toán giữ nguyên | +0,55 ± 1,47 (t = 0,84) | +1,02 ± 1,81 (t = 1,26) |
| `A2` − `A0` | cả hai (tiêu chí E1 ghi trước) | +1,93 ± 2,19 (t = 1,97) | +2,03 ± 1,59 (t = 2,84) |

Tương phản sạch cho câu hỏi "tuân thủ tốn gì" là `A2` − `A1`. Ở đó thiệt hại còn giữ lại **82% (DTD)** và **77% (Pets)**, tức tuân thủ chỉ xoá được **18–23%** cuộc tấn công, chứ không phải 43%/38% như tương phản ghi trước gợi ý. Cả hai đều **không có ý nghĩa thống kê** ở n = 5.

**Đây là lỗi thiết kế trong phần ghi trước của tôi**, không phải phát hiện hậu nghiệm để gỡ gạc: tiêu chí E1 chọn sai nhóm đối chứng.

Tiêu chí E1 còn bỏ sót một thứ nữa: **cơ chế chỉ xoá tấn công ở những round bị kiểm toán**, mà cấu hình ghi trước chỉ kiểm toán **10 trong 50 round**. Xoá 18–23% thiệt hại bằng 20% số round là **xấp xỉ đúng tỉ lệ** — cơ chế chạy đúng như thiết kế, chỉ là liều quá thấp. Tiêu chí ghi trước đã trộn *cơ chế* với *liều lượng*, và không đăng ký liều lượng như một biến. Đó là lý do chính đáng để chạy một lượt đo liều — **không phải** lý do để tuyên bố E1 đạt.

## 4. E2 đạt, và đạt ở đúng phép so sánh khó nhất

AUC(−`r_align`), gộp 5 seed, mỗi client lấy trung bình qua mọi round probe:

| Lượt | Kẻ tấn công làm gì | AUC so với **mọi client khác** | so với riêng **client nhiễu** |
|---|---|---|---|
| `dtd_A0_refuse` | từ chối | **0,993** | **0,987** |
| `dtd_A1_refuse_audit` | từ chối | **1,000** | – |
| `dtd_A2_comply_audit` | tuân thủ | 0,487 | 0,507 |
| `dtd_N_control` | không có tấn công | 0,487 | – |
| `dtd_N_audit` | không có tấn công | 0,497 | – |
| `oxford_pets_A0_refuse` | từ chối | **0,965** | **0,907** |
| `oxford_pets_A1_refuse_audit` | từ chối | **0,930** | – |
| `oxford_pets_A2_comply_audit` | tuân thủ | 0,695 | 0,227 |
| `oxford_pets_N_control` | không có tấn công | 0,385 | – |
| `oxford_pets_N_audit` | không có tấn công | 0,345 | – |

Đây là một **bảng chân trị sạch**: tín hiệu kêu khi và chỉ khi có client từ chối. Không ai tấn công thì nó nằm ở mức ngẫu nhiên hoặc dưới (0,345–0,497). Đối chứng Gate D trước đây bị lỗi đúng ở chỗ này, và bản sửa được xác nhận tại đây.

**Cột cuối là cột quan trọng nhất của cả đồ án.** Tách độc hại khỏi **client nhiễu** đạt 0,987 và 0,907 — việc mà Gate C (hình học prompt) và Gate D (phản ứng sửa nhãn) đều không làm được — và làm được trên **cả hai dataset**, không phụ thuộc chế độ dataset như `s_conc`. Lý do gọn trong một câu:

> Ý đồ không quan sát được, nhưng **sự tuân thủ với một yêu cầu do server ra thì quan sát được**. Client nhiễu không có lý do từ chối; kẻ tấn công thì có.

Một hệ quả cũng phải nói: kẻ tấn công **tuân thủ** thì *không* tách được khỏi client nhiễu (0,507 và 0,227, tức ở mức ngẫu nhiên hoặc đảo chiều). Điều đó **không phải lỗ hổng** — đó chính là nội dung của thế lưỡng nan: muốn ẩn thì phải tuân thủ, mà tuân thủ thì mất tấn công.

## 5. Phát hiện ngoài dự kiến: kiểm toán là **lãi**, không phải phí

Cấu hình `N_audit` được thêm để đo **cái giá** của cơ chế khi không có ai tấn công. Nó ra dấu ngược:

| Dataset | `N_control` | `N_audit` | Chênh | t | p |
|---|---|---|---|---|---|
| DTD | 52,06 | **52,92** | **+0,86** | 2,36 | 0,078 |
| OxfordPets | 81,23 | **82,24** | **+1,01** | 4,87 | **0,008** |

Kiểm toán thay đóng góp của client bằng prompt mà chính client huấn luyện lại **dưới nhãn do model toàn cục gán**. Trong một federation có nhiễu nhãn, nhãn của model toàn cục **sạch hơn** nhãn của client nhiễu, nên phép thay thế đó là một bước **khử nhiễu**. Nói cách khác cơ chế này không chỉ là phòng thủ, nó là một **luật gộp có sửa nhãn**, và nó có lãi ngay cả khi không có kẻ địch nào.

## 6. E3 trượt rõ: luật gộp cố định tốt nhất vẫn hơn

So với Gate B mục 8 (cùng cấu hình vai trò và nhiễu, `last10` dưới `P0_disguise`):

| Dataset | `median` (Gate B) | `A1_refuse_audit` | `A2_comply_audit` | Chênh tốt nhất |
|---|---|---|---|---|
| DTD | 48,67 | 48,93 | 49,48 | **+0,81** |
| OxfordPets | **80,81** | 76,89 | 77,91 | **−2,90** |

Trên Pets, trung vị theo toạ độ hơn giao thức kiểm toán **2,90 điểm**. Ngưỡng E3 là +2,0. Trượt dứt khoát.

Nhưng hai thứ này **không loại trừ nhau**: kiểm toán quyết định *đóng góp nào được gộp*, trung vị quyết định *gộp thế nào*. Chưa lượt nào chạy cả hai cùng lúc. Đó là một job, không phải một hướng mới.

## 7. Cái chưa bao giờ được chạy: dùng nhãn "từ chối" để **làm gì đó**

Gate E đo được một bộ phát hiện ở AUC 0,91–0,99 rồi **không làm gì với nó**. Cả 5 cấu hình đều gộp mọi client, kể cả client bị bắt quả tang từ chối. Cái "giao thức đầy đủ" mà E3 so sánh **chưa từng tồn tại trong code**.

Đó là lý do thật sự khiến E1 và E3 trượt, và nó sửa được:

| Kẻ tấn công chọn | Hậu quả ở Gate E | Hậu quả khi có loại trừ |
|---|---|---|
| Từ chối | bị phát hiện, **vẫn được gộp** | bị phát hiện rồi **bị loại** — mất **toàn bộ** cuộc tấn công |
| Tuân thủ | mất 18–23% cuộc tấn công | như cũ, và tăng theo tần suất kiểm toán |

Đã hiện thực hoá phần còn thiếu: `--refusal_rule`, `--refusal_k`, `--refusal_floor`, `--refusal_patience` trong `flip/flcore/servers/server_base.py` và `flip/main.py`. Luật chạy hoàn toàn trực tuyến, chỉ dùng `r_align` mà server đã có sẵn: không vai trò, không số kẻ địch giả định, không dữ liệu held-out.

## 8. Hiệu chỉnh luật loại trừ, **không tốn giờ GPU nào**

Bản ghi probe của Gate E chứa đủ `r_align` từng client từng round, nên luật loại trừ được mô phỏng lại ngoại tuyến trước khi chạy bất cứ thứ gì trên GPU. Ba phiên bản đầu đều hỏng, và hỏng theo cách đáng ghi:

| Phiên bản | Kết quả mô phỏng |
|---|---|
| Ngưỡng trên `r_align` **từng round**, `median − 2·MAD` | Pets `N_control` (không ai tấn công): **12/40 client vô tội bị cấm** |
| Tỉ lệ so với median từng round (`r_align < 0,75·median`) | còn tệ hơn: Pets `N_control` 19/40 |
| Trung bình luỹ kế + MAD, sàn tuyệt đối `1e−3` | Pets `N_audit`: **13/40** — federation mà ai cũng tuân thủ có MAD gần 0, nên luật luôn tìm ra ai đó ở đáy một cụm rất chặt |

Bản dùng được cần cả ba thứ cùng lúc: **trung bình luỹ kế** của `r_align` (không phải giá trị từng round), ngưỡng `median − k·spread`, và `spread` có **sàn tương đối** bằng `refusal_floor · |median|`. Với `k = 2,0`, `refusal_floor = 0,12`, `refusal_patience = 3`:

| Lượt | Thật thà bị cấm | Nhiễu bị cấm | Độc hại bị cấm |
|---|---|---|---|
| `dtd_A0_refuse` | **0/25** | **0/15** | **9/10** |
| `dtd_A1_refuse_audit` | **0/25** | **0/15** | **7/10** |
| `dtd_A2_comply_audit` | 0/25 | 1/15 | **0/10** |
| `dtd_N_control` | 2/25 | 0/15 | 0/10 |
| `dtd_N_audit` | **0/25** | **0/15** | 0/10 |
| `oxford_pets_A0_refuse` | **0/25** | **0/15** | 4/10 |
| `oxford_pets_A1_refuse_audit` | 0/25 | 1/15 | 4/10 |
| `oxford_pets_A2_comply_audit` | 0/25 | 1/15 | 1/10 |
| `oxford_pets_N_control` | 2/25 | 3/15 | 0/10 |
| `oxford_pets_N_audit` | **0/25** | 8/15 | 0/10 |

Ba điều đọc được, hai tốt một xấu:

1. **Client thật thà gần như không bao giờ bị cấm**: 0/25 ở 8 trong 10 lượt, 2/25 ở hai lượt còn lại. Đây đúng là chỗ `multikrum` thất bại ở Gate B, nơi nó loại client nhiễu nhiều gấp 17,7 lần client thật thà.
2. **Kẻ tấn công tuân thủ không bị cấm** (0/10 và 1/10) — đúng lời hứa của thế lưỡng nan: tuân thủ thì được ở lại, nhưng phải trả giá bằng cuộc tấn công.
3. **Recall phụ thuộc dataset**: DTD bắt 9/10 và 7/10, Pets chỉ 4/10. Và trên `oxford_pets_N_audit`, **8/15 client nhiễu bị cấm oan**, vì trên Pets client nhiễu cũng có `r_align` thấp (AUC nhiễu so với thật thà = 0,963). Đây chính là chế độ hỏng mà đồ án đã phê phán ở `multikrum`, nên phải báo cáo chứ không giấu.

Luật được **chốt trước khi chạy**: `mad`, `k = 2,0`, `floor = 0,12`, `patience = 3`.

Thêm một chặn an toàn không liên quan tới ngưỡng: **không bao giờ cấm quá một nửa số client**, dù luật nói gì. Với cấu hình Gate F (10 client, nhiều nhất 2 kẻ tấn công) chặn này không bao giờ chạm tới, nên nó không ảnh hưởng con số mô phỏng ở trên; nó chỉ để một luật hỏng không làm rỗng federation.

Kiểm trên CPU: chạy sạch `rc = 0`, bản ghi `refusal` được lưu vào `noise_seed_*.json`, và một phép thử dương tính ép `bottom_k` cấm client đã xác nhận bước gộp vẫn chạy đúng sau khi 2 trong 4 client bị loại.

## 9. Tiêu chí Gate F (ghi trước, 2026-09-21, trước khi chạy)

Dùng lại `N_control` và `A0_refuse` của Gate E làm đối chứng (chúng không có kiểm toán nên không phụ thuộc tần suất probe).

| # | Điều kiện | Ngưỡng | Nếu trượt |
|---|---|---|---|
| **F1** | **Loại trừ xoá được cuộc tấn công.** `A3_refuse_audit_exclude` so với `A0_refuse` | thiệt hại còn lại ≤ **25%** trên ≥ 2/3 dataset | Bộ phát hiện đúng nhưng vô dụng; quay về phương án lui `docs/phase6_plan.md` mục 5 |
| **F2** | **Liều lượng là biến, không phải hằng số.** Với `--correction_every 2` (25/50 round bị kiểm toán), đo lại tương phản sạch `A2` − `A1` | thiệt hại còn lại ≤ **60%** (so với 77–82% ở liều 10/50) | Cơ chế không phụ thuộc liều; thế lưỡng nan chỉ có một vế dùng được |
| **F3** | **Ghép với luật gộp bền vững.** `median` + kiểm toán + loại trừ, so với `median` một mình | ≥ **+2,0 điểm** trên ≥ 2/3 dataset | Hai cơ chế không cộng hưởng; báo cáo giao thức như một lựa chọn song song với `median`, không phải thứ thay thế nó |

Không sửa ba ngưỡng này sau khi nhìn kết quả.

**Phát biểu trung thực của đồ án ngay lúc này, trước Gate F:**

> Suy đoán ý đồ từ vật phẩm client gửi lên **không hoạt động**, và lý do đã tìm ra trên 5 dataset (Gate C). Kiểm chứng **sự tuân thủ** thì hoạt động, ổn định qua dataset, và tách được độc hại khỏi nhiễu ở AUC 0,91–0,99 (Gate E, E2). Cơ chế kiểm toán còn **có lãi ròng**: federation có nhiễu tốt lên 0,86–1,01 điểm ngay cả khi không có kẻ địch. Nhưng **chưa có gì được làm với nhãn phát hiện được**, nên tính đến lúc này giao thức chưa hơn một luật gộp trung vị tầm thường. Gate F kiểm đúng chỗ đó.
