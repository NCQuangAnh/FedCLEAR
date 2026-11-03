# Tóm tắt đồ án

Cập nhật: 2026-09-19. Số liệu trong bài lấy từ `results/`, mỗi con số đều có lượt chạy kèm theo.

## Bài toán, nói cho dễ hiểu

Hãy tưởng tượng mười bệnh viện cùng muốn huấn luyện chung một mô hình nhận dạng ảnh, nhưng không ai được gửi dữ liệu của mình đi đâu cả. Cách làm là **học liên kết** (federated learning): mỗi nơi tự huấn luyện trên dữ liệu của mình, rồi chỉ gửi **phần mô hình đã học** về máy chủ để gộp lại.

Gần đây có một cách làm rất tiết kiệm: lấy một mô hình thị giác–ngôn ngữ lớn đã huấn luyện sẵn như **CLIP**, **đóng băng toàn bộ**, và chỉ học một đoạn mô tả ngắn gọi là **prompt** — vài nghìn con số thay vì hàng trăm triệu. Mỗi nơi chỉ cần vài tấm ảnh mỗi lớp. Đó là **federated prompt learning**.

Vấn đề nảy sinh khi không phải nơi nào cũng đáng tin, và họ **không đáng tin theo hai kiểu khác hẳn nhau**:

- **Client gán nhãn sai (nhiễu):** thật thà, nhưng dán nhãn cẩu thả hoặc thiếu chuyên môn. Dữ liệu của họ **vẫn có giá trị**, chỉ là một phần nhãn bị sai.
- **Client độc hại:** cố tình phá, và thường **cố tình làm cho giống hệt một người gán nhãn cẩu thả** để không bị phát hiện. Dữ liệu của họ có **giá trị âm**.

Hai loại này cần **cách xử lý ngược nhau**: với client nhiễu phải **sửa nhãn rồi giữ lại**, còn với client độc hại phải **loại bỏ**. Xử lý nhầm chiều nào cũng hỏng — loại nhầm client nhiễu thì mất dữ liệu quý, giữ nhầm client độc hại thì mô hình bị đầu độc.

Rắc rối là **các phương pháp phòng thủ hiện có không phân biệt được hai loại**. Chúng đều nhìn vào một thứ duy nhất: cập nhật của client này lệch khỏi số đông bao nhiêu. Mà gán nhãn cẩu thả cũng làm cập nhật lệch.

## Những gì đồ án đã đo được

Ba điều sau không phải giả định, mà là kết quả đo trên ba bộ dữ liệu chuẩn (DTD, Caltech101, OxfordPets), mỗi kết quả 5–7 lần chạy độc lập:

1. **Nhiễu nhãn gây thiệt hại lớn.** Khi một nửa số client có 40% nhãn sai, độ chính xác mất **4,7 đến 13,2 điểm**. Trên hai trong ba bộ dữ liệu, mô hình sau huấn luyện còn **tệ hơn cả việc không huấn luyện gì** và dùng thẳng CLIP.
2. **Loại bỏ client nhiễu gần như vô ích.** Ngay cả một bộ phát hiện **hoàn hảo**, loại đúng mọi client nhiễu, cũng chỉ mua lại được tối đa **3,1 điểm** trên những bộ dữ liệu mà việc huấn luyện thực sự có ích — vì mất dữ liệu đắt gần bằng chính nhiễu. Trong khi sửa nhãn có thể mua lại toàn bộ 4,7–13,2 điểm.
3. **Phòng thủ chuẩn phân biệt sai đối tượng.** Luật gộp bền vững Multi-Krum loại client **nhiễu** với tần suất **gấp 17,7 lần** client thật thà, và trên OxfordPets việc bật nó lên còn làm mô hình **tệ hơn 1,6 điểm so với không phòng thủ gì**. Một tấn công cố tình nguỵ trang thành nhiễu gây thiệt hại 3,5–3,6 điểm mà vẫn lọt qua.

