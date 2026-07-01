import pandas as pd
from src.plotting.plots import plot_grouped_curve
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'robustness_curve.csv')
    
    plot_grouped_curve(
        df=df,
        out_path=RESULTS_FIGURES_DIR / 'robustness_curve.png',
        x_col='f',
        y_col='mean',
        std_col='std',
        group_col='model',
        x_label='Number of Byzantine nodes (f)',
        y_label='Macro F1',
        title='Robustness to Byzantine ratio (N=7 nodes)',
        vline_x=2.5,
        vline_label='PBFT safety bound (f ≤ 2)',
        x_ticks=[1, 2, 3],
        y_lim=(0.5, 1.0),
        markers={
            'decision_tree': 'o',
            'random_forest': 's',
            'xgboost': '^',
            'logistic_regression': 'D',
        },
    )


if __name__ == '__main__':
    main()