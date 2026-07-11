import pandas as pd
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR
from src.plotting.plots import plot_grouped_bar


def main():
    df_ml = pd.read_csv(RESULTS_TABLES_DIR / 'model_metrics_default_13.csv')
    df_base = pd.read_csv(RESULTS_TABLES_DIR / 'baseline_metrics_multiseed.csv')
    df = pd.concat([df_base, df_ml], ignore_index=True)

    rows = []
    for _, r in df.iterrows():
        for metric in ['accuracy', 'precision', 'recall', 'f1']:
            rows.append({'model': r['model'], 'metric': metric,
                         'mean': r[f'{metric}_mean'], 'std': r[f'{metric}_std']})
    long_df = pd.DataFrame(rows)

    plot_grouped_bar(long_df, RESULTS_FIGURES_DIR / 'baseline_vs_ml.png',
                     x_col='metric', y_col='mean', std_col='std', group_col='model',
                     x_label='Metric', y_label='Score', y_lim=(0.5, 1.0),
                     title='Static baselines vs ML monitors (main test split, 5 seeds)')


if __name__ == '__main__':
    main()
