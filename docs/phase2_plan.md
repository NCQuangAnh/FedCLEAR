# Giai đoạn 2: đo dư địa trước khi thiết kế phương pháp

Cập nhật: 2026-09-18. Tiếp nối `phase1_plan.md` (giai đoạn 1 đã xong, 9/9 ô đạt).

## 1. Mục tiêu

Trả lời một câu duy nhất, **trước khi** viết bất kỳ phương pháp nào:

> Trong federated prompt learning few-shot, nhiễu nhãn có thực sự gây thiệt hại đủ lớn, và việc phát hiện đúng client nhiễu có mua lại được bao nhiêu phần thiệt hại đó?

Đây đúng là bài học rút ra từ FedSNC: ở đó trần (ORACLE) chỉ được đo ở vòng 11, sau khi đã tốn 34 lần chạy cho các cải tiến không có chỗ để cải tiến. Lần này trần được đo trước.

## 2. Những gì đã cài (2026-09-18)

`flip/flcore/datasets/noise.py`, nối vào `ImageLoader` ngay sau bước chia Dirichlet.

**Điểm quan trọng về vị trí:** nhiễu được tiêm **sau** khi chia client, nên với cùng seed thì lượt sạch và lượt nhiễu có **cùng một cách chia dữ liệu**, cùng thứ tự batch, cùng khởi tạo prompt. Chỉ nhãn khác nhau. Đó là điều cho phép so ghép cặp từng run.

Ba mô hình nhiễu:

| Cờ | Mô hình | Ghi chú |
|---|---|---|
| `--noise_type sym` | lật sang một lớp khác bất kỳ, đều xác suất | symmetric flip, thông lệ chuẩn |
| `--noise_type pair` | lật sang lớp kế tiếp theo chỉ số | pair flip. Khó hơn `sym` rất nhiều ở mọi phương pháp trong RFedLR và FedDR-LoRA |
| `--noise_type instance` | nhiễu phụ thuộc mẫu theo Xia et al. 2020 | mỗi ảnh có tỉ lệ lật riêng và phân phối lật phụ thuộc chính ảnh đó |

**Đặc trưng cho nhiễu phụ thuộc mẫu là pixel thô hạ mẫu 16×16, không phải đặc trưng CLIP.** Lý do ghi trong `noise.py`: tín hiệu phát hiện mà đồ án nghiên cứu là tín hiệu ngữ nghĩa từ CLIP, nên nếu sinh nhiễu bằng CLIP thì đáp án bị rò rỉ vào dữ liệu.

Phân bổ tỉ lệ nhiễu cho client:

| Cờ | Ý nghĩa |
|---|---|
| `--noise_rate` | tỉ lệ lật của một client nhiễu |
| `--noisy_client_frac` | phần client bị nhiễu (0,5 = một nửa) |
| `--noise_mode uniform` | mọi client nhiễu dùng đúng `--noise_rate` |
| `--noise_mode hetero` | tỉ lệ dàn đều trên (0, `--noise_rate`]; với rate 0,5 và frac 1,0 thì 10 client nhận 0,05 … 0,50 — đúng kịch bản nhiễu dị biệt của FedCorr |

Hai chế độ ORACLE, là phần cốt lõi của cổng Gate A:

| Cờ | Nghĩa | Dùng để |
|---|---|---|
| `--noise_oracle clean` | tiêm nhiễu rồi hoàn nhãn về đúng | **Phép kiểm bất biến.** Phải cho kết quả **giống hệt** lượt nhiễu 0%. Nếu khác thì bộ tiêm nhiễu đã làm hỏng thứ gì khác ngoài nhãn |
| `--noise_oracle drop_noisy` | loại hẳn client nhiễu khỏi huấn luyện | **Trần của triage mức client.** Một bộ phát hiện client hoàn hảo không thể tốt hơn mức này |

Chi tiết kỹ thuật đã xử lý:
- `loader.stats` được **tính lại** từ nhãn đã nhiễu (điểm 7 của `phase1_plan.md`). Các loss `bce` và `lc` đọc bảng này, nếu không tính lại thì chúng thấy phân phối nhãn sạch.
- `samples` được chuẩn hoá về list các tuple `(path, int)`. Sau bước few-shot, `np.delete` đã biến nó thành mảng numpy toàn chuỗi, nên nhãn trả về là `np.str_`.
- Mỗi client giữ `clean_targets`, nên biết chính xác mẫu nào bị lật mà không phải chạy lại.
- `drop_noisy` **không** thay đổi luồng RNG: `select_clients` vẫn rút y nguyên rồi mới lọc bỏ client bị loại. Nhờ vậy lượt `drop_noisy` vẫn ghép cặp được với các lượt khác.
- Mỗi lần chạy in một dòng `NOISE_REPORT {...}` dạng JSON và nhét cả báo cáo vào file kết quả, nên vài tuần sau đọc lại vẫn biết ground truth: client nào nhiễu, tỉ lệ đặt ra và tỉ lệ thực tế, số nhãn bị lật.

