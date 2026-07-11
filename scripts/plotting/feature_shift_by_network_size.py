import pandas as pd
from config import DATA_RAW_DIR, RAW_DATA_FILE, RESULTS_FIGURES_DIR, FEATURE_COLUMNS_EXTEND
from src.plotting.plots import plot_feature_distribution_by_group


def main():
    frames = []
    for name, path in [('N=7', RAW_DATA_FILE),
                       ('N=10', DATA_RAW_DIR / 'scalability_n10.csv'),
                       ('N=13', DATA_RAW_DIR / 'scalability_n13.csv')]:
        df = pd.read_csv(path)
        df['network_size'] = name
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)

    plot_feature_distribution_by_group(
        combined, FEATURE_COLUMNS_EXTEND, 'network_size',
        RESULTS_FIGURES_DIR / 'feature_shift_by_network_size.png',
        title='Feature distributions across network sizes')


if __name__ == '__main__':
    main()
