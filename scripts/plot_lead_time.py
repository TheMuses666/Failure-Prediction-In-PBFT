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
    # 图 1：FAR 随 cutoff 的曲线（normal 轮误报率）
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

    # 图 2：lead time 按 (fault_type, model) 的柱状图
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

    print('Saved lead_time_false_alarm.png and lead_time_comparison.png')


if __name__ == '__main__':
    main()
