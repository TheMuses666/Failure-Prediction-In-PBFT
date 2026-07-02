## Phase 12.A-1: Default vs Tuned Hyperparameter Ablation

The Phase 11 tuned models reported test F1 with mean ± std over 5 seeds,
while the Phase 9 default-hyperparameter models were trained on a single
seed. Comparing the two directly was not statistically meaningful.

Phase 12.A-1 closes this gap by re-running default-hyperparameter
training under the same multi-seed framework as Phase 11. The new script
`scripts/train_model_default.py` reuses the train / test split logic and
seed list from `train_model_tuned.py`, removing only the GridSearchCV
step. The downstream script `scripts/ablation_default_vs_tuned.py`
merges `model_metrics_default_multiseed.csv` and `model_metrics_tuned.csv`
on `model`, computes `delta_f1_mean = tuned − default`, and writes
`results/tables/ablation_tuning.csv`.

Across all four candidates the tuning gain is small:

| model               | default F1 | tuned F1 | Δ      |
|---------------------|------------|----------|--------|
| logistic_regression | 0.858      | 0.869    | +0.010 |
| xgboost             | 0.942      | 0.949    | +0.007 |
| random_forest       | 0.909      | 0.915    | +0.006 |
| decision_tree       | 0.877      | 0.883    | +0.006 |

Three observations:

1. The largest gain comes from logistic regression, the only linear
   model, because its single regularisation parameter `C` directly
   controls behaviour under class imbalance. Tree models are more
   robust to default values.
2. Hyperparameter tuning contributes less than 1.5% F1 across all
   models. Model selection (e.g. XGBoost vs Logistic Regression,
   Δ = 0.07) is roughly an order of magnitude more impactful than
   hyperparameter search on this dataset.
3. This result implies the existing features carry enough signal that
   default-parameter models already approach the model-class capacity
   ceiling. Tuning improvements should therefore not be over-claimed in
   the report.

## Phase 12.A-2: Feature Set Ablation (11 → 13 Features)

Two new features were added to `src/data/feature_extractor.py`:

- `quorum_margin = voting_consistency − quorum_size / total_nodes`
  expresses the per-round safety distance to the PBFT commit quorum.
- `prepare_count_std = std(prepare messages received per node)` measures
  the unevenness of prepare-phase delivery across nodes.

The implementation reads `quorum_size` and `total_nodes` from
`round_result` rather than from the global config. This decouples
`extract_features` from `NUM_NODES` / `QUORUM` and allows Phase 12.A-4
scalability runs (N ∈ {7, 10, 13}) to reuse the same extractor without
modification. `config.FEATURE_COLUMNS_EXTEND` was added alongside
`FEATURE_COLUMNS`, and `assert_feature_schema` was switched to check
against the extended set so that `generate_main_dataset` accepts the new
keys.

A four-tier ablation in `scripts/ablation.py` quantifies the
contribution of each new feature independently:

| model               | 11 baseline | +quorum only | +prepare only | 13 both | Δ quorum | Δ prepare |
|---------------------|------------|--------------|--------------|---------|----------|-----------|
| decision_tree       | 0.877      | 0.873        | 0.957        | 0.957   | −0.005   | +0.080    |
| random_forest       | 0.909      | 0.911        | 0.966        | 0.971   | +0.002   | +0.057    |
| logistic_regression | 0.858      | 0.864        | 0.915        | 0.917   | +0.005   | +0.057    |
| xgboost             | 0.942      | 0.942        | 0.972        | 0.972   |  0.000   | +0.030    |

Three observations:

1. `quorum_margin` provides no measurable F1 gain (Δ ∈ [−0.005, +0.005]
   across models). This is consistent with the correlation check:
   `quorum_margin` and `voting_consistency` have identical Pearson
   correlations with the label (−0.625), because `quorum_margin` is a
   constant-offset linear transformation of `voting_consistency`. No new
   information is added; default decision tree variability accounts for
   the small negative delta.
2. `prepare_count_std` accounts for the entire 11 → 13 improvement. Its
   global correlation with the label is only +0.11, but grouped by
   `fault_type` it shows a strong replay-attack signature
   (mean 0.635 under replay vs ≤ 0.36 for all other fault types). This
   is a genuinely independent signal not captured by the original 11
   features.
