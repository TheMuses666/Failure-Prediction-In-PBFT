import pandas as pd

from src.plotting.plots import plot_grouped_curve, plot_grouped_bar
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR, CUTOFFS_MS

MARKERS = {
    'decision_tree': 'o',
    'random_forest': 's',
    'xgboost': '^',
    'logistic_regression': 'D',
}


def main():
    # Figure 1: false alarm rate vs cutoff (normal rounds)
    fa = pd.read_csv(RESULTS_TABLES_DIR / 'lead_time_false_alarm.csv')
    plot_grouped_curve(
        df=fa,
        out_path=RESULTS_FIGURES_DIR / 'lead_time_false_alarm.png',
        x_col='cutoff',
        y_col='false_alarm_rate_mean',
        std_col='false_alarm_rate_std',
        group_col='model',
        x_label='Prediction cutoff (ms)',
        y_label='False alarm rate',
        title='False alarm rate vs prediction cutoff (normal rounds)',
        x_ticks=CUTOFFS_MS,
        y_lim=(0, 0.5),
        markers=MARKERS,
    )

    # Figure 2: lead time bars per (fault_type, model)
    lt = pd.read_csv(RESULTS_TABLES_DIR / 'lead_time_summary.csv')
    plot_grouped_bar(
        df=lt,
        out_path=RESULTS_FIGURES_DIR / 'lead_time_comparison.png',
        x_col='fault_type',
        y_col='lead_time_ms_mean',
        std_col='lead_time_ms_std',
        group_col='model',
        x_label='Fault type',
        y_label='Prediction lead time (ms)',
        title='Prediction lead time by fault type (higher = earlier warning)',
        y_lim=(0, 150),
    )

    # Figure 3: macro-F1 vs cutoff
    f1 = pd.read_csv(RESULTS_TABLES_DIR / 'lead_time_f1_by_cutoff.csv')
    plot_grouped_curve(
        df=f1,
        out_path=RESULTS_FIGURES_DIR / 'lead_time_f1_by_cutoff.png',
        x_col='cutoff',
        y_col='f1_mean',
        std_col='f1_std',
        group_col='model',
        x_label='Prediction cutoff (ms)',
        y_label='Macro-F1',
        title='Macro-F1 vs prediction cutoff',
        x_ticks=CUTOFFS_MS,
        y_lim=(0.4, 1.0),
        markers=MARKERS,
    )

    # Figure 4: degraded/failure detection rate vs cutoff
    det = pd.read_csv(RESULTS_TABLES_DIR / 'early_detection_rate_by_cutoff.csv')
    plot_grouped_curve(
        df=det,
        out_path=RESULTS_FIGURES_DIR / 'early_detection_rate_by_cutoff.png',
        x_col='cutoff',
        y_col='detection_rate_mean',
        std_col='detection_rate_std',
        group_col='model',
        x_label='Prediction cutoff (ms)',
        y_label='Detection rate (degraded/failure rounds)',
        title='Early detection rate vs prediction cutoff',
        x_ticks=CUTOFFS_MS,
        y_lim=(0.4, 1.0),
        markers=MARKERS,
    )

    print('Saved lead_time_false_alarm.png, lead_time_comparison.png, '
          'lead_time_f1_by_cutoff.png and early_detection_rate_by_cutoff.png')


if __name__ == '__main__':
    main()
