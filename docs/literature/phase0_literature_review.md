# Literature review, giai đoạn 0: Federated prompt learning trên CLIP, few-shot, client nhiễu nhãn

- Ngày tạo: 2026-09-17
- Loại review: scoping review kèm kiểm tra novelty có giao thức (không phải systematic review đầy đủ, xem mục 7)
- Cửa sổ tìm kiếm: 2021-01-01 đến 2026-09-17
- Nguồn: arXiv API, OpenAlex (boolean trên title + abstract), OpenAlex forward citation, Semantic Scholar forward citation (một phần), 20 truy vấn web search
- Dữ liệu thô và script: `thesis_direction/phase0_raw/` (`search.py`, `snowball.py`, `s2_snowball.py`, các file JSON kết quả)

---

## 0. Kết luận

**Chưa tìm thấy bài nào làm đúng tổ hợp**: prompt learning trên VLM đóng băng (kiểu CoOp/PromptFL) trong federated learning, dữ liệu few-shot, có client nhiễu nhãn, và coi nhiễu nhãn là bài toán chính. Độ tin cậy của kết luận này: **trung bình**. "Không tìm thấy" không có nghĩa "không tồn tại" (giới hạn ở mục 7).

Nhưng khoảng trống **hẹp**, bị kẹp giữa bốn nhánh đã có người làm:

1. **FL nhiễu nhãn có dùng CLIP.** FedPN (IEEE TBD, 11/2025) tự nhận là "framework đầu tiên dùng CLIP cho federated noisy label learning". Bài closed access, mới đọc được abstract. Đây là bài phải đọc full text đầu tiên.
2. **Federated PEFT dưới nhiễu nhãn.** RFedLR (NeurIPS 2025) và FedDR-LoRA (ICML 2026) đều của nhóm Mang Ye (ĐH Vũ Hán). Cả hai dùng LoRA, dữ liệu đầy đủ, không phải prompt trên CLIP. Cùng nhóm này có bài empirical study về federated prompt learning (IJCAI 2025). **Đây là nguy cơ bị trùng lớn nhất**: họ đã có cả hai mảnh ghép.
3. **Noisy-label prompt learning tập trung (không FL).** Rất đông, ít nhất 14 phương pháp 2024–2026 (JoAPR, DeFT, NLPrompt, CRoF, TrustCLIP, VisPrompt, DSPT...). Các kỹ thuật lọc/sửa nhãn từng mẫu gần như đã có đủ. Nếu chỉ "federated hoá" một trong số đó thì sẽ bị đánh giá là incremental.
4. **Độ bền của federated prompt learning trước client xấu.** Đã có SABRE-FL (ICLR 2026) và BadPromptFL cho backdoor, FedAPT (ACM MM 2025) cho adversarial, FOCoOp (ICML 2025) cho OOD. Nhiễu nhãn thì chưa. SABRE-FL lọc prompt update bằng anomaly detector trong không gian embedding của CLIP, **rất gần ý tưởng "phát hiện client nhiễu từ prompt"** đã đề xuất trước đó.

**Bằng chứng mâu thuẫn cần lưu ý:** bài ICCV 2023 kết luận prompt tuning *bền* với nhiễu nhãn. Các bài 2025–2026 (TrustCLIP, VisPrompt, DSPT) lại mở đầu bằng khẳng định prompt tuning *rất dễ tổn thương*. Dư địa thật sự phụ thuộc vào mức nhiễu, số shot và dataset, nên **bắt buộc phải đo ở giai đoạn 2** trước khi thiết kế phương pháp.

**Đánh giá cho đồ án:** đủ mới về setting để làm đồ án tốt nghiệp. Muốn thành paper thì đóng góp phải nằm ở chỗ không trùng bốn nhánh trên. Mục 6 liệt kê các khoảng trống cụ thể.

---

## 1. Câu hỏi nghiên cứu

Khung kỹ thuật:

| Thành phần | Nội dung |
|---|---|
| Hệ thống | Federated learning, client có ít dữ liệu (few-shot), một phần client có nhãn nhiễu, phân phối non-IID |
| Phương pháp | Prompt learning / PEFT trên VLM đóng băng (CLIP) |
| Mốc so sánh | Các phương pháp federated prompt learning (PromptFL, FedOTP, FedPGP...), noisy-label prompt learning tập trung, FL nhiễu nhãn truyền thống |
| Chỉ số | Accuracy toàn cục / cá nhân hoá, base-to-novel, độ chính xác phát hiện client/mẫu nhiễu |

- **RQ1 (novelty):** Đã có bài nào nghiên cứu federated prompt learning hoặc federated PEFT trên VLM dưới nhiễu nhãn chưa?
- **RQ2 (bản đồ):** Ba nhánh liên quan (federated prompt learning, noisy-label prompt learning, FL nhiễu nhãn) đang ở đâu?
- **RQ3 (khoảng trống):** Khoảng trống cụ thể nào còn lại, và mức rủi ro trùng của từng cái?

