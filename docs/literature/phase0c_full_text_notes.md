# Giai đoạn 0c: đọc full text các bài chặn trước đó

Cập nhật: 2026-09-18. PDF gốc ở `refs/`.

Ba bài trước đây chỉ đọc được abstract, nay đã đọc đủ:

1. FLIP bản NeurIPS 2025 camera-ready (Liao, Gao, Xu — University of Macau / SIAT).
2. RFedLR — "Towards Robust Parameter-Efficient Fine-Tuning for Federated Learning", NeurIPS 2025 (Fang & Ye, Wuhan University).
3. FedDR-LoRA — "Decoupled Low-Rank Adaptation for Robust Federated Fine-Tuning", ICML 2026, PMLR 306 (Fang, Yang & Ye, cùng nhóm).

Còn chờ: FedPN (IEEE TBD), noisy data-based attack (FGCS), zkCor (ICDE), FedMGP+ (TPAMI), multi-stage group-wise (J. Supercomputing).

## 1. FLIP camera-ready: ảnh hưởng tới giai đoạn 1

**Mốc số không đổi.** Table 1 của bản camera-ready giống hệt bản arXiv v1 mà ta đang dùng: ZS-CLIP Caltech 86,0 / DTD 41,7 / Pets 85,7; PromptFL 91,5 ± 0,5 / 57,6 ± 1,3 / 89,4 ± 0,5; FedOTP 91,8 ± 0,1 / 58,0 ± 0,8 / 89,1 ± 0,1. Không phải sửa tiêu chí tái lập.

Bảng ViT-B/16 là **Table 13** trong bản camera-ready (trước ta ghi Table 12): PromptFL 95,5 ± 0,1 / 59,6 ± 0,7 / 92,4 ± 0,2.

**Appendix B.4 xác nhận chẩn đoán transform.** Nguyên văn quy trình xử lý ảnh: resize 240 × 240, crop 224 × 224, lật ngang, **và chuẩn hoá**. Đúng biến thể `paper` mà ta đã chọn sau thí nghiệm chẩn đoán. Kết luận "code public không phải phiên bản sinh ra số trong paper" giờ dựa trên chính bản chính thức của bài, không chỉ bản arXiv.

**Điểm mới, quan trọng cho tái lập: paper báo cấu hình hyperparameter tốt nhất.** Appendix B.4.2 + Table 9: mỗi thuật toán được dò một số giá trị rồi "report the averaged results of 3 experimental runs under the best hyperparameter configuration". Với FedOTP, họ dò γ ∈ {0,7; 0,8; 0,9} (khối lượng của unbalanced OT).

Trong code FLIP, γ chính là `self.top_percent` trong `flcore/models/clip/FedOTP.py:27`, **đặt cứng bằng 1** và không có cờ dòng lệnh. Nghĩa là:
- Lần chạy của ta dùng γ = 1 (OT cân bằng), tức là **ngoài cả ba giá trị paper dò**.
- Một phần độ lệch còn lại của FedOTP có thể do đây, chứ không phải lỗi cài đặt.
- Nếu cần, thêm cờ `--otp_gamma` rồi chạy 3 giá trị trên DTD là kiểm được. Chi phí khoảng 1,8 giờ T4. Chưa cần cho giai đoạn 1: FedOTP không phải phương pháp trung tâm của đồ án.

Thêm nữa, "báo cấu hình tốt nhất trong nhiều cấu hình, chọn theo tập test" là **một lớp thiên lệch chọn lọc nữa** cộng vào chỉ số `best_acc` (max qua các round). Ghi vào luận văn, và giữ nguyên kỷ luật báo thêm `last` và `last10_mean`.

**Chi tiết setting khớp với những gì ta đã đọc từ code:** 8 ảnh mỗi lớp rồi mới chia Dirichlet α = 0,1 (16 ảnh/lớp cho kịch bản partial participation); FedOTP ở benchmark global được sửa để truyền cả prompt cục bộ; AMP; cluster A100.

Few-shot trong paper là kịch bản riêng: lấy IID **K ảnh mỗi lớp cho từng client** (không phải cho cả liên đoàn), chạy trên Tiny-ImageNet với k ∈ {1, 2, 4, 8, 16}. Dùng làm mẫu cho phần quét số shot ở giai đoạn 2.

