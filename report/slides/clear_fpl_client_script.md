# CLEAR-FPL: hoạt động tại client (kịch bản thuyết minh)

Ví dụ dùng bộ OxfordPets (37 lớp). Các con số trong ví dụ là minh hoạ, làm tròn.

## Bước 1: Nhận prompt chung

1. **Lúc bắt đầu (một lần).** Mỗi client tự nạp CLIP và tự dựng khuôn câu giống hệt server, vì dùng cùng code và cùng danh sách lớp. Client giữ phần đầu và phần đuôi của khuôn câu, bỏ 4 hàng "X" để chừa 4 chỗ trống cho prompt.

   Cũng trong lúc này, client chuẩn bị thêm 2 thứ chỉ làm một lần:
   - **Câu mô tả viết tay của CLIP gốc** cho từng lớp. Mỗi bộ dữ liệu có một câu mẫu riêng: Pets là "a type of pet, a photo of a <tên lớp>.", DTD là "a texture of <tên lớp>.", Caltech là "a photo of a <tên lớp>.". Câu này cố định, không học.
   - **Lớp giống nhất của mỗi lớp.** Lấy đặc trưng chữ của 37 câu viết tay, đo độ giống giữa từng cặp lớp, rồi ghi lại lớp gần nhất của mỗi lớp. Ví dụ: lớp gần nhất của "american bulldog" là "american pit bull terrier". Việc này chỉ dùng tên lớp, không cần ảnh nào.

2. **Mỗi vòng.** Client chỉ nhận 4 × 512 số từ server, đặt vào 4 chỗ dành cho prompt, ghi đè lên prompt của vòng trước. "Mô hình chung" là CLIP cộng với prompt vừa nhận.

3. **Khác DBR-FPL:**
   - Server không gửi mức lệch chuẩn b, cũng không gửi lệnh mềm hay cứng.
   - Ngưỡng τ = 0,05 được gửi đúng một lần lúc đầu, dùng chung cho mọi client và mọi vòng.

## Bước 2: Chấm điểm client và dọn ảnh (mọi vòng)

Bước 2 làm ngay đầu vòng, trước khi học, bằng prompt vừa nhận. Vì vậy client không cần cất thêm bản sao P_ref như DBR-FPL. Ảnh được đọc theo cách dùng khi kiểm tra (thu về 224 × 224, cắt giữa, không lật ngẫu nhiên), nên cùng một ảnh luôn cho cùng một kết quả.

### Nhánh ảnh

Giống DBR-FPL. Mỗi ảnh được thu về 224 × 224 điểm ảnh, mỗi điểm 3 màu, tức 150.528 số, rồi chuẩn hoá màu theo thang của CLIP.
- Khối số đi qua bộ đọc ảnh ResNet-50 (đóng băng). Lưới ảnh thu nhỏ dần còn 7 × 7, cho ra khối 2.048 × 7 × 7: 49 vùng, mỗi vùng 2.048 số.
- Lớp gộp có chú ý lấy trung bình 49 vùng làm truy vấn, cộng các vùng theo mức liên quan, được **đặc trưng ảnh** 1.024 số.
- Đặc trưng ảnh được chuẩn hoá về độ dài 1.

### Nhánh chữ: hai bộ đặc trưng chữ cho 37 lớp

- **Theo prompt chung (như DBR-FPL).** Lắp 4 hàng prompt vào khuôn câu, được bảng 77 × 512, rồi cho qua 12 tầng transformer (đóng băng). Lấy ô [kết thúc], chiếu thành 1.024 số, chuẩn hoá độ dài 1. Làm cho cả 37 lớp được 37 vector t₁…t₃₇. Phần này phải tính lại mỗi vòng, vì prompt thay đổi.
- **Theo CLIP gốc (mới).** Câu viết tay của 37 lớp đi qua **cùng bộ đọc chữ đó**, được 37 vector z₁…z₃₇. Câu không đổi nên chỉ tính **một lần**, rồi dùng mãi.

### Hai giám khảo, một ý kiến chung