## 2. Giao thức tìm kiếm

**Tiêu chí "trúng novelty"**, phải thoả cả bốn điều kiện:
- (a) FL / decentralized;
- (b) VLM tiền huấn luyện (CLIP hoặc tương tự) được thích nghi bằng prompt hoặc PEFT;
- (c) nhiễu nhãn ở client là yếu tố được nghiên cứu;
- (d) bài toán phân loại ảnh.

**Tiêu chí "gần" (đưa vào bảng đe doạ):** thoả (a) và (c), cộng một phần của (b) (backbone tiền huấn luyện hoặc PEFT), hoặc thoả (a) và (b) với một dạng "client xấu" khác nhiễu nhãn.

**Loại trừ:**
- "noise" theo nghĩa differential privacy;
- "noise memorization" trong lý thuyết feature learning;
- nhiễu adversarial trên ảnh;
- OOD thuần tuý;
- NLP/LLM, trừ khi là federated PEFT dưới nhiễu nhãn.

Các bài bị loại vì các lý do này nhưng liên quan vẫn được ghi là "lân cận".

**Ngôn ngữ:** tiếng Anh. **Loại tài liệu:** bài peer-reviewed và preprint (preprint được ghi rõ).

**Chuỗi truy vấn:** xem mục 8 và `phase0_raw/search_log.json`.

## 3. Luồng sàng lọc

| Bước | Số lượng |
|---|---:|
| Kết quả thô từ arXiv + OpenAlex (8 truy vấn × 2 nguồn) | 609 |
| Sau dedup theo tiêu đề chuẩn hoá | 409 (loại 200 trùng) |
| Nhóm lõi novelty N1–N5 (unique) | 38 |
| Nhóm lõi sau sàng lọc title/abstract: bài "gần" | 3 (FedPN, OvA-LP, Local K-Similarity) |
| Nhóm lõi thoả đủ tiêu chí novelty | **0** |
| M1 federated prompt learning (unique) | 87, trong đó **0** bài nghiên cứu nhiễu nhãn |
| M2 noisy-label prompt/VLM tập trung (unique) | 35, khoảng 16 bài đúng chủ đề |
| M3 FL nhiễu nhãn (unique) | 272. Lọc từ khoá VLM/PEFT được 9 bài, còn 3 bài liên quan thật (trùng nhóm lõi) |
| Snowball OpenAlex: 14 bài gốc (2 không resolve được) | 14 bản ghi trích dẫn khớp bộ lọc, **0** bài trúng mới |
| Snowball Semantic Scholar | PromptFL: 243 bài trích dẫn, **0** bài nhắc nhiễu nhãn. Các bài gốc khác chưa chạy xong vì bị rate limit |
| Web search (20 truy vấn) | Tìm thêm RFedLR, FedDR-LoRA, SABRE-FL, BadPromptFL, FNBench, DSPT, VisPrompt, FedRG, FedCova. **0** bài trúng |

Lưu ý: RFedLR và FedDR-LoRA **không** hiện trong truy vấn cơ sở dữ liệu, chỉ tìm được qua web search. Độ phủ (recall) của truy vấn database vì thế không đầy đủ (mục 7).

---

## 4. Bảng bằng chứng

### 4.1 Các bài gần nhất (bảng đe doạ novelty)

Ký hiệu: Có / Không / ? (chưa xác minh được).

