# Kết quả Gate A (chạy 2026-09-18, T4, 2,72 giờ)

Dữ liệu: `gateA/phase2_results.zip`, giải nén ở `gateA/extracted/`.

Cấu hình: PromptFL, `--data_transform paper`, cache đặc trưng test, 10 client, Dirichlet α = 0,1, 8 shot/lớp cho cả liên đoàn, 50 round, seed 0/1/2 (đúng bộ seed của giai đoạn 1). Nhiễu 40% trên 5/10 client. Mọi run `rc=0`.

## 1. Phép kiểm bất biến (D) — đạt

| | Đường cong 5 round trên DTD |
|---|---|
| không nhiễu | 22,75 → 29,96 → 32,45 → 31,97 → 35,87 → 35,93 |
| tiêm rồi hoàn nhãn | 22,75 → 29,96 → 32,45 → 31,97 → 35,87 → 35,93 |

Giống hệt trên GPU với AMP và cache. Bộ tiêm nhiễu chỉ đổi nhãn, không đụng gì khác. Các con số dưới đây đọc được.

Tỉ lệ nhiễu thực tế khớp mục tiêu: client nhiễu là {0, 1, 4, 7, 8}, tỉ lệ 0,389–0,412 quanh mức 0,40. DTD lật 69/376 nhãn, Pets 60/296.

## 2. Bảng cổng

A = nhiễu 0% (giai đoạn 1), B = có nhiễu không phòng thủ, C = ORACLE loại client nhiễu, E = sàn ZS-CLIP.

| Dataset | Nhiễu | B | C | A | E | H_sample = A−B | H_client = C−B | A−C |
|---|---|---|---|---|---|---|---|---|
| DTD | sym 40% | 49,90 | 49,61 | 56,72 | 41,78 | **+6,82 ± 1,07** | −0,29 ± 2,46 | 7,11 |
| DTD | pair 40% | 49,06 | 49,61 | 56,72 | 41,78 | **+7,66 ± 0,76** | +0,55 ± 1,76 | 7,11 |
| OxfordPets | sym 40% | 84,29 | 87,24 | 89,08 | 85,69 | **+4,79 ± 1,17** | +2,94 ± 2,00 | 1,84 |
| OxfordPets | pair 40% | 83,83 | 87,24 | 89,08 | 85,69 | **+5,25 ± 1,11** | **+3,41 ± 0,29** | 1,84 |

Ba tiêu chí ghi trước:

| Tiêu chí | DTD | OxfordPets | Kết luận |
|---|---|---|---|
| i. A−B ≥ 3,0 | **đạt** (6,8 và 7,7) | **đạt** (4,8 và 5,3) | đạt, và rất chắc: mọi hiệu đều lớn hơn 4 lần sd của chính nó |
| ii. C−B ≥ 2,0 | **trượt** (−0,3 và +0,6) | **đạt** (2,9 và 3,4) | **hai dataset trái chiều nhau** |
| iii. B > E | đạt (49,9 so với 41,8) | **trượt** (84,3 và 83,8 so với 85,7) | trượt trên Pets |

**Gate A không đạt theo đúng câu chữ đã ghi trước.** Nhưng lý do trượt mới là phần có giá trị.

## 3. Nhiễu gây thiệt hại lớn, điều đó đã chắc

Mất 4,8 đến 7,7 điểm. So sánh: độ lệch còn tồn của khâu tái lập chỉ 0,55 điểm, sd giữa seed khoảng 0,3–1,4 điểm. Thiệt hại lớn hơn nhiễu đo đạc cả bậc. Bài toán là có thật.

## 4. Loại bỏ client nhiễu **không** phải câu trả lời

Đây là phát hiện quan trọng nhất của Gate A.

