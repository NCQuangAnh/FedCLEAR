# FPL-Triage: phân loại client nhiễu nhãn và client độc hại trong federated prompt learning

Đồ án tốt nghiệp, bắt đầu 2026-09-17.

**Đọc trước:**
- `docs/abstract.md` — tóm tắt, tiếng Việt và tiếng Anh. Giải thích bài toán cho người đọc lần đầu.
- `docs/overview.md` — tổng quan đầy đủ: bài toán, ba mệnh đề đã đo, phương pháp, vị trí so với các bài liên quan, kỷ luật đánh giá.

**Hướng nghiên cứu:**
- Federated prompt learning trên CLIP, few-shot, có client gán nhãn sai (vô tình) và client độc hại (cố ý).
- Mục tiêu: tách được hai loại client, rồi xử lý khác nhau: sửa nhãn và giữ client nhiễu, loại client độc hại.
- Cơ sở chọn hướng và mức độ trùng với các bài đã có: `docs/literature/`.

## Cấu trúc

```
FPL-Triage-17.9.2026-thesis/
├── flip/                 FLIP (0-ml/flip @ ec3a848) + bản vá, là code chính
├── tools/                công cụ: tạo dữ liệu giả, đọc log, đóng gói code, sinh notebook
├── scripts/              smoke_cpu.sh: chạy thử trên CPU
├── kaggle/               notebook Kaggle, mỗi giai đoạn một file (sinh bởi tools/build_kaggle_notebook.py)
│   ├── phase1_reproduce.ipynb   tái lập FLIP (đã chạy xong, giữ làm bằng chứng)
│   ├── phase2_gate_a.ipynb      nhiễu nhãn và hai mốc ORACLE
│   ├── phase3_gate_b.ipynb      tấn công giả nhiễu và phòng thủ chuẩn
│   └── phase4_gate_c.ipynb      tín hiệu phát hiện, đo khả năng tách ba vai trò
├── docs/
│   ├── abstract.md       tóm tắt đồ án (Việt + Anh)
│   ├── overview.md       tổng quan: bài toán, số liệu, phương pháp, vị trí học thuật
│   ├── phase1_plan.md    kế hoạch, tiêu chí tái lập, những điểm phát hiện trong code FLIP
│   ├── phase2_plan.md    bộ tiêm nhiễu, các mốc ORACLE, tiêu chí Gate A ghi trước
│   ├── phase3_plan.md    client độc hại, tấn công giả nhiễu, gộp bền vững, tiêu chí Gate B
│   ├── phase4_plan.md    ba tín hiệu tính từ prompt, tiêu chí Gate C, kẻ tấn công thích nghi
│   ├── phase5_plan.md    tín hiệu phản ứng khi sửa nhãn, tiêu chí Gate D, điểm dừng đã cam kết
│   ├── flip_patches.md   danh sách thay đổi so với FLIP gốc (+ flip_patches.diff)
│   └── literature/       literature review giai đoạn 0, 0b, 0c
├── refs/                 PDF các bài tham khảo (không commit)
├── results/              nơi để kết quả tải về từ Kaggle
└── dist/                 file zip để upload lên Kaggle (sinh bởi tools/package_code.py)
```

## Tiến độ

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| 0, 0b | Literature review, kiểm tra novelty | Xong |
| 1 | Dựng pipeline trên FLIP, tái lập PromptFL / FedOTP / ZS-CLIP | **Xong (2026-09-18).** 9/9 ô đạt tiêu chí ghi trước, 4,76 giờ T4. Nguyên nhân lệch ban đầu: code FLIP public không chuẩn hoá ảnh lúc train, sửa bằng `--data_transform paper`. Có seed tường minh và cache đặc trưng tập test (kiểm là không đổi kết quả) |
| 2 | Đo dư địa nhiễu nhãn, cổng Gate A | **Xong (2026-09-18), 5,14 giờ T4, 3 dataset.** Nhiễu 40% lấy đi 4,7–13,2 điểm (theo `last10`), nhưng loại bỏ client nhiễu gần như vô ích vì mất dữ liệu đắt ngang nhiễu. Theo `last10`, 2/3 dataset tụt xuống dưới cả zero-shot. Kết quả: `results/Phase2/gate_a_results.md` |
| 3 | Trục client độc hại, cổng Gate B | **Xong (2026-09-19, 9,4 giờ T4).** B1 đạt (7 seed: +3,62 DTD p = 0,019; +3,51 Pets p = 0,001), B2 đạt trên DTD, B3′ đạt trên Pets. Gộp bền vững chỉ có tác dụng ở 1/4 tổ hợp, và tổ hợp đó đạt được bằng cách không phân biệt client nào cả; `multikrum` loại client nhiễu gấp 17,7 lần client thật thà. Kết quả: `results/Phase3/gate_b_results.md` |
| 4 | Tín hiệu phát hiện, cổng Gate C | **Đã chạy (2026-09-20, 6,40 giờ).** Gate C không đạt, nhưng hai dataset trượt ở hai tiêu chí khác nhau theo một quy luật: `s_sem` chỉ hoạt động khi zero-shot đã gần trần, `s_conc` chỉ hoạt động khi huấn luyện làm prompt di chuyển nhiều. Tấn công mức cập nhật thì bị bắt trên cả hai (AUC 0,98 và 0,81). Còn: kiểm quy luật trên Caltech101 (~3 giờ, dự đoán đã ghi trước). Kết quả: `results/Phase4/gate_c_results.md` |
| 5 | Tín hiệu phản ứng khi sửa nhãn, cổng Gate D | **Đã chạy (2026-09-20, 7,03 giờ). Trượt cả ba tiêu chí.** `r_align` tách client từ chối sửa khỏi client thật thà gần như hoàn hảo nhưng **ngược dấu** so với dự đoán, và lượt đối chứng có lỗi thiết kế nên trộn lẫn "từ chối tuân thủ" với "dữ liệu bị đầu độc". Đã sửa; còn một lượt đối chứng (~2,2 giờ) rồi **dừng theo cam kết và viết luận văn**. Kết quả: `results/Phase5/gate_d_results.md` |
| 6 | Xử lý phân hoá và đo lợi ích cuối cùng bằng accuracy | Chưa, phụ thuộc Gate D |

## Chạy nhanh

**Smoke test trên CPU** (chỉ kiểm code chạy được, độ chính xác vô nghĩa):

```bash
pip install torch torchvision ftfy regex h5py termcolor tensorboard opencv-python-headless scikit-learn matplotlib pandas tqdm
bash scripts/smoke_cpu.sh
```

**Tái lập trên Kaggle:** xem `docs/phase1_plan.md` mục 7.
- Đóng gói bằng `python tools/package_code.py`.
- Upload thành private dataset.
- Chạy `kaggle/phase1_reproduce.ipynb`.

## Lưu ý

- FLIP không có LICENSE. Giữ Kaggle dataset private; muốn công bố code thì hỏi tác giả trước.
- Sửa notebook bằng cách sửa `tools/build_kaggle_notebook.py` rồi chạy lại script (nó sinh cả hai file), không sửa tay file `.ipynb`.
