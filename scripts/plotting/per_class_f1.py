import pandas as pd
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR, LABEL_NAMES
from src.plotting.plots import plot_grouped_bar


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'per_class_report.csv')
    df = df[df['class'].astype(str).isin(['0', '1', '2'])].copy()
    df['class'] = df['class'].astype(int).map(LABEL_NAMES)

    agg = (df.groupby(['model', 'class'])['f1']
             .agg(['mean', 'std']).reset_index())

    plot_grouped_bar(agg, RESULTS_FIGURES_DIR / 'per_class_f1.png',
                     x_col='class', y_col='mean', std_col='std',
                     group_col='model',
                     x_label='Class', y_label='F1-score', y_lim=(0.5, 1.0),
                     title='Per-class F1 on the main test split (tuned models, 5 seeds)')


if __name__ == '__main__':
    main()
