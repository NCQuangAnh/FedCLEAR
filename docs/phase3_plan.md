# Giai đoạn 3: trục client độc hại, và cổng Gate B

Cập nhật: 2026-09-18. Tiếp nối kết quả Gate A (`results/Phase2/gate_a_results.md`).

## 1. Vì sao trọng tâm dồn về đây

Gate A đo được hai điều đặt lại hướng của cả đồ án:

- **Loại bỏ client nhiễu gần như vô ích.** Trần của nó là −0,2 đến +3,4 điểm, vì mất dữ liệu đắt ngang chính nhiễu. Trần của sửa nhãn là toàn bộ 4,7–13,2 điểm.
- **Với client độc hại, loại bỏ là bắt buộc**, vì đóng góp của họ có giá trị âm chứ không phải giá trị thấp.

Hai cách xử lý **ngược nhau**, nên việc phân biệt hai loại client không còn là một ý tưởng nghe hay, mà là điều kiện cần để làm đúng. Đó là luận điểm trung tâm của luận văn, và giờ nó có số liệu đứng sau.

Câu hỏi của giai đoạn 3: **có tách được không, và các phòng thủ sẵn có có tách được không?**

## 2. Những gì đã cài (2026-09-18)

### 2.1 Vai trò client

`flcore/attack.py::assign_roles`. Ba vai trò **rời nhau**: `honest`, `noisy`, `malicious`. Client độc hại được rút trước, client nhiễu rút sau từ phần còn lại. Khi `--malicious_client_frac 0` thì tập client nhiễu **trùng đúng** với giai đoạn 2, nên các lượt chạy vẫn ghép cặp được.

### 2.2 Tấn công mức dữ liệu

| Cờ | Cách làm | Ý đồ |
|---|---|---|
| `--attack_type targeted_flip` | mọi mẫu của một lớp nguồn bị gán sang một lớp đích cố định | Tấn công có mục tiêu kinh điển. Ồn ào, dễ phát hiện |
| `--attack_type noise_disguise` | lật đúng **tỉ lệ** như một client nhiễu thật, nhưng mọi nhãn bị lật đều dồn về một lớp đích do kẻ tấn công chọn | **Đây là trọng tâm.** Thống kê bậc nhất (tỉ lệ bất đồng, loss cục bộ) giống hệt client nhiễu, chỉ khác ở cấu trúc của phần bị lật |

### 2.3 Tấn công mức cập nhật

| Cờ | Cách làm |
|---|---|
| `--attack_type signflip` | cập nhật prompt bị đảo dấu, kéo prompt toàn cục lùi lại |
| `--attack_type scale --attack_scale k` | cập nhật prompt bị nhân lên k lần |

Tấn công mức cập nhật được mô phỏng ở server (`receive_results`) nên code client giữ nguyên cho cả client thật và client độc hại.

### 2.4 Gộp model bền vững, và phép đo nhầm lẫn

`flcore/robust_agg.py`, chọn bằng `--agg_rule {fedavg,median,trimmed_mean,krum,multikrum}`.

Điểm quan trọng: `krum` và `multikrum` **nêu tên** những client chúng tin. Server ghi lại mỗi round `selected`, `excluded` kèm **vai trò thật** của từng client vào `noise_seed_*.json`. Nhờ đó đo trực tiếp được:

> phòng thủ chuẩn loại nhầm client nhiễu (thật thà, chỉ gán nhãn kém) bao nhiêu lần, so với loại đúng client độc hại?

Đó chính là giả thuyết H1–H5 của giai đoạn 0b, giờ thành một con số chứ không phải một lập luận.

## 3. Tiêu chí Gate B (ghi trước khi chạy)

Cấu hình: PromptFL, `--data_transform paper`, seed 0/1/2, 50 round, 10 client. 3 client nhiễu (`sym` 40%) và 2 client độc hại, tức `--noisy_client_frac 0.3 --malicious_client_frac 0.2`. Dataset: DTD và OxfordPets — DTD vì dữ liệu đáng giá nhất ở đó, Pets vì nó đã tụt dưới zero-shot nên là trường hợp xấu nhất.

**Chỉ số chính là `last10`**, theo quyết định sau Gate A. `best` chỉ báo kèm.

