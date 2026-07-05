import pandas as pd
from src.plotting.plots import plot_grouped_curve
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR

ML_MODELS = ['decision_tree', 'random_forest', 'xgboost', 'logistic_regression']

def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'mixed_n_curve.csv')
    df = df[df['model'].isin(ML_MODELS)].copy()
    df['group'] = df['model'] + ' (' + df['arms'] + ')'

    plot_grouped_curve(
        df=df,
        out_path=RESULTS_FIGURES_DIR / 'mixed_n_curve.png',
        x_col='N',
        y_col='f1_mean', std_col='f1_std',
        group_col='group',
        x_label='Total node count (N)',
        y_label='Macro F1',
        title='Effect of mixed-N training on scale generalisation',
        x_ticks=[7, 10, 13],
        y_lim=(0.5, 1.0),
        legend_outside=True,
    )

if __name__ == '__main__':
    main()