| Bài | Nơi đăng | FL | VLM | Prompt / PEFT | Few-shot | Nhiễu nhãn | Khác hướng đề xuất ở đâu |
|---|---|---|---|---|---|---|---|
| **FedPN**: Toward FL Against Noisy Clients via CLIP-Guided Prototypes (Tan et al.) | IEEE Trans. Big Data, 2025. DOI 10.1109/TBDATA.2025.3630997 | Có | Có (CLIP) | "Prototype Adapter" dựa attention; chưa rõ model cuối là CLIP hay CNN | ? | Có (IID/non-IID, nhiễu dị biệt) | CLIP dùng để lọc mẫu cho "local model training". Theo abstract không phải prompt learning, không nhắc few-shot. **Closed access, cần đọc full text** |
| **RFedLR**: Towards Robust PEFT for FL (Fang, Ye) | NeurIPS 2025. Code: github.com/FangXiuwen/RFedLR | Có | Không (ViT-B/16 ImageNet) | LoRA | Không (CIFAR-100 đầy đủ) | Có (symmetric, pairflip) | Chỉnh LoRA nhạy nhiễu, gộp LoRA theo độ ổn định. Không CLIP, không prompt, không few-shot |
| **FedDR-LoRA**: Decoupled Low-Rank Adaptation for Robust Federated Fine-Tuning (Fang, Yang, Ye) | ICML 2026 | Có | ? | LoRA hai nhánh (clean/noisy) | Không | Có (≤40%, sym/pairflip) | Chi tiết backbone lấy từ nguồn thứ cấp, **chưa xác minh**. Cùng nhóm với RFedLR |
| **OvA-LP** (Park et al.) | arXiv 2511.05028 (preprint) | Có | Encoder đóng băng | Linear probe + one-vs-all head | Không | Có (phụ) | Mục tiêu chính là non-IID drift, nhiễu nhãn chỉ là thí nghiệm phụ |
| **Local K-Similarity Constraint** (Amgain et al.) | arXiv 2511.06169; bản y tế ở ISBI 2026 | Có | Không (SSL pretrained) | Không | Không | Có | Dùng không gian biểu diễn của model SSL để regularize client, model cuối train thường |
| **SABRE-FL** (Khan et al.) | ICLR 2026, arXiv 2506.22506 | Có | Có (CLIP) | Prompt | ? | Không (backdoor) | **Tiền lệ phương pháp**: server lọc prompt update bất thường bằng detector trong không gian embedding CLIP (train offline trên dữ liệu OOD) |
| **BadPromptFL** (Zhang et al.) | arXiv 2508.08040 (preprint) | Có | Có | Prompt | ? | Không (backdoor) | Tấn công, không phòng thủ nhiễu nhãn |
| **FedCoPL**: Cooperative Pseudo Labeling for Unsupervised Federated Classification (Guo et al.) | ICCV 2025 | Có | Có (CLIP) | Prompt (gộp một phần) | Không nhãn | Ngầm (nhãn giả từ zero-shot) | Không có nhãn thật. Xử lý mất cân bằng nhãn giả, không mô hình hoá nhãn người gán sai |
| **CaFPT**: Explore and Cure (context-aware federated prompt tuning) | IEEE TMC 2024 | Có | Có (CLIP) | Prompt | Data-efficient | Không (theo abstract) | Cho thấy federated prompting "nhạy với dữ liệu", nên chọn mẫu hiệu quả. Không nhắm nhãn sai |
| **FOCoOp** (Liao et al.) | ICML 2025 | Có | Có | Prompt | Có | Không (OOD) | Độ bền OOD |
| **FedAPT**: Federated Adversarial Prompt Tuning (Zhai et al.) | ACM MM 2025 | Có | Có | Prompt | ? | Không (adversarial) | Độ bền adversarial |
| **PromptGate** | arXiv 2603.07163 (preprint) | Có | Có (BiomedCLIP) | Prompt | Active learning | Không (OOD trong pool chưa gán nhãn) | Lọc OOD trước khi truy vấn nhãn |

### 4.2 Bản đồ federated prompt learning trên VLM

Ghi chú: nơi đăng có dấu (*) là theo hiểu biết chung, chưa đối chiếu trong phiên này; các nơi đăng khác đã xác minh qua arXiv comment, DOI hoặc trang hội nghị.

| Chủ đề | Bài tiêu biểu | Có xét nhiễu nhãn? |
|---|---|---|
| Nền tảng | PromptFL (arXiv 2208.11625), FedCLIP (IEEE Data Eng. Bull., arXiv 2302.13485) | Không |
| Tổng quát hoá và cá nhân hoá | pFedPrompt (WWW 2023*), FedOTP (CVPR 2024*, arXiv 2403.00041), FedPGP (ICML 2024*, arXiv 2405.09771), FedTPG (ICLR 2024*, arXiv 2310.06123), pFedMoAP (ICLR 2025), FedMGP (arXiv 2511.00480), FedMVP (ICCV 2025), DP2FL (arXiv 2504.16357), SDFed (arXiv 2602.08590) | Không |
| Domain shift / domain generalization | Federated Adaptive Prompt Tuning (arXiv 2211.07864), FedDEAP (arXiv 2510.18837), Domain-specific Soft Prompts (arXiv 2509.20807), Token-level Prompt Mixture (arXiv 2504.21063) | Không |
| Long-tail, multi-label | CAPT (arXiv 2503.06993), FedMPT (CVPR 2026) | Không |
| Privacy | Subspace-Decomposed Expert (ACM MM 2026, arXiv 2607.21417), PPFPL | Không (chỉ nhiễu DP) |
| An toàn / độ bền | SABRE-FL (ICLR 2026), BadPromptFL, FedAPT (ACM MM 2025), FOCoOp (ICML 2025), calibration (arXiv 2512.04305) | Không |
| Một vòng / không huấn luyện | TOFA (AAAI 2026) | Không |
| Lý thuyết | PromptFolio (arXiv 2409.19610) | Không ("noise memorization" là khái niệm lý thuyết, không phải nhãn) |
| Benchmark / empirical | FLIP (arXiv 2503.22263: 8 phương pháp, 12 dataset, 6 kịch bản, **code mở** github.com/0-ml/flip), Empirical Study of FPL (IJCAI 2025: label skew, domain shift) | **Không.** Abstract FLIP không nhắc nhiễu; bài IJCAI 2025 không có từ "noise" |

