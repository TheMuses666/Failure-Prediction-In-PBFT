# Phase 9 — ML Pipeline Design Decisions

This note records non-obvious design choices made during Phase 9 implementation
of the ML pipeline (`ml/preprocessing.py`, `ml/models/*`, `ml/evaluation.py`,
`scripts/train_model.py`). Each decision is recorded so that the report and
future ablation experiments can reference the original reasoning without having
to re-derive it from the code.

---

## 1. Feature set retained as the full 11 features

**Decision:** All 11 features defined in `config.FEATURE_COLUMNS` are passed to
the models unchanged, including `leader_change_frequency`, even though it
currently carries zero variance.

**Why `leader_change_frequency` is kept despite being all-zero:**

- View-change is documented as out of scope for the current simulator
  (see SIMPY_MILESTONES.md Phase 5: *"view-change count, initially 0 if view
  change is documented as out of scope"*).
- Tree-based models (Decision Tree, Random Forest, XGBoost) are completely
  immune to zero-variance features — a feature with no variance can never be
  selected as a split, so it contributes nothing to predictions and harms
  nothing either. It is effectively a no-op for the current model family.
- Removing the column would create a schema mismatch between the design
  document (which advertises 11 features across 3 groups) and the trained
  models, complicating the report and any future view-change extension.
- If view-change is added later, the column will already be wired through the
  pipeline with no schema migration required.

**How to apply:** Do not drop zero-variance columns automatically in
`preprocessing.py`. If a future Phase 11 ablation experiment wants to compare
"with vs without zero-variance features" the experiment script should drop
the column locally rather than changing the global preprocessing contract.

**Report wording (suggested):**
> `leader_change_frequency` was retained as a placeholder for a future
> view-change implementation. Under the current scope it carries zero variance
> and therefore does not contribute to tree splits, but it is preserved in the
> feature schema to keep the design and trained models aligned.

---

## 2. Train / Val / Test split = 70 / 10 / 20, stratified, seed = 42

**Decision:** Two-stage split using `train_test_split` from sklearn:
1. First split: 80 / 20 to isolate the test set.
2. Second split: from the remaining 80%, take 12.5% as val (so val = 10% of
   the full dataset, train = 70%).

Both splits use `stratify=y` (and `stratify=y_trainval` for the second split)
and `random_state=config.RANDOM_SEED`.

**Why stratify:** the label distribution is unbalanced
(approximately normal:544, degraded:281, failure:375 out of 1200). Without
stratification, the val and test sets can end up with too few samples of the
minority class, making per-class metrics noisy.

**Why two stages instead of one three-way split:** `train_test_split` only
returns two splits per call. Chaining two calls is the standard idiom and
keeps the stratification logic explicit.

---

## 3. Min-Max scaling fitted on train only

**Decision:** `MinMaxScaler` is `fit` on `X_train` only, then `transform` is
applied to `X_val` and `X_test`.

**Why:** val and test are intended to behave like "future, unseen data". If
the scaler is allowed to see their min/max values during fitting, information
from the held-out splits leaks into the training pipeline. The leakage is
small in absolute terms for Min-Max scaling but is a hard rule in ML
methodology and is cheap to enforce.

**Why scale at all when the main models are tree-based:** trees do not need
scaling, but enforcing it now keeps the pipeline contract uniform and ready
for non-tree models in the post-submission extension (e.g. Bi-LSTM in the
conference extension, see MILESTONES.md "Post-Submission" section).

---

## 4. Auxiliary columns excluded from `X`

**Decision:** `X = df[config.FEATURE_COLUMNS]` only — the auxiliary columns
defined in `config.AUXILIARY_COLUMNS` (`forged`, `replayed`, `silent_mode`,
`delay_distribution`, etc.) are deliberately excluded from model input.

**Why:** auxiliary fields describe *how the round was generated* (ground-truth
attack metadata), not *how the consensus protocol behaved*. Using them as
input features would let the model trivially recover the label from the
attack metadata rather than learning predictive patterns from consensus
behavior — defeating the research question.

This matches Phase 5's explicit rule:
> "These auxiliary fields are recorded for validation, ablation, and report
> interpretation. They MUST NOT be used as model input features unless the
> corresponding ablation experiment explicitly opts in (see Phase 11)."

---

## 5. Default hyperparameters for the baseline run

**Decision:** All three classifiers are instantiated with only
`random_state=RANDOM_SEED` — no `max_depth`, `n_estimators`, `learning_rate`,
etc. are overridden.

**Why:** Phase 11 includes an ablation experiment that explicitly compares
tuned vs untuned configurations. If Phase 9 already tuned hyperparameters,
there would be no untuned baseline to compare against in Phase 11, and the
ablation story collapses.

**Observed consequence:** all three models report
`train_accuracy ≈ 1.0`, which is normal for unbounded trees on a dataset of
this size and is not interpreted as overfitting in isolation. Generalization
is assessed from the train–val gap (DT: ~10%, RF: ~4%, XGB: ~4%) and from
the test-set metrics in `results/tables/model_metrics.csv`.

---

## 6. `macro` averaging for multi-class precision / recall / F1

**Decision:** `precision_score`, `recall_score`, and `f1_score` are called
with `average="macro"`.

**Why:** the three classes (normal / degraded / failure) are unbalanced.
- `macro` averages per-class scores with equal weight, so the minority class
  (degraded) is not drowned out by the majority class.
- `weighted` would re-introduce the imbalance bias.
- `micro` collapses to overall accuracy on multi-class single-label problems,
  which is already reported separately.

For this research question, failing to detect a `failure` round (recall) is
operationally more costly than a false alarm (precision). `macro` averaging
treats each class as equally important, which aligns with that priority
better than `weighted`.

---

## 7. Response time measured as batch-average

**Decision:** Model inference time is reported as
`(elapsed_for_batch_predict / len(X_test)) * 1000` in milliseconds per sample.

**Why this is an approximation:** `model.predict()` is vectorized internally,
so batch prediction is faster per sample than calling `predict()` 240 times in
a loop. The batch-average underestimates true single-sample latency but is
consistent across all three models and is sufficient to compare them and to
contrast with the ~60 ms duration of a single PBFT round (the deployment
budget).

**When to upgrade:** if a reviewer challenges the figure, replace with a
per-sample timing loop. The metric definition lives in `ml/evaluation.py` and
is the only place that needs to change.

**Disambiguation:** this `model_response_time_ms` is distinct from the
`response_time` feature in `config.FEATURE_COLUMNS`. The feature is a PBFT
node behavior (mean time from pre-prepare to first response, in simulated
ms); the metric is ML inference latency (in wall-clock ms). They share a
name but are unrelated quantities.

---

## 8. Out of scope for Phase 9 — deferred to Phase 11

The following items appear in the Phase 9 milestone but are intentionally
left for Phase 11, because Phase 11 is where the corresponding experiments
are designed end-to-end:

- **Prediction Lead Time** — Phase 11.A.
- **OOD robustness on `extended_robustness.csv`** (Phase 4b/4c modes) —
  Phase 11.B. The trained models and scaler are saved to
  `results/models/` so Phase 11.B can load them without retraining.
- **Hyperparameter ablation** — Phase 11.A.
- **SHAP feature importance** — Phase 11.A.

Phase 9's deliverable is the trained models + main-dataset metrics; the
research-quality experiments that consume those artifacts live in Phase 11.
