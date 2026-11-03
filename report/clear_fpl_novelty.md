# CLEAR-FPL: phần kế thừa và phần mới

Tra cứu ngày 2026-10-25, tra nhanh trên web (chưa rà toàn bộ tài liệu). "Chưa thấy" nghĩa là không tìm ra trong lần tra này, chưa phải chứng minh chưa ai làm.

## Bảng thống kê

| # | Thành phần của CLEAR | Kế thừa / tham khảo | Mức trùng | Ghi chú |
|---|---|---|---|---|
| 1 | Bối cảnh: học prompt CLIP liên kết (FL) có nhãn nhiễu | PromptFL / FLIP; NLPrompt (CVPR 2025, chỉ một máy) | Kế thừa | Bối cảnh, không phải đóng góp |
| 2 | Dùng CLIP zero-shot làm "trọng tài" không bị nhãn nhiễu làm hỏng | CLIPCleaner (ACM MM 2024), DeFT (NeurIPS 2024), Wu và cs. (ICCV 2023), SRRS (IJCAI 2025) | Trùng ý tưởng | Các bài này đều chạy trên một máy, soi từng ảnh |
| 3 | Gộp dự đoán mô hình chung với CLIP zero-shot: P = ½(p_global + p_zs) | CLIPSelector (trong DeFT); SRRS lấy trung bình hai bộ prompt | Trùng một phần | Phép trộn đơn giản; điểm mới là dùng nó để chấm client trong FL |
| 4 | Gộp nhãn với lớp gần nhất theo CLIP (y⁺) trước khi chấm | CLIPCleaner nói CLIP "biết" các lớp giống nhau, nhưng không gộp lớp | **Chưa thấy** | Tránh phạt nhầm các lớp dễ nhầm với nhau |
| 5 | **Điểm "ngạc nhiên vượt mức"**: −log P(y⁺) − E_{k~P}[−log P(k⁺)] | Về toán, đây là "độ lạ trừ độ lạ kỳ vọng" (≈ mất mát trừ entropy), cùng họ với *typicality*: Nalisnick và cs. 2019 (phát hiện dữ liệu lạ), Meister và cs. 2023 (sinh văn bản) | **Công thức không mới; cách dùng chưa thấy** | Chưa thấy bài nào dùng nó để chấm nhãn nhiễu hay chấm client. Các bài nhãn nhiễu dùng mất mát thuần + GMM |
| 6 | Chấm cả client (trung bình điểm), cắm cờ khi > τ = 0,05 (phân vị 95 của client trung thực, Pets sạch) | Tìm client nhiễu: FedCorr (LID + GMM), FedNoRo (mất mát theo lớp + GMM), FedLN (điểm năng lượng), ClipFL (tập kiểm định sạch), FedSIR (phổ đặc trưng) | Trùng hướng, khác thước đo | Mới: thước đo tự trừ phần "lạ do dữ liệu lệch", nên client sạch non-IID ít bị nghi oan |
| 7 | Chỉ client bị cắm cờ mới sửa nhãn | FedCorr, FedNoRo, FedSIR | **Trùng** | Kế thừa, cần trích dẫn |
| 8 | Ảnh nghi sai khi P(y) < 0,1; đổi nhãn nếu P ≥ 0,5, không chắc thì bỏ vòng đó | Lọc mất mát nhỏ, đổi nhãn khi đủ chắc: FedCorr (ngưỡng 0,5), FedDiv, DivideMix, SELFIE | **Trùng** | Kỹ thuật chung |
| 9 | Chặn trên: sửa tối đa 60% ảnh của một client | Chưa thấy đúng dạng | Chi tiết nhỏ | Chi tiết kỹ thuật, không nên nhận là đóng góp chính |
| 10 | Sửa tạm thời, mỗi vòng chấm lại từ nhãn gốc | Co-teaching, DivideMix chọn lại mỗi epoch (một máy). FedCorr, FedSIR đổi nhãn vĩnh viễn | Trùng một phần | Mới trong FL: không ghi đè, nên một lần sửa sai không bị giữ mãi |
| 11 | Máy chủ chỉ FedAvg thường; chỉ gửi P (τ gửi một lần); không loại client | FedNoRo, FedLN đổi cách gộp ở máy chủ; ClipFL loại client | Khác | Ưu điểm: không tốn thêm truyền tin, không đuổi client |

## Riêng phần chấm độ bất ngờ: có độc nhất không?

- **Công thức toán: không độc nhất.** "Độ lạ của nhãn trừ độ lạ trung bình" đã có từ trước dưới tên *typicality*, dùng để phát hiện dữ liệu lạ và để sinh văn bản. Khi viết, không nên nhận là "công thức mới".
- **Cách dùng: chưa thấy ai làm.** Cụ thể là ba thứ đi cùng nhau:
  1. dùng công thức này để chấm nhãn nhiễu, và chấm ở mức cả client;
  2. tính trên phân phối đã trộn CLIP zero-shot, không phải trên mô hình đang học (vốn đã bị nhãn nhiễu làm lệch);
  3. gộp lớp gần nhất (y⁺) trước khi chấm.
- **Tại sao cần trừ phần kỳ vọng:** client sạch nhưng dữ liệu lệch có mất mát cao, vì mô hình chung không quen lớp của nó. Nhưng khi đó mô hình cũng "phân vân" chung chung, nên độ lạ kỳ vọng cao theo. Lấy hiệu thì phần lạ do dữ liệu lệch bị trừ đi, chỉ còn phần lạ do nhãn sai.
- **Cách viết đề xuất:** "Chúng tôi đề xuất dùng độ ngạc nhiên vượt mức, cùng họ với typicality [Nalisnick 2019; Meister 2023], làm điểm chấm nhiễu cho từng client, tính trên phân phối có CLIP zero-shot làm mốc. Theo hiểu biết của chúng tôi, đây là lần đầu dùng trong học liên kết có nhãn nhiễu."
- **Bằng chứng thực nghiệm đã có:** ablation "dùng d cũ" thay cho điểm này làm DTD giảm 6–9 điểm; ablation "không trộn CLIP" giảm 4–7 điểm (DTD_comparison.md).

## Tài liệu

- FedCorr, CVPR 2022: https://openaccess.thecvf.com/content/CVPR2022/papers/Xu_FedCorr_Multi-Stage_Federated_Learning_for_Label_Noise_Correction_CVPR_2022_paper.pdf
- FedNoRo, IJCAI 2023: https://www.ijcai.org/proceedings/2023/0492.pdf
- FedSIR, 2026: https://arxiv.org/html/2604.20825v1
- FedDiv, AAAI 2024: https://arxiv.org/html/2312.12263v2
- ClipFL: https://arxiv.org/pdf/2411.07391
- FedLN: https://github.com/Nousphera/FedLN
- CLIPCleaner, ACM MM 2024: https://arxiv.org/abs/2408.10012
- DeFT, NeurIPS 2024: https://arxiv.org/html/2409.19696v1
- SRRS, IJCAI 2025: https://ijcai.org/proceedings/2025/568
- Wu và cs., ICCV 2023: https://arxiv.org/abs/2307.11978
- NLPrompt, CVPR 2025: https://arxiv.org/pdf/2412.01256
- Typicality, OOD văn bản (dẫn Nalisnick 2019, Meister 2023): https://www.lesswrong.com/posts/Kjo64rSWkFfc3sre5/detecting-out-of-distribution-text-with-surprisal-and
