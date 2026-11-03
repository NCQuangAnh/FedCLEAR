# Lượt J, phiên 4 — phép kiểm độc lập của luật chọn chế độ (chạy 2026-09-24/25, T4)

Dữ liệu: `results/Phase_bonus/J_/regime/{eurosat, caltech_ARM_A_H, caltech_ARM_H_H}`.
8/8 job `rc=0`, 5 seed mỗi job. Tiêu chí viết trước ở `gate_j_plan.md` mục 3.

Caltech101 chạy tách hai phiên (`A0_refuse`+`H_soft` rồi `H_band`+`H_auto`). Đã kiểm: cả 5 seed
có **cùng** cách chia dữ liệu, cùng vai trò client và cùng client độc hại ở hai phiên (so băm
`roles` + số ảnh mỗi client + danh sách kẻ tấn công), nên so ghép cặp giữa hai phiên hợp lệ.

## 1. Kết quả

| Nhánh | EuroSAT | Caltech101 |
|---|---|---|
| `A0_refuse` không phòng thủ | 55,61 | 84,52 |
| `H_soft` ép hạ trọng số | **56,49** (+0,88, p = 0,33) | 87,11 (+2,59, p = 0,001) |
| `H_band` ép xoá hẳn | 52,90 (**−2,71**, p = 0,047) | **88,72** (+4,20, p = 0,011) |
| `H_auto` server tự chọn | 56,00 (+0,39, p = 0,75) | **88,72** (+4,20, p = 0,005) |
| Nhánh thắng | hạ trọng số | xoá hẳn |
| Dự đoán ghi trước | hạ trọng số | xoá hẳn |

## 2. Tiêu chí: **đạt trên cả hai**

| | Server chọn xoá hẳn | Bám nhánh | Lệch so với nhánh thắng |
|---|---|---|---|
| EuroSAT | 6,0% số vòng | **thắng** (hạ trọng số) | −0,49 ± 1,10 (p = 0,37) |
| Caltech101 | 83,6% số vòng | **thắng** (xoá hẳn) | +0,01 ± 0,96 (p = 0,99) |

Tiêu chí ghi trước: *"`H_auto` bám nhánh thắng trên cả hai dataset → luật đứng vững; đây là đóng
góp riêng, viết được vào paper."* Cả hai **dự đoán chế độ** ghi trước khi chạy cũng đúng.

Mốc bẩn trung bình (`dis_baseline`) giờ xếp đúng thứ tự trên **bốn** dataset:

| Dataset | Mốc bẩn | Chế độ thắng |
|---|---|---|
| Caltech101 | 0,096 | xoá hẳn |
| OxfordPets | 0,135 | xoá hẳn |
| — ngưỡng 0,22 — | | |
| DTD | 0,344 | hoà |
| EuroSAT | 0,408 | hạ trọng số |

Ngưỡng 0,22 được khớp trên DTD và Pets **trước** khi thấy EuroSAT và Caltech101; hai dataset
mới rơi đúng hai phía.

## 3. Phải nói cho đúng mức

**EuroSAT: luật đúng, nhưng bộ lọc hỏng.** Độ chính xác bộ lọc chỉ **31–32%**, dưới hẳn ngưỡng
hoà vốn 57,3%, và nó lọc oan **16%** dữ liệu của client thật thà (toàn ảnh sạch). Hệ quả đúng như
mô hình tỉ giá dự đoán: xoá hẳn **hại** (−2,71), hạ trọng số gần như không giúp (+0,88, không có ý
nghĩa). Giá trị của luật ở đây là **tránh được chế độ gây hại**, không phải tạo ra lợi ích.

Nguyên nhân khả dĩ (chưa kiểm): EuroSAT chỉ có 10 lớp, chia Dirichlet α = 0,1 thì mỗi client giữ
1–2 lớp, nên "mức lệch bình thường" giữa các client khác nhau rất xa và mốc sạch không còn mô tả
được client sạch. Đây là giới hạn của **bộ ước lượng hạn mức**, không phải của luật chọn chế độ.

**Seed 4 của EuroSAT** là chỗ duy nhất luật trượt: chọn xoá hẳn 30% số vòng và thua 2,45 điểm so
với hạ trọng số. 4/5 seed còn lại trùng tới từng chữ số với nhánh hạ trọng số.

**Caltech101: kết quả tốt nhất từ trước tới nay.** Bộ lọc chính xác **91%**, client thật thà gần
như không bị đụng (0,1%). `H_auto` = 88,72 **vượt** CLIP không huấn luyện (85,76) **+2,96** —
dataset đầu tiên phương pháp đưa một liên đoàn bị tấn công lên **trên** mức zero-shot (Pets chỉ
tới hoà vốn). Còn cách PromptFL sạch (90,28) 1,56 điểm.

## 4. Kết luận

1. Luật chọn chế độ **qua được phép kiểm độc lập** trên hai dataset nó chưa từng thấy.
2. Phạm vi của luật: nó chọn đúng **cách tiêu hạn mức**. Nó không sửa được một **bộ lọc** kém —
   EuroSAT là ví dụ.
3. Điểm yếu mới lộ ra: bộ ước lượng hạn mức vỡ khi mỗi client chỉ giữ 1–2 lớp.

## 5. Việc tiếp theo

| # | Việc | Vì sao |
|---|---|---|
| 1 | Kẻ tấn công chiếm quyền máy (bỏ bước lọc) | Đã hứa, và là câu phản biện đầu tiên |
| 2 | Chẩn đoán bộ lọc trên EuroSAT | Lọc oan 16% client thật thà là bất thường; cần biết mốc sạch vỡ vì sao |
| 3 | Food101 | Nằm đúng ranh giới (~0,25), phép thử sắc nhất còn lại cho luật |
