import pandas as pd
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR
from src.plotting.plots import plot_grouped_bar

COUNTERS = [
    'wrong_content_prepare_quorums',
    'wrong_content_commit_quorums',
    'max_wrong_content_prepare_votes',
    'max_wrong_content_commit_votes',
]


def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'strict_ablation_quorum.csv')

    rows = []
    for _, r in df.iterrows():
        for counter in COUNTERS:
            rows.append({'scenario': r['scenario'], 'counter': counter,
                         'value': r[counter]})
    long_df = pd.DataFrame(rows)

    plot_grouped_bar(long_df, RESULTS_FIGURES_DIR / 'strict_ablation_quorum.png',
                     x_col='counter', y_col='value', std_col=None,
                     group_col='scenario',
                     x_label='Quorum-level counter', y_label='Count',
                     title='Protocol-level effect of strict round validation (quorum size = 5)',
                     figsize=(11, 5), x_rotation=20)


if __name__ == '__main__':
    main()