Với mỗi ảnh, đo độ giống (cosin) giữa đặc trưng ảnh và từng đặc trưng chữ, nhân 100, rồi đổi sang xác suất bằng softmax. Có hai bộ xác suất trên 37 lớp:
- **p_g**: ý kiến của mô hình chung. Mô hình này đã học từ nhãn của mọi client, kể cả nhãn sai.
- **p_z**: ý kiến của CLIP gốc. Mô hình này chưa từng học nhãn nào, nên không bị nhãn sai làm lệch. Với mỗi ảnh, p_z không đổi qua các vòng, nên client tính một lần rồi giữ lại.

Ý kiến chung **P = ½ (p_g + p_z)**: trung bình của hai giám khảo. Mọi bước sau đều dùng P.

### Độ bất ngờ của từng ảnh

Ý tưởng: nhãn chỉ đáng nghi khi nó **làm mô hình bất ngờ hơn mức chính mô hình tự dự kiến**.
- Mô hình đang phân vân giữa vài lớp (ảnh khó, hai giống chó rất giống nhau): nhãn nào trong các lớp đó cũng không gây bất ngờ.
- Mô hình đang rất chắc là một lớp khác: nhãn đó gây bất ngờ lớn.

Cách tính cho một ảnh có nhãn y:
1. **Gộp nhãn với lớp giống nhất của nó**, gọi là y⁺. Ví dụ y = "american bulldog" thì y⁺ = {american bulldog, american pit bull terrier}. Mô hình nhầm giữa hai giống này nên không tính là nhãn sai.
2. **Mức bất ngờ thực tế** = −ln P(y⁺), với P(y⁺) là tổng xác suất mô hình dành cho hai lớp đó. Nhãn càng ít được tin thì con số càng lớn.
3. **Mức bất ngờ dự kiến:** nếu nhãn được rút ngẫu nhiên đúng theo ý kiến P, thì trung bình mô hình sẽ bất ngờ bao nhiêu (cũng gộp lớp giống nhất như trên). Mô hình càng phân vân thì con số này càng lớn.
4. **Độ bất ngờ của ảnh** = mức thực tế − mức dự kiến.

Hai ví dụ:
- **Ảnh Beagle, nhãn đúng "Beagle", nhưng mô hình phân vân:** P(Beagle) = 0,45, P(Basset) = 0,40, còn lại rải rác. Gộp với lớp giống nhất được 0,85, nên mức thực tế = −ln 0,85 ≈ 0,16. Mức dự kiến cao (khoảng 0,9) vì mô hình đang phân vân. Độ bất ngờ ≈ 0,16 − 0,9 ≈ −0,7, tức **không đáng nghi**.
- **Ảnh Beagle bị ghi nhãn "Pug":** mô hình chắc 90% là Beagle; Pug cộng lớp giống nhất của Pug chỉ được 0,02. Mức thực tế = −ln 0,02 ≈ 3,9, mức dự kiến chỉ khoảng 0,5 vì mô hình đang rất chắc. Độ bất ngờ ≈ 3,4, tức **rất đáng nghi**.

### Điểm của client và việc đánh dấu

- **Điểm client s** = trung bình độ bất ngờ trên mọi ảnh của client.
  - Client sạch có điểm quanh 0 hoặc âm, **kể cả khi nó giữ lớp khó hay lớp hiếm**, vì điểm luôn so với độ phân vân của chính mô hình.
  - Client cẩu thả có điểm cao hẳn. Trên Pets, client sạch có 95% số lượt dưới 0,05, còn client cẩu thả thấp nhất là 0,35.
- **Đánh dấu:** client bị đánh dấu nếu **s > τ = 0,05**. Ngưỡng này lấy theo mức 95% điểm của client sạch trên Pets, khi cả 10 client đều sạch.
- **Khác DBR-FPL:** client không cần biết client khác ra sao. Nó tự so điểm của mình với một ngưỡng cố định, nên vẫn đúng khi không có ai nhiễu hoặc khi ai cũng nhiễu.
- Client gửi s và cờ đánh dấu lên server cùng prompt đã học.

### Chỉ client bị đánh dấu mới dọn ảnh

