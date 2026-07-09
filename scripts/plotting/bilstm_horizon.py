import pandas as pd
from src.plotting.plots import plot_grouped_curve, plot_grouped_bar
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR

CLASS_ORDER = {'normal': '0 normal', 'degraded': '1 degraded', 'failure': '2 failure'}


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'model_metrics_bilstm.csv')
    k5 = df[df['k'] == 5]

    plot_grouped_curve(
        df=k5,
        out_path=RESULTS_FIGURES_DIR / 'bilstm_horizon_comparison.png',
        x_col='horizon',
        y_col='f1_mean', std_col='f1_std',
        group_col='model',
        x_label='Prediction target (0 = current round, 1 = next round)',
        y_label='Macro F1',
        title='Temporal window (BiLSTM) vs last-round tabular models (k=5)',
        x_ticks=[0, 1],
        y_lim=(0.5, 1.0),
        markers={
            'decision_tree': 'o', 'random_forest': 's',
            'xgboost': '^', 'logistic_regression': 'D', 'bilstm': '*',
        },
        legend_outside=True,
    )

    # Per-class F1 at horizon=1: melt the f1_<class>_mean/std columns into rows
    h1 = k5[k5['horizon'] == 1]
    rows = []
    for _, r in h1.iterrows():
        for cls, label in CLASS_ORDER.items():
            rows.append({
                'model': r['model'],
                'class': label,
                'f1_mean': r[f'f1_{cls}_mean'],
                'f1_std': r[f'f1_{cls}_std'],
            })

    plot_grouped_bar(
        df=pd.DataFrame(rows),
        out_path=RESULTS_FIGURES_DIR / 'bilstm_per_class_f1.png',
        x_col='class',
        y_col='f1_mean', std_col='f1_std',
        group_col='model',
        x_label='Class',
        y_label='F1',
        title='Next-round warning (horizon=1, k=5): per-class F1',
        y_lim=(0.0, 1.0),
    )


if __name__ == '__main__':
    main()
