# Giai đoạn 1: dựng pipeline trên FLIP và tái lập baseline

Cập nhật: 2026-09-17

## 1. Mục tiêu

Có một pipeline chạy được, cho ra số khớp với bài FLIP, **trước khi** thêm nhiễu nhãn và client độc hại. Nếu baseline không khớp paper thì mọi so sánh ở giai đoạn 2 đều không đáng tin.

Phạm vi:
- 3 dataset: Caltech101, DTD, OxfordPets;
- 3 phương pháp: ZS-CLIP, PromptFL (CoOp + FedAvg), FedOTP;
- backbone RN50 (setting chính của paper).

## 2. Trạng thái

| Việc | Trạng thái |
|---|---|
| Clone FLIP `0-ml/flip` @ `ec3a848` (NeurIPS 2025 D&B) | Xong |
| Đọc code: luồng dữ liệu, client, server, cách lấy kết quả | Xong (mục 5, 6) |
| Vá lỗi thiếu `clip.py`, thêm chế độ chạy CPU | Xong (`docs/flip_patches.md`) |
| Smoke test trên CPU, dữ liệu giả 6 lớp: ZS-CLIP, PromptFL, FedOTP chạy hết 2 round, ghi `results/*.json` | **Đạt** |
| Notebook Kaggle: tải dữ liệu, chạy, so với paper | Đã chạy 3 dataset (2026-09-17) |
| Tái lập số trên dữ liệu thật | **ZS-CLIP đạt cả 3. PromptFL và FedOTP trượt cả 6 ô, thấp hơn paper 1,3–4,3 điểm, cùng một chiều.** Chi tiết: `results/Phase1/phase1_results.md` |
| Chẩn đoán train transform (`default_norm` / `paper`) trên DTD | **Xong (2026-09-18): cả hai đạt. `paper` 57,51 ± 0,82 (chênh −0,09), `default_norm` 57,03 ± 2,16. Nguyên nhân là code gốc không chuẩn hoá ảnh lúc train. Chọn `paper` làm protocol chính** |
| Seed tường minh cho từng run | **Xong (2026-09-18).** Run *r* dùng seed `args.seed + r`, gieo lại trước khi chọn few-shot, chia client và khởi tạo prompt. Kiểm trên CPU: cùng seed cho kết quả giống hệt, khác seed cho kết quả khác |
| Cache đặc trưng tập test | **Xong (2026-09-18).** `--cache_test_feats true`. Kiểm trên CPU: loss và accuracy từng round **giống hệt** bản không cache, cho cả PromptFL và FedOTP. Trên đường đi phát hiện thêm: tạo iterator DataLoader rút số từ RNG toàn cục, nên đã gán generator riêng cho từng loader |
| Chạy `verify_cache` trên GPU (5 round, có và không cache) | **Xong (2026-09-18): đường cong giống hệt ở cả 3 dataset. Nhanh hơn 19–48% mỗi round** |
| Chạy lại 3 dataset với `paper` (kiêm điểm "nhiễu 0%") | **Xong (2026-09-18): 9/9 ô đạt, 4,76 giờ T4.** Chi tiết: `results/Phase1/phase1_results.md` mục 6 |

**Giai đoạn 1 kết thúc.** Còn một độ lệch âm có hệ thống trung bình −0,55 điểm ở PromptFL và FedOTP, trong dung sai, giải thích ở điểm 13 dưới đây (paper báo cấu hình hyperparameter tốt nhất, ta chạy mặc định).

## 3. Setting tái lập

Theo README FLIP và Appendix B.4 của paper:
- 10 client, tham gia đầy đủ, Dirichlet α = 0,1;
- 8 ảnh mỗi lớp (tổng cho cả liên đoàn, xem mục 5.4);
- 50 round, 1 epoch cục bộ;
- SGD lr 0,002, momentum 0,9, cosine decay, batch 16;
- 4 token context, 1 prompt;
- AMP, 3 run.

**Mốc số** (FLIP Table 1; độ chính xác toàn cục %, trung bình ± sd qua 3 run). Đã đối chiếu bản arXiv:2503.22263v1 với bản NeurIPS 2025 camera-ready ngày 2026-09-18: **giống hệt nhau**, không phải sửa mốc.

| Dataset | ZS-CLIP | PromptFL | FedOTP |
|---|---|---|---|
| Caltech101 | 86,0 | 91,5 ± 0,5 | 91,8 ± 0,1 |
| DTD | 41,7 | 57,6 ± 1,3 | 58,0 ± 0,8 |
| OxfordPets | 85,7 | 89,4 ± 0,5 | 89,1 ± 0,1 |

