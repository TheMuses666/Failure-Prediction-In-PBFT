import pandas as pd
from src.plotting.plots import plot_grouped_curve
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'auth_ablation_detection.csv')
    df['intensity'] = df['fault_type'].str.removeprefix('forgery_i').astype(float)

    plot_grouped_curve(
        df=df,
        out_path=RESULTS_FIGURES_DIR / 'auth_ablation_detection.png',
        x_col='intensity',
        y_col='detection_rate_mean',
        std_col='detection_rate_std',
        group_col='model',
        x_label='Forgery fault intensity',
        y_label='Detection rate',
        title='Detection rate vs forgery intensity (no message authentication)',
        x_ticks=[0.2, 0.5, 1.0],
        y_lim=(0.0, 1.0),
        markers={
            'decision_tree': 'o',
            'random_forest': 's',
            'xgboost': '^',
            'logistic_regression': 'D',
            'threshold_based': 'v',
            'rule_based': 'x',
            'count_based': 'P',
        },
        legend_outside=True,
    )


if __name__ == '__main__':
    main()