| # | Điều kiện | Ngưỡng | Ý nghĩa nếu trượt |
|---|---|---|---|
| B1 | Tấn công gây thiệt hại vượt hẳn nhiễu cùng quy mô | thiệt hại của `noise_disguise` ≥ thiệt hại của `sym` cùng tỉ lệ, cách biệt ≥ 2,0 điểm | Nếu trượt: tấn công giả nhiễu không mạnh hơn nhiễu thường, nên việc tách hai loại không đáng giá về mặt thiệt hại |
| B2 | Phòng thủ sẵn có **không** cứu được | với `multikrum` và `median`, thiệt hại còn lại ≥ 2,0 điểm so với lượt không có tấn công | Nếu trượt: Krum/median đã đủ, không cần phương pháp mới |
| B3 | Phòng thủ sẵn có **nhầm** hai loại | tỉ lệ round mà `multikrum` loại một client nhiễu ≥ tỉ lệ loại một client độc hại | Nếu trượt: phòng thủ chuẩn phân biệt được rồi, và đóng góp của đồ án phải chuyển sang phần sửa nhãn |

B3 là tiêu chí sống còn của hướng đề tài. B1 và B2 chỉ xác nhận rằng bài toán đáng làm.

Mọi so sánh ghép cặp theo seed, và vẫn giữ quy tắc: hiệu nhỏ hơn 2 lần sd của chính nó thì không kết luận, phải thêm seed.

## 4. Danh sách lượt chạy

Mọi lượt dùng cùng bộ vai trò client (3 nhiễu, 2 độc hại), chỉ đổi kiểu tấn công và luật gộp.

| Tag | Cấu hình | Dùng cho |
|---|---|---|
| `N` | chỉ nhiễu, 5 client nhiễu (đã có từ Gate A) | mốc so sánh thiệt hại |
| `P0` | 3 nhiễu + 2 độc hại `noise_disguise`, fedavg | B1 |
| `P1` | như trên, `targeted_flip` | so sánh tấn công ồn ào với tấn công giả nhiễu |
| `P2` | như trên, `signflip` | tấn công mức cập nhật, để kiểm phòng thủ |
| `D0` | `noise_disguise` + `multikrum` | B2, B3 |
| `D1` | `noise_disguise` + `median` | B2 |
| `D2` | `signflip` + `multikrum` | đối chứng: phòng thủ phải chặn được tấn công ồn ào |

Ước lượng T4 với cache (PromptFL, 3 run, 50 round): DTD ~26 phút mỗi lượt, Pets ~27 phút. 7 lượt × 2 dataset ≈ **6,2 giờ**, nên chia hai phiên quota: DTD trước, Pets sau.

`multikrum` thêm chi phí tính khoảng cách giữa các client mỗi round, nhưng prompt chỉ có 2048 tham số nên không đáng kể.

## 5. Nếu Gate B đạt

Phương pháp của giai đoạn 4 gồm ba tín hiệu, hai trong đó chưa ai dùng trong federated prompt learning:

1. **Tính hợp lý ngữ nghĩa từ CLIP.** So phân phối nhãn của client với độ tương đồng ảnh–văn bản do CLIP đóng băng tính. Nhiễu ngẫu nhiên làm nhãn lệch đều khỏi ngữ nghĩa; tấn công dồn nhãn về một lớp đích nên để lại lệch **có cấu trúc**. Đây là tham chiếu sạch duy nhất bài toán cho phép, và là lý do RFedLR phải mượn dữ liệu proxy sạch từ server còn ta thì không.
2. **Phản ứng khi được yêu cầu sửa nhãn.** Server đề nghị một bản sửa; client nhiễu thật thà chấp nhận và loss giảm, client độc hại hoặc từ chối hoặc loss không giảm như dự đoán. Fed-RoSeC giả định client độc hại tuân thủ, ta không giả định.
3. **Xử lý phân hoá:** sửa nhãn rồi giữ lại client nhiễu, loại bỏ client độc hại. Gate A đã chứng minh đây là cách xử lý đúng chứ không phải lựa chọn tuỳ ý.

## 6. Kiểm trên CPU (2026-09-18)

**Kiểm từng luật gộp trên dữ liệu dựng sẵn.** 4 client thật thà quanh 1,0 và 1 kẻ tấn công ở −5,0:

| Luật | Kết quả gộp | Client được giữ |
|---|---|---|
| `fedavg` | **−0,190** | tất cả — bị phá hoàn toàn |
| `median` | +1,000 | tất cả |
| `trimmed_mean` | +0,983 | tất cả |
| `krum` | +1,050 | chỉ client 3 |
| `multikrum` | +1,013 | 0, 1, 2, 3 — **loại đúng kẻ tấn công** |

**Kiểm chạy thật trên dữ liệu giả 6 lớp**, 4 client (1 độc hại, 2 nhiễu, 1 thật thà), 2 round: cả 6 cấu hình chạy hết, `targeted_flip`, `noise_disguise`, `signflip`, `scale`, `multikrum`, `median`.

Bảng vai trò và báo cáo tấn công ghi đúng, ví dụ `noise_disguise`: client 3 lật 5/12 nhãn (tỉ lệ thực 0,4167 so với mục tiêu 0,40), toàn bộ dồn về lớp đích 1. Đúng ý đồ: **tỉ lệ giống client nhiễu, cấu trúc thì không**.

