# Kế hoạch lượt K — sửa nhãn thay vì xoá (ghi TRƯỚC khi chạy, 2026-09-25)

## Vì sao

Gate G loại bỏ hướng sửa nhãn, nhưng nó chỉ đo trên **DTD** và sửa **mọi** ảnh. Đo lại trên log
có sẵn (các client hỏng, sửa theo mô hình chung):

| | Nhãn gốc đúng | Mô hình chung đúng | Sửa mọi ảnh thì |
|---|---|---|---|
| DTD | 61% | 51% | lỗ — vá 1.456, phá 2.457 |
| OxfordPets | 74% | 81% | lãi — vá 923, phá 617 |
| Caltech101 | 75% | 86% | lãi — vá 1.712, phá 883 |

Thang oracle trên DTD: trả nhãn đúng hơn xoá đúng **+2,37**. Hướng này chưa từng được thử ở nơi nó
có thể thắng.

## Thay đổi

Trong nhánh **xoá hẳn** của bộ lọc: ảnh bị nghi mà mô hình chung đoán **khác** nhãn thì thay nhãn bằng
đoán của mô hình chung và **giữ lại**, thay vì xoá. Ảnh bị nghi mà mô hình chung đồng ý với nhãn thì
vẫn xoá như cũ.

Chạy dưới `--filter_soft auto`, nên sửa nhãn **chỉ xảy ra khi server đã chọn xoá hẳn** — tức khi mô
hình chung đủ giỏi. Mô hình chung yếu thì không bao giờ được ghi đè nhãn.

Nhãn được tính lại từ bộ gốc mỗi 5 vòng, nên một nhãn sửa sai có thể được sửa lại.

## Nhánh

| Nhánh | Sửa khi nào |
|---|---|
| `K_fix` | mọi ảnh bị nghi mà mô hình chung không đồng ý |
| `K_fixconf` | như trên, nhưng chỉ khi mô hình chung chắc ≥ 50%; còn lại xoá |

Thêm nhánh `K_base` = phương pháp hiện tại (`H_auto`) chạy lại với **kẻ gian mới**, để hai nhánh K
được so với một mốc chỉ khác đúng một thứ. So `K_base` với `H_auto` cũ cho biết riêng việc đổi kẻ
gian làm thay đổi bao nhiêu.

### Kẻ gian mới (từ lượt K trở đi)

Kẻ gian **chỉ đầu độc dữ liệu**: máy nó chạy phần mềm chuẩn, làm đủ mọi bước — huấn luyện, tự lọc,
sửa nhãn, và trả lời bài kiểm tra tuân thủ **trung thực**. Kẻ gian cũ (gate E–J) còn từ chối bài kiểm
tra — việc chỉ kẻ chiếm được máy mới làm nổi — nên một client mô phỏng đang trộn hai kiểu. Các lượt
cũ giữ kẻ gian cũ (`--attacker_model legacy`) để tái lập đúng số.

## Dự đoán

| | `H_auto` hiện tại | Dự đoán `K_fix` |
|---|---|---|
| OxfordPets | 85,15 | +0,5 đến +1,5 |
| Caltech101 | 88,72 | +0,5 đến +1,5 |

Cơ sở: chỉ sửa **ảnh bị nghi** thì tỉ lệ vá/phá phải tốt hơn con số "sửa mọi ảnh" ở trên, vì trong số
ảnh bị nghi có 85–94% là ảnh hỏng thật — và ở ảnh hỏng thì chỉ có "vá" hoặc "vẫn sai", không thể "phá".

Rủi ro đã biết: với client **độc hại**, mô hình chung có thể đã học một phần lớp đích của kẻ tấn công,
nên có thể "sửa" ảnh về đúng lớp đích đó. Đo được bằng số "phá" ở client độc hại.

## Tiêu chí

| Kết quả | Đọc là |
|---|---|
| Một nhánh K hơn `K_base` với p < 0,05 trên ít nhất một dataset, và không kém hơn 0,3 ở dataset kia | **sửa nhãn thắng**, thành chế độ thứ ba của luật |
| Hơn `K_base` nhưng không đạt p < 0,05 | hướng đúng chiều nhưng chưa đủ bằng chứng; ghi lại, không thêm seed trước khi có lý do mới |
| Kém `K_base` | sửa nhãn thua cả khi thầy giỏi; đóng hẳn hướng này |

Kèm theo, dù kết quả nào: báo số nhãn **vá / phá** theo từng loại client, từ nhật ký kiểm toán.

## Chạy

`MODE = "gate_k_relabel"`, 5 seed.
- 5a `["oxford_pets"]` — ~4 giờ (3 nhánh)
- 5b `["caltech101"]` — ~9 giờ (3 nhánh), đặt `BUDGET_HOURS = 10`

Kỳ vọng thêm: `K_base` ≈ `H_auto` cũ (lệch < 0,5), vì trong các lượt đó kết quả bài kiểm tra không
được dùng vào quyết định nào.

## Addendum, 2026-09-25: the offline test of other relabel rules (written before the data exists)

The K_fix audit on Pets shows two kinds of loss: a clean suspect whose label gets overwritten
(12% of relabels on malicious clients), and a dirty suspect that gets moved to another wrong
class (about 23% of relabels on noisy and malicious clients). The runs on disk do not keep the
global model's per-sample guesses, so no other rule can be scored from them.

`MODE = "gate_k_diag"` reruns K_fix on OxfordPets (5 seeds, about 1.3 h) with
`--filter_relabel_log true`. Every refresh then logs each sample's label, its true label, whether
it was a suspect, and the global model's top 3. `tools/score_relabel_rules.py` scores these rules
on the same suspects:

| Rule | Relabel a suspect only if |
|---|---|
| A client prior | the choice is re-ranked by the client's own label histogram, capped at the median class size so an attacker's target class gets no extra pull |
| B stable | the first choice is the same as at the previous refresh |
| D no over-full | the choice is not a class holding more than 2x the median class size |
| A + D, A + B | both conditions |
| margin 0.2 | the first choice leads the second by at least 0.2 (for comparison) |

Value is priced against deleting the suspect: +0.437 for each right relabel and −0.326 for each
wrong one, per 1000 label-rounds.

Decision rule, fixed now:
- A rule becomes a GPU arm only if its total value beats K_fix by at least 20%, and its right-rate
  on malicious clients is no lower than K_fix's.
- Otherwise the relabel line stays at K_fix, and the Caltech result decides it.
- The accuracy of `K_fix_log` must match `K_fix` (same seeds). If it differs by more than 0.3,
  the logging changed the run and the offline scores are not trusted.
