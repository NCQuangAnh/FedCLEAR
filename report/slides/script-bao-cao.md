# Script báo cáo — slide 1 đến 20

Đi kèm `bao-cao-tien-do.html`. Mỗi slide khoảng 1 phút, tổng khoảng 20 phút. Chữ **đậm** là ý cần nhấn.

---

## Slide 1 — Lọc ảnh, không đuổi client

Em xin báo cáo tiến độ đồ án. Đề tài của em là học prompt liên kết trên mô hình CLIP, khi trong hệ thống có cả client gán nhãn cẩu thả lẫn client cố ý đầu độc, và mỗi client chỉ có rất ít ảnh.

Thông điệp chính của em gói trong tiêu đề: **chữa từng ảnh, không đuổi client.** Còn khi máy của client không đáng tin, server sẽ tự kiểm tra dữ liệu.

## Slide 2 — Federated prompt learning là gì

CLIP được giữ nguyên. Mỗi client chỉ học một đoạn prompt khoảng 2.000 con số trên ảnh của mình, rồi server lấy trung bình. Ảnh không bao giờ rời khỏi máy client.

Cách này nhẹ và chỉ cần 8 ảnh mỗi lớp. Nhưng ít ảnh thì **mỗi nhãn sai rất đắt**.

Con số −9,81 bên dưới là trên OxfordPets: khi có client nhiễu và kẻ gian, huấn luyện chung còn **kém hơn cả không huấn luyện gì**. Đồ án trả lời câu hỏi: làm sao cứu được, khi server không nhìn thấy ảnh hay nhãn nào.

## Slide 3 — Mỗi mảnh đã có người làm

Bảng này tổng hợp các hướng nghiên cứu liên quan. Mỗi hàng là một hướng, mỗi cột là một yếu tố của bài toán.

Hướng nào cũng chỉ phủ vài cột. Có bài làm prompt liên kết nhưng không có nhiễu, có bài làm nhiễu nhưng không có kẻ tấn công. **Chỉ hàng cuối, là đồ án này, phủ đủ cả bảy cột.**

## Slide 4 — Bài toán khác ở đâu

So với các bài hiện có, bài toán của em khác ở bốn điểm:
- Có **cả hai loại** client xấu trong cùng một hệ thống.
- Rất ít dữ liệu.
- Chỉ học 2.048 con số.
- Server **không có gì sạch** để dựa vào.

Ba điểm nổi bật: chưa tìm thấy ai làm bài toán này; đi ngược thói quen "đuổi client xấu" của lĩnh vực; và không cần dữ liệu sạch.

## Slide 5 — Ba loại client

Hệ thống có 10 client: 5 thật thà, 3 cẩu thả lật ngẫu nhiên 40% nhãn, và 2 kẻ gian lật 40% nhãn về **một lớp đích**.

Điểm khó là client cẩu thả và kẻ gian lật cùng một tỉ lệ, nên nhìn thống kê thì **trông giống hệt nhau**.

Kẻ gian có hai kiểu: kiểu 1 chỉ đầu độc dữ liệu; kiểu 2 chiếm quyền cả máy, em trình bày ở phần IV. Bảng dưới là các mốc: CLIP gốc, 10 client sạch, và mức tụt xuống khi có nhiễu và kẻ gian.

## Slide 6 — Hệ thống chạy thế nào

Sơ đồ đọc từ trái sang phải:
1. Mỗi client **tự lọc** những ảnh học mãi không thuộc, vì đó thường là ảnh sai nhãn.
2. Client chỉ gửi prompt lên server.
3. Server gộp prompt và gửi lại một "mức bẩn bình thường", để mỗi client biết mình được lọc tối đa bao nhiêu ảnh.

**Không client nào bị đuổi.** Sơ đồ này dành cho kẻ gian kiểu 1, vì máy của nó vẫn chạy bộ lọc.

## Slide 7 — Toàn bộ tham số

Phần huấn luyện giữ đúng giao thức chuẩn của benchmark FLIP, để so sánh được với các bài khác: CLIP RN50, 10 client, 50 vòng, 8 ảnh mỗi lớp, dữ liệu chia lệch mạnh.

Phần của đồ án là ô "Bộ lọc": chấm lại mỗi 5 vòng, có vùng miễn trừ cho client sạch, lọc tối đa 60% ảnh, sửa nhãn khi mô hình chung chắc từ 50% trở lên. Server có thêm giới hạn độ lớn cập nhật và kiểm ảnh đại diện cho kẻ gian chiếm máy.

Mọi kết quả đều chạy 5 seed và so ghép cặp.