3. The two features are additive: Δ_both ≈ Δ_quorum + Δ_prepare within
   one standard deviation across all models. Adding both gives the same
   F1 as adding only `prepare_count_std`. The features encode
   orthogonal information channels.

We retain the 13-feature set as the project default despite the zero
contribution of `quorum_margin`, because (a) it preserves the
"11 vs 13" narrative used in the ablation comparison and (b)
`quorum_margin` has clear interpretability value (the zero-line equals
the PBFT safety threshold) that may help the report's explanation
section, even if the model does not benefit from it numerically.

## Phase 12.A-2 outstanding debt: Phase 11 tuned models are 11-feature

The persisted `results/models/*_tuned.joblib` files were fitted on the
11-feature set during Phase 11. After Phase 12.A-2, the project default
feature set is 13. The two are incompatible: directly loading a tuned
model and predicting on the 13-feature CSV will fail on shape mismatch.

This is deferred. Phase 12.A-3 and 12.A-4 train new pipelines from
scratch, so they are not affected. Phase 12.B (OOD evaluation) is the
first experiment that needs to reuse persisted tuned models. Two
options will be considered at that time:

- re-run Phase 11 tuning on the 13-feature dataset and save the result
  as `*_tuned_13.joblib`, keeping the original 11-feature versions for
  the Phase 11 reproducibility check;
- keep the 11-feature tuned models as the reference Phase 11 baseline
  and use them as-is, selecting the 11 columns from the 13-column CSV
  at inference time.

## Phase 12.A-3: Robustness Test Design (Plan A)

Phase 12.A-3 evaluates how detection performance degrades when the
Byzantine ratio departs from the trained-on configuration. The
experiment uses Plan A — train once on the existing f=2 dataset, then
predict on three test sets of varying f.

Test sets are generated in `scripts/generate_robustness_test.py` with
1000 rounds each (200 normal + 200 × 4 fault types) under the following
Byzantine configurations:

- f = 1, byzantine_node_ids = [6]
- f = 2, byzantine_node_ids = [4, 5] (existing main dataset, in-distribution)
- f = 3, byzantine_node_ids = [4, 5, 6]

The f=3 set is a strict superset of the f=2 set so that the
"more attackers added" semantics is unambiguous. f=3 also exceeds the
PBFT safety bound f ≤ ⌊(N−1)/3⌋ = 2 for N=7, which makes it an
"out-of-design" robustness probe rather than a within-spec stress test.

Default-hyperparameter pipelines (`utils.helpers.make_pipeline` wrapping
each `build_*` model) are trained on the 80% trainval split of the f=2
CSV under five seeds. For each (seed, model) the fitted pipeline is
evaluated on the 20% in-distribution f=2 test holdout and on the full
f=1 and f=3 datasets. The default models are used in place of Phase 11
tuned models because Phase 12.A-1 established that the tuning gain is
under 1.5% F1, while the robustness experiment is concerned with the
shape of the F1-vs-f degradation curve rather than absolute F1.

The output `results/tables/robustness_curve.csv` is keyed by
(model, f) and contains `f1_mean`, `f1_std` over five seeds. The
accompanying figure `results/figures/robustness_curve.png` plots one
line per model with std as a shaded band.

## Phase 12.A-3: Robustness Results

| model               | f=1            | f=2 (in-dist)  | f=3            | Δ at f=3 |
|---------------------|----------------|----------------|----------------|----------|
| decision_tree       | 0.848 ± 0.011  | 0.957 ± 0.009  | 0.612 ± 0.001  | −0.345   |
| random_forest       | 0.858 ± 0.004  | 0.971 ± 0.010  | 0.616 ± 0.001  | −0.355   |
| xgboost             | 0.747 ± 0.061  | 0.972 ± 0.003  | 0.616 ± 0.001  | −0.356   |
| logistic_regression | 0.831 ± 0.006  | 0.917 ± 0.013  | 0.591 ± 0.003  | −0.326   |

The f=2 column reproduces Phase 12.A-2 results bit-for-bit, confirming
that the train / split / predict pipeline in `scripts/robustness.py`
matches the established baseline. Three observations:

1. All four models exhibit a U-shaped F1 curve with the in-distribution
   f=2 point as the peak. F1 drops at both ends, but the right-side
   drop is severe: ~35 percentage points to F1 ≈ 0.6, which is only
   modestly above the 0.33 random-baseline for three-class
   classification. This degradation is interpreted as a consequence of
   PBFT-level state-space shift — beyond the safety bound the protocol
   no longer "merely contains attacks" but enters a different failure
   regime that the training distribution does not cover.