### 4.3 Noisy-label prompt learning / fine-tune VLM, tập trung (không FL)

| Bài | Nơi đăng | Kỹ thuật chính |
|---|---|---|
| Why Is Prompt Tuning for VLMs Robust to Noisy Labels? (Wu et al.) | ICCV 2023 | Phân tích: text encoder áp cấu trúc lên class embedding nên bền với nhiễu |
| JoAPR | CVPR 2024* | Phân vùng thích nghi và tinh chỉnh nhãn |
| Screening, Rectifying, Re-Screening | IJCAI 2024 | Chia mẫu sạch / mơ hồ / nhiễu bằng prompt hai mức, kiểm chéo bằng VLM phụ |
| DeFT: VLMs are Strong Noisy Label Detectors | NeurIPS 2024 | Prompt dương/âm cho mỗi lớp làm ngưỡng học được |
| NLPrompt | arXiv 2412.01256 (CVPR 2025*) | MAE loss, lọc bằng optimal transport |
| CRoF | arXiv 2412.12793 | Few-shot + nhiễu; sinh prompt phân biệt, gán nhiều nhãn mềm |
| Robust-CLIP | IJCNN 2025 | Chọn mẫu sạch + SemiLoRA |
| TrustCLIP | ACM MM 2025 | Dùng zero-shot CLIP xác minh nhãn, chiếu gradient |
| Adaptive VL Prompt Learners | JVCIR 2025 | (không có abstract) |
| AnomalyNLP | 2025 | Few-shot anomaly detection có nhiễu nhãn |
| Noise-aware few-shot, bi-directional multi-view prompt alignment | arXiv 2603.11617 | Few-shot + nhiễu, căn chỉnh đa góc nhìn |
| VisPrompt: Seeing is Believing | arXiv 2604.09532 | Tiêm ngữ nghĩa ảnh vào prompt |
| DSPT: Intrinsic Gradient Suppression | arXiv 2605.00591 | Double-softmax chặn gradient mẫu lỗi lớn, không siêu tham số |
| NLPP | LNCS 2026 | Hai giai đoạn nâng chất lượng nhãn |
| Entanglement-Aware Sample Selection | LNCS 2026 | Chọn mẫu |
| Delora (LLM, không phải VLM) | ACL 2025 | Hai LoRA sạch/nhiễu làm bộ phát hiện |

### 4.4 FL nhiễu nhãn (nền, chủ yếu train từ đầu)

| Nhóm | Bài |
|---|---|
| Nhiều giai đoạn, phát hiện client nhiễu + sửa nhãn | FedCorr (CVPR 2022), FedNoRo (IJCAI 2023), FedELC (CIKM 2024), MaskedOptim (arXiv 2506.02079), FedProLN (ICASSP 2026), FedSNC (Neurocomputing 2026) |
| Regularization / biểu diễn | FLR (arXiv 2402.05353), FedRG (arXiv 2603.19722), FedCova (arXiv 2603.04062), FedSRCP (APNOMS 2025) |
| Client dị biệt | RHFL (CVPR 2022), RHFL+ data corruption (ICCV 2023) |
| Cắt client | ClipFL (ACM TOMPECS, arXiv 2411.07391) |
| Benchmark | FedNoisy (arXiv 2306.11650), FNBench (arXiv 2505.06684, đang revise ở IEEE TDSC: 18 phương pháp, không có VLM) |
| Có dùng mô hình tiền huấn luyện | FedPN, RFedLR, FedDR-LoRA, OvA-LP, Local K-Similarity (mục 4.1) |

---

## 5. Tổng hợp theo chủ đề

### 5.1 Federated prompt learning chưa đụng tới nhiễu nhãn
- **Độ tin cậy cao** cho phát biểu "các phương pháp và benchmark chính của federated prompt learning không xét nhiễu nhãn". Căn cứ:
  - Đã đọc abstract của các phương pháp chủ lực.
  - Hai công trình đánh giá tổng hợp (FLIP, empirical study IJCAI 2025) đều không có kịch bản nhiễu.
  - Snowball 243 bài trích dẫn PromptFL không có bài nào nhắc nhiễu nhãn.
