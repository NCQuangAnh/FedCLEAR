# Literature review, giai đoạn 0b: Tách client nhiễu nhãn và client độc hại trong federated prompt learning

- Ngày tạo: 2026-09-17
- Nối tiếp: `phase0_literature_review.md` (hướng C: federated prompt learning trên CLIP, few-shot, client nhiễu nhãn)
- Loại review: scoping review kèm kiểm tra novelty có giao thức
- Cửa sổ tìm kiếm: 2021-01-01 đến 2026-09-17 cho database; snowball và web search không giới hạn năm
- Nguồn: arXiv API và OpenAlex (5 truy vấn × 2 nguồn), OpenAlex forward citation (14 bài gốc), 16 truy vấn web search
- Dữ liệu thô và script: `phase0_raw/security/`, `phase0_raw/search_security.py`, `phase0_raw/snowball_security.py`
- **Cập nhật cùng ngày:** đã đọc full text MUD-HoG và Fed-RoSeC, đã kiểm "Cited by" trên Google Scholar + Semantic Scholar, đã tìm kiếm toàn văn trên Google Scholar. Xem **mục 11** ở cuối file.

---

## 0. Kết luận

### 0.1 Ý tưởng "tách ba loại client" KHÔNG mới ở FL nói chung

Các tiền lệ trực tiếp:

| Bài | Tách những loại nào | Khác hướng đề xuất ở đâu |
|---|---|---|
| **MUD-HoG** (ESORICS 2022) | Độc hại / không đáng tin nhưng lành tính / lành tính, và xử lý khác nhau. Còn tách được tấn công có mục tiêu với không mục tiêu | **Đã đọc full text (mục 11).** Client "không đáng tin" ở đây là **ảnh bị làm mờ** (50% ảnh) và chỉ train trên 30% dữ liệu, **không có nhãn sai**. Dùng lịch sử gradient ngắn hạn và dài hạn. MNIST / Fashion-MNIST, CNN train từ đầu, không có VLM, không xét backdoor |
| **Fed-RoSeC**: FL phát hiện mã độc dưới nhãn nhiễu và sybil độc hại (ĐH Palermo, ITASEC 2026) | Ba loại: trung thực / nhiễu (trung thực, nhãn sai hệ thống) / độc hại (sybil lật nhãn). Phân cụm khoảng cách giữa các cập nhật, cụm "trung gian" được coi là client nhiễu | **Đã đọc full text (mục 11).** Bài toán nhị phân trên dữ liệu bảng, không phải ảnh/VLM. Sau khi tách, client nhiễu và client độc hại **được xử lý giống nhau** (cả hai đều tự sửa nhãn bằng global model), tức là giả định kẻ tấn công *làm theo* giao thức sửa nhãn |
| **GShield** (arXiv 2025), **MineDetect** (arXiv 2025), **FedAS-TSAD** (BDDM 2025), **RADAR** (SRDS 2024) | Độc hại / kém chất lượng / cẩu thả | "Kém chất lượng" hiểu chung chung (cảm biến, ảnh xấu, dữ liệu thừa). Không có nhãn nhiễu theo mô hình chuẩn, không VLM |
| **zkCor** (ICDE 2024) | Sửa nhãn kiểu FedCorr, có tính tới client độc hại | Dùng zero-knowledge proof để **ép** client sửa nhãn trung thực (giải pháp mật mã), không phân loại client theo hành vi |
| **Crowdsourcing**: Identifying Unreliable and Adversarial Workers (JMLR 2017) | Người gán nhãn trung thực nhưng kém / người gán nhãn đối nghịch | Khái niệm y hệt, nhưng ở bài toán gom nhãn, không phải FL |

### 0.2 Chưa thấy trong federated prompt learning hay FL trên VLM

Mọi bài bảo mật tìm được trong mảng này **chỉ xét client độc hại**; không bài nào xét nhiễu nhãn, và không bài nào tách hai loại. Đã kiểm ở mức abstract, **và đã kiểm thêm danh sách "Cited by" trên Google Scholar + Semantic Scholar, cùng tìm kiếm toàn văn trên Google Scholar (mục 11.3)**:
- SABRE-FL (ICLR 2026)
- BadPromptFL (arXiv 2025; bản TCSVT 2026)
- FedMGP+ (TPAMI 2026)
- Privacy-Enhanced Federated Prompt Tuning Against Backdoor (IEEE TCC 2026)
- Byzantine-robust federated prompt tuning (Frontiers in CS 2026)
- SecFFT (IoTJ 2024)
- CLIP-Fed (arXiv 2025)
- Backdoor trong federated PEFT (ISC 2025, IoTJ 2026)

### 0.3 Nhầm lẫn giữa client nhiễu và client độc hại là vấn đề có thật

- **Noisy data-based attack** (FGCS 2025): kẻ tấn công biến dữ liệu thành "dữ liệu nhiễu" và **qua mặt được gần như mọi phòng thủ SOTA**. Phòng thủ của chính bài này lại coi client có dữ liệu nhiễu là độc hại, tức là nó không dành chỗ cho client nhiễu trung thực.
- **MUD-HoG** viết thẳng: client lành tính nhưng dữ liệu kém "có thể trông giống client độc hại".
- **Bucketing** (ICLR 2022): khi dữ liệu non-IID, các phòng thủ Byzantine hiện có bị qua mặt; dữ liệu khác biệt tự nhiên làm hỏng giả định của chúng.

### 0.4 Đối chiếu bốn tín hiệu đề xuất trước đó với tài liệu

| Tín hiệu | Đã có chưa | Tiền lệ |
|---|---|---|
| Nhất quán theo thời gian | **Đã có** | FLDetector (KDD 2022), MUD-HoG (ESORICS 2022), FedSCS (ICCST 2025) |
| Dấu hiệu đồng loã (cập nhật giống nhau) | **Đã có** | FoolsGold (arXiv 1808.04866; RAID 2020*) |
| Hình học theo từng lớp | **Có một phần** | LFighter (Neural Networks 2023) dùng gradient của lớp nguồn/đích ở tầng output. Phiên bản dùng *class text embedding sinh từ prompt* thì chưa thấy |
| **Nhầm lẫn có hợp lý về ngữ nghĩa không** (đo bằng độ tương đồng text của CLIP) | **Chưa thấy** | Có cơ sở thực nghiệm: CIFAR-100N (ICLR 2022) cho thấy người gán nhãn thường nhầm sang lớp tương tự. Chưa thấy ai dùng điều này để đoán *ý định* trong FL |
| **Phản ứng khi được yêu cầu sửa nhãn** (kiểm bằng hành vi) | **Chưa thấy** | Gần nhất là zkCor, nhưng dùng mật mã để ép tuân thủ chứ không quan sát hành vi. Fed-RoSeC (full text) còn **ngầm giả định** client độc hại làm theo bước sửa nhãn, nên tín hiệu này nhắm đúng lỗ hổng của nó |

