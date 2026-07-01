# Key Papers — Methodology Support Map

One-to-one mapping from every non-trivial implementation choice in
this project to the paper or specification that justifies it. Use this
file (a) when writing the Methodology chapter, so every design
decision in prose has a citation behind it, and (b) during the viva,
so a "why did you choose X?" question can be answered in one lookup.

This file is the **table form** of [literature_review.md](literature_review.md).
The review is narrative ("here is the landscape"); this file is a
lookup ("here is the receipt"). Every citation listed here already
appears in literature_review.md §7 — no new references are introduced.

Columns:

- **Choice** — the concrete implementation decision
- **Primary citation** — the paper/spec that justifies it (must-cite)
- **Supporting** — secondary citations to deepen the argument (optional)
- **Verification** — file:line where the choice is visible in code

---

## 1. Simulator Design

| Choice | Primary citation | Supporting | Verification |
| --- | --- | --- | --- |
| Three-phase PBFT (pre-prepare → prepare → commit) | Castro & Liskov (1999) | — | [src/simulation/pbft.py](../src/simulation/pbft.py) |
| `n = 7`, `f = 2`, commit quorum `2f + 1 = 5` | Castro & Liskov (1999) §4 | — | [config.py](../config.py) `NUM_NODES`, `FAULT_TOLERANCE` |
| Discrete-event simulation over real containers | Banks et al. (1996) ch. 1 | — | [src/simulation/simpy_network.py](../src/simulation/simpy_network.py) |
| SimPy `env.now` instead of `time.sleep()` | Matloff (2008) | SimPy docs (simpy.readthedocs.io) | grep `env.now` across src/simulation/ |
| Process-based replica modelling (each node = SimPy process) | Matloff (2008) | — | [src/simulation/node.py](../src/simulation/node.py) |
| No view-change implementation (feature recorded as 0) | Castro & Liskov (1999) §4.4 (scoped out) | [notes/phase9_design_decisions.md](phase9_design_decisions.md) | [src/data/feature_extractor.py](../src/data/feature_extractor.py) `leader_change_frequency` |

---

## 2. Fault Models

| Choice | Primary citation | Supporting | Verification |
| --- | --- | --- | --- |
| Five fault classes (silent, delay, replay, equivocation, forgery) | Mastromauro et al. (2025) four-family taxonomy | Rocha (2024) ByzPlug primitives | [src/simulation/fault_injector.py](../src/simulation/fault_injector.py) |
| `silent` = probabilistic message drop | Mastromauro et al. (2025) §VI.D (Communication family) | — | `_on_silent` in fault_injector.py |
| `delay` = configurable extra latency | Mastromauro et al. (2025) §VI.D.2 | — | `_on_delay` in fault_injector.py |
| `replay` = same-round duplicate emission | Rocha (2024) Algorithm 2 (`replay = N`) | Mastromauro et al. (2025) §VI.D.2 | `_on_replay` in fault_injector.py |
| `stale` replay = cross-round buffer replay | Mastromauro et al. (2025) §VI.D.2 ("stale proposal messages") | — | [notes/phase4c_literature.md](phase4c_literature.md) |
| `equivocation` = receiver-parity content fork | Castro & Liskov (1999) §3 (safety property) | — | `_on_equivocation` in fault_injector.py |
| `forgery` = sender_id spoofing under no-auth assumption | Castro & Liskov (1999) §3 (authenticated channels) — framed as ablation | Mastromauro et al. (2025) §V.B | `_on_forgery` in fault_injector.py |
| Phase 4c probabilistic / phase-specific / distribution-based realism | Project's SimPy event model | Rocha (2024); Gonzalez et al. (2025) ByzFL configurable scenarios; Wang et al. (2022) BFT-Simulator design | [notes/phase4c_literature.md](phase4c_literature.md) |
| Deterministic adversary under fixed `RANDOM_SEED` | Project methodology choice | Pedregosa et al. (2011) (reproducibility convention) | [config.py](../config.py) `RANDOM_SEED = 42` |

---

## 3. Feature Set

| Choice | Primary citation | Supporting | Verification |
| --- | --- | --- | --- |
| 11-feature schema computed from event logs (not wall-clock) | Project's A2 methodology | — | [src/data/feature_extractor.py](../src/data/feature_extractor.py) |
| `message_latency`, `propagation_pattern` (timing features) | Sukhwani et al. (2017) PBFT latency study | — | feature_extractor.py |
| `voting_consistency`, `message_consistency` (agreement features) | Castro & Liskov (1999) quorum definition | — | feature_extractor.py |
| `timeout_frequency`, `consensus_agreement_time` | Castro & Liskov (1999) §4.3 (timeout / agreement) | — | feature_extractor.py |
| `leader_change_frequency = 0` (placeholder for future view-change work) | Castro & Liskov (1999) §4.4 (scoped out) | [phase9_design_decisions.md](phase9_design_decisions.md) | feature_extractor.py |
| Auxiliary counters (`forged`, `replayed`, `silent_mode`, etc.) NOT used as model features | Project methodology — separation of input vs metadata | — | [SIMPY_MILESTONES.md:535](../SIMPY_MILESTONES.md) (Phase 5 auxiliary metadata) |

