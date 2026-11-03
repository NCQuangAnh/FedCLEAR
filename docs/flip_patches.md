# Các thay đổi so với FLIP gốc

- Gốc: https://github.com/0-ml/flip, commit `ec3a848b46f3c7d0030052f0c8a4401767d8c09f` (2025-11-19)
- Thư mục `flip/` là bản clone có git: `git -C flip diff` luôn cho thấy chính xác mọi thay đổi.
- Bản diff tại thời điểm viết: `docs/flip_patches.diff`.
- Chưa commit gì vào `flip/`.

| # | File | Thay đổi | Lý do |
|---|---|---|---|
| 1 | `flcore/models/clip/clip.py` | Dựng lại toàn bộ: `_MODELS`, `_download` (kiểm SHA256), `tokenize`, `load`, `load_clip_to_cpu(backbone, zero_shot=False, design_details=None)`. Thư mục cache chọn bằng biến môi trường `FLIP_CLIP_CACHE` | File trong repo gốc rỗng, nên mọi import đều lỗi. Viết theo loader OpenAI CLIP (MIT License) và hàm `load_clip_to_cpu` của CoOp/MaPLe, khớp chữ ký `build_model(state_dict, design_details)` trong `model.py` của FLIP |
| 2 | `flcore/utils.py` | Thêm `get_device(device_id)`: trả CUDA nếu có, không thì CPU | Để chạy smoke test trên máy không có GPU |
| 3 | `flcore/clients/client_base.py`, `flcore/servers/server_base.py`, `flcore/models/clip/base.py`, `flcore/models/text/prompt.py` | Thay `torch.device('cuda', id)` bằng `get_device(id)` | Như trên. Trên GPU hành vi không đổi |
| 5 | `flcore/datasets/imageloader.py`, `main.py` | Thêm lựa chọn `--data_transform default_norm` (transform gốc + Normalize) và `--data_transform paper` (Resize 240×240 → RandomCrop 224 → lật → Normalize, theo Appendix B.4). Giá trị không hợp lệ giờ báo lỗi, thay vì âm thầm trả về `None` | Giai đoạn 1: PromptFL/FedOTP thấp hơn paper 1,3–4,3 điểm, trong khi ZS-CLIP khớp. Nghi do train không Normalize. Mặc định `default` vẫn giữ nguyên như code gốc |
| 6 | `main.py`, `flcore/servers/server_base.py`, `flcore/utils.py` | Seed tường minh cho từng run: run thứ *r* của `--times` dùng seed `args.seed + r`, gieo lại trước khi chọn tập few-shot, trước khi chia client và trước khi khởi tạo prompt (`seed_everything`). Tên file kết quả đổi theo seed thật | Code gốc dùng chỉ số run làm seed chia client, còn bước chọn few-shot lấy RNG toàn cục nên phụ thuộc thứ tự chạy. Giai đoạn 2 cần so ghép cặp theo seed giữa các cấu hình |
| 7 | `flcore/utils.py`, `flcore/models/clip/{CoOp,ZSCLIP,FedOTP}.py`, `flcore/servers/{server_base,server_fedavg}.py`, `main.py` | Thêm `--cache_test_feats true`: tính trước đặc trưng ảnh của tập test một lần (encoder đóng băng, transform test tiền định) rồi dùng lại cho mọi round. Ba model nhận thêm tham số `image_features` | Bỏ phần tính lại encoder ảnh ở mỗi round, vốn chiếm phần lớn thời gian đánh giá. Kết quả giống hệt bản không cache |
| 8 | `flcore/datasets/imageloader.py` | Mỗi DataLoader có generator riêng, gieo từ seed của run | Tạo iterator của DataLoader rút một số từ RNG toàn cục, kể cả khi `shuffle=False`. Vì vậy chỉ cần thay đổi số lần lặp loader (ví dụ bật cache) là thứ tự batch khi train đã khác. Có generator riêng thì thứ tự batch chỉ phụ thuộc seed |
| 9 | `flcore/datasets/noise.py` (mới), `flcore/datasets/imageloader.py`, `flcore/servers/server_base.py`, `main.py` | Tiêm nhiễu nhãn theo client: `--noise_type {none,sym,pair,instance}`, `--noise_rate`, `--noise_mode {uniform,hetero}`, `--noisy_client_frac`, `--noise_oracle {none,clean,drop_noisy}`. Nhiễu vào **sau** bước chia Dirichlet, `loader.stats` được tính lại, `samples` chuẩn hoá về tuple `(path, int)`, mỗi client giữ `clean_targets`, mỗi lần chạy in một dòng `NOISE_REPORT {...}` và ghi `noise_seed_*.json`. `drop_noisy` lọc client **sau** khi `select_clients` đã rút xong, nên không đổi luồng RNG | Giai đoạn 2 cần nhiễu nhãn có kiểm soát, ghép cặp được với lượt sạch cùng seed, và cần hai mốc ORACLE để đo dư địa trước khi thiết kế phương pháp. Nhiễu phụ thuộc mẫu dùng pixel thô hạ mẫu, **không** dùng đặc trưng CLIP, để không rò rỉ đáp án vào chính tín hiệu phát hiện mà đồ án nghiên cứu |
| 10 | `flcore/attack.py` (mới), `flcore/robust_agg.py` (mới), `flcore/datasets/imageloader.py`, `flcore/servers/server_base.py`, `main.py` | Client độc hại và gộp model bền vững: vai trò rời nhau (`honest`/`noisy`/`malicious`), tấn công dữ liệu `targeted_flip` và `noise_disguise`, tấn công cập nhật `signflip` và `scale` (mô phỏng ở server nên code client không đổi), luật gộp `median`, `trimmed_mean`, `krum`, `multikrum`. Mỗi round ghi lại client nào được giữ, client nào bị loại, **kèm vai trò thật**, vào `noise_seed_*.json` | Giai đoạn 3 cần đo xem phòng thủ chuẩn có nhầm client nhiễu với client độc hại không. Krum nêu tên client nó tin, nên bản ghi đó biến giả thuyết thành con số. Khi `--malicious_client_frac 0` thì tập client nhiễu trùng đúng giai đoạn 2, nên vẫn ghép cặp được |
| 11 | `flcore/datasets/base.py` | `shutil.copy` ở ba chỗ dựng thư mục train/val/test đổi thành `place_file`: thử hard link trước, không được thì symlink, cuối cùng mới copy thật | Bước chia dữ liệu **nhân đôi toàn bộ ảnh** trên đĩa mỗi phiên Kaggle. Với Food101 là 101 nghìn file và khoảng 5 GB. Thư mục split không bao giờ sửa ảnh nên hard link là tương đương mà gần như không tốn gì. Symlink là đường lui khi nguồn nằm trên hệ tệp khác, ví dụ dữ liệu gắn sẵn ở `/kaggle/input` chỉ đọc |
| 4 | `flcore/models/clip/simple_tokenizer.py` | Nếu thiếu `bpe_simple_vocab_16e6.txt.gz` thì đọc bản đã giải nén `bpe_simple_vocab_16e6.txt` | Kaggle tự giải nén file `.gz` trong dataset upload lên, làm tokenizer lỗi `FileNotFoundError` (lỗi gặp ngày 2026-09-17). Đã kiểm: cả hai đường cho cùng token. Notebook cũng tự khôi phục file `.gz`, nên dataset cũ trên Kaggle vẫn chạy được |

**Đã kiểm:**
- Token của "a photo of a cat" = `[49406, 320, 1125, 539, 320, 2368, 49407]`.
- RN50 tải về khớp SHA256; image encoder trả tensor `[50, B, 1024]`.
- Smoke test CPU (`scripts/smoke_cpu.sh`) chạy hết ZS-CLIP, PromptFL, FedOTP.

**Chưa kiểm:** số trên dữ liệu thật. Đó là việc của notebook giai đoạn 1.

**Cố ý chưa sửa** (giữ nguyên để tái lập đúng code của paper, xem `docs/phase1_plan.md` mục 5):
- train không Normalize;
- server FedOTP khởi tạo client hai lần;
- `trainloader.stats` tính trước bước chia client;
- cách gieo seed.
