# FedRG: ghi chú chuyển thể sang khung của mình

Ngày viết: 2026-10-31. Tài liệu này để đọc lại, không phải để báo cáo. Chưa viết code, đang chờ cô đồng ý.

- **Bài:** FedRG: Unleashing the Representation Geometry for Federated Learning with Noisy Clients (Wen và cộng sự, CVPR 2026).
- **Code chính thức:** `github.com/Tianjoker/FedRG`. Mình đã đọc: `FedRG/client.py`, `FedRG/manager.py`, `FedRG/server.py`, `conf/`, `loss/SymCE_loss.py`, `model/SemiFed.py`, `model/utils.py`, `README.md`.

Vị trí dòng ghi bên dưới là trong `FedRG/client.py`, trừ khi có ghi khác.

---

## 1. FedRG thực sự làm gì (theo code, không theo trí nhớ)

### Giai đoạn I: học đặc trưng bằng SimCLR
- Mỗi máy train một ResNet-18 từ đầu bằng SimCLR, không dùng nhãn.
- Server gộp phần encoder (`unsup_model`) của các máy.
- Theo README là 150 vòng. File config trong repo chỉ để 1 vòng, có vẻ là bản để thử.

### Giai đoạn II: soi nhãn sai và train chống nhiễu
Theo README là 350 vòng. Hàm chính là `finetune_train_VMF_ori` (dòng 596-857). Mỗi lô ảnh trải qua 4 bước.

**1. Lấy đặc trưng của 2 phiên bản ảnh.**
- Ảnh được biến đổi nhẹ (`X_train`) và biến đổi mạnh (`X_aug`).
- Encoder cho ra `h1` và `h2`, chuẩn hóa thành `z1` và `z2` nằm trên mặt cầu.
- Bộ phân loại đọc trên `h1`.

**2. Mô hình hình học (vMF) để gom cụm.** Đây là lõi của bài.
- Có L cụm, mỗi cụm có một tâm `MU`, một độ chụm `KAPPA` và một tỷ trọng `BETA`.
- Có thêm một **cụm nền** với tỷ trọng `PI0`, để hứng ảnh lạc.
- Mỗi ảnh thuộc về các cụm **theo xác suất**, không bị chia cứng vào một cụm. Softmax có chia nhiệt độ 2.0.
- Độ chụm của từng ảnh tính từ độ giống nhau giữa 2 phiên bản `z1` và `z2`, rồi chặn trong khoảng [0.2, 2] (`r_i`).
- Ma trận `M` (số lớp × L) cho biết mỗi cụm ứng với lớp nào.
- `P_clean` của một ảnh là tỷ lệ "cụm của ảnh có khớp với nhãn của nó không". Nhãn khớp cụm thì `P_clean` cao.

**3. Tách nhóm sạch/bẩn: GMM 2 nhóm trên từng lô ảnh** (dòng 745-765).
- GMM chạy trên giá trị `1 − P_clean` của các ảnh trong lô.
- Nhóm có trung bình thấp là "sạch". Ảnh có xác suất sạch ≥ 0.5 (`gmm_thread`) thì xếp vào nhóm sạch.
- **Lô nào cũng bị ép chia thành 2 nhóm**, kể cả lô toàn ảnh sạch.

**4. Loss** (dòng 767-778).
- `loss = 0.4 × SCE + 1.0 × loss_bẩn`.
- **SCE tính trên cả lô**, không chỉ nhóm sạch: `sce(logits, y_obs).mean()`. Đây là code thật, có thể khác cách bài viết mô tả. Mình theo code.
  - SCE = 0.1 × CE + 1.0 × RCE (`loss/SymCE_loss.py`).
- `loss_bẩn` là NLL của `p @ T`, chỉ tính trên nhóm bẩn.
  - `T` là ma trận nhiễu (số lớp × số lớp), khởi tạo bằng ma trận đơn vị (`model/SemiFed.py:19`).
  - `T` được học, và sau mỗi bước được chặn ≥ 1e-6 rồi chuẩn hóa để mỗi hàng có tổng bằng 1.
  - **`T` là riêng của từng máy:** server không gộp `T` (`finetune_agg_include_keys` = `classifier_head`, `unsup_model`).

**Cập nhật cụm.** Sau mỗi lô, tâm cụm, độ chụm, tỷ trọng và `M` được cập nhật trượt với hệ số 0.1 (`proto_momentum`).
- `M` chỉ học từ các ảnh trong nhóm sạch.
- `PI0` được chặn trong khoảng [0.001, 0.2].
- **Tâm cụm là riêng của từng máy:** nằm trong `self._sbrf_mix`, không nằm trong model, nên server không gộp. Tâm cụm khởi tạo ngẫu nhiên.

Trong giai đoạn II, encoder vẫn được train tiếp, cùng với bộ phân loại và `T`. Bộ tối ưu được viết cứng là SGD với lr 0.01, momentum 0.9, weight decay 5e-4, riêng `T` thì weight decay bằng 0.

