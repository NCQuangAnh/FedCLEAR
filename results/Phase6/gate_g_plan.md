# Gate G: ngưỡng tự tin cho phần sửa nhãn (ghi trước, 2026-09-22)

## 1. Vì sao

Gate F đóng lại một hướng và mở ra một hướng khác. Loại bỏ client là cần gạt sai: nhận diện đúng 7–9 trong 10 kẻ tấn công, chạm 0–1 trong 25 client thật thà, mà accuracy chỉ +0,65 ± 1,41. Thứ duy nhất có lãi chắc chắn trong cả đồ án là **sửa nhãn**: +0,86 trên DTD, +1,01 trên OxfordPets (p = 0,008), và lãi **ngay cả khi không có kẻ địch nào**.

Nhưng phiên bản sửa nhãn mà Gate E và Gate F đo là bản **ngây thơ nhất có thể**: `pseudo_labels` lấy `argmax` của model toàn cục và ghi đè **mọi** nhãn, không hỏi model có chắc không.

| | Tỉ lệ nhãn đúng trên DTD |
|---|---|
| Client cẩu thả, `sym` 40% | **60%** |
| Model toàn cục (`N_control` = 52,06) | **~52%** |

Trên DTD, cái gọi là "sửa" đang **lấy đáp án tệ hơn đè lên bài tốt hơn**. Nó vẫn ăn được 0,86 điểm, vì lỗi của model toàn cục nhất quán còn nhãn nhiễu thì lật ngẫu nhiên, nhưng trần bị chặn ở trình của thầy — và tệ hơn, thầy đang xoá cả những câu học sinh vốn làm đúng.

Điều này giải thích luôn vì sao Pets ăn nhiều hơn DTD: model toàn cục trên Pets đúng ~81%, thầy giỏi hơn hẳn.

## 2. Thay đổi

`--correction_conf` cộng `--correction_conf_mode`. Chỉ nhận đáp án ở những ảnh model **chắc chắn**; còn lại **giữ nguyên nhãn của client**.

Dùng **quantile theo từng client** làm mặc định, không phải ngưỡng tuyệt đối. Lý do: CLIP có `logit_scale ≈ 100` nên softmax cực nhọn, và một ngưỡng tuyệt đối hợp trên Pets sẽ vô nghĩa trên DTD. Đồ án đã bị dataset-dependence cắn ba lần (Gate C hai lần, luật loại trừ một lần); không lặp lại lần thứ tư. Quantile thì **mỗi client tự hiệu chỉnh với chính mình**.

`--correction_conf 0.75` nghĩa là: để yên 75% số ảnh, chỉ sửa **25% ảnh mà model chắc nhất**. `0.0` là bản cũ, sửa tất.

Số nhãn thực sự bị thay được ghi vào log và vào bản ghi probe (`n_replaced`, `n_total`), nên lượt chạy tự nói ngưỡng rơi vào đâu.

## 3. Tiêu chí (ghi trước, không sửa sau khi nhìn số)

Quét `CONF_QUANTILES = [0.5, 0.75, 0.9]`, **cả hai chế độ**, 5 seed, DTD.

| # | Điều kiện | Ngưỡng | Nếu trượt |
|---|---|---|---|
| **G1** | **Là luật gộp.** Không có kẻ tấn công: bản có ngưỡng hơn bản không ngưỡng | ≥ **+1,0 điểm** ở **≥ 2 trong 3** mức | Ngưỡng không phải chỗ thiếu; phần sửa nhãn dừng ở +0,86/+1,01 và viết đúng như vậy |
| **G2** | **Là phòng thủ.** Có kẻ tấn công: hơn lượt không phòng thủ | ≥ **+2,0 điểm** ở **≥ 1** mức | Sửa nhãn không phải phòng thủ; chỉ báo cáo nó như luật gộp |

Yêu cầu "≥ 2 trong 3 mức" ở G1 là cố ý: một mức đơn lẻ vượt ngưỡng có thể là may, ba mức phải cho thấy **xu hướng**.

Mốc để so:

| | DTD |
|---|---|
| `N_control` (không sửa nhãn, không tấn công) | 52,06 |
| `N_audit` (sửa nhãn, không ngưỡng) | 52,92 (**+0,86**) |
| `A0_refuse` (có tấn công, không phòng thủ) | 47,56 |
| `A1_refuse_audit` (sửa nhãn, không ngưỡng) | 48,93 (**+1,37**) |
| `M0_median` (phòng thủ chuẩn của lĩnh vực) | 49,01 (+1,46) |

G2 đặt ở +2,0 vì đó là mức **vượt hẳn `median`**, thứ cho tới giờ vẫn hoà với ta.

## 4. Cái này kiểm được gì mà các cổng trước không kiểm

Mọi cổng trước đều hỏi "**nhận ra ai xấu được không**". Gate F trả lời: được, và không giúp gì.

Gate G hỏi câu khác hẳn: "**chữa được bao nhiêu, mà không cần biết ai xấu?**" Không client nào bị đuổi, không ai bị gán nhãn, không giả định gì về số kẻ địch. Nếu G1 đạt thì đóng góp của đồ án là một **luật gộp có sửa nhãn cho federated prompt learning**, và phần phát hiện kẻ từ chối (AUC 0,91–0,99) trở thành kết quả phụ mạnh chứ không phải trụ chính.

## 5. Nếu cả G1 và G2 đều trượt

Dừng thí nghiệm. Viết bài đo đạc theo `docs/phase6_plan.md` mục 5, với luận điểm của Gate F:

> Nhận diện giải được. Phản ứng thì không. Cần gạt mà cả lĩnh vực đang dùng — loại client ra khỏi phép gộp — là cần gạt sai trong bối cảnh few-shot, và sửa nhãn thì bị chặn bởi chính độ chính xác của model toàn cục.

Đó vẫn là một bài có nội dung, chỉ là không có phương pháp thắng.