**Lợi ích lớn nhất: mục Limitations của chính bài benchmark mở đường cho đề tài của ta.** Họ viết rằng chưa hiểu prompt learning có rủi ro an toàn cao hay thấp hơn FL thường, và rằng cần nghiên cứu thêm về độ bền của FPL trước các client đối kháng gây hại cho quá trình FL "through manipulated local data or corrupted model updates". Đây là câu trích dẫn mạnh nhất có thể có cho phần mở đầu: chính tác giả benchmark đặt tên cho khoảng trống mà ta định làm, và "manipulated local data" phủ đúng cả nhiễu nhãn lẫn tấn công.

## 2. RFedLR (NeurIPS 2025)

| Mục | Nội dung |
|---|---|
| Bài toán | Federated PEFT (LoRA) với nhãn nhiễu |
| Backbone | ViT-B/16 pretrain ImageNet-21K. **Không dùng CLIP, không có text encoder** |
| Dữ liệu | CIFAR-100, 5 client, Dirichlet β = 0,5, 40 round, ảnh 224 |
| Nhiễu | pairflip và symflip, µ ∈ {0,2; 0,4}, tỉ lệ khác nhau giữa các client |
| Chỉ số | accuracy trung bình của **model cục bộ** (không phải model toàn cục) |
| Phương pháp | (a) SRT: chỉ cập nhật tham số "nhạy nhiễu" — nhạy = độ lệch gradient giữa tập proxy sạch và bản nhiễu của nó, giữ top τ = 0,2; (b) AFLA: chọn một trong hai ma trận A/B để train theo điểm importance = Fisher / (độ nhạy nhiễu), rồi gộp có trọng số |
| Giả định mạnh | **Cần một tập proxy sạch trên server** (mini-batch 256 ảnh) gửi cho mọi client |
| Kết quả | pairflip 0,4: 67,08 so với RoLoRA 56,93. So với FedCorr / RHFL / FedFixer đã chuyển sang PEFT: 67,08 so với 55,82 / 57,44 / 55,61 |

**Trùng với đề tài của ta:** thấp. Không CLIP, không prompt learning, không few-shot, không client độc hại, không tham chiếu zero-shot. Bài này khẳng định "we first study and address robust federated PEFT in the presence of label noise" — phạm vi là PEFT/LoRA, không phải prompt learning trên VLM, nên không đụng vào tuyên bố của ta.

**Dùng được gì:** quy ước nhiễu (pairflip/symflip, µ ∈ {0,2; 0,4}, tỉ lệ lệch nhau giữa client) để đặt giao thức giai đoạn 2 cho khớp thông lệ; danh sách baseline FL-nhiễu đã port sang PEFT (FedCorr, RHFL, FedFixer); và một điểm để phản biện: họ phải mượn dữ liệu sạch từ server, còn ta có CLIP zero-shot làm tham chiếu sạch **miễn phí**, không cần dữ liệu ngoài. Đó là lập luận thẳng cho tín hiệu ngữ nghĩa của ta.

## 3. FedDR-LoRA (ICML 2026)

| Mục | Nội dung |
|---|---|
| Bài toán | Như RFedLR, nhưng bỏ giả định proxy sạch |
| Backbone | ViT 12 lớp, ImageNet-21K. CIFAR-100, Tiny-ImageNet, 20 Newsgroups (RoBERTa) |
| Cấu hình | 10 client, β = 0,5, 40 round, LoRA r = 4, SGD |
| Phát hiện lõi | **Bất đối xứng độ bền của LoRA**: ma trận xuống A gần như không đổi giữa train sạch và train nhiễu (cosine ≈ 0,99), ma trận lên B lệch mạnh (≈ 0,75 trên ViT, ≈ 0,47 trên RoBERTa). Có chứng minh: nhiễu tác động lên A chỉ qua phép chiếu Bᵀδg nên bị giới hạn trong không gian hạng r |
| Phương pháp | Hai nhánh dùng chung A: nhánh sạch Bᶜ và nhánh nhiễu Bⁿ. Warm-up chia mẫu theo phân vị loss; sau đó chia mẫu theo **hiệu loss giữa hai nhánh, làm trơn bằng EMA**; cuối cùng negative learning: nhánh sạch dạy soft target cho mẫu nhiễu, đồng thời tối đa hoá KL so với nhánh nhiễu. Gộp riêng Bᶜ và Bⁿ, giữ A cục bộ |
| Kết quả | pairflip 0,4: 88,30 so với RFedLR 63,06. Nhiễu phụ thuộc mẫu: 88,23. Tỉ lệ nhiễu khác nhau giữa client {0,1 … 0,5}: 88,33 |
| Kỷ luật đo | Ablation có 3 seed (0, 1, 42) với mean ± sd, đặt ở phụ lục D.3 |