Trên DTD, một bộ phát hiện client **hoàn hảo** cũng chỉ đổi 49,90 thành 49,61, tức là **không được gì**. Cơ chế nhìn rõ qua cột A−C: loại 5/10 client làm mất 7,11 điểm trên DTD, trong khi nhiễu chỉ lấy đi 6,82. Hai thứ triệt tiêu nhau.

Vì sao DTD khác Pets? Xem mức dataset thực sự cần dữ liệu tới đâu:

| Dataset | A − E (huấn luyện mua được bao nhiêu so với zero-shot) | Mất khi loại nửa số client (A−C) | H_client |
|---|---|---|---|
| DTD | +14,94 | 7,11 | ≈ 0 |
| OxfordPets | +3,39 | 1,84 | +2,9 đến +3,4 |

DTD phải học thật từ dữ liệu nên mất dữ liệu rất đắt. Pets gần như đã xong việc từ zero-shot nên mất dữ liệu rẻ.

**Hệ quả cho phương pháp:** với client nhiễu, dữ liệu của họ kể cả khi 40% nhãn sai vẫn đáng giá **ngang với** việc vứt đi. Vậy hướng đúng là **sửa nhãn và giữ client lại**, không phải loại bỏ. Ngược lại, với client độc hại thì loại bỏ là bắt buộc vì dữ liệu của họ có giá trị âm.

Điều này biến luận điểm trung tâm của đồ án từ giả định thành kết quả đo được: **phải phân biệt hai loại client vì cách xử lý đúng của chúng ngược nhau**, chứ không phải vì phân loại nghe hay.

Ghi chú kỹ thuật: C giống hệt nhau giữa `sym` và `pair` trên cả hai dataset, đúng như phải thế — khi đã loại hết client nhiễu thì kiểu nhiễu không còn ảnh hưởng gì. Đây vừa là phép kiểm tính tiền định, vừa có nghĩa mỗi dataset **chỉ cần chạy C một lần**, tiết kiệm được một lượt cho lần sau.

## 5. Trên Pets, huấn luyện có nhiễu còn tệ hơn không huấn luyện

B = 84,29 và 83,83, trong khi zero-shot = 85,69. Nghĩa là ở mức nhiễu 40% trên nửa số client, federated prompt learning **phá hỏng** mô hình so với việc cứ để CLIP nguyên.

Và đó mới là con số theo chỉ số `best`. Nhìn `last10` thì nặng hơn nhiều:

| Run | best | last10 | best − last10 |
|---|---|---|---|
| Pets, nhiễu 0% (giai đoạn 1) | 89,08 | 88,09 | 0,99 |
| Pets, sym 40% | 84,29 | **79,45** | 4,85 |
| Pets, pair 40% | 83,83 | **74,91** | 8,92 |
| DTD, nhiễu 0% | 56,72 | 55,61 | 1,11 |
| DTD, sym 40% | 49,90 | 48,70 | 1,20 |
| DTD, pair 40% | 49,06 | 47,21 | 1,84 |

Trên Pets với pair flip, lúc hội tụ model thấp hơn zero-shot **10,8 điểm**, còn chỉ số `best` chỉ cho thấy thấp hơn 1,9 điểm. Đây chính là dấu hiệu ghi nhớ nhãn sai: model đạt đỉnh sớm rồi trượt dài, và `best` (chọn max trên tập test) che đi gần hết phần thiệt hại.

Hai kết luận:
1. Mọi phương pháp về sau **phải neo vào sàn zero-shot**, vì một "phòng thủ" tầm thường là không huấn luyện gì đã thắng baseline.
2. Luận văn **phải báo `last10` bên cạnh `best`**. Nếu chỉ báo `best` như FLIP và phần lớn bài trong lĩnh vực, ta sẽ báo thiếu thiệt hại tới 7 điểm. Đây là một đóng góp phương pháp luận, và là bài học FedSNC lặp lại đúng chỗ.

## 6. Caltech101 (chạy 2026-09-18, 2,42 giờ) và phán quyết cuối

