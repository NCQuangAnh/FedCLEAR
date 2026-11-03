# CLEAR-FPL: hoạt động tại server (kịch bản thuyết minh)

Ví dụ dùng OxfordPets (37 lớp), 10 client, 50 vòng. Các con số trong ví dụ là minh hoạ, làm tròn.

## Chuẩn bị (một lần, trước vòng 0)

1. **Nạp CLIP và dựng khuôn câu.** Server nạp CLIP RN50 (đóng băng) và dựng khuôn câu "X X X X <tên lớp>." cho 37 lớp, giống PromptFL. 4 hàng "X" là chỗ của prompt.
2. **Tạo prompt ban đầu.** Prompt gồm 4 × 512 số, rút ngẫu nhiên quanh 0 (độ lệch 0,02) theo một seed cố định, nên mọi lần chạy cùng seed đều bắt đầu giống nhau.
3. **Chuẩn bị phần dùng chung cho CLEAR-FPL.** Cả hai thứ chỉ làm một lần, chỉ dùng tên lớp, không cần ảnh nào. Client tự tính được, server tính sẵn để khỏi tính lặp.
   - Đặc trưng chữ của **câu viết tay CLIP gốc** cho 37 lớp, ví dụ "a type of pet, a photo of a <tên lớp>.".
   - **Bảng lớp giống nhất:** đo độ giống giữa đặc trưng chữ của từng cặp lớp, rồi ghi lớp gần nhất của mỗi lớp. Ví dụ: american bulldog ↔ american pit bull terrier.
4. **Ngưỡng đánh dấu τ = 0,05.** Cố định, dùng cho mọi client, mọi vòng và mọi bộ dữ liệu. Ngưỡng lấy từ thí nghiệm trên Pets khi cả 10 client đều sạch (mức 95% điểm của client sạch).

**Khác DBR-FPL:** server không cần chuẩn bị mức lệch chuẩn b, trung bình trượt hay lệnh mềm/cứng.

## Mỗi vòng (vòng 0 đến 50)

### 1. Gửi xuống

Server gửi prompt chung hiện tại (4 × 512 = 2.048 số) cho cả 10 client. Đó là thứ duy nhất được gửi xuống mỗi vòng. Ngưỡng τ chỉ gửi một lần lúc đầu.

DBR-FPL gửi thêm mức lệch chuẩn b và lệnh lọc. CLEAR-FPL không cần, vì mỗi client tự so điểm của mình với ngưỡng cố định.

### 2. Client làm việc

Server chờ cả 10 client làm Bước 1–3 (xem kịch bản phía client): chấm điểm, tự đánh dấu, dọn ảnh nếu bị đánh dấu, rồi học cục bộ một lượt.

### 3. Nhận lên

Mỗi client k gửi bốn thứ:
- **prompt đã học P_k** (2.048 số);
- **điểm s_k**: mức "bất ngờ" trung bình của nhãn;
- **cờ đánh dấu**: có hoặc không;
- **số ảnh n_k** đã học trong vòng. Ảnh bị tạm bỏ không tính, nên client bị đánh dấu có n_k nhỏ hơn một chút.

### 4. Gộp prompt (FedAvg)

Server lấy trung bình các prompt theo số ảnh:

> P_mới = Σ_k (n_k / Σ n) · P_k

Ví dụ: hai client có 30 và 20 ảnh. Client thứ nhất góp 30/50 = 60%, client thứ hai góp 40% vào prompt mới.

Cách gộp giữ nguyên như PromptFL. CLEAR-FPL **không loại client nào** và không giảm trọng số client bị đánh dấu. Client bị đánh dấu đã tự dọn dữ liệu trước khi học, nên prompt nó gửi lên đã sạch hơn. Loại hẳn client đó sẽ làm mất phần dữ liệu đúng (khoảng 60% ảnh) của nó.

### 5. Ghi sổ client nhiễu

Server ghi lại ở mỗi vòng: client nào bị đánh dấu, cùng điểm s của từng client. Ví dụ một vòng trên Pets:

| client | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| điểm s | −0,12 | −0,08 | 0,01 | −0,15 | **1,35** | −0,05 | −0,10 | **1,10** | **1,42** | −0,09 |
| đánh dấu | | | | | ✔ | | | ✔ | ✔ | |

Đây là phần **MAE không làm được**: sau 50 vòng, server có danh sách client hay bị đánh dấu và điểm của họ. Điểm này còn xếp đúng **thứ tự mức nhiễu**: trên kịch bản lệch mức, tương quan thứ hạng với mức nhiễu thật khoảng 0,93. Server dùng danh sách này để báo cáo, nhắc client kiểm tra lại cách gán nhãn, chứ không dùng để phạt.

**Khác DBR-FPL:** DBR-FPL dùng các d nhận được để tính mức lệch chuẩn b (mốc 25% thấp nhất), cập nhật trung bình trượt, rồi chọn lệnh mềm hay cứng cho vòng sau. Cách đó giả định luôn có vài client sạch, nên khi ai cũng nhiễu hoặc không ai nhiễu thì mốc b bị lệch. CLEAR-FPL bỏ hết các bước này.

### 6. Đánh giá

Sau khi gộp, server thử prompt chung mới trên tập test chung (đủ 37 lớp, nhãn sạch) theo bộ chuẩn FLIP, và ghi độ chính xác của vòng. Kết quả báo cáo là trung bình 10 vòng cuối (last10). Bước này chỉ có trong mô phỏng để đo kết quả, không ảnh hưởng đến cách học.

Sang vòng sau, server gửi prompt chung mới xuống, rồi lặp lại từ mục 1.

## Chi phí và quyền riêng tư

| | PromptFL | DBR-FPL | CLEAR-FPL |
|---|---|---|---|
| Gửi xuống mỗi vòng | 2.048 số | 2.048 số + b + lệnh | **2.048 số** (τ một lần) |
| Gửi lên mỗi vòng | 2.048 số + n | 2.048 số + d + n | 2.048 số + **s + cờ** + n |
| Server tính thêm | không | mốc b, trung bình trượt, chọn lệnh | **không** (chỉ ghi sổ) |
| Phụ thuộc client khác | không | có (b lấy từ các client khác) | **không** |

- Ảnh, nhãn và kết quả chấm từng ảnh luôn ở lại client. Server chỉ thấy một con số tóm tắt mức nhiễu (s) và cờ đánh dấu, tức không nhiều hơn d của DBR-FPL.
- Server không cần biết client nào giữ lớp nào.