**Rủi ro novelty, cần nhớ.** Ý "tách một nhánh sạch và một nhánh nhiễu, chia mẫu theo hiệu loss giữa hai nhánh" là đóng góp chính của bài này. Trong prompt learning, FedOTP và FedPGP đã có sẵn hai bộ prompt (global + local), nên thiết kế kiểu "một prompt sạch, một prompt nhiễu" sẽ là **bản port gần như trực tiếp của FedDR-LoRA sang prompt**, và sẽ bị hỏi ngay ở phần novelty. **Không chọn hướng đó làm phương pháp chính.**

Ba phần vẫn còn nguyên giá trị riêng, vì cả hai bài Wuhan đều không có text encoder và không có client độc hại:
- Tính hợp lý về ngữ nghĩa lấy từ text encoder của CLIP (họ không có).
- Tín hiệu phản ứng khi được yêu cầu sửa nhãn (họ không xét client cố ý).
- Tách client nhiễu với client độc hại, và tấn công giả làm nhiễu.

**Dùng được gì:**
- Baseline mạnh nhất hiện có cho phần "nhiễu" của ta, nhưng phải port sang prompt learning, và phải nói rõ là ta port.
- Thủ thuật "clean probability = sigmoid(hiệu loss) rồi EMA" là baseline mức mẫu rất rẻ, đáng chạy để so với tín hiệu ngữ nghĩa của ta.
- Bộ kịch bản nhiễu đầy đủ để bắt chước ở giai đoạn 2: pairflip, symflip, **nhiễu phụ thuộc mẫu** (theo Xia et al. 2020), **tỉ lệ nhiễu khác nhau giữa các client** (theo FedCorr), và non-IID nặng β = 0,1.
- Dấu hiệu rằng nhiễu pairflip khó hơn symflip rất nhiều ở mọi phương pháp. Giai đoạn 2 phải có cả hai, và nên kỳ vọng dư địa lớn hơn ở pairflip.

## 4. Kết luận về mức trùng lặp

Ước lượng cũ (~50–55%) giữ nguyên. Hai bài Wuhan là đối thủ gần nhất về **bài toán** (FL + PEFT + nhãn nhiễu) nhưng khác hẳn về **thiết lập**: LoRA trên ViT ImageNet-21K với CIFAR-100 đủ dữ liệu, chỉ số là accuracy cục bộ; còn ta là prompt trên CLIP đóng băng, few-shot 8 ảnh/lớp, chỉ số là accuracy toàn cục, và có thêm trục client độc hại.

Tuyên bố an toàn để viết trong luận văn: chưa có bài nào nghiên cứu nhãn nhiễu trong **federated prompt learning trên mô hình thị giác–ngôn ngữ**, cũng chưa có bài nào tách client nhiễu với client độc hại trong bối cảnh đó. Vẫn **không** được viết "đầu tiên tách client nhiễu và client độc hại trong FL" (xem `phase0b_noisy_vs_malicious_review.md`), và **không** được viết "đầu tiên làm FL + PEFT + nhãn nhiễu" (RFedLR đã nhận).

## 5. Ba bài tải thêm ngày 2026-09-18

### FedPN — "Toward Federated Learning Against Noisy Clients via CLIP-Guided Prototypes" (IEEE TBD 2025)

Đây là bài từng lo nhất, vì nó nhận "bài đầu tiên dùng CLIP cho FL nhiễu nhãn". Đọc xong thì mức trùng **thấp hơn dự đoán**.

| Mục | FedPN | Đồ án này |
|---|---|---|
| Mô hình được huấn luyện | ResNet/CNN thường, train từ đầu | **Chính CLIP**, chỉ học prompt |
| CLIP dùng làm gì | encoder ảnh đóng băng để tính prototype mỗi lớp | encoder ảnh **và** encoder văn bản |
| Text encoder | **không dùng** | là nguồn tín hiệu ngữ nghĩa chính |
| Few-shot | không | 8 ảnh/lớp cho cả liên đoàn |
| Client độc hại | **không** | có |
| Dataset | MNIST, CIFAR, Clothing1M, AGNews | DTD, Caltech101, OxfordPets |