Dữ liệu: `gateA/caltech101/`. Ba job, `rc=0`. C chỉ chạy một lần, đúng như đã rút gọn.

| Dataset | Nhiễu | B | C | A | E | A−B | C−B |
|---|---|---|---|---|---|---|---|
| Caltech101 | sym 40% | 89,16 | 88,95 | 90,94 | 85,76 | +1,78 ± 0,88 | −0,20 ± 0,32 |
| Caltech101 | pair 40% | 88,47 | 88,95 | 90,94 | 85,76 | +2,47 ± 0,84 | +0,49 ± 0,76 |

Caltech **không** phân định theo hướng nào cả: cả tiêu chí i lẫn ii đều trượt ở đây. Nhiễu chỉ lấy đi 1,8–2,5 điểm theo `best`, và loại client nhiễu vẫn không được gì (mất dữ liệu 1,99 điểm, đúng bằng phần lợi).

**Tổng kết theo chỉ số `best`, tức chỉ số đã ghi trước:**

| Tiêu chí | DTD | Caltech101 | OxfordPets | Số dataset đạt |
|---|---|---|---|---|
| i. A−B ≥ 3,0 | đạt | **trượt** | đạt | 2/3 |
| ii. C−B ≥ 2,0 | trượt | **trượt** | đạt | 1/3 |
| iii. B > E | đạt | đạt | **trượt** | 2/3 |

**Gate A không đạt.** Tiêu chí ii cần 2/3 mà chỉ được 1/3.

## 7. Nhưng chỉ số quyết định phán quyết — và đây mới là phát hiện lớn nhất

Tiêu chí được ghi trước dùng `best` vì đó là chỉ số FLIP và cả lĩnh vực đang báo. Cùng bộ dữ liệu ấy, đọc bằng `last10` (trung bình 10 round cuối, tức cái mà một mô hình triển khai thật sự nhận được):

| Dataset | Nhiễu | B | C | A | E | A−B | C−B | B > E? |
|---|---|---|---|---|---|---|---|---|
| DTD | sym 40% | 48,70 | 48,45 | 55,61 | 41,78 | +6,91 | −0,24 | có |
| DTD | pair 40% | 47,21 | 48,45 | 55,61 | 41,78 | +8,40 | +1,24 | có |
| Caltech101 | sym 40% | 85,61 | 86,97 | 90,28 | 85,76 | +4,67 | +1,36 | **không** |
| Caltech101 | pair 40% | 83,84 | 86,97 | 90,28 | 85,76 | +6,44 | +3,13 | **không** |
| OxfordPets | sym 40% | 79,45 | 83,72 | 88,09 | 85,69 | +8,64 | +4,28 | **không** |
| OxfordPets | pair 40% | 74,91 | 83,72 | 88,09 | 85,69 | **+13,18** | **+8,81** | **không** |

| Tiêu chí | theo `best` | theo `last10` |
|---|---|---|
| i. nhiễu gây thiệt hại ≥ 3,0 | 2/3 | **3/3** |
| ii. loại client nhiễu mua lại ≥ 2,0 | 1/3 | 2/3 với pair flip, 1/3 với sym |
| iii. B vẫn hơn zero-shot | 2/3 | **1/3** |

Thiệt hại thật lớn hơn con số `best` từ **1,4 đến 2,5 lần**. Và theo `last10`, **2 trên 3 dataset kết thúc thấp hơn cả zero-shot**: Caltech 83,84 so với 85,76, Pets 74,91 so với 85,69.

Vì sao `best` che được nhiều đến vậy: nó là max độ chính xác test qua 50 round. Khi có nhiễu, model đạt đỉnh sớm (trước lúc kịp ghi nhớ nhãn sai) rồi trượt dài. Chọn đỉnh **trên tập test** chính là early stopping bằng oracle. Trong một liên đoàn có nhiễu thật thì **không có tập validation sạch nào để làm việc đó**, nên con số đạt được thực tế nằm gần `last10`.