\* chưa đối chiếu trực tiếp trong phiên này.

### 0.5 Sửa lại ước lượng độ trùng

Lần trước mình ước lượng **~45–50%**. Sau review này sửa thành **~50–55%**, vì khái niệm tách ba loại client và hai trong bốn tín hiệu đã có tiền lệ. **Vẫn nằm trong ngưỡng 50–60%** và vẫn có phần mới rõ ràng:
- setting: federated prompt learning trên VLM với nhiễu nhãn thật sự (không phải ảnh xấu);
- tín hiệu ngữ nghĩa lấy từ chính VLM;
- tín hiệu phản ứng khi sửa nhãn.

### 0.6 Hệ quả bắt buộc

- **Không được claim** "đầu tiên tách client nhiễu với client độc hại". Claim đúng: "đầu tiên trong federated prompt learning, và đầu tiên dùng tín hiệu ngữ nghĩa của VLM để phân biệt ý định".
- **MUD-HoG phải là baseline chính**, cùng FLDetector, FoolsGold và LFighter.
- Phải thử **tấn công giả làm nhiễu** (noisy data-based attack) như một kẻ tấn công thích nghi.

---

## 1. Câu hỏi nghiên cứu

- **RQ-S1:** Đã có bài nào tách client nhiễu nhãn (trung thực) với client độc hại trong FL chưa? Trong federated prompt learning / FL trên VLM thì sao?
- **RQ-S2:** Có bằng chứng các phòng thủ chống client độc hại loại nhầm client nhiễu trung thực, hoặc kẻ tấn công lợi dụng vỏ bọc "nhiễu" không?
- **RQ-S3:** Bản đồ tấn công và phòng thủ trong federated prompt learning, federated PEFT và FL trên VLM.
- **RQ-S4:** Bốn tín hiệu phân biệt đề xuất trước đó đã có tiền lệ chưa?

## 2. Giao thức và luồng sàng lọc

**Tiêu chí "trúng novelty":** thoả cả ba điều kiện
- (a) FL;
- (b) có cả client nhiễu nhãn trung thực lẫn client độc hại, và có cơ chế phân biệt hoặc xử lý khác nhau;
- (c) VLM với prompt hoặc PEFT.

**Tiêu chí "tiền lệ":** thoả (a) và (b), không cần (c).

**Loại trừ:**
- nhiễu differential privacy;
- tấn công suy luận / rò rỉ riêng tư (gradient inversion, privacy backdoor) khi không kèm poisoning;
- prompt injection của LLM.

| Bước | Số lượng |
|---|---:|
| Kết quả thô (5 truy vấn × arXiv + OpenAlex) | 1.056 |
| Sau dedup theo tiêu đề | 813 |
| S1 (FL + nhiễu nhãn + độc hại), unique | 27. Liên quan: 5 (Palermo 2026, zkCor, DWS, FedNoiL, luận án UofT). Trúng novelty: 0 |
| S2 (tấn công lật nhãn trong FL) + S4 (client không đáng tin vs độc hại), unique | 309 + 160. Lọc từ khoá được khoảng 50. Tiền lệ tách ba loại: MUD-HoG, GShield, MineDetect, FedAS-TSAD, RADAR, ARFL. Trúng novelty: 0 |
| S3 (tấn công trên FL prompt / PEFT / VLM), unique | 345. Lọc theo tiêu đề được 32. Liên quan đến poisoning/backdoor trên prompt, PEFT, VLM: khoảng 12. **Nhắc nhiễu nhãn: 0** |
| S5 (trust/reputation + nhiễu + tấn công) | 3, không có bài mới |
| Snowball OpenAlex: 14 bài gốc (FLAME không resolve được; SABRE-FL và BadPromptFL có 0 bài trích dẫn trong OpenAlex) | 69 bài trích dẫn unique khớp bộ lọc. Mới và liên quan: Noisy data-based attack (FGCS 2025), FedSCS (2025), KD for FL with Many Noisy Clients (2026, không có abstract), Data Poisoning to Crowdsourcing (WWW 2021) |
| Web search (16 truy vấn) | Thêm LFighter, "Label noise analysis meets adversarial training" (KBS 2023), MUD-HoG, CLIP-Fed, PEFTGuard, Federated Instruction Tuning backdoor (ICASSP 2026), FedChallenger, JMLR 2017 crowdsourcing, CIFAR-N |

---

## 3. Bảng bằng chứng

### 3.1 Tiền lệ phân biệt hoặc xử lý chung client kém chất lượng và client độc hại (FL thường)

