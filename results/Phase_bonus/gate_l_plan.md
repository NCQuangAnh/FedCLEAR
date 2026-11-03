# Kế hoạch lượt L — kẻ gian nắm cả máy (ghi TRƯỚC khi chạy, cập nhật 2026-09-25)

## Kẻ gian kiểu 2 (`--attacker_model device`)

| Bước | Client thường | Kẻ gian kiểu 2 |
|---|---|---|
| Lật nhãn | — | 40% nhãn về **một lớp đích riêng của nó** (mỗi kẻ gian bốc lớp đích khác nhau) |
| Bài kiểm tra tuân thủ | làm theo | **từ chối**, khai số liệu như thể đã làm |
| Tự lọc / sửa nhãn | có | **không làm** |
| Con số độ lệch gửi server | số thật | **khai man**: gửi đúng mốc sạch vòng trước |

Phương pháp phía client không chạm được vào kẻ gian này. Server không thể tách chính xác 60% sạch
khỏi 40% độc trong một bản cập nhật — mọi cách phía server chỉ là **giảm hoặc cắt một phần** ảnh
hưởng của nó, và phải được phát biểu đúng như vậy.

## Bốn nhánh (mỗi dataset: DTD, OxfordPets, Caltech101; 5 seed 0–4)

| Nhánh | Server làm gì |
|---|---|
| `L_base` | không thêm gì (phương pháp hiện tại) |
| `L_down` | phát hiện ai từ chối → **giảm trọng số theo tỉ lệ bằng chứng**: trọng số = mức tuân thủ của client / mức tuân thủ trung vị, kẹp trong [0, 1]. Xét lại mỗi lần kiểm tra, nghi oan thì tự phục hồi |
| `L_tdr` | **cùng bộ phát hiện từ chối như `L_down`**, nhưng client bị nghi **giữ nguyên trọng số** và bị **cắt hướng lớp đích**: đoán lớp nó kéo các lớp khác về (chỉ bằng bộ mã hoá chữ, không cần ảnh), cộng dồn bằng chứng qua các vòng, chỉ khi nổi bật ≥ 3 độ lệch chuẩn thì cắt **phần vượt mức trung vị** theo hướng đó. **Client không bị nghi — kể cả client cẩu thả — không bao giờ bị cắt**: nhiễu của client cẩu thả được sửa ngay trên máy nó |
| `L_tdr_early` | như `L_tdr`, nhưng server **biết kẻ gian ngay từ vòng 0** (oracle chỉ về *ai*, lớp đích vẫn phải tự đoán). Chênh `L_tdr_early − L_tdr` = mức tối đa mà mọi cách xử lý ~15 vòng đầu chưa phát hiện — kể cả quay ngược kiểu FedRecover — có thể đem lại |
| `L_oracle60` | **trần**: kẻ gian chỉ học trên 60% ảnh sạch của nó (gian lận có chủ đích, không phải phương pháp) |

### Các con số đã cố định trước, không chỉnh sau

| Tham số | Giá trị | Căn cứ |
|---|---|---|
| Trọng số khi bị nghi | tỉ lệ theo `r_align` | để bằng chứng quyết định; thay cho con số 0,25 trước đây vốn không có căn cứ |
| Bộ phát hiện từ chối | k = 2, sàn 0,12, chờ 3 lần | đã hiệu chỉnh ở Gate E |
| TDR: độ nhớ bằng chứng | 0,8 | kẻ gian cố định qua mọi vòng |
| TDR: ngưỡng tự tin | 3 độ lệch chuẩn (trung vị + MAD) | ngưỡng chuẩn cho giá trị ngoại lai |
| TDR: chờ | 3 vòng | như bộ phát hiện từ chối |
| TDR: cắt bao nhiêu | đúng phần vượt trung vị (λ = 1) | không có hệ số tự chọn |
| TDR: hướng lớp | **dùng hướng thô, không trừ phần chung** | kiểm CPU: hướng thô đã đủ khác nhau (cos trung bình 0,22 DTD / 0,26 Pets, không cặp nào > 0,9); trừ phần chung lại làm **trùng hơn** (0,69 / 0,77) |
| Giới hạn độ lớn | 2 × trung vị | chặn bản cập nhật bị phóng đại |

