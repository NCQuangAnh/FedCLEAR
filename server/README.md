# Chạy các lượt Caltech trên server Linux (qua VS Code Remote-SSH)

Bộ này chạy đúng các lượt như notebook Kaggle (cùng tham số, lấy từ `tools/make_notebook.py`), nhưng
trên GPU của server. Danh sách lượt chạy nằm ở `server/queue_caltech.txt`: 47 lượt, mỗi lượt
5 seed × 50 vòng, xếp theo thứ tự ưu tiên.

## 1. Kết nối và đưa code lên

1. VS Code → `Ctrl+Shift+P` → **Remote-SSH: Connect to Host…** → chọn server.
2. Mở terminal trên server: **Terminal → New Terminal**.
3. Kéo file `dist/fpl-triage-code.zip` từ máy mình vào cửa sổ Explorer của VS Code, thả vào thư
   mục home trên server. Sau đó giải nén:
   ```bash
   cd ~ && unzip -o fpl-triage-code.zip -d fpl-triage && cd fpl-triage
   ```

## 2. Môi trường Python (một lần)

```bash
nvidia-smi                                   # xem số GPU và bộ nhớ trống
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Nếu chưa có PyTorch dùng được GPU, tạo môi trường riêng. Chọn bản `cu121` hoặc `cu118` theo
phiên bản CUDA mà `nvidia-smi` hiện:

```bash
python3 -m venv ~/fplenv && source ~/fplenv/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Mỗi lần mở terminal mới, nhớ chạy `source ~/fplenv/bin/activate`.

## 3. Cài gói, tải dữ liệu và CLIP (một lần)

```bash
bash server/setup.sh
```

Script này:
- cài các gói còn thiếu;
- tải Caltech101 vào `~/fpl_data/caltech101` (khoảng 130 MB);
- chép file chia train/val/test có sẵn trong code;
- tải trọng số CLIP RN50 vào `~/.cache/clip`.

Muốn để dữ liệu ở chỗ khác thì chạy `DATA_ROOT=/duong/dan bash server/setup.sh`, và khi chạy
nhớ thêm `--data-root /duong/dan`.

## 4. Chạy thử nhanh (khoảng 5 phút)

Tạo một hàng đợi chỉ có 1 lượt rồi chạy chế độ thử:

```bash
echo "caltech101 S_sym_nlph" > /tmp/thu.txt
python server/run_queue.py --queue /tmp/thu.txt --gpus 0 --smoke
```

Chế độ `--smoke` chỉ chạy 1 seed × 2 vòng. Thấy `rc=0` là được. Sau đó xóa kết quả thử:

```bash
rm -rf results/server/thu
```

## 5. Chạy thật, trong tmux để không mất khi rớt SSH

```bash
tmux new -s fpl                       # mở phiên tmux
source ~/fplenv/bin/activate          # nếu dùng venv
mkdir -p results/server               # cho tee có chỗ ghi log
python server/run_queue.py --queue server/queue_caltech.txt --gpus 0 --per-gpu 3 \
    2>&1 | tee -a results/server/queue_caltech.out
```

- Thoát khỏi tmux mà vẫn để chạy: bấm `Ctrl+b`, thả ra, rồi bấm `d`.
- Quay lại xem: `tmux attach -t fpl`.

**Chọn `--per-gpu` và `--gpus`:**
- Mỗi lượt chạy cần khoảng 3–4 GB bộ nhớ GPU.
- GPU 24 GB thì để `--per-gpu 3` hoặc `4`. GPU 12–16 GB thì để `2`.
- Server có nhiều GPU thì ghi hết, ví dụ `--gpus 0,1,2,3`.

**Nếu bị dừng giữa chừng** (rớt mạng, lỗi, hoặc tự dừng bằng `Ctrl+c`), chạy lại đúng lệnh trên.
Các lượt đã xong sẽ tự bỏ qua.

## 6. Theo dõi

```bash
python server/run_queue.py --queue server/queue_caltech.txt --status   # lượt nào xong, last10
tail -f results/server/queue_caltech/logs/caltech101_N_sym50_clear.txt  # xem một lượt đang chạy
watch -n 30 nvidia-smi                                                  # GPU có đang bận không
```

## 7. Lấy kết quả về

```bash
cd ~/fpl-triage/results/server && zip -r queue_caltech.zip queue_caltech
```

Trong Explorer của VS Code, chuột phải vào `results/server/queue_caltech.zip` → **Download**,
rồi đặt vào `results/side-research/` trên máy mình. Có thể lấy về giữa chừng: các lượt đã xong
vẫn phân tích được.

## Thời gian ước tính

- Trên Kaggle T4, mỗi lượt Caltech mất khoảng 2,7–5 giờ, tùy phương pháp.
- Trên GPU mạnh hơn, chạy 3 lượt song song, 47 lượt mất khoảng 1,5–3 ngày với 1 GPU, chia
  theo số GPU nếu có nhiều.
- Lượt quan trọng nhất (NLPrompt trên 5 kịch bản chính, CLEAR-FPL khi mọi client nhiễu) nằm
  đầu hàng đợi.