---

## 4. Label Rules

| Choice | Primary citation | Supporting | Verification |
| --- | --- | --- | --- |
| Three-class labels: Normal (0) / Degraded (1) / Failure (2) | Project's A2 schema | — | [src/data/label_generator.py](../src/data/label_generator.py) |
| Failure = timeout OR quorum miss | Castro & Liskov (1999) §4.3 | — | label_generator.py |
| Degraded = quorum reached but latency / drop / consistency degraded | Beyer et al. (2016) SRE Ch. 6 (degraded-state classification) | — | label_generator.py |
| Normal = quorum reached + thresholds met | Sukhwani et al. (2017) baseline latency profile | — | label_generator.py |
| Labels derived from simulated state, not wall-clock | Matloff (2008) — DES reproducibility | — | label_generator.py uses `env.now` only |
| Forgery with successful commit → Degraded (not Failure) | Castro & Liskov (1999) §3 (safety preserved if quorum honest) | [notes/byzantine_realism.md](byzantine_realism.md) | label_generator.py |

---

## 5. Dataset Generation

| Choice | Primary citation | Supporting | Verification |
| --- | --- | --- | --- |
| Main dataset 1200 rows (5 classes × ~240) | Project sample-size choice; constrained by CV stability requirements | Pedregosa et al. (2011) §3.1 (5-fold CV needs ≥200 per class) | [scripts/generate_main_dataset.py](../scripts/generate_main_dataset.py) |
| Extended robustness dataset kept separate from training set | Project methodology — OOD evaluation | Gonzalez et al. (2025) ByzFL — per-attack OOD reporting style | [SIMPY_MILESTONES.md:656](../SIMPY_MILESTONES.md) (Phase 7 extended dataset) |
| Per-round seed diversity (`seed=seed+i`) | Project methodology — independent network noise | Matloff (2008) — DES seed independence | [phase4c_literature.md](phase4c_literature.md) Phase 7 reminders |
| Stratified 70/10/20 train/val/test split (`random_state=42`) | Pedregosa et al. (2011) sklearn `train_test_split` defaults | — | [ml/preprocessing.py](../ml/preprocessing.py) |
| Reproducible dataset under fixed `RANDOM_SEED` | Project methodology | Pedregosa et al. (2011) | [config.py](../config.py) |

---

## 6. Model Selection

| Choice | Primary citation | Supporting | Verification |
| --- | --- | --- | --- |
| Decision Tree (CART) | Breiman et al. (1984) | Pedregosa et al. (2011) — sklearn impl | [ml/models/decision_tree.py](../ml/models/decision_tree.py) |
| Random Forest | Breiman (2001) | Pedregosa et al. (2011) | [ml/models/random_forest.py](../ml/models/random_forest.py) |
| XGBoost | Chen & Guestrin (2016) | — | [ml/models/xgboost_model.py](../ml/models/xgboost_model.py) |
| Logistic Regression (linear baseline tier) | Cox (1958); Pedregosa et al. (2011) impl | — | [ml/models/logistic_regression.py](../ml/models/logistic_regression.py) |
| No deep model (BiLSTM stub kept empty) | Pedregosa et al. (2011) — model complexity ~ dataset size convention | [phase9_design_decisions.md](phase9_design_decisions.md) | [ml/models/bilstm.py](../ml/models/bilstm.py) (empty by design) |
| `class_weight='balanced'` for DT / RF / LR | Pedregosa et al. (2011) sklearn `class_weight` API | — | [scripts/train_model_tuned.py](../scripts/train_model_tuned.py) |
| `sample_weight` via `compute_sample_weight` for XGBoost | XGBoost docs; Chen & Guestrin (2016) | — | [scripts/train_model_tuned.py](../scripts/train_model_tuned.py) |
| Pipeline-wrapped scaler + classifier (CV without leakage) | Pedregosa et al. (2011) `sklearn.pipeline.Pipeline` | — | [phase11.md](phase11.md) "Scaler leakage in CV" section |

---

## 7. Baseline Comparison

| Choice | Primary citation | Supporting | Verification |
| --- | --- | --- | --- |
| Parametric Gaussian threshold (`μ ± k·σ`) | Chandola et al. (2009) §4 | Sukhwani et al. (2017) (Gaussian assumption for PBFT latency) | [baseline/static_detection.py](../baseline/static_detection.py) |
| Rule-based detector encoding PBFT failure conditions | Castro & Liskov (1999) §4 | Beyer et al. (2016) SRE Ch. 6 (industry rule-based practice) | baseline/static_detection.py |
| Same test set + same metrics for baseline vs ML | Mirsky et al. (2018) Kitsune comparison style | — | [scripts/evaluate_baseline.py](../scripts/evaluate_baseline.py) |
| Defence of "deliberately weak" baselines | Beyer et al. (2016) SRE Ch. 6 (production = static thresholds) | — | [phase10_baseline_references.md](phase10_baseline_references.md) §2 |
| Disclosure: rule-based baseline shares threshold constants with label generator | Project transparency choice | [phase10_baseline_references.md](phase10_baseline_references.md) §2 honest disclosure | — |