| Bài | Nơi đăng | Loại "kém" | Cơ chế | Ghi chú |
|---|---|---|---|---|
| MUD-HoG: Long-Short History of Gradients | ESORICS 2022, arXiv 2208.10273 | Ảnh mờ / độ phân giải thấp | Lịch sử gradient ngắn hạn + dài hạn; tách ba loại; xử lý khác nhau; tách targeted / untargeted | **Tiền lệ gần nhất về khái niệm.** Có thử tấn công lật nhãn và lật nhiều nhãn |
| Fed-RoSeC: FL for Robust Malware Detection under Noisy Labels and Malicious Sybils | ITASEC & SERICS 2026, CEUR-WS Vol-4198 paper 5 | Nhãn nhiễu (ε từ 0 đến 0,9) | Khoảng cách DCFL giữa các cập nhật, lượng tử hoá 3 mức, phân cụm K-Modes, chấm điểm cụm + GMM 3 thành phần, dùng dấu của kurtosis để quyết định cụm nào trung thực; sau đó sửa nhãn thận trọng (GMM trên loss, FPR 5%) | **Tiền lệ gần nhất về nhãn nhiễu + độc hại.** Nhị phân, dữ liệu bảng, MLP. Đã đọc full text (mục 11.2) |
| zkCor | ICDE 2024, DOI 10.1109/ICDE60146.2024.00277 | Nhãn nhiễu | FedCorr + zero-knowledge proof ép sửa nhãn trung thực | Giải pháp mật mã |
| DWS Shapley | ICEAAI 2026 | Non-IID + nhãn nhiễu + độc hại | Điểm Shapley có ràng buộc Wasserstein | Không tách loại client, chỉ đánh trọng số |
| GShield | arXiv 2512.19286 | Kém chất lượng | Phân cụm + mô hình Gaussian cho gradient lành tính | |
| MineDetect | arXiv 2508.10212 | Dữ liệu cảm biến kém | Cơ chế theo lịch sử; tách bị tấn công / không đáng tin | |
| FedAS-TSAD | BDDM 2025 | Kém chất lượng | Vết ma trận Fisher + căn chỉnh tham số | Nói rõ mục tiêu là tách độc hại với kém chất lượng |
| RADAR | SRDS 2024 | Cẩu thả / độc hại | Client tự đánh giá + reputation + phân cụm | Thử bằng lật nhãn |
| ARFL: Auto-weighted Robust FL with Corrupted Data Sources | arXiv 2101.05880, DOI 10.1145/3517821 | Ngoại lai, nhãn sai hệ thống, đối nghịch | Học trọng số client theo loss | Không tách loại, chỉ hạ trọng số |
| FedSCS: Stable Cosine Similarity | ICCST 2025 | Client nhiễu + đối nghịch | Cosine + độ ổn định theo thời gian | Không tách loại |
| FedNoiL | arXiv 2205.10110 | Nhãn nhiễu | Lấy mẫu hai cấp | Nói rõ các phương pháp chống độc hại không xử lý nhiễu nhãn |

### 3.2 Bảo mật trong federated prompt learning, federated PEFT và FL trên VLM

| Bài | Nơi đăng | Mô hình | Loại mối đe doạ | Có xét nhiễu nhãn? |
|---|---|---|---|---|
| SABRE-FL | ICLR 2026, arXiv 2506.22506 | CLIP + prompt | Backdoor (phòng thủ: anomaly detector trong không gian embedding) | Không |
| BadPromptFL | arXiv 2508.08040; TCSVT 2026 | CLIP + prompt | Backdoor (tấn công) | Không |
| Compromising Federated Medical AI: backdoor risks in prompt learning (poster) | ACM, DOI 10.1145/3715014.3724042 | VLM y tế + prompt | Backdoor | Không |
| FedMGP+ | TPAMI 2026, DOI 10.1109/TPAMI.2026.3711828 | Prompt đa mức (continual) | Poisoning + rò gradient; "client độc hại hoặc kém chất lượng" chỉ nhắc ở phần động lực | Không |
| Privacy-Enhanced Federated Prompt Tuning Against Backdoor | IEEE TCC 2026 | Soft prompt (LLM) | Backdoor + mã hoá đồng cấu | Không |
| Byzantine-robust federated prompt tuning (ST-HMR) | Frontiers in CS 2026 | ViT + prompt | Byzantine (Multi-Krum) | Không |
| SecFFT | IoTJ 2024 | LVLM federated fine-tuning | Backdoor ẩn | Không |
| CLIP-Fed | arXiv 2508.10315 | Dùng CLIP để phòng thủ cho model thường | Backdoor | Không |
| Silent Penetrator | TIFS 2025 | Federated fine-tuning đa miền | Backdoor do feature shift | Không |
| Exploring Backdoor Attacks in FL under PEFT | ISC 2025 | PEFT | Backdoor | Không (không có abstract) |
| A Targeted Backdoor for Federated PEFT of ViTs | IoTJ 2026 | ViT + PEFT | Backdoor | Không (không có abstract) |
| Revisiting Backdoor Threat in Federated Instruction Tuning | ICASSP 2026 | LLM | Dữ liệu nhiễm độc rải rác ngay trong client lành tính | Không (nhưng làm mờ ranh giới lành tính / độc hại) |
| PEFTGuard | arXiv 2411.17453 (IEEE S&P 2025*) | LoRA | Phát hiện backdoor trong adapter | Không |

### 3.3 Tấn công đội lốt nhiễu, và sự nhầm lẫn giữa nhiễu và độc hại

| Bài | Nơi đăng | Nội dung |
|---|---|---|
| Noisy data-based attack | FGCS 2025, DOI 10.1016/j.future.2025.107900 | Tấn công không mục tiêu bằng cách biến dữ liệu thành "nhiễu", qua mặt hầu hết phòng thủ SOTA. Phòng thủ dùng điểm tin cậy, phát hiện đúng 97% |
| Label noise analysis meets adversarial training | KBS 2023, DOI 10.1016/j.knosys.2023.110384 | Coi tấn công lật nhãn và backdoor là các cơ chế nhiễu nhãn; tiêm nhiễu nhân tạo để "tiêm chủng" cho model |
| Byzantine-Robust Learning on Heterogeneous Datasets via Bucketing | ICLR 2022, arXiv 2006.09365 | Non-IID làm hỏng các phòng thủ Byzantine; đề xuất bucketing |
| Adaptive Adversaries in Byzantine-Robust FL: A survey | IACR ePrint 2025/510 | Tổng quan kẻ tấn công thích nghi |
| FedNed | AAAI 2024, arXiv 2312.12703 | Client cực nhiễu (>90%). Nhận xét của mình: ở mức này hành vi rất khó phân biệt với phá hoại |
| Honest Score Client Selection | arXiv 2311.05826 | Phòng thủ lật nhãn trong non-IID: các phương pháp hiện có sụp khi non-IID |

### 3.4 Tiền lệ cho các tín hiệu phát hiện

| Bài | Nơi đăng | Tín hiệu |
|---|---|---|
| FLDetector | KDD 2022, arXiv 2207.09209 | Cập nhật có nhất quán với dự đoán từ lịch sử không |
| FoolsGold | arXiv 1808.04866 (RAID 2020*) | Các sybil cập nhật giống nhau bất thường |
| LFighter / Defending against the Label-flipping Attack in FL | Neural Networks 2023, arXiv 2207.01982 | Gradient các neuron lớp nguồn/đích ở tầng output, rồi phân cụm |
| SafeFL: Toward Malicious Clients Detection | ASIACCS 2025, arXiv 2505.09110 | Dữ liệu tổng hợp từ chuỗi global model; nói rõ các phương pháp cũ báo động nhầm nhiều client lành tính |
| FedGT | arXiv 2305.05506 | Group testing trên các nhóm client chồng lấn |
| Learning with Noisy Labels Revisited (CIFAR-N) | ICLR 2022, arXiv 2110.12088 | Nhiễu do người gán nhãn phụ thuộc đặc trưng; ở CIFAR-100N nhãn sai đi về vài lớp tương tự |
| FedChallenger | IEEE (doc 11095660) | Challenge-response theo hướng xác thực thiết bị, không phải sửa nhãn |

