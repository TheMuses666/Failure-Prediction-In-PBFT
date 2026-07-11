import pandas as pd
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR
from src.plotting.plots import plot_grouped_bar


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'ablation_tuning.csv')

    rows = []
    for _, r in df.iterrows():
        rows.append({'model': r['model'], 'arm': 'default',
                     'f1_mean': r['default_f1_mean'], 'f1_std': r['default_f1_std']})
        rows.append({'model': r['model'], 'arm': 'tuned',
                     'f1_mean': r['tuned_f1_mean'], 'f1_std': r['tuned_f1_std']})
    long_df = pd.DataFrame(rows)

    plot_grouped_bar(long_df, RESULTS_FIGURES_DIR / 'tuning_ablation.png',
                     x_col='model', y_col='f1_mean', std_col='f1_std',
                     group_col='arm',
                     x_label='Model', y_label='Macro-F1',
                     title='Default vs tuned hyperparameters (11 features, 5 seeds)',
                     y_lim=(0.8, 1.0), figsize=(9, 5), x_rotation=15)


if __name__ == '__main__':
    main()