---

## 8. Evaluation Metrics

| Choice | Primary citation | Supporting | Verification |
| --- | --- | --- | --- |
| Macro-averaged precision / recall / F1 | Pedregosa et al. (2011) sklearn `classification_report` defaults for imbalanced multi-class | — | [ml/evaluation.py](../ml/evaluation.py) |
| Confusion matrix per (model, split) | Pedregosa et al. (2011) | Mirsky et al. (2018) (IDS reporting convention) | evaluation.py |
| `StratifiedKFold(n_splits=5)` CV | Pedregosa et al. (2011) sklearn user guide §3.1 | — | [ml/tuning.py](../ml/tuning.py) |
| `GridSearchCV` with macro-F1 selection | Pedregosa et al. (2011) sklearn `GridSearchCV` | — | ml/tuning.py |
| Multi-seed reporting (mean ± std over ≥5 seeds) | Project methodology — single-seed F1 has high variance | [phase11.md](phase11.md) (motivating example: Phase 9 RF point estimate) | [scripts/train_model_tuned.py](../scripts/train_model_tuned.py) |
| Per-class report saved alongside aggregated metrics | Pedregosa et al. (2011) `classification_report` | — | [results/tables/per_class_report.csv](../results/tables/per_class_report.csv) |
| Test set untouched by CV (single touch at final refit per seed) | Pedregosa et al. (2011) sklearn user guide §3.1 (held-out test convention) | — | scripts/train_model_tuned.py |
| Response time = batch-averaged inference latency | Project methodology — per-sample timing impractical at this scale | [phase9_design_decisions.md](phase9_design_decisions.md) | [ml/evaluation.py](../ml/evaluation.py) |
| SHAP feature importance (Phase 12.A) | Lundberg & Lee (2017) | — | [SIMPY_MILESTONES.md:1268](../SIMPY_MILESTONES.md) (Phase 12.A SHAP) |

---

## 9. Coverage Audit

Every milestone-listed Phase 11c topic has at least one citation:

- [x] PBFT / Byzantine fault tolerance → §1 (Castro & Liskov 1999)
- [x] SimPy-based discrete-event simulation → §1 (Matloff 2008, Banks et al. 1996)
- [x] Byzantine fault injection → §2 (Rocha 2024, Mastromauro et al. 2025)
- [x] ML-based fault detection → §6 (Breiman 2001, Chen & Guestrin 2016, Pedregosa et al. 2011)
- [x] Baseline comparison → §7 (Chandola et al. 2009, Beyer et al. 2016, Mirsky et al. 2018)
- [x] Ablation / robustness study design → §5 + §8 (Pedregosa et al. 2011 CV, ByzFL OOD style, Lundberg & Lee 2017)

---

## 10. Quick lookup index (for the viva)

Sorted alphabetically by topic — if an examiner asks "why did you …",
find the keyword here and jump to the row.

| If asked about … | Go to |
| --- | --- |
| 11 features / feature set | §3 |
| Authentication / forgery framing | §2 (forgery row) |
| `class_weight='balanced'` | §6 |
| Confusion matrix | §8 |
| Cross-validation choice (5-fold stratified) | §8 |
| Decision Tree / Random Forest / XGBoost / LR | §6 |
| Discrete-event simulation / SimPy | §1 |
| Equivocation / replay / silent | §2 |
| Failure / Degraded / Normal labels | §4 |
| Gaussian threshold baseline | §7 |
| GridSearchCV | §8 |
| Macro-averaged F1 | §8 |
| Multi-seed reporting | §8 |
| `n = 7`, `f = 2` | §1 |
| Pipeline (scaler + classifier) | §6 |
| Quorum (`2f + 1 = 5`) | §1, §3 |
| Rule-based baseline shares thresholds with labels | §7 |
| SHAP | §8 |
| Stratified train/val/test split | §5 |
| Three-phase PBFT | §1 |
| View-change not implemented | §1, §3 |

---

## 11. Maintenance

When adding a new implementation choice to the codebase:

1. Add a row to the relevant section (1–8).
2. Make sure the citation already exists in
   [literature_review.md](literature_review.md) §7. If not, add it
   there first.
3. Fill in `Verification` with the actual file:line that demonstrates
   the choice.

When changing an existing choice (e.g. swapping `StratifiedKFold` for
`RepeatedStratifiedKFold`):

1. Update the row in this file.
2. Update the corresponding rationale in
   [phase9_design_decisions.md](phase9_design_decisions.md) or
   [phase11.md](phase11.md).
3. Re-check that the new choice still has a supporting citation in
   [literature_review.md](literature_review.md) §7.
