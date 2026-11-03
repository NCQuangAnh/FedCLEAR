# Pooled-over-rounds client score (offline, stage 0 logs)

Generated 2026-11-01 by `tools/screen_traj.py` after the user asked whether an extra stage (start, middle or end) could improve MNIST / EuroSAT. s = CLEAR xs_m at round R; m = mean of s over rounds 5..R. Threshold for m and s: p95 of Pets honest clients. Result: pooling does not raise AUROC on MNIST (0.85 -> 0.85) or EuroSAT (0.88 -> 0.87); with an oracle threshold set on the dataset itself (5% honest flags), at most 58% (MNIST) and 61% (EuroSAT) of noisy clients are caught. The limit is the information in the score, not when it is read.

```

=== round 10: Pets-honest p95 threshold  per-round s -0.025 | running mean m -0.013
dataset    | AUROC s / m | CLEAR tau .05: hon / noisy / allN | s>p95: hon / noisy / allN | m>p95: hon / noisy / allN | oracle m @5% hon: noisy
MNIST      | 0.83 / 0.81 |   0 /  33 /  25 |   0 /  42 /  40 |   0 /  45 /  40 |  52   (n hon 87, noisy 33, allN 60; median m hon -0.28 noisy -0.12)
EuroSAT    | 0.85 / 0.81 |   3 /  58 /  55 |  15 /  67 /  67 |  24 /  67 /  68 |  45   (n hon 87, noisy 33, allN 60; median m hon -0.14 noisy +0.13)
Pets       | 0.98 / 1.00 |   2 /  91 /   — |   6 /  97 /   — |   6 /  97 /   — |  97   (n hon 87, noisy 33, allN 0; median m hon -0.30 noisy +1.86)
DTD        | 0.99 / 0.99 |   3 /  91 /   — |   5 /  91 /   — |   7 /  91 /   — |  91   (n hon 87, noisy 33, allN 0; median m hon -0.36 noisy +0.58)
Caltech101 | 0.99 / 1.00 |   0 /  91 /   — |   2 /  91 /   — |   1 / 100 /   — | 100   (n hon 87, noisy 33, allN 0; median m hon -0.32 noisy +2.32)

=== round 20: Pets-honest p95 threshold  per-round s -0.054 | running mean m -0.023
dataset    | AUROC s / m | CLEAR tau .05: hon / noisy / allN | s>p95: hon / noisy / allN | m>p95: hon / noisy / allN | oracle m @5% hon: noisy
MNIST      | 0.82 / 0.82 |   0 /  42 /  28 |   2 /  48 /  43 |   0 /  45 /  40 |  52   (n hon 87, noisy 33, allN 60; median m hon -0.30 noisy -0.12)
EuroSAT    | 0.86 / 0.85 |   2 /  55 /  38 |  18 /  70 /  67 |  17 /  67 /  70 |  58   (n hon 87, noisy 33, allN 60; median m hon -0.17 noisy +0.12)
Pets       | 0.99 / 1.00 |   2 /  94 /   — |   6 /  97 /   — |   6 /  97 /   — |  97   (n hon 87, noisy 33, allN 0; median m hon -0.32 noisy +1.66)
DTD        | 1.00 / 0.99 |   0 /  91 /   — |   1 /  94 /   — |   1 /  91 /   — |  94   (n hon 87, noisy 33, allN 0; median m hon -0.39 noisy +0.59)
Caltech101 | 0.98 / 1.00 |   0 /  91 /   — |   3 /  94 /   — |   1 / 100 /   — | 100   (n hon 87, noisy 33, allN 0; median m hon -0.36 noisy +2.14)

=== round 30: Pets-honest p95 threshold  per-round s -0.051 | running mean m -0.032
dataset    | AUROC s / m | CLEAR tau .05: hon / noisy / allN | s>p95: hon / noisy / allN | m>p95: hon / noisy / allN | oracle m @5% hon: noisy
MNIST      | 0.85 / 0.84 |   0 /  48 /  27 |   1 /  48 /  40 |   0 /  48 /  40 |  48   (n hon 87, noisy 33, allN 60; median m hon -0.30 noisy -0.12)
EuroSAT    | 0.87 / 0.85 |   5 /  55 /  38 |   7 /  64 /  63 |  16 /  67 /  68 |  58   (n hon 87, noisy 33, allN 60; median m hon -0.21 noisy +0.12)
Pets       | 0.97 / 0.99 |   2 /  91 /   — |   6 /  94 /   — |   6 /  97 /   — |  97   (n hon 87, noisy 33, allN 0; median m hon -0.33 noisy +1.56)
DTD        | 1.00 / 1.00 |   0 /  85 /   — |   0 /  91 /   — |   0 /  91 /   — |  94   (n hon 87, noisy 33, allN 0; median m hon -0.41 noisy +0.57)
Caltech101 | 0.98 / 1.00 |   0 /  91 /   — |   0 /  91 /   — |   1 / 100 /   — | 100   (n hon 87, noisy 33, allN 0; median m hon -0.36 noisy +2.07)

=== round 50: Pets-honest p95 threshold  per-round s -0.053 | running mean m -0.042
dataset    | AUROC s / m | CLEAR tau .05: hon / noisy / allN | s>p95: hon / noisy / allN | m>p95: hon / noisy / allN | oracle m @5% hon: noisy
MNIST      | 0.85 / 0.85 |   0 /  48 /  28 |   0 /  48 /  38 |   0 /  48 /  38 |  58   (n hon 87, noisy 33, allN 60; median m hon -0.31 noisy -0.12)
EuroSAT    | 0.88 / 0.87 |   2 /  48 /  28 |   5 /  55 /  43 |   9 /  61 /  65 |  61   (n hon 87, noisy 33, allN 60; median m hon -0.25 noisy +0.11)
Pets       | 0.99 / 1.00 |   0 /  85 /   — |   6 /  94 /   — |   6 /  97 /   — |  97   (n hon 87, noisy 33, allN 0; median m hon -0.33 noisy +1.37)
DTD        | 1.00 / 1.00 |   0 /  73 /   — |   0 /  82 /   — |   0 /  91 /   — | 100   (n hon 87, noisy 33, allN 0; median m hon -0.48 noisy +0.52)
Caltech101 | 1.00 / 1.00 |   0 /  97 /   — |   0 /  97 /   — |   0 / 100 /   — | 100   (n hon 87, noisy 33, allN 0; median m hon -0.35 noisy +1.99)
```