## Đo gì

1. **last10** trên bộ test (như mọi lượt).
2. **ASR mới**: với mỗi kẻ gian, trong ảnh test **không** thuộc lớp đích của nó, bao nhiêu phần trăm
   bị đoán thành lớp đích.
3. **Độ chính xác trên ảnh thật của lớp đích** — để biết cách cắt có làm hỏng phần sạch không.
4. **Tỉ lệ cứu được** = (nhánh − `L_base`) / (`L_oracle60` − `L_base`).
5. Nhật ký TDR: lớp đích đoán ra so với lớp đích thật, và TDR cắt nhầm ở client không phải kẻ gian
   bao nhiêu.

## Dự đoán

| | `L_base − H_auto cũ` | `L_down − L_base` | `L_tdr − L_base` |
|---|---|---|---|
| DTD | −1 đến −2 | +0,5 đến +2 | 0 đến +1 |
| OxfordPets | −2 đến −4 | +0,5 đến +2 | ≈ 0 (đoán lớp đích chỉ đúng 23% số vòng) |
| Caltech101 | −1 đến −2,5 | +0,5 đến +2 | +0,5 đến +2 (đoán đúng 45–55% số vòng) |

Cơ sở cho cột TDR: phép kiểm ngoại tuyến trên các lượt không phòng thủ — đoán đúng lớp đích 39% số
vòng (DTD), 23% (Pets), 45% (Caltech), so với mức đoán mò 1–3%.

## Tiêu chí

| Kết quả | Đọc là |
|---|---|
| Một nhánh hơn `L_base` với p < 0,05 trên ≥ 2/3 dataset, **ASR giảm**, và độ chính xác lớp đích **không giảm quá 2 điểm** | phòng thủ **đạt**; đưa vào hệ thống cho lượt M |
| Hơn nhưng không đạt p < 0,05 | đúng chiều, chưa đủ bằng chứng |
| Không hơn, hoặc ASR không giảm | **trượt**; ghi rõ kẻ gian kiểu 2 là giới hạn của phương pháp |
| TDR cắt ở client không phải kẻ gian > 20% số lần cắt | TDR **không an toàn**, loại bất kể điểm (giờ chỉ xảy ra khi bộ phát hiện nghi oan) |

**Quyết định về 15 vòng đầu, ghi trước:** nếu `L_tdr_early − L_tdr` < 0,5 điểm trên cả 3 dataset thì
chấp nhận các vòng đầu bị vấy bẩn và không xây cơ chế quay ngược; nếu lớn hơn thì xây, và đã biết trần.

`L_down` và `L_tdr` dùng **cùng một** bộ phát hiện, nên hiệu giữa hai nhánh đo đúng một câu hỏi:
với client đã bị nghi, **giảm trọng số** hay **cắt hướng lớp đích** giữ lại được nhiều phần tốt hơn.

## Chạy

`MODE = "gate_l_device"`, 5 seed. Tài khoản chạy song song tối đa 2 phiên, mỗi phiên ≤ 12 giờ:
- 6c `["caltech101"]`, `L_ARMS = ["L_base", "L_down", "L_tdr"]` — ~9 giờ, `BUDGET_HOURS = 10` (đang chạy)
- 6x `["caltech101", "dtd"]`, `L_ARMS = {"caltech101": ["L_tdr_early"], "dtd": L_ALL}` — ~9,5 giờ, `BUDGET_HOURS = 10`
- 6y `["caltech101", "oxford_pets"]`, `L_ARMS = {"caltech101": ["L_oracle60"], "oxford_pets": L_ALL}` — ~9,5 giờ, `BUDGET_HOURS = 10`

6x và 6y thay cho 6a, 6b, 6d cũ. Seed cố định nên các nhánh Caltech ở ba phiên khác nhau vẫn so cặp được.

Song song với lượt K được.