### 3.5 Ngoài FL: crowdsourcing

| Bài | Nơi đăng | Nội dung |
|---|---|---|
| Identifying Unreliable and Adversarial Workers in Crowdsourced Labeling Tasks | JMLR 18 (2017) | Tách người gán trung thực nhưng kém với người đối nghịch bằng reputation; nêu rằng đối thủ tinh vi có thể giả làm người bình thường |
| Data Poisoning Attacks and Defenses to Crowdsourcing Systems | WWW 2021 | Tấn công và phòng thủ khi gom nhãn từ client không đáng tin + client độc hại |

---

## 4. Tổng hợp theo chủ đề

### 4.1 Hai cộng đồng phát triển song song, gần đây mới bắt đầu gặp nhau
- Cộng đồng **FL nhiễu nhãn** (FedCorr, FedNoRo, FedNed...) giả định không ai cố ý phá.
- Cộng đồng **FL chống độc hại** (Krum, FLTrust, FLDetector...) giả định client lành tính có dữ liệu "tốt", chỉ khác nhau do non-IID.
- Từ 2022 mới xuất hiện một số bài ghép hai giả định (MUD-HoG), và 2025–2026 nhiều hơn (GShield, FedAS-TSAD, bài Palermo). Độ tin cậy **cao** cho phát biểu "khái niệm đã có".
- Hầu hết các bài ghép này định nghĩa "kém chất lượng" chung chung (ảnh xấu, cảm biến); chỉ bài Palermo và zkCor làm với nhãn nhiễu theo đúng nghĩa.

### 4.2 Mảng federated prompt learning và FL trên VLM vẫn ở giai đoạn "một mối đe doạ"
- Toàn bộ bài bảo mật tìm được chỉ xét backdoor hoặc Byzantine. Độ tin cậy **trung bình–cao** cho phát biểu "chưa ai xét cả nhiễu nhãn lẫn độc hại trong mảng này" (đã kiểm abstract của cả nhóm S3 lẫn snowball).
- OpenAlex chưa có bài nào trích dẫn SABRE-FL và BadPromptFL, nên có thể có bài 2026 chưa được index.

### 4.3 Kẻ tấn công đội lốt nhiễu là rủi ro trung tâm, không phải chuyện phụ
- Noisy data-based attack (FGCS 2025) cho thấy "trông giống nhiễu" đã là chiến lược né phòng thủ hiệu quả.
- Crowdsourcing (JMLR 2017) đã nêu từ lâu rằng đối thủ tinh vi có thể giả làm người gán bình thường.
- Hệ quả: một phương pháp "giữ và sửa client nhiễu" **tạo ra động cơ** để kẻ tấn công giả làm nhiễu, vì được giữ lại có lợi hơn bị loại. Đồ án **bắt buộc** phải đánh giá tình huống này, nếu không sẽ bị bác ngay.

### 4.4 Đánh giá lại các tín hiệu
- **Theo thời gian, đồng loã:** đã có, chỉ dùng làm thành phần hoặc baseline, không phải đóng góp.
- **Hình học theo lớp:** tương tự LFighter. Đóng góp chỉ ở chỗ dùng class text embedding sinh từ prompt, thứ nhỏ, đọc được, không cần tầng output.
- **Hợp lý ngữ nghĩa:** mới.
  - Cơ sở: nhãn sai do người gán thường nằm giữa các lớp tương tự (CIFAR-N), và CLIP có sẵn thang đo độ tương tự giữa các lớp.
  - Giới hạn phải nói rõ: kẻ tấn công thích nghi có thể chọn đích *tương tự*.
  - Lập luận bảo vệ: như vậy kẻ tấn công bị ép vào tập đích hẹp hơn, giảm tác hại. Cần đo thực nghiệm.
- **Phản ứng khi sửa nhãn:** mới.
  - Giới hạn: kẻ tấn công biết giao thức có thể giả vờ phản ứng.
  - Cần thiết kế thử thách mà giả vờ thì tốn kém hoặc làm yếu tấn công. Đây là phần khó nhất và rủi ro nhất.

---

## 5. Bảng thành phần: cái gì đã có, cái gì mới

| Thành phần của đồ án | Đã có? | Nguồn |
|---|---|---|
| Federated prompt learning trên CLIP | Có | PromptFL, FedOTP, FLIP |
| Phát hiện / sửa nhãn nhiễu cho prompt learning (không FL) | Có | TrustCLIP, NLPrompt, DeFT... (xem phase 0) |
| Phát hiện client nhiễu trong FL | Có | FedCorr, FedNoRo, FedSNC |
| Phát hiện client độc hại trong federated prompt learning | Có | SABRE-FL |
| Khái niệm tách ba loại client trong FL | Có | MUD-HoG, bài Palermo 2026, GShield, FedAS-TSAD |
| Tín hiệu theo thời gian / đồng loã | Có | FLDetector, FoolsGold, MUD-HoG |
| Tín hiệu hình học theo lớp | Một phần | LFighter (tầng output) |
| **Tách ba loại client trong federated prompt learning / VLM, với nhiễu nhãn đúng nghĩa** | **Chưa thấy** | |
| **Tín hiệu hợp lý ngữ nghĩa dùng tri thức của VLM** | **Chưa thấy** | |
| **Tín hiệu phản ứng khi sửa nhãn (kiểm bằng hành vi)** | **Chưa thấy** (zkCor dùng mật mã) | |
| **Đánh giá kẻ tấn công đội lốt nhiễu trong federated prompt learning** | **Chưa thấy** | Tấn công gốc: FGCS 2025 (model thường) |

Trong 11 thành phần: 6 đã có, 1 có một phần, 4 chưa thấy. Tính theo khối lượng công việc thì ước lượng trùng **~50–55%**.

---

## 6. Hệ quả cho thiết kế đồ án