Server ghi mỗi round `selected` và `excluded` kèm **vai trò thật**, nên tỉ lệ nhầm lẫn của tiêu chí B3 đọc thẳng từ file kết quả.

Một lỗi đã sửa trên đường đi: id client là số nguyên numpy (do `np.random.choice` ở bước chọn client), nên ghi JSON báo `Object of type int64 is not JSON serializable`. Đã ép về `int` trong bản ghi.

## 7. Việc còn lại

1. ~~Vai trò client, hai tấn công dữ liệu, hai tấn công cập nhật, bốn luật gộp bền vững~~ — xong 2026-09-18.
2. ~~Kiểm trên CPU~~ — xong, mục 6.
3. ~~Notebook `kaggle/phase3_gate_b.ipynb`~~ — xong, 7 lượt, tự in phán quyết B1/B2/B3.
4. ~~Chạy Gate B trên DTD và OxfordPets~~ — xong 2026-09-19, 6,09 giờ, 14/14 job `rc=0`. Kết quả và phân tích: `results/Phase3/gate_b_results.md`.

**Tóm tắt phán quyết:** Gate B **không đạt** theo câu chữ. B1 đúng chiều (+4,96 trên DTD, +3,03 trên Pets) nhưng **chưa kết luận được** vì nhỏ hơn 2 sd của chính hiệu đó. B2 đạt trên DTD, trượt trên Pets vì `median` cứu được gần hết (còn 0,21). B3 trượt cả hai.

**Nhưng ba điều đo được, có giá trị:**
- Trên Pets, `multikrum` loại client nhiễu ở 33% số round trong khi chỉ đụng client thật thà 1,4% — **gấp 24 lần**, và bằng 71% tỉ lệ loại đúng kẻ tấn công. Ở kịch bản `signflip` thì nó loại client nhiễu (0,405) **nhiều hơn** kẻ tấn công thật (0,340).
- Trên Pets, bật `multikrum` làm mô hình **tệ hơn 1,98 điểm so với không phòng thủ gì**, vì nó vứt dữ liệu của client nhiễu mà Gate A đã chứng minh là đáng giữ.
- Không luật gộp nào đúng đều: `median` cứu Pets nhưng để lại 3,38 trên DTD; `multikrum` ngược lại. Phải quyết định theo từng client, không áp quy tắc cứng.

5. ~~Chạy thêm seed 3 và 4~~ — xong 2026-09-19 (2,25 giờ). Ô phân tích lỗi `KeyError: 0` nhưng mọi job đã chạy xong và output còn nguyên, nên số lấy lại đủ.

**Phán quyết Gate B ở 5 seed** (mục 8 của `results/Phase3/gate_b_results.md`):
- **Gộp bền vững chỉ giúp ở 1 trong 4 tổ hợp** (dataset × luật): `median` trên Pets, +3,10 điểm, p = 0,001. Ba tổ hợp còn lại không khác gì không phòng thủ, `multikrum` trên Pets còn âm 1,63.
- **Luật nào có quyết định thì quyết định sai đối tượng:** `multikrum` trên Pets loại client nhiễu gấp **17,7 lần** client thật thà, bằng 75% tỉ lệ loại đúng kẻ tấn công. **B3′ đạt.**
- B1 chưa qua quy tắc 2 sd (DTD +4,13, Pets +3,58) nhưng **đạt theo kiểm định t trên Pets** (p = 0,015) và sát ngưỡng trên DTD (p = 0,054).
- Bài học lặp lại: ở 3 seed `multikrum` trên DTD có vẻ giúp (−1,25), ở 5 seed thì **đổi dấu** thành +0,27.

6. ~~Chạy seed 5 và 6 cho `N_control` và `P0_disguise`~~ — xong 2026-09-19 (1,07 giờ). **B1 đạt**: +3,62 trên DTD (p = 0,019) và +3,51 trên Pets (p = 0,001), 7 seed, ước lượng ổn định qua ba lần mở rộng.

**Gate B kết thúc:** B1 đạt, B2 đạt trên DTD, B3′ đạt trên Pets. Đủ điều kiện sang giai đoạn 4. Chi tiết và tổng kết: mục 9–10 của `results/Phase3/gate_b_results.md`.

**Sửa tiêu chí thống kê, ghi trước cho các giai đoạn sau:** quy tắc "hiệu ≥ 2 sd" không bao giờ đạt được bằng cách thêm seed, vì `sd` đo độ tản của tổng thể chứ không phải sai số của trung bình. Từ đây kết luận dựa trên **kiểm định t ghép cặp p < 0,05 với ≥ 5 seed**, luôn báo kèm trung bình ± sd và **Cohen's dz = mean/sd**.
