# CLEAR-FPL v2: nền lý thuyết của bước kiểm toán nhiễu

Tài liệu đi kèm:
- kế hoạch: `results/side-research/clear2/clear2_plan.md`;
- số liệu offline: `results/side-research/idea_audit/offline_findings.md`;
- mã nguồn: `flip/flcore/sure.py`, hàm `_audit`.

## 1. Thiết lập

- Một client có n ảnh x_i với nhãn đã cho ỹ_i; nhãn thật Y_i chưa biết; có K lớp.
- **Trọng tài** p(·|x) là một phân phối trên K lớp. Trong CLEAR v2, đó là CLIP zero-shot đóng băng.
- Ký hiệu:
  - S(x) = Σ_k p_k(x)²: "độ sắc" của trọng tài trên ảnh x;
  - c(x) = (1 − S(x))/(K − 1).

**Giả thiết A1 (hiệu chỉnh).** P(Y = k | p(x)) = p_k(x). Nghĩa là trọng tài nói "chắc 40%" thì đúng 40% số lần.

Hệ quả của A1:
- E[p_Y(X)] = E[S(X)];
- độ lệch hiệu chỉnh Δ := E[p_Y(X)] − E[S(X)] bằng 0;
- Δ > 0 nghĩa là trọng tài thiếu tự tin, Δ < 0 nghĩa là trọng tài quá tự tin.

**Giả thiết A2 (nhiễu đều, không phụ thuộc ảnh).** ỹ = Y với xác suất 1 − ρ; ngược lại ỹ được chọn đều trong K − 1 lớp còn lại.

## 2. Ước lượng tỉ lệ nhiễu

**Mệnh đề 1 (không lệch).** Dưới A1 và A2:

E[p_ỹ(X)] = (1 − ρ)·E[S(X)] + ρ·E[c(X)],

nên

ρ = (E[S] − E[p_ỹ]) / (E[S] − E[c]).

*Chứng minh.* Cố định X = x:

E[p_ỹ | x] = Σ_y p_y(x)·[(1 − ρ)·p_y(x) + ρ·Σ_{k≠y} p_k(x)/(K − 1)]
          = (1 − ρ)·S(x) + ρ·(1 − S(x))/(K − 1).

Lấy kỳ vọng theo X. ∎

Ước lượng mẫu (phép tính moment, không có tham số nào phải chỉnh):

ρ̂ = Σ_i (S_i − p_ỹᵢ(x_i)) / Σ_i (S_i − c_i).

- Ước lượng này nhất quán, độ lệch cỡ O(1/n).
- Mô phỏng (40 lớp, n = 35, 200 lần lặp) cho trung bình ρ̂ lần lượt là −0,009 / 0,249 / 0,492 / 0,738 khi ρ thật là 0 / 0,25 / 0,5 / 0,75.

**Bản gộp lớp gần nhất** (`--sure_audit_merge true`):
- Thay p_k bằng m_k = p_k + p_nn(k), với nn(k) ≠ k là lớp gần nhất của k trong không gian văn bản của CLIP.
- Đặt S⁺ = Σ_k p_k·m_k, M = Σ_k m_k, c⁺ = (M − S⁺)/(K − 1).
- Chứng minh giống hệt Mệnh đề 1.
- Mục đích: nhầm lẫn giữa hai lớp vốn giống nhau không bị tính là nhiễu.

**Điều kiện xác định:** E[S] − E[c] > 0, tức trọng tài phải tốt hơn đoán bừa. Nếu trọng tài phẳng (p gần đều) thì mẫu số tiến về 0 và ước lượng mất thông tin. Sai số chuẩn ở mục 4 phản ánh đúng điều đó.

## 3. Độ lệch khi trọng tài không được hiệu chỉnh

**Mệnh đề 2.** Chỉ dưới A2, đặt S̄ = E[S] và c̄ = (1 − S̄)/(K − 1). Giới hạn của ρ̂ là

ρ̃ = ρ − Δ·(1 − ρK/(K − 1)) / (S̄ − c̄).

*Chứng minh.*
- Ta có E[p_ỹ | X, Y] = (1 − ρ)·p_Y + ρ·(1 − p_Y)/(K − 1).
- Gọi A = E[p_Y] = S̄ + Δ. Khi đó E[p_ỹ] = (1 − ρ)A + ρ(1 − A)/(K − 1).
- Thay vào S̄ − E[p_ỹ] rồi khai triển:

  S̄ − E[p_ỹ] = ρ(S̄ − c̄) − Δ·(1 − ρ − ρ/(K − 1)). ∎

Hệ quả:
1. Với client sạch (ρ = 0): ρ̃ = −Δ/(S̄ − c̄).
   - Trọng tài **thiếu tự tin** cho ước lượng **âm**, tức bỏ sót.
   - Trọng tài **quá tự tin** cho ước lượng **dương**, tức nghi oan.
2. Độ lệch tỉ lệ với Δ, **không phụ thuộc độ chính xác** của trọng tài. Trọng tài kém chính xác nhưng hiệu chỉnh tốt vẫn là trọng tài tốt.
3. Độ lệch nhỏ dần khi ρ tiến tới (K − 1)/K, mức nhãn hoàn toàn ngẫu nhiên.