- **Không bị đánh dấu:** client học trên dữ liệu gốc, **không đụng tới ảnh nào**.
- **Bị đánh dấu:**
  1. **Ảnh nghi:** ảnh mà ý kiến chung chỉ tin nhãn dưới 10%, tức P(y) < 0,1. Xếp từ ít được tin nhất trở lên. Để an toàn, client không bao giờ đụng tới quá 60% số ảnh của mình.
  2. **Xử lý từng ảnh nghi:**
     - Nếu ý kiến chung đoán một lớp khác và tin lớp đó từ 50% trở lên: **sửa nhãn** sang lớp đó.
     - Nếu không: **tạm bỏ** ảnh này trong vòng hiện tại.

  Trên Pets, khoảng 90–98% ảnh nghi đúng là ảnh sai nhãn, và khoảng 79–86% số lần sửa nhãn là sửa đúng.

### Làm lại mỗi vòng

Khác DBR-FPL (chấm lại 5 vòng một lần), CLEAR-FPL **chấm lại mọi vòng**, luôn bắt đầu từ dữ liệu gốc (đủ mọi ảnh, nhãn gốc). Một ảnh bị bỏ hay sửa nhầm ở vòng này sẽ được xét lại ở vòng sau, khi mô hình chung đã tốt hơn. Một client bị đánh dấu nhầm cũng được xét lại ở vòng sau.

## Bước 3: Học cục bộ (mọi vòng)

Đây là bước duy nhất làm prompt thay đổi. Giống DBR-FPL, chỉ có một điểm khác: **không có trọng số**, vì CLEAR-FPL không có chế độ mềm.

Học trên nhãn nào, trong 1 lượt (1 epoch):
- client không bị đánh dấu: mọi ảnh, nhãn gốc;
- client bị đánh dấu: ảnh không nghi giữ nhãn gốc; ảnh nghi được sửa thì mang nhãn mới; ảnh nghi bị tạm bỏ thì không tham gia vòng này.

Chia nhóm 16 ảnh, xáo trộn ngẫu nhiên. Với mỗi nhóm:
1. Lắp prompt hiện tại (v₁…v₄) vào khuôn câu của 37 lớp, cho qua bộ đọc chữ, được 37 đặc trưng chữ.
2. Cho các ảnh trong nhóm qua bộ đọc ảnh, được đặc trưng ảnh.
3. Đo độ giống (cosin × 100), rồi đổi sang xác suất bằng softmax.
4. Tính sai số của từng ảnh so với nhãn của nó (cross-entropy), rồi lấy trung bình cả nhóm.
5. Truyền ngược sai số qua hai bộ đọc (vẫn đóng băng). Chỉ 4 hàng prompt nhận được hướng chỉnh.
6. Chỉnh 4 hàng prompt: tốc độ học 0,002, SGD có quán tính 0,9.

Ở bước này chỉ dùng prompt đang học. Dự đoán của CLIP gốc chỉ dùng ở Bước 2 để chấm điểm và sửa nhãn, không tham gia tính sai số khi học.

Ví dụ: ảnh Beagle bị ghi "Pug".
- Ở Bước 2, client bị đánh dấu, ảnh này là ảnh nghi (P(Pug) rất nhỏ), và ý kiến chung tin "Beagle" khoảng 90%, nên nhãn được sửa thành "Beagle".
- Ở Bước 3, ảnh này kéo prompt về đúng hướng thay vì dạy mô hình rằng ảnh Beagle là Pug.

## Bước 4: Gửi lên server

Client gửi bốn thứ:
- **prompt đã học** (4 × 512 = 2.048 số);
- **điểm s** (1 số);
- **cờ đánh dấu** (có hoặc không);
- **số ảnh n** đã học trong vòng (để server lấy trung bình có trọng số).

Ảnh, nhãn và CLIP luôn ở lại máy client. So với PromptFL, mỗi vòng chỉ gửi thêm 2 con số.

## Server kết thúc vòng

- Server lấy trung bình các prompt theo số ảnh (FedAvg), được prompt chung mới.
- Server ghi lại client nào bị đánh dấu ở vòng này, để báo cáo client nào có nhãn nhiễu.
- **Server không tính toán hay quyết định gì thêm:** không có mức lệch chuẩn, không có lệnh mềm hay cứng.
- Sang vòng sau, server chỉ gửi prompt chung xuống, rồi quy trình lặp lại từ Bước 1. Tổng cộng 50 vòng.
