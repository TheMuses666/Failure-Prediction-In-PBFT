import pandas as pd
from src.plotting.plots import plot_grouped_bar
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'per_fault_type.csv')

    plot_grouped_bar(
        df=df,
        out_path=RESULTS_FIGURES_DIR / 'detection_rate_by_fault_type.png',
        x_col='fault_type',
        y_col='detection_rate_mean',
        std_col='detection_rate_std',
        group_col='model',
        x_label='Fault type',
        y_label='Detection rate',
        title='Detection rate per fault type (mean ± std over 5 seeds)',
        y_lim=(0, 1.05),
    )
    FT_WITH_ENOUGH_FAILURE = ['delay', 'equivocation', 'silent']
    df_failure = df[df['fault_type'].isin(FT_WITH_ENOUGH_FAILURE)]
    plot_grouped_bar(
        df=df_failure,
        out_path=RESULTS_FIGURES_DIR / 'failure_recall_by_fault_type.png',
        x_col='fault_type',
        y_col='failure_recall_mean',
        std_col='failure_recall_std',
        group_col='model',
        x_label='Fault type',
        y_label='Failure recall',
        title='Recall of failure label (label=2) per fault type',
        y_lim=(0, 1.05),
    )

if __name__ == '__main__':
    main()