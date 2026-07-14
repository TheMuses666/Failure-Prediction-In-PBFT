# ML-Assisted Predictive Monitoring in BFT Consensus Protocols

A SimPy-based discrete-event PBFT simulator with controlled Byzantine fault
injection, used to generate labelled consensus-round datasets and to evaluate
whether machine-learning classifiers can predict consensus degradation and
failure earlier and more accurately than static threshold/rule baselines.

**Research question:** can round-level observable features (latency, drop
rate, vote consistency, ...) support *predictive* monitoring of a PBFT
cluster — detecting degraded and failing rounds, ahead of the timeout, under
attacks the model has and has not seen during training?

Core components:

- **Simulator** — event-driven PBFT (pre-prepare / prepare / commit, quorum
  2f+1, timeout) on SimPy simulated time; no wall-clock sleeping; fully
  deterministic under a fixed seed.
- **Fault injection** — `silent`, `delay`, `replay`, `equivocation` (main
  set) plus advanced modes: `forgery` (sender spoofing), phase-targeted
  silence, log-normal delay, stale-round replay.
- **Dataset** — 13 numeric features + 3-class label
  (0 normal / 1 degraded / 2 failure) per round. Auxiliary attack counters
  (e.g. `forged`, `stale_replayed`) are recorded for labelling and analysis
  but are **never** used as model inputs.
- **Models** — Decision Tree, Random Forest, XGBoost, Logistic Regression
  (multi-seed, CV-tuned variants), compared against static
  threshold/rule/count-based detectors.
- **Experiments** — feature & tuning ablations, Byzantine-ratio robustness,
  network-size scalability, per-fault-type analysis, prediction lead time,
  SHAP explanation, OOD evaluation on advanced faults, authentication
  ablation (forgery intensity sweep), strict-round-validation ablation.

---

## 1. Setup

Requires Python 3.12+ (developed on 3.14). From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

All commands below are run from the repository root using module form
(`python -m ...`), which is required for the imports to resolve.

**Determinism:** every random draw (network latency, drops, attacker
behaviour, ML seeds) goes through seeded RNGs (`config.RANDOM_SEED = 42`,
multi-seed list `config.RANDOM_SEEDS = [42, 31, 8, 66, 2]`). Re-running the
pipeline reproduces every table bit-for-bit.

---

## 2. Repository structure

```text
bft_project/
├── config.py                  # single source of truth: paths, seeds, protocol
│                              #   constants, label thresholds, feature schema
├── requirements.txt
├── SIMPY_MILESTONES.md        # phase-by-phase plan, pass criteria, progress
│
├── src/
│   ├── simulation/            # SimPy discrete-event PBFT simulator
│   │   ├── message.py         #   Message dataclass
│   │   ├── simpy_network.py   #   delivery layer: latency, drops, injector hooks
│   │   ├── node.py            #   event-driven replica: vote logs, quorum detection
│   │   ├── pbft.py            #   round orchestrator, multi-round simulation entry
│   │   ├── fault_injector.py  #   Byzantine behaviours (on_send / extra_latency)
│   │   └── round_result.py    #   raw round output -> structured result dict
│   ├── data/
│   │   ├── feature_extractor.py  # 13 features + auxiliary counters
│   │   │                         #   (+ time-sliced variant for lead time)
│   │   └── label_generator.py    # 3-class label rules
│   └── plotting/              # reusable matplotlib/seaborn helpers
│
├── ml/                        # preprocessing, tuning (CV/GridSearch), evaluation
│   └── models/                # decision_tree, random_forest, xgboost, logistic_regression
├── baseline/                  # static detectors: threshold-, rule-, count-based
├── utils/                     # shared glue: pipelines, multi-seed training,
│                              #   shared OOD detection loop
│
├── scripts/                   # runnable entry points, one subpackage per experiment
│   ├── data_generation/       #   main + extended datasets
│   ├── training/              #   default (multi-seed), tuned (CV), legacy (Phase 9)
│   ├── diagnostics/           #   simulator validation, baselines, SHAP, per-fault
│   ├── feature_ablation/      #   11 vs 13 features          (Phase 12.A-2)
│   ├── tuning_ablation/       #   default vs tuned           (Phase 12.A-1)
│   ├── robustness/            #   Byzantine-ratio shift      (Phase 12.A-3)
│   ├── scalability/           #   network-size shift         (Phase 12.A-4)
│   ├── lead_time/             #   early prediction           (Phase 12.A-6)
│   ├── advanced_fault/        #   OOD on advanced faults     (Phase 12.B)
│   ├── authentication_ablation/  # forgery intensity sweep   (Phase 12.C)
│   ├── strict_round_ablation/    # stale replay vs validation (Phase 12.D)
│   └── plotting/              #   report figures from result tables
│
├── data/raw/                  # generated datasets   (gitignored, reproducible)
├── results/                   # tables / figures / models (gitignored, reproducible)
└── notes/                     # research notes (untracked)
```

