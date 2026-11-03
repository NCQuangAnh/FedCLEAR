# Gate K_proto plan: find suspects by cluster, relabel image by image (written 2026-09-28, before any run)

## Why

Gate K's relabel mode (`K_fixconf`) selects suspects image by image, from the loss ranking and the
global model's per-image reading. Gate P showed that a label cluster's centroid is read far more
reliably than one image: relabelled clusters failed the check 90-100% of the time, clean ones
passed 90-94%. In gate K the attacker's machine runs our code, so its flipped images can be
repaired, not just dropped. The goal is the all-clean ceiling, not `L_oracle60`.

One cluster can mix several source classes: an attacker relabels images of all its classes into one
target. So the cluster only decides who is a suspect, and each suspect is relabelled on its own.
The user pointed this out, and it is why the whole cluster is never given one label.

## Method (`correction.proto_select`, `--sample_filter proto`)

This runs on the client's own machine, at every filter refresh (every 5 rounds). Nothing extra
leaves the client.
1. For each label, k-means (K = 3) on its images' CLIP features.
2. A cluster passes if the round's global prompt OR CLIP's zero-shot template reads its centroid as
   the label. Every image of a failing cluster is a suspect.
3. For each suspect, the average of the global and zero-shot readings of that image predicts its
   class:
   - the prediction is its label: keep it;
   - the prediction is ≥ 0.5 confident: relabel it to that class;
   - otherwise: delete it.

There is no budget and no soft mode. The thresholds (K = 3, 0.5, the equal-weight average) are fixed
here and not tuned.

## Arms (`MODE = "gate_k_proto"`, data-only attacker, 5 seeds, Pets and Caltech)

| Arm | What |
|---|---|
| `K_proto` | the method above |
| `K_restore` | ORACLE, the all-clean ceiling in this exact configuration: every damaged label, noisy and malicious, put back, with no filter and no probes |

`K_base`, `K_fix` and `K_fixconf` are in the notebook's references (same seeds).

## Criteria, fixed now

- **Main.** `K_proto > K_fixconf` with p < 0.05 on at least one of Pets and Caltech, and not more than
  0.3 worse on the other.
- **Suspect quality**, reported per role: the share of suspects that are really damaged, and the
  share of all damage they catch. Compared with `K_fixconf`'s filter precision (Pets: noisy 89%,
  malicious 84%).
- **Safety.** Honest clients' broken labels no higher than under `K_fixconf`. ASR not above `K_fixconf`'s.
- **Report**, for every K arm: the share of the gap closed,
  (arm − no defence) / (`K_restore` − no defence). "No defence" = `A0_refuse`.

If `K_proto` does not beat `K_fixconf`, `K_fixconf` stays and the cluster check is reported as helping
only where the device is untrusted (gate P).

## Amendment after the first CPU smoke, before any GPU run

On random synthetic data both readers are at chance, every cluster fails, and every suspect was
deleted. That emptied a client and crashed its data loader. `proto_select` now applies the same safety
cap as the loss filter (`--filter_max_frac`, 0.6): never delete more than 60% of a client's images.
The deletions kept are those whose own label the readers support least. The report carries
`capped`. On Pets and Caltech this should almost never fire; how often it fires is reported.