**Khi test:** dùng bộ phân loại chung, không dùng `T`.

### Thiết lập thí nghiệm của họ
- CIFAR-10/100 và SVHN, ảnh 32×32.
- 10 máy, chia Dirichlet 0.1.
- Thí nghiệm chính: **mọi máy đều nhiễu 40%**, kiểu sym hoặc pair.
- Code có thêm chế độ `random`: khoảng 60% số máy bị nhiễu, mỗi máy nhiễu từ 50% trở lên (`manager.py:41-46`, giống FedCorr). README không nhắc tới chế độ này.
- Kích thước lô 64. Số cụm |G|: CIFAR-10 là 10, CIFAR-100 là 50, SVHN là 10.

---

## 2. Giữ nguyên, không sửa

Toàn bộ giai đoạn II, đúng như code, gồm các giá trị sau.

**Mô hình cụm (vMF):**
- `KAPPA` khởi tạo 5, chặn trong khoảng [0.5, 100];
- `PI0` khởi tạo 0.05, chặn trong khoảng [0.001, 0.2];
- `dp_alpha` 5, `dirichlet_smooth` 0.5, `proto_momentum` 0.1;
- nhiệt độ softmax 2.0, `r_i` chặn trong khoảng [0.2, 2].

**Tách nhóm và loss:**
- GMM 2 nhóm trên từng lô, ngưỡng 0.5;
- loss 0.4 × SCE (trên cả lô) + 1.0 × NLL qua `T` (trên nhóm bẩn); SCE với alpha 0.1, beta 1.

**Ma trận nhiễu `T`:**
- khởi tạo bằng ma trận đơn vị, riêng từng máy, không gộp;
- chặn ≥ 1e-6, chuẩn hóa theo hàng, weight decay 0.

**Tâm cụm:** riêng từng máy, không gộp.

**Khi test:** không dùng `T`.

---

## 3. Thay đổi bắt buộc

Mỗi thay đổi kèm lý do vì sao không giữ được bản gốc.

### 3.1. Mô hình: ResNet-18 từ đầu được thay bằng CLIP RN50 giữ nguyên, chỉ học prompt
- **Lý do:** muốn đo cách xử lý nhãn sai thì mọi baseline phải dùng chung mô hình. FedProx, FedCorr, NLPrompt và CLEAR đều chạy trên CLIP RN50 + prompt.
- **Cụ thể:**
  - `classifier_head` của họ ứng với bộ phân loại bằng prompt của mình: so ảnh với câu chữ.
  - `logits` là logits của CLIP + prompt.
  - `p = softmax(logits)`.
- **Hệ quả:** encoder không được train tiếp như ở giai đoạn II của họ. Cái được học chỉ còn prompt và `T`.

### 3.2. Bỏ giai đoạn I (SimCLR); đặc trưng ảnh lấy từ CLIP
- **Lý do:** SimCLR train từ đầu với khoảng 30 ảnh mỗi máy không học được. Kết quả khi đó sẽ chỉ đo việc có CLIP hay không.
- **Vì sao vẫn đúng tinh thần:** FedRG cần đặc trưng **không học từ nhãn nhiễu**. Đặc trưng ảnh của CLIP thỏa điều đó, vì CLIP được học sẵn từ trước và không bao giờ thấy nhãn của mình.
- **Cụ thể:** `z1` và `z2` là đặc trưng ảnh CLIP (1024 chiều), được chuẩn hóa. Của họ là 512 chiều.

### 3.3. Thêm phiên bản ảnh biến đổi mạnh `X_aug`
- **Lý do:** độ chụm của từng ảnh (`r_i`) cần 2 phiên bản của cùng một ảnh. Bộ nạp dữ liệu FLIP của mình chỉ trả 1 phiên bản.
- **Cụ thể:**
  - Phiên bản nhẹ là ảnh train bình thường của mình.
  - Phiên bản mạnh dùng đúng phép biến đổi mạnh trong code của họ (`data_preprocessing/randaugment.py` và `own_transforms.py`), chỉnh cho ảnh 224×224 thay vì 32×32.
  - Cả hai đều đi qua CLIP để lấy đặc trưng.
- **Chi phí:** mỗi lô phải chạy encoder CLIP 2 lần, nên chậm hơn PromptFL.

### 3.4. Tham số học của `T`
- Prompt dùng lr chung của mọi baseline: 0.002, SGD, cos (giữ khung chung).
- `T` dùng đúng cấu hình của họ: lr 0.01, momentum 0.9, weight decay 0, trong một nhóm tham số riêng.

### 3.5. Sửa một chỗ code gốc chỉ chạy được với 10 lớp
- `SCELoss` mặc định `num_classes=10`, và lúc gọi không truyền số lớp (dòng 610).
- Với 37 lớp trở lên, `one_hot(labels, 10)` sẽ báo lỗi.
- **Sửa:** truyền đúng số lớp của từng bộ dữ liệu. Đây là sửa lỗi, không đổi phương pháp.

