import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shap

from config import (
    RAW_DATA_FILE, RANDOM_SEED,
    FEATURE_COLUMNS_EXTEND, RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR,
)
from ml.preprocessing import load_and_split_trainval_ext
from utils.helpers import build_and_fit_all_candidates

CLASS_NAMES = {0: 'normal', 1: 'degraded', 2: 'failure'}
SHAP_MODELS = ['xgboost', 'random_forest']   # tree models only; LR uses coefficients


def mean_abs_shap(clf, X_scaled):
    """Return (n_features, n_classes) mean(|SHAP|) matrix for a tree model."""
    shap_values = shap.TreeExplainer(clf).shap_values(X_scaled)
    if isinstance(shap_values, list):
        # list of (n_samples, n_features), one per class
        stacked = np.stack(shap_values, axis=-1)      # (n, features, classes)
    else:
        stacked = shap_values                          # already (n, features, classes)
    return np.abs(stacked).mean(axis=0)                # (features, classes)


def main():
    X_tv, X_test, y_tv, y_test = load_and_split_trainval_ext(
        feature_cols=FEATURE_COLUMNS_EXTEND, csv_path=RAW_DATA_FILE, seed=RANDOM_SEED)

    fitted = build_and_fit_all_candidates(RANDOM_SEED, X_tv, y_tv)

    records = []
    per_class = {}   # model -> (features, classes) matrix
    for name in SHAP_MODELS:
        pipe = fitted[name]
        X_scaled = pipe.named_steps['scaler'].transform(X_test)
        m = mean_abs_shap(pipe.named_steps['clf'], X_scaled)
        per_class[name] = m
        for i, feat in enumerate(FEATURE_COLUMNS_EXTEND):
            records.append({
                'model': name,
                'feature': feat,
                'shap_total': m[i].sum(),
                **{f'shap_{CLASS_NAMES[c]}': m[i, c] for c in range(m.shape[1])},
            })

    table = pd.DataFrame(records)
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(RESULTS_TABLES_DIR / 'shap_importance.csv', index=False)
    print(table.sort_values(['model', 'shap_total'], ascending=[True, False])
          .to_string(index=False))

    # Figure: per-class stacked mean(|SHAP|) bar for XGBoost, sorted by total
    m = per_class['xgboost']
    order = np.argsort(m.sum(axis=1))                  # ascending, for barh
    feats = [FEATURE_COLUMNS_EXTEND[i] for i in order]

    fig, ax = plt.subplots(figsize=(8, 6))
    left = np.zeros(len(order))
    for c in range(m.shape[1]):
        vals = m[order, c]
        ax.barh(feats, vals, left=left, label=CLASS_NAMES[c])
        left += vals
    ax.set_xlabel('mean(|SHAP value|)')
    ax.set_title('XGBoost feature importance (SHAP, test set)')
    ax.legend(title='class')
    ax.grid(True, alpha=0.3, axis='x')

    out = RESULTS_FIGURES_DIR / 'feature_importance.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches='tight')
    print(f'Figure saved --> {out}')


if __name__ == '__main__':
    main()