`data/` and `results/` are intentionally **not** committed: every artefact is
regenerated deterministically by the pipeline below.

---

## 3. Reproducing the experiments

Steps must be run in order within each stage (later stages consume earlier
outputs). Approximate runtimes on a laptop are noted; the full pipeline
completes in well under an hour.

### Stage 1 — Datasets

```bash
.venv/bin/python -m scripts.data_generation.main_dataset
```

Produces `data/raw/consensus_data.csv` (1200 rows: 400 normal + 200 per main
fault type) and `data/raw/extended_robustness.csv` (800 rows across 7
advanced-fault subtypes; OOD evaluation only, never used for training unless
explicitly opted in). ~1 min.

Sanity check:

```bash
.venv/bin/python -c "import pandas as pd; df = pd.read_csv('data/raw/consensus_data.csv'); print(df.shape); print(df['label'].value_counts())"
```

Optional simulator validation (distribution plots, per-fault summaries,
Phase 4c variance comparison):

```bash
.venv/bin/python -m scripts.diagnostics.validate_simulator
```

### Stage 2 — Model training

```bash
.venv/bin/python -m scripts.training.default   # multi-seed default-hyperparameter baseline (~1 min)
.venv/bin/python -m scripts.training.tuned     # Phase 11: 5-fold CV + GridSearch + multi-seed (~several min)
```

Outputs: `results/tables/model_metrics_default_multiseed.csv`,
`model_metrics_tuned.csv`, `cv_results.csv`, `best_hyperparameters.csv`,
`per_class_report.csv`, and persisted models under `results/models/`.

(`scripts.training.legacy` is the original Phase 9 single-seed pipeline,
kept for provenance; it is not required for any downstream experiment.)

### Stage 3 — Main experiments (Phase 12.A)

```bash
# 12.A-1 default vs tuned (needs both Stage 2 runs)
.venv/bin/python -m scripts.tuning_ablation.evaluate

# 12.A-2 feature-set ablation: 11 vs +quorum_margin vs +prepare_count_std vs 13
.venv/bin/python -m scripts.feature_ablation.evaluate

# 12.A-3 Byzantine-ratio robustness: generate f=1/f=3 test sets, evaluate, plot
.venv/bin/python -m scripts.robustness.generate
.venv/bin/python -m scripts.robustness.evaluate
.venv/bin/python -m scripts.robustness.plot

# 12.A-4 scalability: generate N=10/N=13 test sets, evaluate, plot
.venv/bin/python -m scripts.scalability.generate
.venv/bin/python -m scripts.scalability.evaluate
.venv/bin/python -m scripts.scalability.plot

# 12.A-5 per-fault-type detection/recall breakdown
.venv/bin/python -m scripts.diagnostics.per_fault_type

# 12.A-6 prediction lead time: snapshot dataset (7200 rows), per-cutoff training, plots
.venv/bin/python -m scripts.lead_time.generate_snapshots
.venv/bin/python -m scripts.lead_time.evaluate
.venv/bin/python -m scripts.lead_time.plot

# 12.A-7 SHAP feature importance (XGBoost + Random Forest)
.venv/bin/python -m scripts.diagnostics.shap_analysis

# Phase 10 static baselines on the shared test split
.venv/bin/python -m scripts.diagnostics.evaluate_baseline
```

### Stage 4 — Advanced-fault and ablation experiments (Phase 12.B–E)

```bash
# 12.B OOD evaluation on the extended set; optional exposure arm
.venv/bin/python -m scripts.advanced_fault.evaluate
.venv/bin/python -m scripts.advanced_fault.evaluate --train-on-extended

# 12.C authentication ablation: forgery intensity in {0.2, 0.5, 1.0}
.venv/bin/python -m scripts.authentication_ablation.generate
.venv/bin/python -m scripts.authentication_ablation.evaluate
.venv/bin/python -m scripts.authentication_ablation.plot

# 12.D strict-round-validation ablation: stale replay, paired arms
.venv/bin/python -m scripts.strict_round_ablation.generate
.venv/bin/python -m scripts.strict_round_ablation.evaluate
.venv/bin/python -m scripts.strict_round_ablation.plot

# 12.E mixed-N training: add N=10/N=13 exposure and compare scale generalisation
.venv/bin/python -m scripts.mixed_n_train.generate
.venv/bin/python -m scripts.mixed_n_train.evaluate
.venv/bin/python -m scripts.mixed_n_train.plot
```