## Slide 8 — Huấn luyện có thể tệ hơn không huấn luyện

Phát hiện đầu tiên: trên 2 trong 3 dataset, có kẻ gian thì huấn luyện chung **tệ hơn cả không huấn luyện**.

Lý do nằm ở bảng bên phải. Huấn luyện chỉ có lợi khi phần lãi lớn hơn phần bị lấy đi. Trên Pets, CLIP vốn đã nhận ra chó mèo 85,7%, nên phần lãi chỉ 2,4 điểm, rất dễ bị ăn hết.

Vì vậy em luôn so với mốc "không huấn luyện gì", và dùng chỉ số trung bình 10 vòng cuối thay vì vòng tốt nhất.

## Slide 9 — Giao một việc chỉ kẻ gian mới từ chối

Nhìn prompt thì không phân biệt được cẩu thả với cố ý. Nên server **giao một việc**: sửa nhãn theo mô hình chung rồi học lại.
- Client cẩu thả không có gì để mất nên làm theo.
- Kẻ gian mà làm theo thì mất luôn chất độc, nên nó từ chối.

Server tự đo xem prompt học lại có đổi hướng không, **không tin con số nào client tự khai**.

## Slide 10 — Nhận ra được

Cách này nhận ra kẻ gian rất tốt: AUC 0,99 trên DTD và 0,97 trên Pets.

Quan trọng hơn là phép thử khó: so riêng với client cẩu thả, vốn là nhóm dễ nhầm nhất. Tín hiệu của em **gần như không tụt**, còn tín hiệu cũ tụt về mức đoán mò.

Nhưng slide sau cho thấy: nhận ra được chưa có nghĩa là chữa được.

## Slide 11 — Nhận diện không phải bài toán

Đây là kết quả quan trọng nhất của phần đầu. Thang này xếp các cách can thiệp từ thấp đến cao.

Kể cả biết trước hoàn hảo và **đuổi kẻ gian ngay từ vòng 0**, cũng chỉ thêm khoảng 1 điểm. Đuổi cả 5 client hỏng còn **tệ hơn** không làm gì. Trong khi đó, xử lý ở **mức từng ảnh** hơn mức client 7,33 điểm.

Lý do: kẻ gian vẫn có 60% ảnh đúng. Đuổi nó là vứt luôn phần tốt đó.

## Slide 12 — Mỗi client tự lọc, trong một hạn mức

Phương pháp có ba bước:
1. **Ảnh nào đáng ngờ:** ảnh học mãi không thuộc. Không tốn thêm chi phí.
2. **Lọc bao nhiêu:** mỗi client báo một con số, server lấy mức của nhóm sạch nhất làm mốc; ai lệch hơn mốc bao nhiêu thì được lọc bấy nhiêu. Bảng cho thấy mức ước lượng khớp với mức hỏng thật.
3. **Xoá hẳn hay hạ trọng số:** tuỳ mô hình chung đang giỏi đến đâu.

Toàn bộ chạy trên máy client. Client chỉ gửi thêm một con số mỗi 5 vòng.

## Slide 13 — Bỏ nhầm ảnh sạch đắt hơn

Em đo được một "tỉ giá": bỏ nhầm một ảnh sạch đắt gấp **1,34 lần** bỏ đúng một ảnh bẩn. Nghĩa là trong số ảnh bị bỏ, phải có trên **57,3%** là ảnh hỏng thật, nếu không thì lọc càng nhiều càng hại.

Bảng bên trái xác nhận: bản bắt được nhiều nhưng kém chính xác thì thua. **Bắt đúng quan trọng hơn bắt nhiều.**

## Slide 14 — So với các mốc của lĩnh vực

So với cách phòng thủ chuẩn của lĩnh vực là gộp theo trung vị (median), phương pháp của em hơn **+1,75 điểm** trên DTD và **+4,66 điểm** trên Pets.

Em nói đúng mức: trên Pets mới là **hoà vốn** với CLIP gốc, chưa vượt. Nhưng nó biến một lượt huấn luyện đang lỗ 9,81 điểm thành hoà vốn.

## Slide 15 — Xoá hẳn hay hạ trọng số

Không cách nào thắng ở mọi nơi. Bộ lọc hay nhầm, như trên DTD, thì nên hạ trọng số; bộ lọc giỏi, như trên Pets, thì nên xoá hẳn.

Server **tự chọn** mà không cần nhãn thật: nó nhìn mô hình chung sai bao nhiêu trên các client sạch nhất. Kết quả bám sát lựa chọn tốt nhất, chỉ lệch 0,01 và 0,35 điểm.

## Slide 16 — Bài thi thật