**Baseline bắt buộc**
- Phát hiện độc hại / tách ba loại: MUD-HoG, FLDetector, FoolsGold, LFighter, SABRE-FL.
- Gộp model bền vững: Krum / Multi-Krum, coordinate-wise median, bucketing.
- Xử lý nhiễu: bộ lọc kiểu TrustCLIP (lọc bằng zero-shot) được federated hoá, phát hiện client nhiễu kiểu FedCorr.
- FLTrust chỉ thêm nếu chấp nhận giả định server có tập dữ liệu sạch nhỏ.

**Tấn công cần cài**
1. Lật nhãn có mục tiêu, hai biến thể: đích tương tự ngữ nghĩa và đích khác xa.
2. Backdoor kiểu BadPromptFL.
3. Noisy data-based attack (đội lốt nhiễu).
4. Biến thể thích nghi: biết tín hiệu ngữ nghĩa nên chọn đích tương tự, biết giao thức sửa nhãn nên giả vờ phản ứng.

**Mô hình mối đe doạ phải viết rõ:** tỉ lệ client độc hại tối đa, kẻ tấn công biết những gì, có đồng loã không.

**Claim được phép:**
- "Đầu tiên tách client nhiễu nhãn với client độc hại trong federated prompt learning."
- "Đề xuất tín hiệu ngữ nghĩa dựa trên VLM và tín hiệu phản ứng khi sửa nhãn."

**Claim KHÔNG được phép:** "đầu tiên tách client nhiễu với client độc hại trong FL".

**Cổng kiểm tra từ kế hoạch trước giữ nguyên, và bổ sung:**
- đo cả MUD-HoG, không chỉ Krum/median/SABRE-FL;
- nếu MUD-HoG đã tách tốt client nhiễu nhãn với client độc hại trong federated prompt learning thì phần đóng góp phải dời sang kẻ tấn công thích nghi, hoặc bỏ hướng mở rộng.

---

## 7. Giới hạn của review này

1. ~~Phần lớn chỉ đọc abstract.~~ **Đã xử lý một phần:** đã đọc full text MUD-HoG và Fed-RoSeC (bài Palermo), xem mục 11. Vẫn chỉ đọc abstract: zkCor, Noisy data-based attack, FedMGP+ (đều closed access), và bài J. Supercomputing 2025 "Multi-stage FL with group-wise bidirectional guidance" (không lấy được cả abstract).
2. ~~OpenAlex chưa có bài nào trích dẫn SABRE-FL và BadPromptFL.~~ **Đã xử lý:** đã kiểm "Cited by" trên Google Scholar và Semantic Scholar, cùng tìm kiếm toàn văn trên Google Scholar, xem mục 11.3. Còn một điểm lẻ: poster backdoor y tế hiện "Cited by 2" trên Scholar nhưng danh sách trống.
3. OpenAlex không resolve được FLAME (USENIX Security 2022), nên thiếu snowball cho bài này.
4. Lọc S2 và S4 dựa trên từ khoá trong abstract; nhiều bản ghi OpenAlex thiếu abstract nên có thể sót.
5. Nơi đăng có dấu * chưa đối chiếu trực tiếp.
6. Chỉ tiếng Anh.

## 8. Nhật ký tìm kiếm

### 8.1 Database (chạy 2026-09-17, từ 2021-01-01)

| ID | Database | Truy vấn | Kết quả |
|---|---|---|---:|
| S1 | arXiv | `all:federated AND (all:"noisy label" OR all:"noisy labels" OR all:"label noise" OR all:"noisy clients") AND (all:malicious OR all:Byzantine OR all:poisoning OR all:backdoor)` | 3 |
| S1 | OpenAlex | `federated AND ("noisy label" OR "noisy labels" OR "label noise" OR "noisy clients") AND (malicious OR Byzantine OR poisoning OR backdoor)` | 31 |
| S2 | arXiv | `all:federated AND (all:"label flipping" OR all:"label-flipping")` | 49 |
| S2 | OpenAlex | `federated AND ("label flipping" OR "label-flipping")` | 344 |
| S3 | arXiv | `all:federated AND (all:prompt OR all:LoRA OR all:adapter OR all:"parameter-efficient" OR all:CLIP OR all:"vision-language") AND (all:backdoor OR all:poisoning OR all:Byzantine OR all:malicious)` | 224 |
| S3 | OpenAlex | `federated AND (prompt OR LoRA OR adapter OR "parameter-efficient" OR CLIP OR "vision-language") AND (backdoor OR poisoning OR Byzantine OR malicious)` | 201 |
| S4 | arXiv | `all:federated AND (all:"unreliable clients" OR all:"low-quality clients" OR all:"data quality" OR all:"honest clients") AND (all:malicious OR all:Byzantine OR all:poisoning)` | 25 |
| S4 | OpenAlex | `federated AND ("unreliable clients" OR "low-quality clients" OR "data quality" OR "honest clients") AND (malicious OR Byzantine OR poisoning)` | 175 |
| S5 | arXiv | `all:federated AND (all:reputation OR all:trust) AND (nhiễu) AND (all:malicious OR all:poisoning OR all:attack)` | 1 |
| S5 | OpenAlex | tương tự S5 arXiv | 3 |

### 8.2 Forward citation (OpenAlex)

| Bài gốc | Tổng trích dẫn | Bộ lọc | Khớp |
|---|---:|---|---:|
| SABRE-FL | 0 | không lọc | 0 |
| BadPromptFL | 0 | không lọc | 0 |
| Krum | 982 | nhiễu nhãn | 8 |
| Trimmed mean (Yin et al.) | 666 | nhiễu nhãn | 12 |
| FLTrust | 941 | nhiễu nhãn | 4 |
| FLAME | không resolve được | | |
| FoolsGold | 82 | nhiễu nhãn | 0 |
| FLDetector | 345 | nhiễu nhãn | 2 |
| Data Poisoning Attacks Against FL (Tolpegin) | 854 | nhiễu nhãn | 8 |
| How To Backdoor FL | 890 | nhiễu nhãn | 10 |
| FedNed | 33 | tấn công | 7 |
| FedCorr | 130 | tấn công | 10 |
| FedNoRo | 65 | tấn công | 7 |
| RHFL | 200 | tấn công | 24 |
| **Unique** | | | **69** |

### 8.3 Web search (2026-09-17)

