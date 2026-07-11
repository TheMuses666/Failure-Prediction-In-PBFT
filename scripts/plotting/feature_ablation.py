import pandas as pd
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR
from src.plotting.plots import plot_grouped_bar

FEATURE_SETS = ['11_features', '12_quorum_only', '12_prepare_only', '13_features']


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'ablation_feature_set.csv')

    rows = []
    for _, r in df.iterrows():
        for fs in FEATURE_SETS:
            rows.append({'model': r['model'], 'feature_set': fs,
                         'f1_mean': r[f'f1_mean_{fs}'],
                         'f1_std': r[f'f1_std_{fs}']})
    long_df = pd.DataFrame(rows)

    plot_grouped_bar(long_df, RESULTS_FIGURES_DIR / 'feature_ablation.png',
                     x_col='feature_set', y_col='f1_mean', std_col='f1_std',
                     group_col='model',
                     x_label='Feature set', y_label='Macro-F1',
                     title='Feature-set ablation (5 seeds)',
                     y_lim=(0.8, 1.0), figsize=(10, 5))


if __name__ == '__main__':
    main()
