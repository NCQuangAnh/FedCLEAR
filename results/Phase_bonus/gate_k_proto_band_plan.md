# Gate K_proto_band plan (written 2026-09-28, before any run)

## Why

`K_proto` won big on Pets (+1.71 over `K_fixconf`, 95% of the gap to the all-clean oracle) and lost on
Caltech (−1.04). The audit (`K_results.md`) names two reasons, and `K_fixconf` has a safeguard against
each:
1. `K_proto` checks every client, so about 6% of an honest client's clean clusters fail and get
   relabelled or deleted. That is ~7,200 harmed honest label-rounds on Caltech, 20x `K_fixconf`.
   `K_fixconf` leaves alone any client inside the **clean band**.
2. `K_proto` relabels from round 0 with the global + zero-shot average, and 10% of its relabels break a
   clean label (Caltech), against 4% for `K_fixconf`. `K_fixconf` relabels only in **hard rounds**,
   when the server has judged the global model good, and with the global model as teacher.

`K_proto_band` = `K_proto`'s way of FINDING suspects, inside `K_fixconf`'s safeguards.

## How the three compare

| Step | `K_fixconf` (current) | `K_proto` | **`K_proto_band`** |
|---|---|---|---|
| Which clients are touched | only those outside the clean band (disagreement > baseline + 0.10) | **all** | only those outside the clean band (as `K_fixconf`) |
| How many images per client | a budget from the client's estimated contamination | no budget (cap 60%) | no budget (cap 60%) |
| Which images are suspects | the highest-loss images, up to the budget | every image of a label cluster that neither the global model nor zero-shot CLIP reads as the label | as `K_proto` |
| Soft round (global model not yet good) | suspects down-weighted by loss rank | relabel / delete anyway | suspects down-weighted **to their label's support** (global + zero-shot average) |
| Hard round (global model good) | suspect whose teacher reading differs: relabel if ≥ 50% sure, else delete | same rule, teacher = global + zero-shot average | same rule, **teacher = global model** (as `K_fixconf`) |
| Suspect the teacher agrees with | deleted | kept | kept |

The only difference between `K_proto_band` and `K_fixconf` is how suspects are chosen: by cluster,
without a budget, instead of by loss rank. The soft-round weight also follows from that, since there
is no loss rank among cluster suspects. Nothing is tuned: the band 0.10, the 50% bar, K = 3 and the
60% cap are all taken unchanged from the earlier gates.

## Arm (`MODE = "gate_k_proto"`, `K_ARMS = ["K_proto_band"]`, data-only attacker, 5 seeds)

Pets (~1.3 h) and Caltech (~3.3 h). `K_base`, `K_fixconf`, `K_proto` and `K_restore` are in the notebook's
references (same seeds).

## Criteria, fixed now

- **Main.** `K_proto_band > K_fixconf` with p < 0.05 on at least one of Pets and Caltech, and not more
  than 0.3 worse on the other.
- **The Caltech repair worked.** Honest clients' harmed label-rounds (broken + deleted) are no more
  than 2x `K_fixconf`'s on both datasets.
- **The Pets gain survived.** Damage caught (recall) on noisy and malicious clients is ≥ 85% on Pets,
  and `K_proto_band` is at least 1.0 above `K_fixconf` on Pets.
- **Report** the share of the gap to `K_restore` closed, for every K arm.

If the main criterion fails, `K_fixconf` stays, and the thesis reports the cluster check as a
dataset-dependent option: strong where the per-image filter leaves room (Pets), harmful where it
does not (Caltech).