1. federated learning distinguish "noisy clients" and "malicious clients" simultaneously label noise Byzantine robust
2. "honest but noisy" OR "benign noisy" clients misclassified as malicious federated learning defense false positive label noise
3. federated prompt learning vision-language robust aggregation malicious clients noisy labels unified framework
4. FedNed extremely noisy clients negative distillation federated learning Byzantine
5. label flipping attack versus label noise distinguish intentional poisoning from annotation errors federated learning
6. federated learning backdoor attack LoRA parameter-efficient fine-tuning defense vision-language CLIP 2025 2026
7. challenge-response verification federated learning clients follow protocol detect malicious "proof of learning" OR "verifiable training" poisoning
8. Byzantine-robust aggregation evaluation under label noise noisy benign clients excluded Krum median FLTrust performance degradation
9. "benign", "noisy" and "malicious" clients three types federated learning client identification framework
10. "Label noise analysis meets adversarial training" defense label poisoning federated learning
11. crowdsourcing distinguish spammers careless workers from adversarial malicious workers truth inference label aggregation
12. label flipping attack detection semantic similarity source target class plausibility confusion federated defense
13. "Noisy data-based attack" new type of untargeted attack federated learning countermeasures Future Generation Computer Systems
14. adaptive attack mimic label noise evade detection federated learning disguise as noisy client poisoning stealthy
15. human label noise concentrated semantically similar classes versus adversarial label flipping arbitrary target detect intent semantic prior text embedding
16. "Learning with Noisy Labels Revisited" CIFAR-N real-world human annotations noise transition similar classes ICLR 2022

---

## 9. Việc tiếp theo

1. ~~Đọc full text MUD-HoG, bài Palermo.~~ Đã xong (mục 11). Còn lại (closed access, cần thư viện trường): Noisy data-based attack (FGCS), zkCor (ICDE), FedMGP+ (TPAMI).
2. ~~Kiểm "Cited by" của SABRE-FL, BadPromptFL.~~ Đã xong (mục 11.3).
3. **Cổng kiểm tra ở giai đoạn 2:** cho MUD-HoG, Fed-RoSeC, SABRE-FL, Krum và median chạy trên kịch bản *chỉ có client nhiễu* trong federated prompt learning, đo tỉ lệ loại nhầm. Kiểm thêm các giả thuyết H1–H5 ở mục 11.4.
4. Code MUD-HoG có sẵn (github.com/LabSAINT/MUD-HoG_Federated_Learning). Fed-RoSeC chưa thấy link code trong bài, phải tự cài lại theo Algorithm 1.

## 10. Tài liệu tham khảo

- MUD-HoG: Gupta A., Luo T., Ngo M. V., Das S. K., "Long-Short History of Gradients is All You Need: Detecting Malicious and Unreliable Clients in Federated Learning", ESORICS 2022. arXiv:2208.10273
- Fed-RoSeC: Augello A., De Paola A., Lo Re G., "Federated Learning for Robust Malware Detection under Noisy Labels and Malicious Sybils", ITASEC & SERICS 2026, CEUR-WS Vol-4198, paper 5. https://ceur-ws.org/Vol-4198/paper5.pdf
- MUD-HoG code: https://github.com/LabSAINT/MUD-HoG_Federated_Learning (ESORICS 2022, pp. 445–465)
- Multi-stage federated learning with group-wise bidirectional guidance, The Journal of Supercomputing 2025. https://doi.org/10.1007/s11227-025-07449-7 (chưa đọc được abstract)
- A Systematic Literature Review of Robust Federated Learning, ACM Computing Surveys 2025. https://doi.org/10.1145/3727643
- Federated Prompt Learning: A Unified Framework, Empirical Analysis, and Future Directions. arXiv:2608.13844
- CPInj: Uncovering Prompt Injection Risks in Textual Collaborative Prompt Optimization. arXiv:2607.18622
- EmoAttack: adaptive prompt optimization for multimodal emotion backdoor attacks, Information Processing & Management 2027
- A Survey on Vision-Language Models for Multimodal Federated Learning Tasks, TechRxiv 2025. https://doi.org/10.36227/techrxiv.175624545.56457516/v2
- Cross-Modal Multi-Level Backdoor Poisoning in Multimodal Federated Learning, IMIS 2026. https://doi.org/10.1007/978-3-032-29561-3_15
- zkCor: "Label Noise Correction for Federated Learning: A Secure, Efficient and Reliable Realization", ICDE 2024. https://doi.org/10.1109/ICDE60146.2024.00277
- DWS: "A Shapley-Based Robust Federated Learning Framework with Data Distribution Weighting Constraints", ICEAAI 2026. https://doi.org/10.1109/ICEAAI68945.2026.11442375
- GShield. arXiv:2512.19286
- MineDetect: "Detecting Untargeted Attacks and Mitigating Unreliable Updates in FL for Underground Mining Operations". arXiv:2508.10212
- FedAS-TSAD, BDDM 2025. https://doi.org/10.1109/BDDM68348.2025.11442184
- RADAR, SRDS 2024. https://doi.org/10.1109/SRDS64841.2024.00030
- ARFL: Auto-weighted Robust Federated Learning with Corrupted Data Sources. arXiv:2101.05880 ; https://doi.org/10.1145/3517821
- FedSCS: Robust Federated Learning via Stable Cosine Similarity, ICCST 2025. https://doi.org/10.1109/ICCST63435.2025.11295691
- FedNoiL. arXiv:2205.10110
- SABRE-FL, ICLR 2026. arXiv:2506.22506
- BadPromptFL. arXiv:2508.08040 ; TCSVT 2026 https://doi.org/10.1109/TCSVT.2026.3704659
- Backdoor Risks in Prompt Learning (poster). https://doi.org/10.1145/3715014.3724042
- FedMGP+, TPAMI 2026. https://doi.org/10.1109/TPAMI.2026.3711828
- Privacy-Enhanced Federated Prompt Tuning Against Backdoor Attack, IEEE TCC 2026. https://doi.org/10.1109/TCC.2026.3660272
- Spatiotemporal ViTs with Byzantine-robust federated prompt tuning, Frontiers in CS 2026. https://doi.org/10.3389/fcomp.2026.1892207
- SecFFT, IEEE IoTJ 2024. https://doi.org/10.1109/JIOT.2024.3510695
- CLIP-Fed. arXiv:2508.10315
- Silent Penetrator, IEEE TIFS 2025. https://doi.org/10.1109/TIFS.2025.3581026
- Exploring Backdoor Attacks in FL under PEFT, ISC 2025. https://doi.org/10.1007/978-3-032-08124-7_16
- A Targeted Backdoor for Federated PEFT of ViTs, IEEE IoTJ 2026. https://doi.org/10.1109/JIOT.2026.3726861
- Revisiting Backdoor Threat in Federated Instruction Tuning, ICASSP 2026. arXiv:2602.15671
- PEFTGuard. arXiv:2411.17453
- Noisy data-based attack, FGCS 2025. https://doi.org/10.1016/j.future.2025.107900
- Label noise analysis meets adversarial training, KBS 2023. https://doi.org/10.1016/j.knosys.2023.110384
- Bucketing: Karimireddy et al., ICLR 2022. arXiv:2006.09365
- Adaptive Adversaries in Byzantine-Robust FL: A survey. IACR ePrint 2025/510
- FedNed, AAAI 2024. arXiv:2312.12703
- Honest Score Client Selection. arXiv:2311.05826
- FLDetector, KDD 2022. arXiv:2207.09209
- FoolsGold: Fung et al. arXiv:1808.04866
- LFighter / Defending against the Label-flipping Attack in FL: Jebreel N. M., Domingo-Ferrer J. et al., Neural Networks 2023. arXiv:2207.01982
- SafeFL, ASIACCS 2025. arXiv:2505.09110
- FedGT. arXiv:2305.05506
- CIFAR-N: Wei et al., ICLR 2022. arXiv:2110.12088
- FedChallenger. https://ieeexplore.ieee.org/document/11095660/
- Jagabathula et al., "Identifying Unreliable and Adversarial Workers in Crowdsourced Labeling Tasks", JMLR 18, 2017. https://jmlr.org/papers/v18/15-650.html
- Data Poisoning Attacks and Defenses to Crowdsourcing Systems, WWW 2021. https://doi.org/10.1145/3442381.3450066