Cách họ phát hiện client nhiễu: đo độ chính xác của **prototype toàn cục** trên dữ liệu cục bộ, dưới ngưỡng γ = 0,5 thì coi là client nhiễu, rồi gán lại nhãn. Đáng chú ý: họ cũng **giữ client nhiễu và sửa nhãn**, không loại bỏ — trùng đúng kết luận Gate A của ta, và là bằng chứng độc lập cho lựa chọn đó.

**Dùng được ngay:** bộ phát hiện của FedPN là baseline công bằng nhất cho phần phát hiện của ta (cùng dùng CLIP, rẻ, đã công bố). Và vì nó chấm client theo *độ chính xác*, nó **không thể** phân biệt client nhiễu với client độc hại — cả hai đều cho điểm thấp. Đó chính là giả thuyết H1, giờ kiểm được trên một bộ phát hiện thật thay vì một bộ rơm.

**Trích dẫn quan trọng:** mục hạn chế của chính họ viết rằng FedPN không xử lý client đối kháng hay Byzantine, nơi kẻ tấn công có thể "inject targeted noise", và gợi ý ghép thêm gộp model bền vững kiểu Krum hoặc median. Đúng khoảng trống Gate B đang đo.

**Không được viết:** "đầu tiên dùng CLIP cho FL nhiễu nhãn" — FedPN đã nhận.

### zkCor — "Label Noise Correction for FL: A Secure, Efficient and Reliable Realization" (ICDE 2024)

Bài mật mã, không phải bài học máy: phần ML là FedCorr giữ nguyên, đóng góp là zero-knowledge proof để client **chứng minh** mình tính đúng bước phát hiện nhiễu. Không có CLIP, không prompt, không báo độ chính xác (chỉ báo thời gian chứng minh).

Giá trị với ta là một câu trích: họ viết rằng các giải pháp sửa nhãn hiện có đều giả định mọi client đều thành thật và **không xét việc phát hiện client độc hại**. Đó là phát biểu bài toán của ta, do một bài ICDE nói hộ.

Và một điểm phân biệt sắc: ZKP chứng minh **tính đúng của phép tính** trên dữ liệu đã cam kết, **không** chứng minh dữ liệu trung thực. Một client độc hại vẫn có thể cam kết dữ liệu đã đầu độc rồi chứng minh thật thà mọi phép tính trên đó. Nên hướng mật mã ép tuân thủ, còn hướng của ta là **phát hiện sự không tuân thủ bằng thống kê** — bổ sung cho nhau, không cạnh tranh.

### FedMGP+ — "Robust Personalized Federated Continual Learning via Explainable Multi-Granularity Prompt" (TPAMI 2026)

Prompt + client độc hại, nên là bài dễ đụng novelty nhất. Kết luận: **không đụng**.

- Backbone là ViT ImageNet-21K, **không phải CLIP**, không có encoder văn bản.
- Bài toán là federated **continual** learning có cá nhân hoá, dữ liệu CIFAR-100 / ImageNet-R / CUB-200.
- **Không có nhiễu nhãn** ở đâu cả.
- "Client độc hại" của họ là client có dữ liệu lấy ngẫu nhiên từ toàn bộ dataset, tức lệch phân phối — không phải tấn công có mục tiêu, càng không phải tấn công giả làm nhiễu.
- Phòng thủ PSPF cần **dữ liệu thay thế sạch trên server** (20 ảnh/lớp với CIFAR-100), lọc theo độ nhất quán đặc trưng. Lại thêm một bài nữa phải mượn dữ liệu sạch từ server, giống RFedLR. Ràng buộc "không dùng dữ liệu sạch phía server" của ta càng đáng giữ.

**Dùng được ngay — cặp chỉ số của họ:** Attack Detection Rate (phần cập nhật độc hại bị chặn) và Mis-classification Rate (phần cập nhật lành bị chặn nhầm). Hình 7 cho thấy ngưỡng chặt (τ = 0,05–0,1) chặn gần hết tấn công nhưng đánh nhầm rất nhiều client lành. Ta nên dùng đúng cặp chỉ số này cho tiêu chí B3, và **thêm hạng mục thứ ba** mà họ không có: tỉ lệ client **nhiễu nhưng thật thà** bị loại nhầm. Chính hạng mục thứ ba là đóng góp của đồ án.
