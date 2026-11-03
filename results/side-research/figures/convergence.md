# Tốc độ hội tụ

Vòng đầu tiên mà độ chính xác trung bình 5 seed đạt 95% mức last10 của chính phương pháp đó; trong ngoặc là last10. Sinh bởi `tools/plot_curves.py`.

| bộ dữ liệu | kịch bản | CLEAR-FPL | DBR-FPL (cũ) | NLPrompt (gốc) | NLPrompt (chỉnh) | PromptFL |
|---|---|---|---|---|---|---|
| Pets | 3 client nhiễu đều 40% | 2 (88.0) | 2 (86.9) | 3 (88.0) | 2 (87.2) | 1 (80.5) |
| Pets | mọi client nhiễu cặp 50% | 2 (86.9) | 0 (58.3) | 3 (85.3) | 0 (70.1) | 0 (53.4) |
| Pets | mọi client nhiễu đều 75% | 1 (78.4) | 0 (42.7) | 3 (80.9) | 1 (74.7) | 0 (39.6) |
| Pets | mọi client nhiễu cặp 75% | 0 (73.5) | 0 (32.8) | 2 (75.3) | 0 (51.4) | 0 (28.8) |
| DTD | 3 client nhiễu đều 40% | 20 (53.4) | 23 (53.3) | 26 (48.2) | 27 (52.4) | 18 (51.9) |
| DTD | mọi client nhiễu cặp 50% | 16 (47.4) | 5 (33.9) | 19 (43.7) | 9 (41.9) | 4 (32.7) |
| DTD | mọi client nhiễu đều 75% | 6 (39.7) | 0 (24.5) | 11 (38.2) | 6 (35.5) | 0 (23.7) |
| DTD | mọi client nhiễu cặp 75% | 5 (39.1) | 0 (17.5) | 11 (37.8) | 0 (28.1) | 0 (16.1) |
| Caltech101 | 3 client nhiễu đều 40% | 1 (89.8) | 2 (89.8) | 1 (89.5) | 1 (89.9) | 2 (87.8) |
| Caltech101 | mọi client nhiễu cặp 50% | 1 (87.7) | 0 (69.3) | 1 (86.9) | 0 (82.9) | 0 (65.8) |
| Caltech101 | mọi client nhiễu đều 75% | 0 (83.0) | 5 (64.9) | 2 (85.5) | 0 (80.3) | 0 (62.4) |
| Caltech101 | mọi client nhiễu cặp 75% | 0 (74.8) | 0 (36.1) | 1 (83.9) | 0 (62.5) | 0 (33.1) |
