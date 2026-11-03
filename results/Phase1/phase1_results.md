# Kết quả giai đoạn 1: tái lập FLIP (RN50, T4, chạy 2026-09-17)

- Dữ liệu gốc: `DTD/`, `Caltech101/`, `Oxfordpets/`, mỗi thư mục có `phase1_results.zip` và bản giải nén `extracted/`.
- Đường cong accuracy theo round của cả 18 run: `parsed_all.json`.

## 1. Bảng tổng hợp

Accuracy toàn cục (%), 3 run, train transform = `default` của FLIP gốc (không Normalize khi train).

| Dataset | Phương pháp | Ta: best | Paper | Chênh | Dung sai | Đạt? | Ta: last | Ta: last10 | Phút GPU |
|---|---|---|---|---|---|---|---|---|---|
| DTD | ZS-CLIP | 41,78 | 41,7 | +0,08 | 0,5 | **Đạt** | – | – | 0,8 |
| DTD | PromptFL | 53,29 ± 2,68 | 57,6 ± 1,3 | **−4,31** | 2,6 | Trượt | 52,82 | 52,38 | 34,3 |
| DTD | FedOTP | 53,84 ± 0,41 | 58,0 ± 0,8 | **−4,16** | 1,6 | Trượt | 53,49 | 53,15 | 45,2 |
| Caltech101 | ZS-CLIP | 85,76 | 86,0 | −0,24 | 0,5 | **Đạt** | – | – | 0,8 |
| Caltech101 | PromptFL | 90,18 ± 0,56 | 91,5 ± 0,5 | −1,32 | 1,0 | Trượt | 89,51 | 89,47 | 63,9 |
| Caltech101 | FedOTP | 90,29 ± 0,20 | 91,8 ± 0,1 | −1,51 | 1,0 | Trượt | 89,64 | 89,57 | 102,4 |
| OxfordPets | ZS-CLIP | 85,69 | 85,7 | −0,01 | 0,5 | **Đạt** | – | – | 0,9 |
| OxfordPets | PromptFL | 87,89 ± 0,63 | 89,4 ± 0,5 | −1,51 | 1,0 | Trượt | 86,21 | 86,30 | 46,9 |
| OxfordPets | FedOTP | 87,41 ± 0,88 | 89,1 ± 0,1 | −1,69 | 1,0 | Trượt | 86,04 | 86,30 | 57,1 |

Tổng thời gian GPU khoảng 5,9 giờ.

## 2. Đọc kết quả

1. **ZS-CLIP khớp paper ở cả 3 dataset**, chênh không quá 0,24 điểm. Các phần sau là đúng:
   - loader CLIP viết lại (`clip.py`);
   - tokenizer;
   - phép biến đổi ảnh lúc test;
   - các file split dữ liệu.

   Lỗi, nếu có, nằm ở phần **huấn luyện**.
2. **PromptFL và FedOTP thấp hơn paper ở cả 6 ô, cùng một chiều.** Trên cùng một dataset, hai phương pháp lệch gần như bằng nhau:
   - DTD: −4,3 và −4,2;
   - Caltech: −1,3 và −1,5;
   - Pets: −1,5 và −1,7.

   Lệch đều như vậy chỉ ra một yếu tố **dùng chung cho cả hai phương pháp**, không phải lỗi cài đặt của riêng phương pháp nào.
3. **Thứ tự hai phương pháp giữ đúng như paper ở cả 3 dataset:**
   - Caltech: FedOTP > PromptFL;
   - DTD: FedOTP > PromptFL;
   - Pets: PromptFL > FedOTP.
4. **Nghi vấn chính là phép biến đổi ảnh khi train.** Code gốc dùng RandomResizedCrop, **không Normalize**, trong khi lúc test có Normalize. Paper (Appendix B.4) mô tả: resize 240×240, crop 224, lật ngang, **có normalize**. Khi train và test thấy phân phối ảnh khác nhau thì prompt học chậm và lệch. Hai quan sát khớp với giải thích này:
   - Trên DTD, accuracy ở round 0 (22–34%) thấp hơn cả zero-shot (41,8%), và đến round 50 vẫn còn đang tăng, tức chưa hội tụ.
   - DTD là dataset lệch nhiều nhất, và cũng là dataset phụ thuộc màu sắc/kết cấu nhiều nhất.
5. **`best` thiên lệch lên so với `last10` từ 0,7 đến 1,6 điểm**, lớn nhất trên Pets. Trên Pets, accuracy đạt đỉnh sớm (round 5–10) rồi giảm dần. Nghĩa là trong setting few-shot federated, model bắt đầu overfit từ sớm. Điểm này quan trọng cho giai đoạn 2: khi có nhiễu nhãn, model sẽ học thuộc nhãn sai trong chính khoảng thời gian đó.

## 3. Chẩn đoán tiếp theo (ghi trước khi chạy)