---

## 11. Cập nhật: đọc full text và kiểm trích dẫn (2026-09-17)

### 11.1 MUD-HoG (ESORICS 2022): đọc full text

**Thiết lập**
- 40 client, Dirichlet 0,9, MNIST và Fashion-MNIST, CNN train từ đầu, 40 round, 4 epoch cục bộ.
- Tối đa 47,5% client độc hại và 10% client không đáng tin.

**Client "không đáng tin"**
- Bị làm mờ 50% ảnh (Gaussian, kernel 7, σ=50) và chỉ train trên 30% dữ liệu cục bộ.
- **Không có nhãn sai.**
- Khi gộp model, trọng số của nhóm này bị nhân α=0,5.

**Tấn công được xét**
- Không mục tiêu: lật dấu gradient, cộng nhiễu Gaussian (σ=0,01).
- Có mục tiêu: lật nhãn 1→7, lật nhiều nhãn {1,2,3}→7.
- **Không xét backdoor** (tác giả tự loại trừ).
- Giả định: kẻ tấn công tấn công mọi round; số client độc hại ít hơn phần còn lại; mọi kẻ tấn công có mục tiêu dùng *cùng một* cặp nguồn→đích.

**Thuật toán (chạy tuần tự trên server)**
1. HoG ngắn = trung bình gradient 3 round gần nhất. Client có cosine âm so với median bị coi là kẻ lật dấu.
2. DBSCAN trên HoG ngắn tách ra một nhóm nhỏ. Trong nhóm này, dùng "khoảng trống lớn nhất" trên khoảng cách Euclid để chọn ra kẻ cộng nhiễu.
3. HoG dài = tổng toàn bộ gradient. Chạy **K-means với K=2**, **cụm nhỏ hơn luôn bị gán là kẻ tấn công có mục tiêu** (Algorithm 1, dòng 17–18).
4. Với phần còn lại, dùng "khoảng trống lớn nhất" trên cosine distance để chọn client không đáng tin.

**Giới hạn tác giả tự nêu:** tấn công có mục tiêu tinh vi, backdoor, và client đổi vai theo thời gian.

**Hệ quả cho đồ án.** Đây là giả thuyết rút ra từ việc đọc thuật toán, **chưa kiểm bằng thí nghiệm**:
- **H1.** Bước 3 và 4 *luôn* chia đôi, kể cả khi không có kẻ tấn công. Trong kịch bản chỉ có client nhiễu, MUD-HoG gần như chắc chắn loại oan một nhóm client trung thực.
- **H2.** Client nhiễu kiểu pairflip mà cùng nhầm một cặp lớp (người gán nhãn hay nhầm mèo↔chó) sẽ có HoG dài cùng hướng, trông giống kẻ tấn công có mục tiêu, nên dễ bị K-means loại.
- **H3.** Client nhiễu symmetric (mỗi client nhiễu ngẫu nhiên khác nhau) nhiều khả năng rơi vào nhóm "không đáng tin" hoặc "bình thường". MUD-HoG không có cơ chế sửa nhãn cho họ.

### 11.2 Fed-RoSeC (ĐH Palermo, ITASEC & SERICS 2026): đọc full text

**Thiết lập**
- Phát hiện mã độc Android (Kronodroid, 200 đặc trưng tĩnh), **nhị phân**, MLP 4 lớp.
- 100 client, mỗi round chọn 20.
- Chia train/test theo thời gian (trước / từ 2016).

**Ba loại client**
- trung thực;
- **nhiễu**: trung thực, nhãn sai hệ thống với xác suất ε ∈ [0; 0,9], *làm theo giao thức*;
- **độc hại**: sybil lật *toàn bộ* nhãn, không sửa tham số được.

**Thuật toán**
1. Train khởi động bằng FedProx.
2. Tính khoảng cách DCFL giữa các client (kết hợp Euclid và góc của cập nhật), lượng tử hoá thành 3 mức.
3. Phân cụm K-Modes thành √N cụm, chấm điểm Ω cho từng cụm, rồi GMM 3 thành phần trên các điểm. Cụm giữa được coi là client nhiễu; dùng dấu của kurtosis để quyết định cụm đầu nào trung thực.
4. Retrain global model chỉ với client trung thực.
5. Client **nhiễu và độc hại đều** tự sửa nhãn: GMM trên loss từng mẫu, sửa thận trọng ở mức FPR 5%, rồi xin quay lại nếu mức nhiễu ước lượng đủ thấp.
6. Client còn kẹt lại thì bị gán toàn bộ nhãn bằng dự đoán của global model. Kết thúc bằng một pha FedAvg với tất cả client.

