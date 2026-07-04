import pandas as pd
from src.plotting.plots import plot_grouped_bar
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'strict_ablation_detection.csv')
    df['scenario'] = df['fault_type'].map({
        'replay_stale_strict_on':  'baseline (strict on)',
        'replay_stale_strict_off': 'weakened (strict off)',
    })

    plot_grouped_bar(
        df=df,
        out_path=RESULTS_FIGURES_DIR / 'strict_ablation_detection.png',
        x_col='scenario',
        y_col='detection_rate_mean',
        std_col='detection_rate_std',
        group_col='model',
        x_label='Round validation setting',
        y_label='Detection rate',
        title='Stale replay detection: strict vs weakened round validation',
        y_lim=(0.0, 1.0),
    )


if __name__ == '__main__':
    main()