2. XGBoost is anomalous at f=1: F1 = 0.747 with σ = 0.061 (12× the std
   of any other model). This suggests XGBoost's non-linear interactions
   over-fit the specific Byzantine-node identity at f=2
   (byzantine_node_ids = [4, 5]) rather than to fault-type generality.
   When the byzantine_node_ids changes to [6] at f=1 the model loses
   confidence on a seed-dependent basis.
3. Drops at f=1 (6–10 percentage points for RF / DT / LR) confirm that
   *fewer attackers do not imply easier detection* — the dominant
   factor is whether the test distribution matches the trained
   distribution, not raw attack intensity.

## Phase 12.A-3: Helper Refactor and Regression Test

Phase 12.A-2 introduced `train_default_pipeline_multiseed` in
`utils.helpers`. Phase 12.A-3 required training the same four models
on f=2 data and predicting on three separate test CSVs, which the
existing helper could not express because it bundled train + evaluate
on a single CSV and discarded the fitted pipelines.

The helper was therefore split into two layers:

- `build_and_fit_all_candidates(seed, X_tv, y_tv)` returns
  `{model_name: fitted_pipeline}`. It encapsulates the four `build_*`
  calls, `compute_sample_weight`, the XGBoost-vs-others sample_weight
  branch, and `make_pipeline` wrapping. This is the new shared unit.
- `train_default_pipeline_multiseed` was refactored to call
  `build_and_fit_all_candidates` internally, removing its inline
  four-candidate loop. Its public signature and behaviour are
  unchanged.

`scripts/robustness.py` calls `build_and_fit_all_candidates` directly,
then predicts on three test sets per (seed, model). This avoids the
"train discarded immediately" limitation of the higher-level helper.

A regression test re-ran `train_model_default.py` and `ablation.py`
after the refactor and verified that
`model_metrics_default_multiseed.csv` and `ablation_feature_set.csv`
are bit-for-bit identical to their pre-refactor versions. This rules
out unintended semantic drift in either the four-candidate training
loop or the `evaluation` / `classification_report` glue.

## Phase 12.A-3: Reusable Plotting Helper

The figure `robustness_curve.png` is produced by a thin orchestrator
script `scripts/plot_robustness.py` that defers all matplotlib work to
`src.plotting.plots.plot_grouped_curve`. This helper accepts
configurable column names (`x_col`, `y_col`, `std_col`, `group_col`),
optional safety-bound annotation (`vline_x`, `vline_label`), per-group
markers, and standard layout parameters (`figsize`, `dpi`,
`bbox_inches='tight'`). It is designed so that Phase 12.A-4
(scalability) and any future per-group curve figure can be produced by
swapping the CSV and the axis labels with no additional plotting code.

## Phase 12.A-4: Scalability Test Design

Phase 12.A-4 evaluates whether the detection model trained at N=7
generalises to larger PBFT networks. Following the same
train-once-evaluate-many pattern as Phase 12.A-3, models are trained on
the existing N=7 dataset and evaluated on newly generated N=10 and
N=13 test sets.

Byzantine node count is set to the PBFT safety-bound maximum
`f = ⌊(N−1)/3⌋` for each configuration:

- N = 7,  f = 2, byzantine_node_ids = [4, 5] (in-distribution)
- N = 10, f = 3, byzantine_node_ids = [7, 8, 9]
- N = 13, f = 4, byzantine_node_ids = [9, 10, 11, 12]

This holds the Byzantine ratio approximately constant (0.286 / 0.300 /
0.308) so that the sole varying dimension is network size, not attack
intensity. Test sets contain 1000 rows each (200 normal + 200 per fault
type), matching the Phase 12.A-3 protocol.

The scalability experiment relies on the `feature_extractor` decoupling
introduced in Phase 12.A-2 (`quorum_margin` and the prepare-count loop
now read `total_nodes` and `quorum_size` from `round_result` rather than
from `config.NUM_NODES` / `QUORUM`). Without this precondition, features
extracted at N=10 or N=13 would be computed against the fixed N=7
quorum threshold and become incorrect.

## Phase 12.A-4: Config-Driven Refactor