## Hướng giải quyết

Đồ án đề xuất **phân loại ba lớp rồi xử lý phân hoá**: client thật thà giữ nguyên, client nhiễu sửa nhãn rồi giữ lại, client độc hại loại bỏ.

Điểm mấu chốt là phải tìm được tín hiệu phân biệt, trong khi **máy chủ không được xem dữ liệu của ai, cũng không có sẵn một tập dữ liệu sạch nào**. Lời giải khai thác chính CLIP: vì CLIP biểu diễn ảnh và chữ trong cùng một không gian, **mô tả bằng chữ của mỗi lớp đóng vai một tấm ảnh đại diện**, cho máy chủ một bộ dữ liệu thử miễn phí mà không cần tấm ảnh nào. Từ đó tính hai tín hiệu **chỉ dựa vào prompt mà client gửi lên**:

- **độ trôi ngữ nghĩa** — prompt của client kéo khái niệm các lớp ra xa cách hiểu gốc của CLIP bao nhiêu; cao ở cả hai loại client xấu;
- **độ tập trung** — phần trôi đó **dồn vào một lớp** hay **rải đều ra nhiều lớp**. Gán nhãn cẩu thả thì sai lung tung; tấn công thì dồn về lớp mà kẻ tấn công muốn. Đây là tín hiệu tách hai loại.

## Đóng góp

1. Bằng chứng định lượng rằng trong federated prompt learning, client nhiễu và client độc hại **đòi hỏi cách xử lý ngược nhau**, và các phòng thủ hiện có **nhầm lẫn hai loại theo hướng có hại**.
2. Một họ tín hiệu phát hiện **không cần dữ liệu sạch, không cần xem dữ liệu client**, khai thác không gian ngữ nghĩa của chính mô hình đang được huấn luyện.
3. Một phát hiện về phương pháp đánh giá: chỉ số mà lĩnh vực này đang dùng — độ chính xác cao nhất qua các vòng — **làm nhẹ tác hại của nhiễu nhãn đi 1,4 đến 2,5 lần**, vì nó ngầm giả định một khả năng dừng đúng lúc mà bài toán không hề cho phép.

---

# Abstract (English)

Federated prompt learning adapts a frozen vision–language model such as CLIP by training only a small prompt, which makes federated learning practical when each client holds just a handful of labelled images. This work studies what happens when clients are unreliable in two different ways: **noisy** clients label carelessly, while **malicious** clients corrupt labels on purpose and deliberately imitate careless labelling to stay hidden.

We show the two require **opposite treatment**, and quantify it on DTD, Caltech101 and OxfordPets. With 40% label noise on half of the clients, accuracy drops by **4.7 to 13.2 points**, and on two of three datasets the trained model ends up **below the zero-shot CLIP floor**. Yet even a perfect detector that removes every noisy client recovers at most **3.1 points** wherever training is worth doing at all, because discarding their data costs nearly as much as the noise itself; correcting their labels, by contrast, could recover the full loss. Malicious clients are the opposite case: their contribution has negative value and must be removed.

Standard robust aggregation cannot make this distinction. It ranks clients by how far an update deviates, and careless labelling deviates too: Multi-Krum excludes noisy clients **17.7 times more often** than honest ones and leaves the model **1.6 points worse than no defense at all**, while a noise-disguised attack still costs 3.5–3.6 points.

We therefore propose a three-way triage with differentiated treatment, driven by signals computed from a client's prompt alone — no client data, no clean validation set. Using CLIP's shared image–text space, each class's text embedding serves as a free probe image, which yields a semantic-drift signal that flags both kinds of unreliable client and a concentration signal that separates them: careless labelling scatters errors across classes, whereas an attack concentrates them on one.

We also report a measurement finding: the best-round accuracy this field reports understates label-noise damage by **1.4 to 2.5 times**, because it implicitly assumes an early-stopping ability the problem does not provide.