**Thí nghiệm:** PromptFL trên DTD, 3 run, giữ nguyên mọi thứ, chỉ đổi train transform:
- `default_norm`: như code gốc nhưng thêm Normalize;
- `paper`: đúng mô tả ở Appendix B.4.

Hai biến thể dùng chung cách chia client và khởi tạo prompt với lần chạy gốc, nên so ghép cặp từng run được.

**Quy tắc quyết định:**

| Kết quả | Kết luận | Việc làm |
|---|---|---|
| Có biến thể đưa best về ≥ 55,0 (trong dung sai) | Nguyên nhân là train transform | Dùng biến thể đó làm protocol chính (nếu cả hai đạt thì chọn `paper`, vì đó là protocol paper mô tả). Chạy lại Caltech/Pets theo protocol mới, gộp luôn làm điểm "nhiễu 0%" của giai đoạn 2 |
| Không đạt, nhưng cải thiện ≥ 2 điểm (so ghép cặp) | Train transform là một phần nguyên nhân | Giữ biến thể tốt nhất, xét tiếp phiên bản torch và AMP |
| Cải thiện < 1 điểm | Không phải do transform | Chấp nhận độ lệch có hệ thống và ghi rõ trong luận văn. Thứ tự các phương pháp khớp paper, nên so sánh nội bộ vẫn hợp lệ |

**Chi phí:** khoảng 1,2 giờ GPU T4.

## 4. Kết quả chẩn đoán (chạy 2026-09-18, T4)

PromptFL trên DTD, 3 run, chỉ đổi cách xử lý ảnh lúc train:

| Train transform | best | last | last10 | Chênh so với paper (57,6 ± 1,3) | Đạt? | Cải thiện so với `default` |
|---|---|---|---|---|---|---|
| `default` (FLIP gốc, không Normalize) | 53,29 ± 2,68 | 52,82 | 52,38 | −4,31 | Trượt | – |
| `default_norm` (gốc + Normalize) | 57,03 ± 2,16 | 56,64 | 56,16 | −0,57 | **Đạt** | **+3,74** |
| `paper` (Appendix B.4) | **57,51 ± 0,82** | 57,05 | 56,81 | **−0,09** | **Đạt** | **+4,22** |

**Kết luận:** nguyên nhân đúng là cách xử lý ảnh lúc train. Code FLIP public không chuẩn hoá ảnh khi train, trong khi lúc test có, nên bản public gần như chắc chắn **không phải** phiên bản tạo ra số trong paper.

Theo quy tắc đã ghi trước, cả hai biến thể đều đạt nên **chọn `paper`**. Biến thể này cũng có độ lệch giữa các run nhỏ nhất (0,82, so với 2,16 và 2,68) và gần sd của paper (1,3) nhất.

**Protocol chính từ đây:** `--data_transform paper`. Notebook đã đặt sẵn `TRAIN_TRANSFORM = "paper"`.

## 5. Kiểm cache đặc trưng tập test trên GPU (2026-09-18, T4)

PromptFL, 1 run, 5 round, cùng seed, chạy hai lần: tắt và bật `--cache_test_feats`.

| Dataset | Đường cong accuracy | Giống hệt? | Giây/round tắt cache | Giây/round bật cache | Nhanh hơn | Bộ nhớ cache |
|---|---|---|---|---|---|---|
| DTD | 22,75 → 35,93 | **Có** | 12,8 | 9,0 | −30% | 173 MB |
| Caltech101 | 83,85 → 88,15 | **Có** | 25,5 | 20,6 | −19% | 252 MB |
| OxfordPets | 69,91 → 85,99 | **Có** | 17,7 | 9,2 | −48% | 376 MB |

Cache dựng mất 6–12 giây một lần cho mỗi run.

Mức tiết kiệm tỉ lệ với cỡ tập test so với tập train: Pets có tập test lớn nhất và tập train nhỏ nhất nên lợi nhất, Caltech ngược lại.

**Ước lượng lượt chạy lại đầy đủ** (3 dataset × ZS-CLIP + PromptFL + FedOTP, 3 run, có cache): khoảng **4,5 giờ T4**, so với 5,9 giờ trước đây.

## 6. Tái lập chính thức: 3 dataset với protocol `paper` (chạy 2026-09-18, T4)

Dữ liệu: `3datasets/phase1_results.zip`, bản giải nén ở `3datasets/extracted/`, đường cong từng round của cả 18 run ở `3datasets/parsed_all.json`.

Cấu hình: `--data_transform paper`, `--cache_test_feats true`, 3 run với seed 0, 1, 2, 50 round, RN50, còn lại giữ nguyên mục 3 của `docs/phase1_plan.md`.