Phase 12.A-3 (`robustness.py`) hard-coded three test CSVs as explicit
variables (`df_f1`, `df_f3`) and enumerated the three test scenarios in
a literal list. This design does not extend cleanly: adding f=4 would
require touching the script in three places (import, variable, tuple
entry).

Phase 12.A-4 (`scalability.py`) adopts a config-driven pattern instead.
`SCALABILITY_NODE_COUNTS` in `config.py` lists the OOD node counts, and
the script iterates over that list to build `ood_nodes_scenarios`:

```python
ood_nodes_scenarios = []
for n in SCALABILITY_NODE_COUNTS:
    df = pd.read_csv(DATA_RAW_DIR / f'scalability_n{n}.csv')
    ood_nodes_scenarios.append(
        (n, df[FEATURE_COLUMNS_EXTEND], df[TARGET_COLUMN])
    )

all_scenarios = [(NUM_NODES, X_test_raw, y_test)] + ood_nodes_scenarios
```

Adding N=16 to the experiment requires only two changes:
extend `SCALABILITY_NODE_COUNTS` and add the byzantine_id mapping in
`generate_scalability_test.py`. No further code changes are needed.
`plot_scalability.py` also picks up the new x-tick automatically because
`plot_grouped_curve` reads the unique x-values from the DataFrame
itself. Phase 12.A-3's `robustness.py` follows the older explicit-list
pattern and is left unchanged for reproducibility; adopting the
config-driven pattern there is a documented follow-up.

## Phase 12.A-4: Scalability Results

| model               | N=7 (in-dist)  | N=10          | N=13          | Δ (7→13) |
|---------------------|----------------|---------------|---------------|----------|
| decision_tree       | 0.957 ± 0.009  | 0.919 ± 0.009 | 0.824 ± 0.013 | −0.133   |
| random_forest       | 0.971 ± 0.010  | 0.946 ± 0.003 | 0.906 ± 0.008 | −0.065   |
| xgboost             | 0.972 ± 0.003  | 0.942 ± 0.003 | 0.893 ± 0.010 | −0.079   |
| logistic_regression | 0.917 ± 0.013  | 0.898 ± 0.002 | 0.887 ± 0.004 | −0.030   |

N=7 F1 reproduces the Phase 12.A-3 f=2 values bit-for-bit, confirming
the training and split pipeline is unchanged. Three observations:

1. Degradation is monotone and gentle (5–13 percentage points from N=7
   to N=13), in sharp contrast to Phase 12.A-3 where crossing the
   PBFT safety bound at f=3 produced ~35-point drops. This asymmetry
   reflects a substantive protocol distinction: at N=13 with f=4 the
   system still operates within its safety envelope and merely
   experiences distribution shift, whereas at f=3 for N=7 the protocol
   is fundamentally beyond its correctness guarantees and enters a
   different state-space.
2. The usual model ranking inverts under scale-shift. Logistic
   Regression retains 96.7% of its in-distribution F1 at N=13, while
   Decision Tree retains only 86.1%. This is consistent with the design
   of ratio-normalised features (`voting_consistency`, `quorum_margin`,
   `message_drop_rate`) which preserve their semantic meaning across N.
   A linear decision boundary applied to a normalised feature vector is
   naturally scale-invariant; axis-aligned tree splits are not, because
   they memorise numeric thresholds anchored to the training N.
3. Random Forest and XGBoost degrade similarly (−0.065 vs −0.079). The
   tree ensembles' averaging effect partially mitigates the scale
   sensitivity of individual trees, but does not close the gap to the
   linear model at N=13.

The result should be reported alongside Phase 12.A-3 to expose the
asymmetry between the two OOD directions (safety-bound violation vs
network-size shift). It also motivates a discussion of whether
production deployment should prefer the more scale-invariant linear
model despite its lower in-distribution ceiling.

## Phase 12.A-5: Per-Fault-Type Analysis

Phase 12.A-5 breaks down the aggregate F1 numbers reported in earlier
phases into per-fault-type metrics on the standard 20% test holdout of
`consensus_data.csv`. For each (model, fault_type) pair three metrics
are reported:

- `accuracy`: fraction of test samples in the subset whose predicted
  label matches ground truth.
- `detection_rate`: fraction of test samples in the subset for which
  the model predicts a non-zero label. For `fault_type == 'normal'`
  this becomes the false alarm rate (FAR).