### Stage 5 — Report figures

```bash
.venv/bin/python -m scripts.plotting.confusion
.venv/bin/python -m scripts.plotting.model_comparison
.venv/bin/python -m scripts.plotting.per_fault_type
```

### Optional — Results dashboard

```bash
.venv/bin/streamlit run src/plotting/dashboard.py
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\streamlit.exe run src\plotting\dashboard.py
```

---

## 4. Key outputs

| File | Content |
|---|---|
| `results/tables/model_metrics_tuned.csv` | headline test metrics, mean ± std over 5 seeds |
| `results/tables/ablation_feature_set.csv` | 11 vs 13 feature ablation (12.A-2) |
| `results/tables/robustness_curve.csv` + `figures/robustness_curve.png` | F1 vs Byzantine count f (12.A-3) |
| `results/tables/scalability_curve.csv` + `figures/scalability_curve.png` | F1 vs network size N (12.A-4) |
| `results/tables/lead_time_summary.csv` + `figures/lead_time_comparison.png` | early-warning lead time (12.A-6) |
| `results/tables/shap_importance.csv` + `figures/feature_importance.png` | SHAP importances (12.A-7) |
| `results/tables/ood_f1*.csv`, `ood_per_subtype*.csv` | OOD degradation and exposure arm (12.B) |
| `results/tables/auth_ablation*.csv` + `figures/auth_ablation_detection.png` | forgery intensity sweep (12.C) |
| `results/tables/strict_ablation_*.csv` + `figures/strict_ablation_detection.png` | validation ablation (12.D) |

### Results dashboard (Phase 15)

A lightweight Streamlit viewer over the generated tables and figures.
It only reads existing `results/tables/*.csv`, `results/figures/*.png`,
and `data/raw/*.csv` outputs — missing files render as placeholders with
the command needed to regenerate them.

```bash
streamlit run src/plotting/dashboard.py
```

---

## 5. Configuration

All knobs live in `config.py`; the important ones:

- `NUM_NODES = 7`, `NUM_BYZANTINE_NODES = 2` — main network configuration
  (quorum 2f+1 = 5, safety bound f ≤ ⌊(N−1)/3⌋ = 2).
- `RANDOM_SEED` / `RANDOM_SEEDS` — single-run seed and the multi-seed list.
- `CONSENSUS_TIMEOUT_MS = 150` — round timeout; also the lead-time reference.
- Label thresholds — `NORMAL_LATENCY_THRESHOLD_MAX`, `DROP_RATE_WARNING`,
  `MESSAGE_CONSISTENCY_WARNING`.
- `FEATURE_COLUMNS` / `FEATURE_COLUMNS_EXTEND` — 11- vs 13-feature schema;
  `AUXILIARY_COLUMNS` are excluded from model input by design.
- `STRICT_ROUND_VALIDATION = True` — receiver-side round validation default;
  the 12.D ablation overrides it per run via the
  `strict_round_validation` parameter, never by editing this constant.

## 6. Scope and limitations

This project is a controlled simulation study, not a production PBFT
implementation. The simulator focuses on PBFT normal-case consensus and
monitoring signals. It does not implement full view-change recovery, real
cryptographic authentication, client request batching, persistent replicated
state, or deployment-level networking.

Forgery experiments are authentication-ablation scenarios: production PBFT
would reject spoofed messages using signatures or authenticated channels. The
purpose is to measure what the authentication assumption protects against,
not to claim that real PBFT accepts forged votes.

## 7. Main findings

- ML models outperform static threshold/rule baselines on most fault modes,
  especially when multiple weak signals must be combined (e.g. forgery
  detection). The comparison inverts when an attack moves only a single
  monitored axis: the weakened-validation stale-replay experiment is caught
  almost entirely by one hand-written consistency rule that ML models miss.
- Delay faults are easiest to detect; equivocation and stale replay are
  harder because they may leave little observable consensus footprint.
- Logistic Regression is less accurate in-distribution but more stable under
  some distribution shifts (network size), while tree models achieve
  stronger peak performance.
- Authentication ablation shows forged votes can make consensus appear
  *faster and healthier*, demonstrating why production PBFT requires
  authenticated messages.
- Strict round validation neutralises stale replay at the protocol boundary;
  disabling it makes stale replay visible as message-consistency
  degradation, but safety is never violated — content-keyed vote buckets
  act as a second implicit defence layer.

## 8. Documentation

- `SIMPY_MILESTONES.md` — the full phase plan (0 → 12), per-phase pass
  criteria, and completion status; the authoritative map of what was built
  and why.
- Design rationale and per-experiment findings are kept in research notes
  and are summarised in the final report.
