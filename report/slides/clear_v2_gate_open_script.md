# CLEAR v2: nhánh "cổng mở" (kịch bản thuyết minh)

Đi kèm hình `clear_v2_client_figure.html`, phần màu tím. Các con số ví dụ là minh hoạ, đã làm tròn; con số thật ghi rõ nguồn.

## 0. Nhánh này nằm ở đâu

- Bước 1 (chấm điểm client) và bước 3 (học prompt) giữ nguyên như CLEAR v1.
- Thay đổi chỉ nằm ở bước 2, khi client đã bị gắn cờ (s > τ). Trước khi chọn ảnh nghi, client hỏi: **cổng đang mở hay đóng?**
  - Cổng đóng, hoặc chưa tới vòng 6: chọn ảnh nghi đúng như v1 (P(nhãn) < 0,1, tối đa 60% số ảnh).
  - Cổng mở (từ vòng 6): đi nhánh màu tím, trình bày dưới đây.
- Client không bị gắn cờ thì vẫn học trên dữ liệu gốc, không bị đụng tới, dù cổng mở hay đóng.

## 1. Cổng quyết định thế nào (một lần, sau vòng 5)

1. **Vòng 1–5 chạy đúng CLEAR v1.** Mỗi vòng, mỗi client gửi thêm 2 con số: số ảnh nghi, và số ảnh trong đó được sửa nhãn (P chỉ ra một lớp khác với độ chắc ≥ 0,5).
2. **Sau vòng 5, server cộng dồn** hai con số này của mọi client, tính tỉ lệ "được sửa nhãn / ảnh nghi".
3. **Tỉ lệ này đo độ mạnh của trọng tài P.** Trọng tài mạnh thì khi nghi một nhãn, nó thường chỉ ra được lớp đúng một cách tự tin. Trọng tài yếu thì nghi nhưng không biết sửa thành gì. Trên các lần chạy CLEAR v1:

   | Bộ dữ liệu | Tỉ lệ sửa nhãn / ảnh nghi |
   |---|---|
   | Caltech101 | 0,79 – 0,88 |
   | Pets | 0,55 – 0,82 |
   | DTD | 0,13 – 0,29 |
   | MNIST | 0 – 0,15 |
   | EuroSAT | 0,03 – 0,06 |

4. **Luật mở cổng:** cận dưới một phía 95% (Wilson) của tỉ lệ trên ≥ 0,12 thì mở. Dùng cận dưới để vài ảnh nghi lẻ tẻ không đủ mở cổng. Ví dụ: 5/5 ảnh được sửa thì tỉ lệ là 100%, nhưng chỉ có 5 ảnh nên cận dưới thấp.
5. **Quyết định một lần**, áp dụng cho vòng 6 đến 50. Nếu cổng không mở, cả lần chạy là CLEAR v1, không khác gì.

Thực tế: cổng mở trên Pets, Caltech và DTD. Trên MNIST và EuroSAT cổng gần như luôn đóng (chỉ 1 seed mỗi bộ bật).

Lưu ý trung thực: ngưỡng 0,12 được chọn sau khi xem số liệu (mọi ngưỡng trong khoảng 0,06–0,18 đều cho kết quả tương tự). Để bù lại, phương pháp được kiểm chứng trên seed 8–10, là các seed chưa lần chạy nào dùng tới, với luật pass/fail viết trước khi chạy.

## 2. Hiệu chỉnh nhiệt độ T (mỗi vòng, khi cổng mở)

**Vấn đề:** P thường "rụt rè" (xác suất bị dàn mỏng), nên ngưỡng cố định như 0,1 lúc chặt quá, lúc lỏng quá tuỳ bộ dữ liệu. Ta muốn chỉnh P cho đúng mức tự tin trước khi dùng nó để xét nhãn.