- `failure_recall`: for subsets that contain at least one true label=2
  sample, the recall of label=2. Reported as NaN when the subset has
  no label=2 samples (e.g. `normal`, or `replay` in most seeds).

The evaluation logic lives in `ml.evaluation.evaluate_per_fault_type`,
so the same computation can be reused by Phase 12.B (OOD),
Phase 12.C (authentication ablation), and Phase 12.D
(strict-round-validation ablation).

### Refactor: aggregate_metrics helper

Phase 12.A-5 also introduced `ml.evaluation.aggregate_metrics`, a
reusable groupby + mean/std + save-to-CSV helper. The four scripts
`train_model_default.py`, `robustness.py`, `scalability.py`, and the
new `per_fault_type_analysis.py` now share this helper. Column naming
switched from `{metric}` to `{metric}_mean` / `{metric}_std`, so
`plot_robustness.py` and `plot_scalability.py` were updated
accordingly. A regression test verified that the numeric contents of
`model_metrics_default_multiseed.csv`, `robustness_curve.csv`, and
`scalability_curve.csv` match the pre-refactor versions exactly, so
the change is a pure DRY refactor with no semantic drift.

### Phase 12.A-5 Results

**Detection rate per (model, fault_type):**

| fault_type    | DT     | LR     | RF     | XGB    | Support |
|---------------|--------|--------|--------|--------|---------|
| normal (FAR)  | 0.058  | 0.108  | 0.048  | 0.037  | 80      |
| silent        | 0.682  | 0.673  | 0.682  | 0.682  | 40      |
| replay        | 0.927  | 0.852  | 0.947  | 0.946  | 40      |
| equivocation  | 0.574  | 0.527  | 0.584  | 0.584  | 40      |
| delay         | 0.989  | 1.000  | 1.000  | 1.000  | 40      |

**Failure recall per (model, fault_type) — reported only for subsets with sufficient label=2 support:**

| fault_type   | DT     | LR     | RF     | XGB    |
|--------------|--------|--------|--------|--------|
| silent       | 1.000  | 0.988  | 1.000  | 1.000  |
| delay        | 0.992  | 0.992  | 1.000  | 1.000  |
| equivocation | 0.968  | 0.884  | 1.000  | 1.000  |

Four observations:

1. **Equivocation is the hardest attack to detect prophylactically.**
   Detection rate is 53–58% across all four models. However, of the
   equivocation rounds that produce a true failure (label=2), 88–100%
   are correctly identified. The 42–47% "missed" cases are rounds
   where the equivocation attack did not manifest in observable
   consensus metrics — the features cluster with normal rounds and
   the classifier has no signal to trigger on. Equivocation is
   therefore not *undetected* but rather *inherently silent when it
   fails to disrupt consensus*.
2. **Delay is the loudest attack** with 99–100% detection across all
   models. This is consistent with delay's mechanism: elevated
   `consensus_agreement_time` and `phase_completion_time` are directly
   observable and strongly correlated with label.
3. **Logistic Regression has the highest false alarm rate** on normal
   rounds (10.8% vs 3.7%–5.8% for tree models). This aligns with the
   Phase 12.A-2 observation that linear boundaries do not carve out
   the normal-round region as tightly as tree ensembles can.
4. **Replay reveals a label-distribution asymmetry.** Replay attacks
   in this dataset produce 198/200 label=1 (degraded) and only 2/200
   label=2 (failure), which is why `failure_recall` cannot be reliably
   estimated for replay under multi-seed 20% test splits. The metric
   is reported as NaN for replay, and replay is omitted from the
   failure_recall figure. This is a property of the dataset (replay
   attacks in a 7-node network with f=2 rarely cause outright
   failure), not a metric or model issue.

## Phase 12.A-6: Prediction Lead Time

Phase 12.A-6 measures how far in advance a trained classifier can flag
a failure-causing round, measured in milliseconds of "lead time" from
the earliest cutoff at which the model predicts label=2 back to the
round's timeout deadline (`CONSENSUS_TIMEOUT_MS = 150 ms`). Cutoffs
are 25/50/75/100/125/150 ms (`config.CUTOFFS_MS`).

The phase went through two failed-then-diagnosed iterations before the
final design. Both dead ends are documented here because the diagnosis
chain is itself a report-worthy result.

### Iteration 1: naive slicing — 100% detection, 100% false alarm

