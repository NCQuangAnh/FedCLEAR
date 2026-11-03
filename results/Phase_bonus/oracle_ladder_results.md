# Thang oracle (chạy 2026-09-22, T4, 1,77 giờ, 3/3 job `rc=0`)

Dữ liệu: `results/Phase_bonus/oracle/`. DTD, 5 seed, ghép cặp theo seed với `A0_refuse` và `N_control`.

Oracle là **trần**, không phải phương pháp: chúng dùng `clean_targets` — nhãn thật mà bộ tiêm nhiễu giữ lại — thứ server không bao giờ có.

## 1. Thang

| Bậc | Can thiệp | `last10` | Lấy lại được | p |
|---|---|---|---|---|
| `L_clientdrop` | đuổi **cả 5 client hỏng** (oracle) | 46,25 ± 4,04 | **−1,31** | 0,427 |
| `A0_refuse` | không phòng thủ | 47,56 ± 2,90 | – | |
| `O_drop_mal` | đuổi 2 client độc hại (oracle) | 48,57 ± 2,02 | +1,02 | 0,131 |
| *(phương pháp tốt nhất đã đo)* | *sửa nhãn, liều 25/50* | *49,11* | *+1,56* | *0,045* |
| `L_drop` | **xoá đúng từng ảnh hỏng** (oracle) | 53,58 ± 1,05 | **+6,02** | **0,010** |
| `L_restore` | **trả lại nhãn thật** (oracle) | **55,94 ± 0,77** | **+8,39** | **0,002** |

## 2. Ba phép trừ đã định trước khi chạy

| Phép trừ | Kết quả | Ý nghĩa |
|---|---|---|
| `L_restore` − `L_drop` | **+2,37 ± 1,71**, p = 0,036 | Chữa một ảnh đáng giá hơn xoá nó 2,37 điểm |
| `L_drop` − `L_clientdrop` | **+7,33 ± 3,69**, p = 0,011 | Mức-ảnh hơn mức-client **7,33 điểm** |
| 55,61 (giai đoạn 1, sạch) − `L_restore` | **−0,33** | Nhãn bẩn giải thích **toàn bộ** khoảng cách |

## 3. Đọc ra ba kết luận, và một trong đó bác bỏ phát biểu trước đây của tôi

### 3.1. Nhãn bẩn **là** nút thắt. Khan hiếm dữ liệu thì không.

`L_restore` = **55,94**, trong khi baseline 10 client đều sạch của giai đoạn 1 là **55,61**. Chênh 0,33 điểm, nằm trong nhiễu.

Nghĩa là: **cùng bộ dữ liệu đó, cùng cách chia lệch Dirichlet α = 0,1 đó, chỉ cần nhãn đúng là đạt trần sạch.** Không còn gì cho "dữ liệu quá ít", "chia lệch", hay "prompt learning bất ổn" giải thích.

**Đây bác bỏ kết luận tôi đưa ra trước đó** ("nút thắt là dữ liệu, không phải nhiễu"). Phát biểu đó suy từ Gate A — bỏ 5 client mất 7,11 điểm còn nhiễu chỉ gây hại 6,82 — nhưng nó chỉ đúng cho **việc loại bỏ**, và tôi đã khái quát quá tay thành một phát biểu về toàn bài toán. Thang oracle cho thấy: **loại bỏ đắt vì mất dữ liệu, nhưng dữ liệu thì không thiếu — nhãn mới là thứ hỏng.**

### 3.2. Mức-ảnh hơn mức-client **7,33 điểm**, và mức-client thậm chí âm

`L_clientdrop` (đuổi cả 5 client hỏng, biết trước, từ vòng 0) ra **46,25 — thấp hơn cả việc không làm gì** (47,56).

Cộng với Gate F (oracle đuổi 2 client độc hại chỉ mua +1,02, không có ý nghĩa) và Gate B (gộp bền vững có tác dụng ở 1/4 tổ hợp), kết luận "loại bỏ client là cần gạt sai" giờ có **trần đo được**, trên **cả hai hướng**: đuổi ít thì gần như vô ích, đuổi nhiều thì có hại.

### 3.3. Chỉ cần biết ảnh nào hỏng, **không cần biết nhãn đúng**

`L_drop` lấy lại **6,02 trong 8,39 điểm — 72% của trần** mà **chỉ xoá**, không sửa gì.

Đây là tin tốt nhất về mặt kỹ thuật: bài toán "ảnh này có hỏng không" là **phân loại nhị phân**, dễ hơn hẳn bài toán "nhãn đúng của ảnh này là gì" (47 lựa chọn) — vốn đang bế tắc vì thầy chỉ đúng 47–52%.

2,37 điểm còn lại là phần thưởng cho việc **chữa** thay vì **xoá**, và đó là phần cần thầy giỏi. Để sau.

## 4. Khoảng cách giữa cái đạt được và cái đang có

| | Điểm |
|---|---|
| Trần (`L_restore`) | **+8,39** |
| Chỉ xoá (`L_drop`) | +6,02 |
| Phương pháp tốt nhất hiện có | **+1,56** |

Ta đang nắm **19% của trần**. Phần còn lại không bị chặn bởi bản chất bài toán — nó bị chặn bởi **việc chưa có bộ phát hiện ở mức ảnh**.

## 5. Bước tiếp theo, và nó rẻ

Câu hỏi duy nhất còn lại: **phân biệt ảnh hỏng với ảnh sạch, không cần oracle, tốt tới đâu?**

Đo được trong **một lượt ~15 phút, 1 seed**, cùng thủ thuật như lượt chẩn đoán trước: ghi cho từng ảnh `(loss, độ tự tin của thầy, thầy có đồng ý với nhãn không, ảnh này có thật sự hỏng không)`, rồi tính AUC ngoại tuyến cho **mọi tín hiệu ứng viên cùng lúc**:

| Tín hiệu | Cơ sở |
|---|---|
| **Small-loss** | Nhãn sai thì mô hình học mãi không thuộc, loss cao bất thường. Chuẩn mực của lĩnh vực nhãn nhiễu, ta **chưa từng thử** |
| **Thầy không đồng ý** | Thầy đúng 47–52% nói chung, nhưng ở nhóm chắc chắn nhất thì đúng 91,3% |
| **Hai thầy cùng đồng ý** | Model toàn cục cộng CLIP gốc — hai nguồn sai ở những chỗ khác nhau |
| **Ổn định qua các vòng** | Ảnh mà thầy đổi ý liên tục thì đáng ngờ |
| **Bất thường theo lớp trong một client** | Lớp bị đầu độc có tỉ lệ đồng ý gần 0, khác hẳn ~50% của lớp bình thường. Bắt được cả kẻ tấn công rải nhiều lớp đích |

Tín hiệu nào cho AUC cao thì xây phương pháp quanh nó, và mốc để đuổi theo là **53,58** (`L_drop`), không phải 55,94.
