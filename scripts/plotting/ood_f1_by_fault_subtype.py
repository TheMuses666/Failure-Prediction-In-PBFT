import pandas as pd
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR
from src.plotting.plots import plot_grouped_bar


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'ood_per_subtype.csv')

    plot_grouped_bar(df, RESULTS_FIGURES_DIR / 'ood_f1_by_fault_subtype.png',
                     x_col='fault_type', y_col='detection_rate_mean',
                     std_col='detection_rate_std', group_col='model',
                     x_label='Advanced fault subtype',
                     y_label='Detection rate (flagged degraded/failure)',
                     title='OOD detection rate by advanced-fault subtype (trained on main faults only)',
                     y_lim=(0, 1.05), figsize=(12, 5), x_rotation=30)


if __name__ == '__main__':
    main()