The first implementation trained models on `consensus_data.csv`
(full-round features) and predicted on time-sliced features from
`compute_features_at_time(rr, cutoff_ms)`. Result: detection rate 100%
at cutoff=25 for every (model, fault_type) — but false alarm rate on
normal rounds was **also 100%** at cutoff=25/50. The initial suspicion
was `message_drop_rate`, which at the time was not time-sliced: it
used the full-round `dropped / sent` scalars, leaking the round's
final outcome into the earliest snapshot.

### Fix 1: real time-slicing of `message_drop_rate`

- `build_round_result` now exposes `'all_messages'` (every message
  sent during the round, delivered or not; dropped messages have
  `delivery_time=None`).
- `compute_features_at_time` computes
  `sent_by_cutoff = |{m : send_time <= cutoff}|` and
  `dropped_by_cutoff = |{m : send_time <= cutoff, delivery_time=None}|`.
  Known approximation: whether an undelivered message is "dropped" vs
  "in flight" uses the end-of-simulation truth, since drop events are
  not timestamped. Acceptable for this experiment.
- The `test_lead_time.py` invariant
  (`compute_features_at_time(rr, ∞) == extract_features(rr)`) still
  passes: at infinity the sliced counters equal the round scalars.

**Side discovery — ghost messages in `message_log`.** The invariant
test caught a latent `simpy_network.py` bug: `send_message` appended
the original `msg` to `message_log` unconditionally, but when the
fault injector *substitutes* the message (equivocation returns
`[forked]` without the original), the original was never delivered
nor removed — a permanent `delivery_time=None` ghost entry. Invisible
before now because all prior consumers filtered on
`delivery_time is not None`; the time-sliced drop-rate count was the
first code path to read undelivered messages. Fixed by removing the
original from `message_log` when `result[0] is not msg`. **No prior
phase is affected**: `extract_features` and all dataset generation
read the `round_stats` scalars, never `message_log`.

### Iteration 2 diagnosis: the real cause is train/inference distribution mismatch

After Fix 1, the false-alarm curve was essentially unchanged (still
~100% at cutoff=25/50). Drop-rate leakage was real but was not the
main driver. A feature-level comparison of normal-round snapshots
against the training distribution located the actual cause:

| feature | normal @ 25ms | label=0 train mean | label=2 train mean |
|---|---|---|---|
| voting_consistency | 0.000 | 0.996 | 0.488 |
| quorum_margin | −0.714 | +0.282 | −0.227 |
| message_consistency | 0.000 | 0.983 | 0.695 |
| response_time | 97.4 | 34.6 | 126.1 |

At 25 ms no node has committed yet, so a *healthy* round's snapshot
(nothing committed, zero consistency, deeply negative quorum margin)
sits squarely in — indeed beyond — the label=2 region of the training
distribution. A model trained only on end-of-round features has never
seen "a round 1/6 of the way through" and faithfully classifies every
early snapshot as failure. The 100% false alarm rate was the model
working as trained, not a feature bug. Conversely, the 100% detection
rate was meaningless: the model flagged *everything* early.

### Final design: per-cutoff training on snapshot features

The fix is to let the model see mid-round snapshots at training time
(standard early-classification setup):

- `scripts/generate_lead_time_train.py` (new) simulates the main-set
  composition (4 fault types × `ROUNDS_PER_FAULT` + `NORMAL_ROUNDS`
  normal = 1200 rounds) and writes
  `data/raw/lead_time_snapshots.csv`: one row per (round, cutoff) =
  7200 rows. Features are sliced at the cutoff; the label is computed
  **once per round from full-round features** (the final outcome),
  so every cutoff row of a round carries the same label — the model
  learns "given the view at t, will this round fail", i.e. genuine
  prediction rather than description of current state.
- `scripts/lead_time.py` (rewritten) trains one model set **per
  cutoff** (6 cutoffs × 4 models × 5 seeds). Train/test split is
  **group-wise by `round_uid`** (stratified by round label,
  `test_size=0.2`, per-seed `random_state`): all 6 snapshots of a
  round stay on the same side, otherwise correlated slices of the
  same round would leak across the split.
- Lead time per (seed, model, failure round): the earliest cutoff
  whose *own* model predicts 2, `lead = 150 − cutoff`; never-alarmed
  rounds count as missed (`detected=0`, `lead_time_ms=0`). False
  alarm per (model, cutoff): fraction of normal-round snapshots
  predicted as 2.