- Các hướng "độ bền" đã có đều nhắm client có ác ý (backdoor, adversarial) hoặc dữ liệu lạ (OOD), không nhắm client *vô tình* gán nhãn sai.

### 5.2 Noisy-label prompt learning tập trung: đông, và mâu thuẫn về mức độ nghiêm trọng
- **Mâu thuẫn:**
  - ICCV 2023 cho rằng prompt tuning bền với nhiễu, vì text encoder cố định cấu trúc class embedding.
  - Từ 2024 trở đi nhiều bài khẳng định ngược lại: TrustCLIP "highly vulnerable", DSPT "highly sensitive", VisPrompt "prompt itself is highly susceptible".
  - Cách hoà giải khả dĩ: mức độ phụ thuộc vào tỉ lệ nhiễu, loại nhiễu, số shot và dataset. **Chưa có bài nào đo điều này trong FL**, nơi non-IID có thể khuếch đại hoặc làm loãng tác động.
- **Bộ công cụ đã bão hoà:**
  - dùng zero-shot CLIP xác minh nhãn (TrustCLIP, DeFT, Screening–Rectifying);
  - loss bền (NLPrompt);
  - chặn gradient (DSPT);
  - chọn mẫu (JoAPR, NLPP).
  - Hệ quả: ý tưởng "lọc nhãn từng mẫu bằng đồng thuận với zero-shot" đề xuất trước đó **không mới** ở mức mẫu, chỉ có thể mới ở cách phối hợp giữa các client.

### 5.3 FL nhiễu nhãn đang chuyển sang mô hình tiền huấn luyện
- 2025–2026 xuất hiện một cụm bài đưa backbone tiền huấn luyện hoặc PEFT vào FL nhiễu nhãn: FedPN, RFedLR, FedDR-LoRA, OvA-LP, Local K-Similarity.
- Nhóm Mang Ye có chuỗi RHFL (2022), RHFL+ (2023), RFedLR (2025), FedDR-LoRA (2026), cùng empirical study FPL (2025). Bước tự nhiên tiếp theo của họ chính là federated prompt learning dưới nhiễu nhãn. **Rủi ro bị trùng: cao**, nên phải làm nhanh và chọn góc riêng.

### 5.4 Phát hiện client xấu từ prompt update đã có tiền lệ
- SABRE-FL chứng minh prompt update mang đủ tín hiệu để server phân biệt client backdoor mà không cần dữ liệu client.
- Chưa thấy ai dùng tín hiệu này cho **mức nhiễu nhãn** (tín hiệu yếu hơn, liên tục, không nhị phân), hay dùng hình học của bộ phân loại text (C×d) thay cho detector train trên dữ liệu OOD.

---

## 6. Khoảng trống còn lại

| # | Khoảng trống | Gần nhất đã có | Độ mới | Rủi ro trùng | Vai trò trong đồ án |
|---|---|---|---|---|---|
| G1 | **Nghiên cứu thực nghiệm**: federated prompt learning dưới nhiễu nhãn (sym / pairflip / nhiễu thật như Food-101N) × non-IID × số shot × prompt ngôn ngữ / thị giác. Kết luận "prompt tuning bền với nhiễu" (ICCV 2023) có còn đúng trong FL không? | Empirical study IJCAI 2025 (không nhiễu), FNBench (không VLM), FLIP (không nhiễu) | Cao về setting | Trung bình–cao (nhóm Mang Ye) | **Nền móng.** Trùng luôn với việc đo dư địa ở giai đoạn 2, và tự nó đã là một chương đồ án |
| G2 | **Server phát hiện client nhiễu từ prompt update**, không cần proxy set hay tập validation sạch (dùng hình học bộ phân loại text, so với mốc zero-shot) | FedSNC (cần proxy set), ClipFL (cần validation sạch), SABRE-FL (backdoor, detector train trên dữ liệu OOD) | Trung bình–cao | Trung bình | Phương pháp, phần 1 |
| G3 | **Xung đột giữa cá nhân hoá và nhiễu**: FedOTP, FedPGP, pFedMoAP giữ prompt cục bộ, nên prompt cục bộ dễ học thuộc nhiễu của chính client đó. Nên cá nhân hoá bao nhiêu theo mức nhiễu ước lượng? | Không tìm thấy | Cao | Thấp–trung bình | Phương pháp, phần 2 |
| G4 | **Nhiễu nhãn làm hỏng tổng quát hoá sang lớp chưa thấy** (base-to-novel, kiểu FedTPG) | Không tìm thấy trong FL | Trung bình | Thấp | Thí nghiệm mở rộng |
| G5 | **Nhiễu pairflip giữa các lớp giống nhau về ngữ nghĩa**, nơi chính zero-shot CLIP cũng nhầm, khiến các bộ lọc dựa trên CLIP thất bại | Các bài tập trung chủ yếu thử symmetric + nhiễu thật | Trung bình | Thấp | Nối tiếp nhấn mạnh pairflip của FedSNC |