**Kết quả**
- Hơn FedAvg, FedCorr, FoolsGold ở mức nhiễu tổng cao (so ghép cặp bằng kiểm định Wilcoxon).
- Ở mức nhiễu thấp không khác biệt có ý nghĩa với FedCorr (p=0,07).
- Bản ORACLE (biết trước client trung thực) vẫn cao hơn rõ, nên bước phân cụm còn nhiều chỗ cải thiện.
- Khi nhiễu thấp (khoảng 10–20%), client nhiễu gom chung với client trung thực. Khi nhiễu cao, họ gom chung với client độc hại.

**Giới hạn tác giả tự nêu:** dựa vào các heuristic về hành vi trong không gian khoảng cách; hướng tương lai là kẻ tấn công phức tạp hơn và ước lượng nhiễu thích nghi.

**Hệ quả cho đồ án**
- **H4.** Fed-RoSeC *ngầm giả định* client độc hại chịu chạy bước sửa nhãn. Kẻ tấn công thật sẽ không làm theo, hoặc giả vờ làm. Đây đúng là chỗ tín hiệu "phản ứng khi được yêu cầu sửa nhãn" của đồ án nhắm vào, nên độ mới của tín hiệu này **được củng cố**.
- **H5.** Mô hình tấn công "lật toàn bộ nhãn" chỉ hợp lý cho bài toán nhị phân. Với phân loại nhiều lớp trên ảnh, tấn công có mục tiêu (lật một cặp lớp) trông **giống pairflip noise hơn nhiều**, và đây là nơi tín hiệu ngữ nghĩa từ CLIP có ý nghĩa, trong khi bài toán nhị phân của Fed-RoSeC không dùng được tín hiệu này.
- Fed-RoSeC nên là **baseline thứ hai** bên cạnh MUD-HoG. Bài không kèm link code, nên phải tự cài lại theo Algorithm 1.
- Cách báo cáo của họ (bản ORACLE, so ghép cặp bằng Wilcoxon) khớp với quy trình rút ra từ FedSNC.

### 11.3 Kiểm "Cited by" và tìm kiếm toàn văn (Google Scholar qua trình duyệt tự động + Semantic Scholar API)

| Bài gốc | Google Scholar | Semantic Scholar | Các bài trích dẫn | Có đụng nhiễu nhãn / tách client nhiễu–độc hại? |
|---|---|---|---|---|
| SABRE-FL (ICLR 2026) | Cited by 2 | 2 | Federated Prompt Learning survey (arXiv 2608.13844); CPInj: prompt injection trong tối ưu prompt dạng text hợp tác (arXiv 2607.18622) | Không |
| BadPromptFL (arXiv 2025) | Cited by 3 | 0 | EmoAttack (IP&M 2027, backdoor cảm xúc đa phương thức); Survey VLM cho Multimodal FL (TechRxiv 2025); Cross-Modal Multi-Level Backdoor Poisoning in MFL (IMIS 2026) | Không (theo tiêu đề và đoạn trích) |
| BadPromptFL bản TCSVT 2026 | 0 | 0 | | |
| Poster backdoor trong prompt learning y tế (ACM 2025) | Cited by 2, **nhưng danh sách trống** | | | Không xác định được |
| MUD-HoG (ESORICS 2022) | Cited by 62; lọc trong các bài trích dẫn với "noisy labels" còn 6 | | Multi-stage FL with group-wise bidirectional guidance (J. Supercomputing 2025, nhiễu + tấn công, FL thường, chưa đọc được abstract); ACM CSUR 2025 review; luận văn thạc sĩ Sidoti (tiền thân của Fed-RoSeC); HisHFL (2025); combined reconstruction + poisoning (2026); một luận án HAL | Không bài nào dùng VLM hay prompt |

**Tìm kiếm toàn văn trên Google Scholar** (có tìm trong nội dung bài, không chỉ abstract):

| Truy vấn | Từ năm | Kết quả | Liên quan? |
|---|---|---:|---|
| `"federated prompt learning" "noisy labels"` | 2023 | 3 | Không (MetePFL dự báo thời tiết; một review về recommender; mục lục ICPADS) |
| `"federated prompt tuning" "label noise"` | 2023 | 0 | |
| `"noisy clients" "malicious clients" "prompt" CLIP federated` | 2022 | 1 | Không (DP + robust aggregation cho IIoT) |

**Kết luận 11.3:** mọi bài trích dẫn hai bài bảo mật gốc của federated prompt learning đều đi theo hướng tấn công hoặc khảo sát. Tìm kiếm toàn văn không ra bài nào ghép federated prompt learning với nhiễu nhãn. **Nâng độ tin cậy** của phát biểu ở mục 0.2 từ trung bình–cao lên **cao** (tính tới ngày 2026-09-17; chưa tính bài đã nộp nhưng chưa công bố).

### 11.4 Kết luận sau cập nhật

- **Verdict không đổi, nhưng chắc hơn.**
  - Tách client nhiễu với client độc hại đã có ở FL thường (MUD-HoG, Fed-RoSeC...).
  - Chưa có trong federated prompt learning / VLM.
  - Ước lượng trùng vẫn **~50–55%**.
- **Tín hiệu "phản ứng khi được yêu cầu sửa nhãn" mới hơn và có động lực rõ hơn**, vì Fed-RoSeC ngầm giả định kẻ tấn công làm theo giao thức.
- **Tín hiệu ngữ nghĩa từ CLIP** có chỗ đứng rõ, vì cả hai tiền lệ đều không khai thác được ngữ nghĩa lớp (MUD-HoG chỉ nhìn gradient; Fed-RoSeC làm bài toán nhị phân).
- **Giả thuyết cần kiểm ở cổng giai đoạn 2:**
  - **H1:** MUD-HoG loại oan client khi không có kẻ tấn công.
  - **H2:** MUD-HoG coi client pairflip chung một cặp lớp nhầm là kẻ tấn công có mục tiêu.
  - **H3:** client symmetric noise không được sửa nhãn.
  - **H4:** Fed-RoSeC sụp khi kẻ tấn công không chịu (hoặc giả vờ) sửa nhãn.
  - **H5:** ở bài toán nhiều lớp, tấn công lật một cặp lớp khó tách khỏi pairflip noise nếu không có tín hiệu ngữ nghĩa.
- **Hai baseline chính:** MUD-HoG (có code) và Fed-RoSeC (tự cài lại).
