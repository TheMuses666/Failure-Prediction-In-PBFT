from src.plotting.plots import plot_grouped_bar
from config import RESULTS_FIGURES_DIR, RESULTS_TABLES_DIR
import pandas as pd

def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'model_metrics_default_13.csv')
    rows = []
    for _, r in df.iterrows():
        for metric in ['accuracy', 'precision', 'recall', 'f1']:
            rows.append({'model': r['model'], 'metric': metric,
                     'mean': r[f'{metric}_mean'], 'std': r[f'{metric}_std']})
    long_df = pd.DataFrame(rows)

    plot_grouped_bar(long_df, RESULTS_FIGURES_DIR / 'model_comparison.png',
                     x_col='metric', y_col='mean', std_col='std', group_col='model',
                     x_label='Metric', y_label='Score', y_lim=(0.8, 1.0),
                     title='Model comparison (13 features, 5 seeds)')
    
if __name__ == '__main__':
    main()