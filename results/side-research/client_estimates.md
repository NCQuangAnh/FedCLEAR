# Mỗi phương pháp đọc được gì về từng client

Sinh bởi `tools/analyze_client_estimates.py`. Cách đọc từng số: xem docstring của script.

## Phân biệt client nhiễu / client sạch (AUROC; 4 kịch bản có cả hai loại client, 5 seed)

| Phương pháp | Thời điểm | Pets | DTD | Caltech101 |
|---|---|---|---|---|
| CLEAR-FPL | vòng đầu | 1.00 | 0.99 | 1.00 |
| CLEAR-FPL | vòng cuối | 1.00 | 1.00 | 1.00 |
| DBR-FPL | vòng đầu | 0.90 | 0.81 | 0.99 |
| DBR-FPL | vòng cuối | 0.96 | 0.96 | 1.00 |
| NLPrompt (gốc) | vòng đầu | 0.87 | 0.80 | 0.96 |
| NLPrompt (gốc) | vòng cuối | 0.92 | 0.87 | 1.00 |
| NLPrompt (chỉnh) | vòng đầu | 1.00 | 0.93 | 1.00 |
| NLPrompt (chỉnh) | vòng cuối | 1.00 | 0.99 | 1.00 |
| FedCorr | vòng 0 | 0.38 | 0.46 | 0.72 |
| FedCorr | vòng 4 (hết tiền xử lý) | 0.51 | 0.54 | 0.79 |

## Sai số ước lượng tỉ lệ ảnh sai nhãn của client (điểm phần trăm; 11 kịch bản, 5 seed)

| Phương pháp | Thời điểm | Pets | DTD | Caltech101 |
|---|---|---|---|---|
| CLEAR-FPL | vòng đầu | 5 | 15 | 5 |
| CLEAR-FPL | vòng cuối | 5 | 11 | 4 |
| DBR-FPL | vòng đầu | 33 | 33 | 33 |
| DBR-FPL | vòng cuối | 23 | 25 | 26 |
| NLPrompt (gốc) | vòng đầu | 40 | 54 | 36 |
| NLPrompt (gốc) | vòng cuối | 32 | 43 | 21 |
| NLPrompt (chỉnh) | vòng đầu | 11 | 31 | 10 |
| NLPrompt (chỉnh) | vòng cuối | 7 | 14 | 5 |
| FedCorr | vòng 0 | 31 | 40 | 28 |
| FedCorr | vòng 4 (hết tiền xử lý) | 31 | 35 | 29 |

## Run đã dùng

- CLEAR-FPL Pets: 11/11 settings, 55 seed files
- CLEAR-FPL DTD: 11/11 settings, 55 seed files
- CLEAR-FPL Caltech101: 11/11 settings, 55 seed files
- DBR-FPL Pets: 11/11 settings, 55 seed files
- DBR-FPL DTD: 11/11 settings, 55 seed files
- DBR-FPL Caltech101: 11/11 settings, 55 seed files
- NLPrompt (gốc) Pets: 11/11 settings, 55 seed files
- NLPrompt (gốc) DTD: 11/11 settings, 55 seed files
- NLPrompt (gốc) Caltech101: 11/11 settings, 55 seed files
- NLPrompt (chỉnh) Pets: 11/11 settings, 55 seed files
- NLPrompt (chỉnh) DTD: 11/11 settings, 55 seed files
- NLPrompt (chỉnh) Caltech101: 11/11 settings, 55 seed files
- FedCorr Pets: 11/11 settings, 55 seed files
- FedCorr DTD: 11/11 settings, 55 seed files
- FedCorr Caltech101: 11/11 settings, 55 seed files