Ngưỡng chọn chế độ được rút ra từ DTD và Pets, nên em thử lại trên **hai dataset mới** là EuroSAT và Caltech, với dự đoán ghi trước khi chạy.

**Cả hai dự đoán đều đúng.** Caltech lần đầu tiên vượt được CLIP gốc. EuroSAT thì luật chọn đúng, nhưng bộ lọc chỉ chính xác 31%. Nên luật chỉ giúp tránh cách gây hại, chưa tạo ra lợi ích. Đây là giới hạn em ghi rõ.

## Slide 17 — Sửa nhãn thay vì xoá

Từ đây là phần mở rộng. Với kẻ gian kiểu 1, máy nó vẫn chạy code của em, nên ảnh bị lật **sửa được**, không cần xoá.

Cách `K_fixconf`: khi mô hình chung đã giỏi, ảnh nghi mà mô hình chắc từ 50% trở lên thì sửa nhãn. So với oracle "trả lại mọi nhãn đúng", cách này **lấy lại được 80–87%**.

Em thử thêm cách chọn ảnh nghi theo nhóm: thắng lớn trên Pets (95%) nhưng thua trên Caltech, vì làm hỏng cả ảnh của client thật thà. Bản sửa có vùng miễn trừ đang chạy.

## Slide 18 — Kẻ gian thứ hai: chiếm quyền cả máy

Kẻ gian kiểu 2 không chạy bộ lọc, từ chối kiểm tra và khai man số liệu. Nó làm phương pháp **mất thêm tới 5 điểm**.

Em đã thử 5 cách ở phía server, với tiêu chí ghi trước cho từng cách. Cách hiệu quả là **giới hạn độ lớn cập nhật**: kẻ gian không lọc nên cập nhật to bất thường, bị thu nhỏ lại, còn client tốt gần như không bị ảnh hưởng. Cách này đạt trên cả 3 dataset. Cách cắt lớp đích thì em tưởng có tác dụng, nhưng thực ra không.

Bài học ở cuối slide: kể cả đuổi hẳn kẻ gian vẫn thiếu 3,4 điểm, vì mất luôn phần ảnh sạch của nó.

## Slide 19 — Kiểm tra bằng ảnh đại diện

Để giữ được phần sạch đó, em đổi giao thức một chút. Mỗi client gửi thêm **ảnh đại diện** cho từng nhóm ảnh cùng nhãn. Đó là trung bình đặc trưng CLIP, không phải ảnh gốc.

Server kiểm: nhóm có nhãn "Pug" mà trông như Pug thì giữ; trông như Beagle thì bỏ. Sau đó server dựng lại bản cập nhật chỉ từ phần qua kiểm tra.

Kết quả: **chạm mức oracle** trên cả Pets và Caltech, hơn cách tốt nhất trước đó 2–4 điểm. Cái giá là ảnh đại diện lộ nhiều thông tin hơn prompt; em đang làm tiếp phần bảo vệ riêng tư.

## Slide 20 — Lấy lại được bao nhiêu so với oracle

Slide này tổng hợp: phần trăm thiệt hại đã lấy lại được, so với mức tốt nhất có thể.
- **Kẻ gian đầu độc dữ liệu:** lọc và sửa nhãn trên máy client lấy lại **80–87%**.
- **Kẻ gian chiếm máy:** kiểm ảnh đại diện ở server lấy lại **khoảng 100%**.

Kết luận của em là **hai tầng cho hai kiểu kẻ gian**: máy đáng tin thì chữa từng ảnh ngay trên máy; máy không đáng tin thì server kiểm dữ liệu. Không tầng nào phải đuổi client.

---

## Nếu cô hỏi

- **"Oracle là gì?"** Là mức tốt nhất nếu biết trước mọi đáp án, dùng làm trần để đo phương pháp đạt bao nhiêu phần trăm.
- **"Vì sao không đuổi client xấu?"** Vì mỗi client giữ những lớp riêng. Đuổi đi là mất dữ liệu tốt: trên Pets có những giống chó mèo gần như chỉ kẻ gian có ảnh.
- **"Ảnh đại diện có lộ dữ liệu không?"** Có, nhiều hơn prompt, đây là cái giá của cách này. Hướng giảm rủi ro em sắp làm: gửi một lần thay vì mỗi vòng, gộp tối thiểu 5 ảnh và thêm nhiễu, hoặc chỉ gửi mức độ giống từng lớp.
- **"DTD thì sao?"** Trên DTD mô hình chung còn yếu nên kết quả thấp hơn. Em coi đó là giới hạn của phương pháp và ghi rõ trong đồ án.