Với ViT-B/16 (Table 13 của bản camera-ready, dùng sau nếu chuyển backbone):

| Dataset | ZS-CLIP | PromptFL | FedOTP |
|---|---|---|---|
| Caltech101 | 93,5 | 95,5 ± 0,1 | 95,6 ± 0,1 |
| DTD | 45,0 | 59,6 ± 0,7 | 60,6 ± 0,7 |
| OxfordPets | 89,2 | 92,4 ± 0,2 | 92,2 ± 0,5 |

## 4. Tiêu chí tái lập (ghi trước khi chạy)

- **PromptFL, FedOTP:** |trung bình `best_acc` của ta − số paper| ≤ max(1,0; 2 × sd của paper) điểm %.
- **ZS-CLIP:** |chênh lệch| ≤ 0,5 điểm % (không có tính ngẫu nhiên nên phải khớp gần tuyệt đối).
- **Không chỉnh hyperparameter để cho khớp số.** Nếu trượt, chẩn đoán theo thứ tự:
  1. **ZS-CLIP trượt** thì lỗi nằm ở loader CLIP dựng lại, tiền xử lý ảnh hoặc file split. Phải sửa trước mọi thứ khác.
  2. **PromptFL/FedOTP thấp hơn paper** thì nghi đầu tiên là bước train **không chuẩn hoá ảnh** (mục 5.2). Chạy lại PromptFL trên DTD với Normalize để kiểm.
  3. Khác phiên bản torch/numpy so với paper (paper dùng torch 2.1.0), và AMP.
  4. Cách gieo seed (mục 5.5).
- Ngoài `best_acc` còn báo `last` và `last10_mean` cho giai đoạn 2, nhưng **tiêu chí tái lập chỉ dùng `best_acc`**, vì đó là chỉ số paper báo.

## 5. Những điểm cần biết, phát hiện khi đọc code

1. **`flcore/models/clip/clip.py` rỗng trong repo public**, nên FLIP không chạy được ngay. Đã dựng lại từ loader OpenAI CLIP (MIT) và kiểm tra:
   - token của "a photo of a cat" khớp ID chuẩn;
   - trọng số RN50 qua kiểm SHA256;
   - image encoder trả `[1+HW, B, D]`, đúng như FedOTP dùng.
2. **Bước train không chuẩn hoá ảnh, bước test thì có** (`datasets/imageloader.py`, hàm `augment`: dòng `Normalize` bị comment ở nhánh train), trong khi Appendix B.4 viết là có normalize. Giữ nguyên để tái lập đúng code, và ghi lại làm nghi vấn số 1 nếu số bị thấp. **Đã xác nhận trên bản camera-ready (2026-09-18):** Appendix B.4 ghi resize 240×240, crop 224, lật ngang, có chuẩn hoá — đúng biến thể `paper`.
3. **Chỉ số paper là max độ chính xác test qua các round**, tức chọn trên tập test nên bị thiên lệch lên. Đây đúng là bài học từ FedSNC, nên ta báo thêm `last` và `last10_mean` (`tools/parse_flip_log.py`).
4. **"8-shot" là 8 ảnh/lớp cho toàn bộ liên đoàn**, rồi mới chia Dirichlet cho 10 client (Appendix B.2.2), không phải 8 ảnh/lớp mỗi client. Mỗi client có rất ít ảnh, và nhiều lớp vắng hẳn.
5. **Seed:**
   - `--times N` dùng chỉ số run (0..N-1) làm seed khi chia client.
   - Còn bước chọn tập few-shot dùng RNG toàn cục, được gieo một lần từ `--seed` và bị `split_dataset` gieo lại.
   - Hệ quả: các run trong cùng một tiến trình phụ thuộc thứ tự chạy. Để phân tích ghép cặp theo seed ở giai đoạn 2, cần thêm cơ chế seed tường minh cho mỗi run (việc tiếp theo, không làm trước khi tái lập xong).
6. **Server FedOTP khởi tạo client hai lần** (hàm `__init__` của FedAvg rồi của FedOTP):
   - tốn gấp đôi thời gian khởi tạo;
   - client thực sự được dùng là `ClientFedAvg`, nên prompt "cục bộ" cũng bị gộp. Điều này khớp mô tả của paper cho benchmark global ("allow all local prompt parameters to be communicated"), nhưng sẽ **sai** nếu sau này dùng benchmark personal.