| Dataset | Phương pháp | Ta: best | Paper | Chênh | Dung sai | Đạt? | Ta: last | Ta: last10 | Tăng so với `default` | Phút GPU |
|---|---|---|---|---|---|---|---|---|---|---|
| DTD | ZS-CLIP | 41,78 | 41,7 | +0,08 | 0,5 | **Đạt** | – | – | – | 1,0 |
| DTD | PromptFL | 56,72 ± 0,91 | 57,6 ± 1,3 | −0,88 | 2,6 | **Đạt** | 56,21 | 55,61 | **+3,43** | 24,9 |
| DTD | FedOTP | 57,60 ± 1,44 | 58,0 ± 0,8 | −0,40 | 1,6 | **Đạt** | 57,35 | 56,71 | **+3,76** | 37,9 |
| Caltech101 | ZS-CLIP | 85,76 | 86,0 | −0,24 | 0,5 | **Đạt** | – | – | – | 0,5 |
| Caltech101 | PromptFL | 90,94 ± 0,29 | 91,5 ± 0,5 | −0,56 | 1,0 | **Đạt** | 90,22 | 90,28 | +0,76 | 56,1 |
| Caltech101 | FedOTP | 91,10 ± 0,57 | 91,8 ± 0,1 | −0,70 | 1,0 | **Đạt** | 90,82 | 90,72 | +0,81 | 96,1 |
| OxfordPets | ZS-CLIP | 85,69 | 85,7 | −0,01 | 0,5 | **Đạt** | – | – | – | 0,6 |
| OxfordPets | PromptFL | 89,08 ± 0,65 | 89,4 ± 0,5 | −0,32 | 1,0 | **Đạt** | 88,12 | 88,09 | +1,19 | 27,7 |
| OxfordPets | FedOTP | 88,69 ± 0,41 | 89,1 ± 0,1 | −0,41 | 1,0 | **Đạt** | 87,55 | 87,62 | +1,28 | 40,7 |

**9/9 ô đạt tiêu chí đã ghi trước.** Tổng 4,76 giờ T4, mọi run `rc=0`.

### Đọc kết quả

1. **Thứ tự hai phương pháp khớp paper ở cả ba dataset:** FedOTP > PromptFL trên DTD và Caltech, PromptFL > FedOTP trên Pets. Ở lượt `default` trước đây thứ tự cũng đã đúng, nhưng giờ đúng cả về mức.
2. **Còn một độ lệch âm nhỏ, có hệ thống:** cả 6 ô của PromptFL và FedOTP đều thấp hơn paper, từ −0,32 đến −0,88, trung bình −0,55. Không ô nào vượt dung sai, và độ lệch này khớp với điểm 13 của `docs/phase1_plan.md`: paper báo **cấu hình hyperparameter tốt nhất** trong số vài cấu hình dò được, còn ta chạy cấu hình mặc định (với FedOTP là γ = 1, nằm ngoài {0,7; 0,8; 0,9} mà họ dò). Không chỉnh gì để bù độ lệch này.
3. **Mức tăng nhờ `paper` transform lớn nhất trên DTD** (+3,4 và +3,8), nhỏ hơn nhiều trên Caltech và Pets (+0,8 đến +1,3). Khớp giải thích ở mục 2: DTD phụ thuộc màu sắc và kết cấu nhiều nhất nên chịu thiệt nhiều nhất khi train không chuẩn hoá ảnh.
4. **Phương sai giữa run đổi theo hướng đáng chú ý.** Trên DTD, PromptFL giảm hẳn (2,68 xuống 0,91), nhưng FedOTP lại tăng (0,41 lên 1,44, lớn hơn cả sd 0,8 của paper). Với 8 ảnh/lớp cho cả liên đoàn, 3 run là ít. Ở giai đoạn 2 phải so ghép cặp theo seed, và nếu hiệu ứng nhỏ hơn sd thì tăng số seed chứ không kết luận.
5. **`best` vẫn cao hơn `last10` từ 0,4 đến 1,1 điểm**, giảm so với lượt `default` (0,7–1,6) nhưng không mất. Giữ kỷ luật báo cả ba chỉ số.

### Vai trò của lượt này ở giai đoạn 2

Đây là điểm **"nhiễu 0%"** để mọi so sánh sau đó dựa vào. Cụ thể:
- seed 0, 1, 2 là bộ seed bắt buộc dùng lại, để so ghép cặp từng run;
- `parsed_all.json` giữ đường cong từng round, nên so được cả hình dạng hội tụ, không chỉ con số cuối;
- ZS-CLIP là sàn (41,78 / 85,76 / 85,69): một phương pháp chống nhiễu mà tụt xuống dưới mức này thì vô nghĩa, vì bỏ hết prompt learning còn tốt hơn.

## 7. Trạng thái giai đoạn 1

Xong. Pipeline chạy được, số khớp paper trong dung sai đã ghi trước, có seed tường minh và cache đặc trưng tập test đã kiểm là không đổi kết quả. Việc tiếp theo thuộc giai đoạn 2: bộ tiêm nhiễu nhãn theo client, bảng vai trò client, và cổng Gate A.