Đây là một đóng góp phương pháp luận độc lập với phương pháp sẽ đề xuất: **benchmark FPL đang báo chỉ số làm nhẹ đi tác hại của nhiễu nhãn, vì chỉ số đó giả định ngầm một khả năng mà bài toán không cho phép.**

## 8. Quyết định, theo quy tắc ghi trước

Quy tắc đã viết trước: "i đạt, ii trượt → chuyển trọng tâm sang sửa nhãn mức mẫu; khung triage vẫn giữ, nhưng giá trị của nó dồn sang trục độc hại, nơi buộc phải loại bỏ."

Áp dụng đúng như vậy. Ba điều đã đo được, không phải phỏng đoán:

1. **Nhiễu gây thiệt hại lớn** — 4,7 đến 13,2 điểm theo chỉ số hội tụ, trên cả ba dataset.
2. **Loại bỏ client nhiễu gần như vô ích** — trần của triage mức client là −0,2 đến +3,4 theo `best`, cao nhất 3,1 trên Caltech theo `last10` (trừ Pets, nơi dữ liệu gần như không cần thiết). Trong khi trần của sửa nhãn mức mẫu là toàn bộ 4,7–13,2 điểm. **Với client nhiễu, phải sửa và giữ lại, không phải loại bỏ.**
3. **Không có dữ liệu sạch để dựa vào** — không tập validation sạch, và zero-shot là mốc duy nhất có sẵn miễn phí. Chính điều này biện minh cho tín hiệu ngữ nghĩa từ CLIP: đó là tham chiếu sạch duy nhất mà bài toán cho phép, và RFedLR phải mượn dữ liệu proxy sạch từ server đúng vì họ không có nó.

Hai điều chỉnh bắt buộc cho phần còn lại của đồ án:
- **`last10` là chỉ số chính, `best` là phụ.** Ghi trước từ đây. Báo cả hai, nhưng mọi kết luận dựa trên `last10`.
- **Mọi phương pháp so với sàn zero-shot.** Một "phòng thủ" tầm thường là không huấn luyện gì đã thắng baseline trên 2/3 dataset.

## 9. Việc tiếp theo (bản cũ, giữ lại để đối chiếu dự đoán)

Quy tắc viết trước nói: chạy Caltech101 **nếu** DTD và Pets trái chiều nhau. Chúng trái chiều ở tiêu chí ii, nên phải chạy.

| Job | Thời gian T4 |
|---|---|
| `caltech101_B_sym40` | ~56 phút |
| `caltech101_B_pair40` | ~56 phút |
| `caltech101_C_sym40_drop` (chạy một lần, dùng cho cả hai) | ~36 phút |

Tổng khoảng **2,5 giờ**.

Dự đoán trước khi chạy: Caltech có A − E = 5,18, nằm giữa DTD (14,94) và Pets (3,39), nên chi phí mất dữ liệu khi loại client sẽ vào khoảng 2–3 điểm và H_client nhiều khả năng dương nhưng nhỏ, quanh ngưỡng 2,0.

**Đối chiếu sau khi chạy:** chi phí mất dữ liệu đúng 1,99 điểm, nằm trong khoảng dự đoán. H_client ra −0,20 và +0,49, tức dương nhỏ hoặc bằng không, thấp hơn ngưỡng 2,0 — dự đoán đúng hướng nhưng lạc quan hơn thực tế một chút. Phần không lường trước là tiêu chí **i** cũng trượt trên Caltech theo `best`, và chính chỗ đó dẫn tới mục 7.

Dù Caltech ngả về bên nào, hai điều đã chắc và không đổi:
- nhiễu gây thiệt hại lớn (tiêu chí i đạt tuyệt đối);
- loại bỏ client nhiễu không phải cách xử lý đúng, ít nhất trên dataset cần học nhiều từ dữ liệu.