**Đề xuất:** làm G1 trước (2–3 tháng đầu, trùng với giai đoạn 1–2), rồi chọn G2 + G3 làm phương pháp. Không chọn "federated hoá TrustCLIP/NLPrompt" làm đóng góp chính, vì hướng đó incremental.

**Thay đổi so với kế hoạch trước:**
- Pipeline nên dựng trên **FLIP** (github.com/0-ml/flip: 8 phương pháp FPL, 12 dataset đã cài sẵn) thay vì repo PromptFL gốc.
- Ý tưởng 2 cũ ("lọc nhãn bằng đồng thuận zero-shot") hạ xuống thành baseline.
- Ý tưởng 3 cũ ("gộp prompt theo mức nhiễu") là kỹ thuật chuẩn của FL nhiễu nhãn, chỉ nên là một thành phần phụ.

---

## 7. Giới hạn của review này

1. **arXiv API không ổn định**: cùng một truy vấn lúc trả 1 kết quả, lúc trả 0. Kết quả arXiv chỉ mang tính bổ sung.
2. **Truy vấn database bỏ sót**: OpenAlex và arXiv không bắt được RFedLR, FedDR-LoRA (NeurIPS 2025, ICML 2026). Nhiều bản ghi OpenAlex thiếu abstract nên lọc từ khoá bị hụt.
3. **Semantic Scholar bị rate limit**: mới xong snowball cho PromptFL. Các bài gốc còn lại (FedOTP, NLPrompt, CoOp...) chưa có kết quả. Chạy lại `phase0_raw/s2_snowball.py` khi có API key.
4. **Chưa đọc full text**: FedPN (closed access), FedDR-LoRA (OpenReview chặn truy cập tự động). Thông tin backbone của FedDR-LoRA lấy từ nguồn thứ cấp.
5. **Không thấy được bài chưa công bố**: bài đã nộp NeurIPS 2026, ICLR 2027 hay đã nhận nhưng chưa lên mạng.
6. **Chỉ tiếng Anh**: không tra tạp chí tiếng Trung.
7. **Nơi đăng có dấu (*)** chưa đối chiếu trực tiếp trong phiên này.

## 8. Nhật ký tìm kiếm

### 8.1 Database (chạy 2026-09-17, từ 2021-01-01)

| ID | Database | Truy vấn | Kết quả |
|---|---|---|---:|
| N1 | arXiv | `all:federated AND all:prompt AND (all:noisy OR all:"label noise" OR all:"noisy labels")` | 0 |
| N1 | OpenAlex | `federated AND prompt AND (noisy OR "label noise")` | 6 |
| N2 | arXiv | `all:federated AND (all:CLIP OR all:"vision-language" OR all:"vision language") AND (all:"noisy label" OR all:"noisy labels" OR all:"label noise")` | 0 |
| N2 | OpenAlex | `federated AND (CLIP OR "vision-language" OR "vision language") AND ("noisy label" OR "noisy labels" OR "label noise")` | 5 |
| N3 | arXiv | `all:federated AND (all:LoRA OR all:adapter OR all:"parameter-efficient" OR all:PEFT) AND (all:"noisy label" OR all:"noisy labels" OR all:"label noise" OR all:"noisy data")` | 16 |
| N3 | OpenAlex | `federated AND (LoRA OR adapter OR "parameter-efficient" OR PEFT) AND ("noisy label" OR "noisy labels" OR "label noise" OR "noisy data")` | 6 |
| N4 | arXiv | `all:federated AND (all:"foundation model" OR all:"pre-trained" OR all:pretrained) AND (all:"noisy label" OR all:"noisy labels" OR all:"label noise")` | 2 |
| N4 | OpenAlex | `federated AND ("foundation model" OR "pre-trained" OR pretrained) AND ("noisy label" OR "noisy labels" OR "label noise")` | 13 |
| N5 | arXiv | `all:federated AND (all:"few-shot" OR all:"few shot") AND (all:noisy OR all:"label noise")` | 0 |
| N5 | OpenAlex | `federated AND ("few-shot" OR "few shot") AND (noisy OR "label noise")` | 3 |
| M1 | arXiv | `all:federated AND (all:prompt OR all:prompts) AND (all:CLIP OR all:"vision-language" OR all:"vision language")` | 44 |
| M1 | OpenAlex | `federated AND prompt AND (CLIP OR "vision-language" OR "vision language")` | 109 |
| M2 | arXiv | `(all:prompt OR all:"prompt tuning" OR all:"prompt learning") AND (all:CLIP OR all:"vision-language") AND (all:"noisy label" OR all:"noisy labels" OR all:"label noise")` | 16 |
| M2 | OpenAlex | `prompt AND (CLIP OR "vision-language") AND ("noisy label" OR "noisy labels" OR "label noise")` | 46 |
| M3 | arXiv | `ti:federated AND ti:noisy` | 37 |
| M3 | OpenAlex | `federated AND ("noisy label" OR "noisy labels" OR "label noise" OR "noisy clients")` | 306 |