1. **Mô hình nhãn của một client:** mỗi nhãn, với xác suất 1 − ε, được rút theo P đã chỉnh nhiệt độ (P_t); với xác suất ε, là một lớp bất kỳ (nhãn sai). ε là tỉ lệ nhãn sai của client đó.
2. **Mỗi client thử 25 mức nhiệt độ t** (từ 0,1 đến 2,0). Với mỗi t, client tìm ε khớp dữ liệu nhất và ghi lại độ khớp ℓ(t). Client gửi lên **25 con số** này, không gửi ảnh, không gửi nhãn.
3. **Server cộng 25 con số của mọi client**, chọn t khớp nhất, rồi **giới hạn T ≤ 1**. Server gửi T xuống mọi client.
4. **Vì sao nhãn sai không làm lệch T:** nhãn sai đã được ε "hút" vào phần ngẫu nhiên, nên client nhiễu nặng vẫn không kéo T đi. Ngay cả khi mọi client đều nhiễu, ta vẫn có một T dùng được.
5. **Vì sao chặn T ≤ 1:** P đã được làm mềm sẵn khi trộn với zero-shot CLIP. T > 1 là làm mềm thêm, và chuyện này chỉ xảy ra khi prompt đã học theo nhãn sai. Ví dụ: Pets, mọi client nhiễu 75% kiểu pair, T bị đẩy lên 2, tập dự đoán phình to, bỏ sót nhãn sai, rồi prompt học thêm nhãn sai ở vòng sau. Chặn T ≤ 1 cắt vòng luẩn quẩn này.

## 3. Chốt ε₀: tỉ lệ nhiễu tự ước lượng của client

1. Ở vòng hiệu chỉnh đầu tiên (vòng 6), mỗi client ghi lại ε của mình tại T vừa nhận. Đó là **ε₀**, giữ cố định tới hết.
2. **Vì sao chốt, không tính lại mỗi vòng:** càng về sau prompt càng học theo nhãn sai, khiến ε bị đánh giá thấp dần. Ví dụ thật: DTD, mọi client nhiễu pair 75%, seed 5, ε là 0,72 ở vòng 6 nhưng tụt còn 0,57 ở vòng 20.
3. **Ở vòng 6, ε₀ khá chính xác:** gộp cả client thì sai 0,00–0,03 so với tỉ lệ nhiễu thật trên Pets, Caltech và DTD. Tính riêng từng client thì sai trung bình 0,00–0,07, tệ nhất 0,29 (DTD).

## 4. Chọn ảnh nghi bằng tập dự đoán 95%

1. Client chỉnh P theo nhiệt độ T: P_T (lũy thừa 1/T rồi chuẩn hoá lại cho tổng bằng 1).
2. **Với mỗi ảnh**, xếp các lớp theo xác suất P_T. Tính **π = tổng xác suất của các lớp mà P_T đánh giá không cao hơn nhãn đang có**.
   - Nhãn là lớp P_T tin nhất thì π = 1: hoàn toàn bình thường.
   - Nhãn nằm ở đuôi, gần như không ai tin, thì π rất nhỏ.
3. **π < 0,05 thì ảnh bị nghi**, nghĩa là nhãn nằm ngoài "tập 95% lớp đáng tin nhất" của P_T. Đây là một phép kiểm định ở mức 5%, thay cho ngưỡng cứng 0,1.
4. **Bỏ trần 60%.** Ở 75% nhiễu, trần 60% là thứ chặn v1 lại: client có 75 nhãn sai trên 100 ảnh mà chỉ được sửa tối đa 60 ảnh.

Ví dụ minh hoạ (Pets, 37 lớp): nhãn "beagle", P_T cho "basset hound" 0,70, "beagle" 0,02, phần còn lại rải rác. Các lớp không cao hơn "beagle" cộng lại khoảng 0,03, tức π ≈ 0,03 < 0,05, nên ảnh bị nghi.

## 5. Sàn ε₀·n: không nghi ít hơn số nhãn sai mình tự ước lượng

1. **Vấn đề trên DTD:** CLIP yếu ở DTD (zero-shot 42%, 47 lớp), nên tập dự đoán 95% rất rộng. Nhiều nhãn sai vẫn lọt vào trong tập và không bị nghi. Số liệu thật: ở 75% nhiễu, client chỉ nghi 0,36–0,53 ảnh trên mỗi ảnh, trong khi chính nó ước lượng ε là 0,72–0,78.
2. **Luật sàn:** client bị gắn cờ phải nghi **ít nhất làm_tròn(ε₀ · n)** ảnh. Thiếu bao nhiêu thì bổ sung bấy nhiêu, lấy các ảnh có π nhỏ nhất (hoà thì lấy P_T(nhãn) nhỏ nhất), tức các nhãn kém hợp lý nhất.
3. Ví dụ minh hoạ: client có 100 ảnh, ε₀ = 0,75, nên sàn là 75 ảnh. Tập dự đoán chỉ bắt được 45 ảnh, client thêm 30 ảnh kém hợp lý nhất cho đủ 75.
4. **Không thêm con số nào phải chỉnh:** ε₀ là thứ đã ước lượng ở bước 3, dùng nguyên như vậy.