**Đối chiếu số liệu** (offline, ước lượng trên client sạch):
- CLIP zero-shot: Δ nhỏ, độ lệch chỉ −0,01 đến −0,06 trên cả ba tập, dù trên DTD nó chỉ đúng 41%.
- Mô hình chung (g) bị huấn luyện trên nhãn nhiễu nên thiếu tự tin, và **càng nhiều nhiễu trong liên kết càng thiếu tự tin**:
  - Pets: −0,06 (không ai nhiễu), −0,20 (đều), −0,39 (lệch mức);
  - DTD: −0,09, −0,19, −0,32;
  - Caltech: −0,03, −0,13, −0,23.

  Mệnh đề 2 cho biết độ lệch này đi thẳng vào mọi cách ước lượng nhiễu dựa trên độ tự tin của mô hình chung. Ví dụ FedNoiL: họ vá bằng một nhiệt độ chọn tay và coi đó là hiện tượng "lúc đầu".
- Hỗn hợp ½(g + z) của CLEAR bị lệch −0,31 trên DTD ngay cả khi mọi client sạch. Trung bình của hai phân phối bất đồng thì phẳng hơn từng phân phối, nên thiếu tự tin. Điều này khớp với kết quả đã biết: ensemble của các mô hình đã hiệu chỉnh thường thiếu tự tin (Wu & Gales 2021; Rahaman & Thiery 2021). Đây là lý do ngưỡng 0,1 của CLEAR chạm vào khoảng 25% ảnh đúng trên DTD.

## 4. Sai số chuẩn, kiểm định và giới hạn phát hiện

- Đặt t_i = (S_i − m_i)/D̄ với D̄ = mean(S_i − c_i). Khi đó ρ̂ = mean(t_i) và se = sd(t)/√n.
- Client bị cắm cờ khi ρ̂/se > z_{1−α}.
- Dưới H₀ (ρ = 0, trọng tài hiệu chỉnh), tỉ lệ nghi oan xấp xỉ α. Offline: 0–4% với α = 5%.

**Giới hạn phát hiện.** Với độ mạnh 1 − β, mức nhiễu nhỏ nhất phát hiện được là

ρ_min ≈ (z_{1−α} + z_{1−β})·se, với se ≈ σ_t/√n và σ_t ∝ 1/D̄.

Nghĩa là việc phát hiện khó lên khi:
- client có ít ảnh (n nhỏ);
- trọng tài phẳng (D̄ nhỏ, tức CLIP phân vân).

Không phương pháp nào dựa trên cùng trọng tài và cùng số ảnh vượt qua được giới hạn này.

Số đo offline (α = 5%, β = 50%):

| | se (mỗi client) | ρ_min ≈ 1,645·se |
|---|---|---|
| Caltech | 0,04 | ≈ 0,06 |
| Pets | 0,06 | ≈ 0,10 |
| DTD | 0,13 | ≈ 0,21 |

Điều này giải thích vì sao trên DTD bỏ sót nhiều client nhiễu hơn, và vì sao client nhiễu 16% trong kịch bản lệch mức gần như không thể phát hiện.

## 5. Khi giả thiết A2 sai

**Nhiễu cặp:** ỹ = π(Y) với xác suất ρ.
- E[p_ỹ | x] = (1 − ρ)·S + ρ·ε(x), với ε = Σ_y p_y·p_π(y).
- Thay c bằng ε gây độ lệch ρ(c − ε)/(S − c). Độ lệch này nhỏ khi π nối các lớp không giống nhau.
- Offline, Pets: ước lượng 0,36 khi ρ thật là 0,395.

**Nhiễu theo ảnh** (lật về lớp trông giống):
- ε lớn hơn c, nên ước lượng thấp hơn thật, tức thận trọng.
- Offline, DTD: ước lượng 0,325 khi ρ thật là 0,386.

**Nhiễu cặp làm hỏng trọng tài là mô hình chung** ("đồng thuận bị chiếm"):
- Khi client nhiễu nắm phần lớn ảnh của một lớp, mô hình chung học luôn ánh xạ sai.
- Tỉ lệ nó đoán theo nhãn sai tăng theo phần sở hữu: DTD 4% lên 17%, Caltech 1% lên 7%.
- CLIP zero-shot không học từ liên kết nên miễn nhiễm (0–4%).
- Vì vậy CLEAR v2 dùng zero-shot để **chọn ảnh**, và chỉ dùng mô hình chung khi **gán lại nhãn**.

## 6. Ngân sách sửa

- Sửa round(ρ̂·n) ảnh có p_ỹ thấp nhất.
- Nếu ước lượng không lệch và thứ hạng tốt (AUROC zero-shot trong client nhiễu: 0,92–0,99), số ảnh bị chạm xấp xỉ số ảnh sai thật.
- Client sạch có ρ̂ ≈ 0 và không bị cắm cờ, nên không bị chạm. Cách này thay thế cả trần 60% lẫn ngưỡng 0,1.
- Lần thử "budget" trước đây (gate D giai đoạn 3) thất bại vì lấy số lượng kỳ vọng từ hỗn hợp ½(g + z), vốn thiếu tự tin (Mệnh đề 2). Kiểm toán bằng zero-shot sửa đúng nguyên nhân đó.

## 7. Phạm vi và giới hạn

- A1 chỉ đúng gần đúng. Mức hiệu chỉnh của CLIP phụ thuộc mẫu câu prompt. Với mẫu câu riêng của từng tập, cả ba tập đều đạt |độ lệch| ≤ 0,06. Tập mới cần kiểm tra lại.
- Các con số còn lại:
  - α = 0,05: quy ước;
  - 0,5: quy tắc "đúng nhiều hơn sai" khi gán lại nhãn;
  - tỉ lệ trộn ½: chỉ dùng để chọn nhãn mới. Sẽ phân tích độ nhạy nếu v2 được chọn.
