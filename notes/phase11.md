## Phase 11: Random Forest tuning outcome

After tuning over a search space of 108 parameter combinations
(n_estimators × max_depth × min_samples_leaf × min_samples_split
× max_features), the tuned RF achieved mean macro-F1 = 0.9149 ± 0.0139
across 5 seeds, which is marginally below the Phase 9 single-seed
default result (0.9252).

Three observations:

1. The Phase 9 0.9252 is a single-seed point estimate without
   reported variance. The Phase 11 multi-seed reporting reveals
   the true mean lies about 1 std below it.
2. Across all 5 seeds, the best `max_features` was always `'sqrt'`,
   which is the sklearn default, and `min_samples_split` was
   typically 2 or 5 (near-default). RF was already close to optimal
   with default parameters on this dataset.
3. We retain the tuned model for consistency with the Phase 11
   pipeline (CV + multi-seed reporting), but acknowledge that the
   gain from tuning is marginal for RF on this 1200-row dataset.

## Per-class report scope

`per_class_report.csv` now records per-class precision / recall / F1
for all 5 Phase 11 seeds. Overall multi-seed stability is summarized
by `model_metrics_tuned.csv` (mean ± std across 5 seeds), while
`per_class_report.csv` keeps the class-level detail needed to inspect
which labels are hardest to detect under each model and seed.

## Scaler leakage in CV

Phase 11 initially fit MinMaxScaler on the full `trainval` before
GridSearchCV, meaning CV validation folds technically saw the scaler
statistics. For tree-based models (DT, RF, XGBoost) this introduces
no measurable leakage because they are invariant under monotonic
feature transformations.

Phase 11b adopts `sklearn.pipeline.Pipeline` to fold scaling into
CV correctly. Every candidate is wrapped as
`Pipeline([('scaler', MinMaxScaler()), ('clf', estimator)])` so that
each fold's scaler fits only on its train portion. After refit on
the full `trainval`, the Pipeline is persisted as the canonical
artifact (`results/models/*_tuned.joblib`); a standalone
`scaler_tuned.joblib` is no longer produced, removing the risk of
downstream code double-scaling raw inputs.

The numerical impact on Logistic Regression was zero across all
five seeds: `GridSearchCV` selected `C=10.0` (the boundary of the
search space) both before and after the fix, and the final refit
on the full `trainval` produces an identical model in either case.
The change is therefore methodological — eliminating the leakage
contract rather than the leakage value — and the qualitative
ranking (LR < DT < RF < XGB) is unchanged.

## Class weighting

Decision Tree and Random Forest use `class_weight='balanced'`.
XGBoost does not expose `class_weight`; instead, `sample_weight`
computed via `compute_sample_weight('balanced', y_trainval)` is
passed through `GridSearchCV.fit(...)`. Test-set evaluation uses
unweighted metrics to reflect true class distribution. The effect
on macro-F1 was marginal (Δ < 0.005), consistent with the moderate
2:1 class imbalance in this dataset.

## CV results scope

`cv_results.csv` records the full GridSearchCV trace for the
representative seed (RANDOM_SEED=42), serving as process
documentation. Multi-seed reporting is captured at the higher
levels of abstraction: `model_metrics_tuned.csv` (test performance
mean ± std), `best_hyperparameters.csv` (parameter selection
stability across seeds), and `per_class_report.csv` (per-class
metric stability). Expanding `cv_results.csv` to 5 seeds (≈690 rows)
would provide finer granularity but no additional research-question
insight, as CV scores across different data splits are not directly
comparable.