## 3. Các mốc tham chiếu

Ở mỗi mức nhiễu, năm điểm sau được đo hoặc đã có:

| Ký hiệu | Cấu hình | Nghĩa |
|---|---|---|
| **A** | nhiễu 0% | Đã có từ giai đoạn 1 (DTD 56,72 / Caltech 90,94 / Pets 89,08 với PromptFL). Trần tuyệt đối: sửa được mọi nhãn sai |
| **B** | có nhiễu, không phòng thủ | Mức phải vượt |
| **C** | `--noise_oracle drop_noisy` | Trần của triage mức client |
| **D** | `--noise_oracle clean` | Phép kiểm bất biến, phải bằng A |
| **E** | ZS-CLIP | Sàn: 41,78 / 85,76 / 85,69. Không huấn luyện gì |

Hai đại lượng dư địa:
- **H_client = C − B**: phát hiện đúng client nhiễu mua lại được bao nhiêu.
- **H_sample = A − B**: sửa đúng từng nhãn mua lại được bao nhiêu. Đây là trần của mọi phương pháp.

Khoảng cách **A − C** cũng phải đọc: nếu lớn, nghĩa là loại client làm mất dữ liệu quá nhiều, nên triage mức client một mình không đủ và phải sửa nhãn ở mức mẫu.

## 4. Tiêu chí Gate A (ghi trước khi chạy)

Cấu hình cổng: PromptFL, `--data_transform paper`, `--cache_test_feats true`, seed 0/1/2 (đúng bộ seed của giai đoạn 1 để ghép cặp), 50 round, `sym` 40% với `--noisy_client_frac 0.5`, sau đó `pair` 40% cùng thiết lập. Dataset: DTD và OxfordPets trước, Caltech101 sau nếu cần.

Gate A **đạt** khi cả ba điều kiện sau đúng:

| # | Điều kiện | Ngưỡng |
|---|---|---|
| i | Nhiễu thực sự gây thiệt hại | A − B ≥ 3,0 điểm, trên ít nhất 2 trong 3 dataset |
| ii | Triage mức client mua lại được | C − B ≥ 2,0 điểm, trên ít nhất 2 trong 3 dataset |
| iii | Bài toán không suy biến | B > E, tức có nhiễu thì huấn luyện vẫn hơn zero-shot |

Mọi so sánh là **ghép cặp theo seed**: lấy hiệu từng seed rồi mới trung bình. Nếu độ lớn trung bình của hiệu nhỏ hơn 2 lần sd của chính hiệu đó thì **không** kết luận, mà tăng lên 5 seed. Phương sai ở giai đoạn 1 đã cho thấy điều này là cần: DTD FedOTP có sd 1,44 điểm.

Quy tắc quyết định, ghi trước:

| Kết quả | Kết luận | Việc làm |
|---|---|---|
| Đạt cả i, ii, iii | Có dư địa cho triage mức client | Sang giai đoạn 3: tín hiệu ngữ nghĩa, tín hiệu phản ứng khi sửa nhãn |
| i đạt, ii trượt | Nhiễu có hại, nhưng loại client không phải câu trả lời (mất dữ liệu đắt hơn nhiễu) | Chuyển trọng tâm sang sửa nhãn mức mẫu. Khung "triage" vẫn giữ, nhưng giá trị của nó dồn sang trục độc hại, nơi buộc phải loại bỏ |
| i trượt | Ở mức nhiễu này không có dư địa | Thử `pair` 60% một lần. Vẫn trượt thì đây là **phát hiện có giá trị** (prompt learning trên CLIP đóng băng bền với nhiễu nhãn nhờ few-shot và prompt nhỏ), và đồ án dồn về trục client độc hại, nơi thiệt hại là chắc chắn |
| iii trượt | B ≤ E | Ghi rõ thành phát hiện: FPL có nhiễu còn tệ hơn không huấn luyện. Mọi phương pháp sau đó phải neo vào zero-shot |

**Không** chỉnh mức nhiễu, số client nhiễu hay hyperparameter để cổng này đạt.

## 5. Danh sách lượt chạy và ngân sách

Ước lượng dùng số giây/round đo được ở giai đoạn 1 khi bật cache (PromptFL: DTD 9,0 s, Pets 9,2 s, Caltech 20,6 s mỗi round).

| Lượt | Cấu hình | Dataset | Thời gian T4 |
|---|---|---|---|
| D | `--noise_oracle clean`, 5 round, 1 run | DTD | ~2 phút |
| B1 | `sym` 40%, frac 0,5 | DTD, Pets | ~54 phút |
| C1 | `sym` 40%, frac 0,5, `drop_noisy` | DTD, Pets | ~54 phút |
| B2 | `pair` 40%, frac 0,5 | DTD, Pets | ~54 phút |
| C2 | `pair` 40%, frac 0,5, `drop_noisy` | DTD, Pets | ~54 phút |