### 8.2 Forward citation

| Nguồn | Bài gốc | Bộ lọc trên bài trích dẫn | Khớp |
|---|---|---|---:|
| OpenAlex | FedOTP, FedPGP, pFedPrompt, FedCLIP (PromptFL, FedTPG không resolve được) | nhiễu | 2 bản ghi, cùng là ProFiMed; "noise-resilient" ở đây nói về căn chỉnh vision–text, không phải nhiễu nhãn |
| OpenAlex | FedPN (không lọc) | | 2 (FedSC: backdoor; FedEG: fairness), không liên quan |
| OpenAlex | PTRobust (ICCV 2023), NLPrompt, JoAPR, CRoF | federated | 0 |
| OpenAlex | FedCorr, FedNoRo, FedNoisy | prompt / CLIP / VLM / pretrained / PEFT | 10 bản ghi (7 bài). Liên quan: FedPN, Local K-Similarity. Không liên quan: FedProLN ("pre-train" là tự train bộ phân loại), FedRnd ("LogitClip"), FedStitch (ghép block pretrained, không nhiễu), "Free lunch" remote sensing PEFT (không có abstract, tiêu đề không nhắc nhiễu) |
| Semantic Scholar | PromptFL (243 bài trích dẫn) | nhiễu nhãn | 0 |
| Semantic Scholar | 17 bài gốc còn lại | | chưa xong (rate limit) |

### 8.3 Web search (2026-09-17)

1. federated prompt learning CLIP noisy labels few-shot
2. "federated" prompt tuning vision-language model "label noise" clients arXiv 2025 2026
3. federated learning CLIP noisy labels clients prompt label correction
4. federated prompt learning benchmark codebase github PromptFL FedOTP FedPGP
5. "FedPN" CLIP-guided prototypes federated noisy clients
6. "federated prompt tuning" "noisy labels"
7. "noisy clients" "prompt learning" vision-language federated
8. federated parameter-efficient fine-tuning foundation model "label noise" LoRA adapter robust 2025
9. Xiuwen Fang Mang Ye federated noisy labels vision-language prompt 2025 2026
10. site:arxiv.org federated prompt learning vision-language models noisy labels robust
11. federated CLIP adapter "noisy labels" clients zero-shot label correction
12. "federated" "visual prompt tuning" OR "prompt tuning" "label noise" CVPR 2026 OR AAAI 2026 OR ICLR 2026
13. Wenke Huang Mang Ye federated noisy label vision-language model prompt
14. federated prompt learning CLIP poisoning OR "label flipping" OR backdoor attack defense
15. "federated" "vision-language" "noisy labels" few-shot personalized prompt clients 2026
16. "federated learning" "noisy labels" "pre-trained vision-language" OR "CLIP" label-noise-robust aggregation arXiv 2026
17. "Prototype Adapter" CLIP federated noisy labels FedPN github OR arXiv
18. "Context-aware Federated Prompt Tuning" CaFPT noisy samples label noise experiments
19. "Decoupled Low-Rank Adaptation for Robust Federated Fine-Tuning" arXiv
20. federated learning distinguish noisy clients from Byzantine malicious clients 2025 (phiên trước, cho hướng dự phòng)

---

## 9. Việc tiếp theo

1. **Đọc full text theo thứ tự:**
   1. FedPN: lấy qua thư viện HUST / IEEE Xplore.
   2. FedDR-LoRA, RFedLR.
   3. SABRE-FL.
   4. Empirical Study of FPL (IJCAI 2025), FLIP.
   5. TrustCLIP, NLPrompt, DSPT, ICCV 2023.
2. **Theo dõi đối thủ:**
   - đặt Google Scholar alert cho "federated prompt" + "noisy labels";
   - theo dõi trang tác giả Xiuwen Fang, Mang Ye;
   - chạy lại `phase0_raw/search.py` mỗi tháng.
3. **Giai đoạn 1:** clone FLIP, tái lập PromptFL và FedOTP trên 2–3 dataset.
4. **Giai đoạn 2 (= G1):** đo dư địa. Chạy lưới nhiễu × shot × non-IID, 3 seed, có ORACLE và zero-shot, với tiêu chí dừng ghi trước.

## 10. Tài liệu tham khảo (đã xác minh ID)