### Results (5 seeds)

False alarm rate on normal rounds:

| cutoff | DT    | LR    | RF    | XGB   |
|--------|-------|-------|-------|-------|
| 25     | 0.334 | 0.062 | 0.252 | 0.284 |
| 50     | 0.107 | 0.062 | 0.072 | 0.070 |
| 75     | 0.027 | 0.025 | 0.017 | 0.012 |
| 100+   | ~0    | ~0    | ~0    | ~0    |

Lead time (ms, mean ± std over detected rounds) and detection rate:

| fault_type | DT | LR | RF | XGB | detection |
|---|---|---|---|---|---|
| silent | 113.6 ± 20.5 | 118.2 ± 20.6 | 119.7 ± 13.5 | 115.5 ± 20.6 | 100% |
| delay | 108.2 ± 25.3 | 110.8 ± 20.9 | 111.2 ± 20.1 | 109.3 ± 22.5 | 100% |
| equivocation | 86.9 ± 22.8 | 88.1 ± 21.2 | 88.8 ± 20.6 | 88.8 ± 19.5 | 92–100% |

Observations:

1. The lead-time ordering matches attack mechanics: silent leaks the
   earliest signal (Byzantine nodes drop messages from t=0, visible in
   the now-correctly-sliced `message_drop_rate`), delay is next
   (elevated latency is observable early), equivocation is last
   (~60 ms before its signature surfaces) — consistent with the
   Phase 12.A-5 finding that equivocation is the stealthiest attack.
2. **Logistic Regression achieves 6.2% FAR at cutoff=25**, vs 25–33%
   for the tree models. Under a `FAR < 25%` gate, LR is usable from
   25 ms while trees are usable from 50 ms: the linear model wins the
   earliest-warning regime, echoing the Phase 12.A-4 result that LR
   is the most distribution-shift-robust model despite its lower
   in-distribution ceiling.
3. Detection is near-total (≥99%; LR 92% on equivocation) once all
   six cutoffs are allowed, so the informative quantities are the
   lead-time distribution and the FAR-vs-cutoff curve, not the
   detection rate itself.

### Files touched in this phase

- `src/simulation/round_result.py` (added `all_messages`)
- `src/simulation/simpy_network.py` (ghost-message fix in `send_message`)
- `src/data/feature_extractor.py` (added `compute_features_at_time`;
  time-sliced `message_drop_rate`)
- `scripts/generate_lead_time.py` (new — pickle generator; superseded
  by the snapshot CSV for training, kept for round-level inspection)
- `scripts/generate_lead_time_train.py` (new — snapshot CSV generator)
- `scripts/lead_time.py` (rewritten — per-cutoff training + group split)
- `scripts/plot_lead_time.py` (new — FAR curve + lead-time bar chart)
- `test_lead_time.py` at project root (new — invariant test)
- `config.py` (added `FAILURE_CAUSING_FAULTS`, `BYZ_IDS`, `CUTOFFS_MS`)
- `data/raw/lead_time_snapshots.csv` (generated, 7200 rows)
- `results/tables/lead_time_raw.csv`,
  `results/tables/lead_time_summary.csv`,
  `results/tables/lead_time_detection_rate.csv`,
  `results/tables/lead_time_false_alarm.csv`
- `results/figures/lead_time_false_alarm.png`,
  `results/figures/lead_time_comparison.png`

## Cross-phase feature-extractor decoupling

Before Phase 12.A-2, `feature_extractor.py` referenced `NUM_NODES` and
`QUORUM` from `config.py`. This made the extracted features incorrect
when `run_pbft_simulation` was called with a non-default `total_nodes`,
which was the case for any scalability experiment.

Phase 12.A-2 switches `quorum_margin` and the prepare-count loop to
read `round_result['quorum_size']` and `round_result['total_nodes']`
instead. The round result already carries the per-round true values,
populated by `build_round_result` from the actual node list. The
`QUORUM` and `NUM_NODES` config imports were removed from
`feature_extractor.py`.

This change was a precondition for Phase 12.A-4 (scalability) and is
also exercised by Phase 12.A-3, since `generate_robustness_test.py`
passes byzantine_node_ids lists of varying length through the same
simulator + extractor pipeline.