---

## 4. Thông số bài không cho sẵn: chốt trước khi chạy

| Thông số | Bài gốc | Mình chọn | Lý do |
|---|---|---|---|
| Số cụm L (MNIST, EuroSAT) | 10 lớp → 10 cụm | 10 | giống CIFAR-10/SVHN |
| Số cụm L (Caltech, 100 lớp) | 100 lớp → 50 cụm | 50 | giống hệt CIFAR-100 |
| Số cụm L (Pets 37 lớp, DTD 47 lớp) | không có bộ cùng cỡ | 37 và 47 (bằng số lớp) | họ dùng số cụm bằng số lớp ở 2 trên 3 bộ; không tự chế công thức |
| Số vòng | 150 (I) + 350 (II) | 50 vòng, toàn bộ là giai đoạn II | giống mọi baseline; giai đoạn I đã bỏ |
| Kích thước lô | 64 | 16 | khung chung; mỗi máy chỉ vài chục ảnh |
| Số máy mỗi vòng | config chọn 2 trên 10 | cả 10 máy | khung chung FLIP, giống mọi baseline |
| Số epoch mỗi vòng | 1 | 1 | giống nhau |
| Nhiễu, chia dữ liệu, seed | của họ | của mình | cùng 11 setting và 5 seed như mọi baseline |

---

## 5. Rủi ro và những điều cần biết khi đọc kết quả

1. **Tâm cụm riêng từng máy, quá ít ảnh.**
   - Một máy Pets có khoảng 30 ảnh mà phải giữ 37 cụm, nên đa số cụm trống. Cụm nền và độ chụm bị chặn giúp code vẫn chạy được, nhưng phát hiện nhãn sai có thể yếu.
   - Nếu FedRG kém, phải ghi đúng nguyên nhân này. Không được chỉnh số cụm sau khi thấy kết quả.
2. **GMM trên lô nhỏ.**
   - Số ảnh mỗi máy, đo trên 5 seed của các lượt chạy cũ:

     | Bộ dữ liệu | Ảnh mỗi máy | Phần lớn máy |
     |---|---|---|
     | MNIST, EuroSAT | 5-12 | — |
     | Pets | 10-38 | 23-36 |
     | DTD | 22-47 | — |
     | Caltech | 53-95 | — |
   - Lô 16 chỉ là mức tối đa. Máy có ít hơn 16 ảnh dùng cả máy làm một lô. Trên MNIST và EuroSAT, mỗi vòng GMM chỉ chia đôi 5-12 giá trị.
   - **Lô cuối bị lẻ:** code không bỏ lô thiếu (`drop_last=False`).
     - Máy có 18 ảnh tạo lô 16 và lô 2. GMM trên 2 giá trị luôn chia 1 sạch, 1 bẩn.
     - Máy có 17 ảnh tạo lô 1, và code của họ **bỏ qua lô 1 ảnh** (`if bs==1: continue`), nên ảnh đó không được train trong vòng đó.
     - Mình giữ đúng như vậy và ghi chú lại. Không đổi kích thước lô riêng cho FedRG, vì mọi baseline dùng lô 16.
   - Chia đôi vài giá trị sẽ dao động mạnh giữa các lô.
   - Lô toàn ảnh sạch vẫn bị ép chia đôi. Ở các setting S có 7 máy sạch, điều này xảy ra thường xuyên.
   - Phần bị xếp nhầm vào nhóm bẩn được train qua `T`, khởi tạo bằng ma trận đơn vị, nên thiệt hại có thể nhỏ.
3. **Ma trận `T` của từng máy.** Mỗi máy chỉ có vài lớp, nhưng `T` có kích thước số lớp × số lớp (100 × 100 với Caltech). Phần lớn `T` không bao giờ được cập nhật. Việc này vô hại nhưng không giúp được gì.
4. **SCE trên cả lô.** Nhãn sai vẫn đi vào loss, với trọng số 0.4. Vì đây là code gốc nên mình giữ, và ghi chú lại trong bài.
5. **Kịch bản S** (3 máy nhiễu, hoặc 5 máy nhiễu với mức khác nhau): bài gốc chủ yếu thử kịch bản mọi máy nhiễu. Kết quả ở đây là phép thử mới, không phải lỗi của mình.

---

## 6. Trước khi chạy thật

- Viết code thành một arm mới trong `flip/` (ví dụ `--fedrg true`), dùng chung bộ khung.
- Viết `fedrg_plan.md`: chép mục 4 vào, ghi rõ không sửa sau khi chạy, và dự đoán trước kết quả.
- Chạy thử ở máy trên bộ dữ liệu nhỏ, giống các baseline trước. Kiểm tra:
  - chạy hết, không lỗi (rc 0);
  - `P_clean` có tách được nhãn sai không: đo AUROC với nhãn thật;
  - `T` có học không.
- Số lượt: 33 cho Pets/DTD/Caltech, thêm 22 nếu làm cả MNIST/EuroSAT.