- FedPN: Tan Z. et al., "Toward Federated Learning Against Noisy Clients via CLIP-Guided Prototypes", IEEE TBD, 2025. https://doi.org/10.1109/TBDATA.2025.3630997
- RFedLR: Fang X., Ye M., "Towards Robust Parameter-Efficient Fine-Tuning for Federated Learning", NeurIPS 2025. https://neurips.cc/virtual/2025/loc/san-diego/poster/119736 ; https://github.com/FangXiuwen/RFedLR
- FedDR-LoRA: Fang X., Yang X., Ye M., "Decoupled Low-Rank Adaptation for Robust Federated Fine-Tuning", ICML 2026. https://openreview.net/forum?id=eNcIILpv8F
- Empirical Study of FPL: Wang Z. et al., IJCAI 2025. arXiv:2505.23024
- FLIP: Liao et al., preprint. arXiv:2503.22263 ; https://github.com/0-ml/flip
- SABRE-FL: Khan M. A. et al., ICLR 2026. arXiv:2506.22506
- BadPromptFL: Zhang et al., preprint. arXiv:2508.08040
- FedAPT: Zhai et al., ACM MM 2025. arXiv:2509.06992
- FOCoOp: Liao et al., ICML 2025. arXiv:2506.16218
- FedCoPL: Guo et al., ICCV 2025. arXiv:2510.10100
- CaFPT: "Explore and Cure", IEEE TMC 2024. https://doi.org/10.1109/TMC.2024.3439864
- OvA-LP: Park et al., preprint. arXiv:2511.05028
- Local K-Similarity: Amgain et al., preprint. arXiv:2511.06169 ; ISBI 2026 https://doi.org/10.1109/ISBI61048.2026.11515355
- PromptFL: Guo et al. arXiv:2208.11625
- FedCLIP: Lu et al., IEEE Data Eng. Bull. arXiv:2302.13485
- FedOTP: Li et al. arXiv:2403.00041
- FedPGP: Cui et al. arXiv:2405.09771
- FedTPG: Qiu et al. arXiv:2310.06123
- pFedMoAP: Luo et al., ICLR 2025. arXiv:2410.10114
- FedMVP: Singha et al., ICCV 2025. arXiv:2504.20860
- FedMPT: Wang X. et al., CVPR 2026. arXiv:2605.28347
- TOFA: Zhang et al., AAAI 2026. arXiv:2511.16423
- CAPT: Hou et al., preprint. arXiv:2503.06993
- FedMGP: Bo et al., preprint. arXiv:2511.00480
- Subspace-Decomposed Expert FPT: Wang et al., ACM MM 2026. arXiv:2607.21417
- Federated CLIP calibration: Singha et al., preprint. arXiv:2512.04305
- PromptFolio: Pan et al. arXiv:2409.19610
- PromptGate: preprint. arXiv:2603.07163
- Why Is Prompt Tuning for VLMs Robust to Noisy Labels?: Wu et al., ICCV 2023. arXiv:2307.11978
- DeFT: Wei T. et al., NeurIPS 2024. arXiv:2409.19696
- NLPrompt: Pan B. et al. arXiv:2412.01256
- CRoF: Deng et al. arXiv:2412.12793
- Screening, Rectifying, Re-Screening: IJCAI 2024. https://doi.org/10.24963/ijcai.2024/568
- Robust-CLIP: IJCNN 2025. https://doi.org/10.1109/IJCNN64981.2025.11227884
- TrustCLIP: ACM MM 2025. https://doi.org/10.1145/3746027.3755415
- VisPrompt: Geng et al., preprint. arXiv:2604.09532
- DSPT: Li J. et al., preprint. arXiv:2605.00591
- Noise-aware few-shot multi-view prompt alignment: Niu et al., preprint. arXiv:2603.11617
- Delora: Yuan B. et al., ACL 2025. arXiv:2510.10208
- FedCorr: Xu et al., CVPR 2022. arXiv:2204.04677
- FedNoRo: Wu et al., IJCAI 2023. arXiv:2305.05230
- FedELC: Jiang X. et al., CIKM 2024. arXiv:2408.04301
- MaskedOptim: Jiang X. et al., preprint. arXiv:2506.02079
- FNBench: Jiang X. et al., preprint (IEEE TDSC major revision). arXiv:2505.06684
- FedNoisy: Liang et al. arXiv:2306.11650
- FLR: Kim et al. arXiv:2402.05353
- FedRG: Wen T. et al. arXiv:2603.19722
- FedCova: Zhong X. et al., preprint. arXiv:2603.04062
- FedProLN: ICASSP 2026. https://doi.org/10.1109/ICASSP55912.2026.11461755
- ClipFL: Morafah M. et al., ACM TOMPECS. arXiv:2411.07391
- RHFL: Fang X., Ye M., CVPR 2022.