7. **`trainloader.stats` (đếm số mẫu mỗi lớp của client) được tính trước bước chia client.** Khi thêm nhiễu nhãn phải tính lại, nếu không các loss `bce`/`lc` sẽ đọc được phân phối nhãn sạch. Với `ce` thì không dùng tới, nhưng vẫn phải sửa cho đúng.
8. `filter_states` sửa trực tiếp một list toàn cục, chỉ ảnh hưởng FedPGP.
9. Script mẫu trong README truyền `--eval_multi`, nhưng argparse không định nghĩa tham số này, nên phải bỏ đi.
10. Tên thư mục dữ liệu phải trùng khoá dataset: `caltech101/`, không phải `caltech-101/` như `docs/DATASETS.md` ghi.
11. `FedNPL.py` import module `neural_process` không tồn tại, nhưng không được dùng ở đâu.
12. **FLIP không có file LICENSE.** Giữ Kaggle dataset ở chế độ private. Nếu muốn công bố code đồ án, cần hỏi tác giả FLIP.
13. **Paper báo cấu hình hyperparameter tốt nhất, không phải cấu hình mặc định** (Appendix B.4.2 + Table 9 bản camera-ready): mỗi thuật toán được dò vài giá trị rồi báo trung bình 3 run của cấu hình tốt nhất. Với FedOTP họ dò γ ∈ {0,7; 0,8; 0,9} (khối lượng của unbalanced OT). Trong code γ chính là `self.top_percent` ở `flcore/models/clip/FedOTP.py:27`, **đặt cứng bằng 1** và không có cờ dòng lệnh, tức nằm ngoài cả ba giá trị họ dò. Đây có thể là một phần độ lệch còn lại của FedOTP. Muốn kiểm thì thêm cờ `--otp_gamma` và chạy 3 giá trị trên DTD, khoảng 1,8 giờ T4. Chưa cần: FedOTP không phải phương pháp trung tâm của đồ án.
14. Hệ quả của điểm 13: `best_acc` vừa là max qua các round, **vừa** là max qua các cấu hình hyperparameter. Hai lớp thiên lệch chọn lọc trên cùng một tập test. Ghi rõ trong luận văn và giữ kỷ luật báo thêm `last`, `last10_mean`.
15. Mục Limitations của bản camera-ready tự nêu hai khoảng trống: rủi ro an toàn của prompt learning so với FL thường, và độ bền của FPL trước client đối kháng phá hoại qua "manipulated local data or corrupted model updates". Trích dẫn này dùng cho phần mở đầu của luận văn: chính tác giả benchmark đặt tên cho khoảng trống của đề tài, và "manipulated local data" phủ cả nhiễu nhãn lẫn tấn công.

## 6. Điểm cắm cho giai đoạn 2 (đã xác định vị trí trong code)

| Thành phần | Chỗ sửa |
|---|---|
| Nhiễu nhãn theo client (symmetric, pairflip, theo ngữ nghĩa) | Sau `split_dataset` trong `datasets/imageloader.py::ImageLoader`: sửa `ImageSubset.samples`/`targets` của client được chọn, rồi tính lại `loader.stats` |
| Client độc hại (lật nhãn có mục tiêu, backdoor, giả làm nhiễu, phóng đại cập nhật) | Lớp con của `ClientFedAvg`, override `local_train`/`_step`; bảng ánh xạ client id → vai trò |
| Gộp model bền vững / phát hiện client | `server_base.receive_results` và `aggregate`; log prompt của từng client mỗi round để phân tích |
| Tín hiệu ngữ nghĩa từ prompt | `prompt_learner` + `text_encoder` sinh embedding text mỗi lớp cho từng client |
| Seed tường minh cho phân tích ghép cặp | `main.py` và `server_base.init_dataset` |

## 7. Việc cần bạn làm

1. Chạy `python tools/package_code.py`, rồi upload `dist/fpl-triage-code.zip` lên Kaggle thành **private dataset**.
2. Mở `kaggle/phase1_reproduce.ipynb` trên Kaggle: bật GPU và Internet, Add Data dataset vừa tạo.
3. Chạy tới hết **ô đo thời gian**, gửi lại số giây mỗi round để chốt ngân sách quota.
4. Chạy các ô còn lại (chia nhiều session bằng cách rút gọn `DATASETS`), rồi gửi file `phase1_summary.json` hoặc `phase1_results.zip`.