## 6. Sửa nhãn và học: giữ nguyên như v1

- Mỗi ảnh nghi: nếu P (bản gốc, chưa chỉnh nhiệt độ) chắc ≥ 0,5 về một lớp khác thì đổi nhãn sang lớp đó; không thì bỏ ảnh ra khỏi vòng này.
- Mọi quyết định làm lại từ dữ liệu gốc ở vòng sau, nên một lần sửa sai có thể được gỡ.
- Học prompt và gửi prompt lên server như v1. Server vẫn lấy trung bình có trọng số theo số ảnh còn lại.

## 7. Chi phí thêm

- **Truyền thông:** mỗi vòng có cổng mở, mỗi client gửi thêm 25 số và nhận 1 số (T). Ở vòng 1–5, mỗi client gửi thêm 2 số đếm. Quá nhỏ so với prompt 4 × 512 = 2.048 số.
- **Riêng tư:** không gửi ảnh, nhãn hay đặc trưng. 25 số chỉ là độ khớp tổng của client ở 25 mức nhiệt độ.
- **Thời gian:** khoảng 1,33–1,41 lần CLEAR v1, do phải tính P thêm một lượt mỗi vòng để gửi ℓ(t).

## 8. Kết quả, nói ngắn

- Kiểm chứng trên seed mới 8–10 với luật viết trước: không seed nào sụp (tệ nhất −1,86), tăng trung bình +4,40 điểm trên các bài khó, MNIST và EuroSAT không đổi. **Đạt cả 4 luật nên được chấp nhận.**
- Seed 0–4, tức số trong bảng (đã có Pets, Caltech; DTD đang chạy):

  | | CLEAR v1 | CLEAR v2 |
  |---|---|---|
  | Pets, pair 75% | 73,5 | 84,7 |
  | Pets, sym 75% | 78,4 | 83,9 |
  | Caltech, pair 75% | 74,9 | 83,8 |
  | Caltech, sym 75% | 83,0 | 87,8 |
  | DTD, sym 75% | 39,7 | 41,8 |
  | DTD, pair 75% | 39,1 | 40,4 |

  Các kịch bản còn lại (kịch bản 1, nhiễu 25/50%) lệch trong khoảng ±1.
- **Vì sao tăng:** số nhãn sai còn sót lại khi học giảm mạnh. Ví dụ Pets 75%: từ 0,22 xuống 0,11; Caltech 75%: từ 0,21 xuống 0,08.

## 9. Câu hỏi cô có thể hỏi

- **"Ngưỡng 0,12 có phải chỉnh cho đẹp không?"** Có chọn sau khi xem số liệu, và em nói rõ điều đó. Nhưng cả khoảng 0,06–0,18 đều cho kết quả gần nhau, và phương pháp được kiểm chứng trên seed mới với luật viết trước.
- **"Client sạch bị gắn cờ nhầm thì sao?"** Đây là rủi ro chính: client sạch có ε₀ bị ước lượng cao thì sàn sẽ bắt nó bỏ hoặc sửa một số ảnh đúng. Trên Pets và Caltech kịch bản 1 không thấy hại (lệch trong ±0,1). DTD kịch bản 1 đang chạy, chưa có kết quả.
- **"Sao không bỏ hẳn trần 60% trong v1 cho đơn giản?"** Bỏ trần mà không có cổng thì hỏng trên EuroSAT và MNIST, nơi trọng tài yếu. Cổng chính là để chỉ bật phần sửa mạnh tay ở nơi trọng tài đủ tin cậy.
- **"Sao phải chặn T ≤ 1?"** Ở bản chưa chặn T (gate), trên Pets pair 75% T bị đẩy lên 2: tập dự đoán quá rộng nên bỏ sót nhãn sai. Bản chặn T nhưng chưa có sàn (gatec) vẫn sụp một seed trên DTD (−5,1). Thêm sàn ε₀·n (gatef) thì hết sụp.
