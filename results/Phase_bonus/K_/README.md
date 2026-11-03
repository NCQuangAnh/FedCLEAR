# Gate K runs (data-only attacker: poisons labels, runs our client code)

Each folder has the Kaggle zip (`phase6_results.zip`) and its extracted copy (`x/`).

| Folder | Session | Arms | Plan / results |
|---|---|---|---|
| `pets/`, `caltech/` | 5a / 5b | `K_base`, `K_fix`, `K_fixconf` | `../gate_k_plan.md`, `../K_results.md` |
| `diag/` | gate_k_diag | `K_fix_log` (per-sample teacher log, Pets) | `../K_results.md` |
| `prior/` | gate_k_prior | `K_prior` (Pets, Caltech) | `../K_results.md` |
| `proto/pets`, `proto/caltech` | gate_k_proto | `K_proto`, `K_restore` (all-clean oracle) | `../gate_k_proto_plan.md`, `../K_results.md` |
| `proto_band/pets`, `proto_band/caltech` | gate_k_proto | `K_proto_band` | `../gate_k_proto_band_plan.md`, `../K_results.md` |

Gate Q (noise only, no attacker) lives in `../Q_/{pets,caltech}`: arms `Q_none`, `Q_filter`, `Q_fixconf`.
Plan `../gate_q_plan.md`, results at the end of `../K_results.md`.