Tổng khoảng **3,6 giờ T4**, vừa một phiên quota. Caltech101 (+3,7 giờ cho 4 lượt) chỉ chạy nếu DTD và Pets cho kết quả trái chiều nhau.

Sau khi cổng đạt, giai đoạn 2b quét mức nhiễu (20 / 40 / 60%) và kịch bản `hetero` cùng `instance`, chỉ trên DTD, khoảng 2,6 giờ.

## 6. Kiểm trên CPU (2026-09-18)

Dữ liệu giả 6 lớp, 4 client, 2 round, seed 5, `--data_transform paper`. Mỗi client có 12 ảnh.

| Lượt | Cấu hình | Kết quả |
|---|---|---|
| clean0 | không nhiễu | loss 1,895 / 1,808 / 1,791, top1 16,67 / 25,00 / 25,00 |
| sym40 | `sym` 40%, frac 0,5 | 2/4 client nhiễu, 10/48 nhãn lật (20,8% toàn cục, 41,67% ở client nhiễu). Đường cong **khác** lượt sạch, đúng như phải thế |
| sym40 + oracle `clean` | tiêm rồi hoàn nhãn | loss 1,895 / 1,808 / 1,791, top1 16,67 / 25,00 / 25,00 — **giống hệt clean0 tới từng chữ số** |
| sym40 + oracle `drop_noisy` | loại client nhiễu | log ghi `excluding clients [0, 2]`, mỗi round nhanh hơn (11,4 s so với 17,5 s) vì chỉ còn 2 client huấn luyện |
| pair40 | `pair` 40% | 10/48 nhãn lật, đúng hạn mức |
| inst40 | `instance` 40% | 11/48 nhãn lật (22,9%). Không đúng hạn mức là **đúng thiết kế**: mỗi ảnh có tỉ lệ lật riêng |

**Phép kiểm quan trọng nhất đã đạt:** oracle `clean` tái tạo chính xác lượt sạch. Nghĩa là bộ tiêm nhiễu chỉ đổi nhãn, không đụng tới cách chia dữ liệu, thứ tự batch hay khởi tạo prompt. Nếu phép kiểm này trượt thì mọi con số của Gate A đều vô nghĩa, vì không biết phần chênh lệch đến từ nhiễu hay từ chính hạ tầng.

Phép kiểm này được chạy lại trên GPU như một job riêng (`RUN_INVARIANCE = True` trong notebook), vì AMP và cache đặc trưng có thể làm hỏng tính tái lập mà CPU không thấy.

## 7. Việc còn lại của giai đoạn 2

1. ~~Bộ tiêm nhiễu theo client, ba mô hình nhiễu, hai chế độ ORACLE~~ — xong 2026-09-18.
2. ~~Kiểm trên CPU~~ — xong, mục 6.
3. ~~Notebook Kaggle cho Gate A~~ — xong: `kaggle/phase2_gate_a.ipynb`, notebook **riêng**, không dùng chung với giai đoạn 1. Bảng cổng tự in phán quyết theo tiêu chí mục 4. Cả hai notebook sinh từ `tools/build_kaggle_notebook.py`, dùng chung các ô môi trường, tải dữ liệu và chạy job; chỉ ô config, ô plan và ô thu kết quả là khác nhau.
4. ~~Chạy Gate A trên T4~~ — xong 2026-09-18, cả 3 dataset, 5,14 giờ. Kết quả và phân tích: `results/Phase2/gate_a_results.md`. Tóm tắt: tiêu chí i đạt mạnh (nhiễu lấy đi 4,8–7,7 điểm), tiêu chí ii **trái chiều** giữa hai dataset (DTD ≈ 0, Pets +3), tiêu chí iii trượt trên Pets (huấn luyện có nhiễu tệ hơn zero-shot). Caltech101 đã chạy: trượt cả i lẫn ii theo `best`. **Gate A không đạt** (ii chỉ 1/3). Nhưng đọc bằng `last10` thì i đạt 3/3 và thiệt hại lớn hơn 1,4–2,5 lần — chỉ số quyết định phán quyết, xem mục 7 của file kết quả.

**Quyết định đứng từ đây (ghi trước cho phần còn lại của đồ án):**
- `last10` là **chỉ số chính**, `best` là phụ. Báo cả hai, kết luận theo `last10`.
- Mọi phương pháp so với **sàn zero-shot**, vì "không huấn luyện gì" đã thắng baseline trên 2/3 dataset.
- Với client nhiễu: **sửa nhãn và giữ lại**, không loại bỏ (trần của loại bỏ chỉ −0,2 đến +3,4; trần của sửa nhãn là 4,7–13,2).
- Loại bỏ dành cho client độc hại. Đó là nơi khung triage có giá trị, và là trọng tâm giai đoạn 3.
5. Bảng vai trò client (`honest` / `noisy` / `malicious`). Chỗ cắm đã có: khoá `role` trong báo cáo của `noise.py`. Phần `malicious` thuộc giai đoạn 3.
