import pandas as pd
from config import RAW_DATA_FILE, RESULTS_FIGURES_DIR, FEATURE_COLUMNS_EXTEND
from src.plotting.plots import plot_feature_distribution_by_group, plot_correlation_heatmap


def main():
    df = pd.read_csv(RAW_DATA_FILE)

    plot_feature_distribution_by_group(
        df, FEATURE_COLUMNS_EXTEND, 'fault_type',
        RESULTS_FIGURES_DIR / 'feature_distribution_by_fault.png',
        title='Feature distributions by fault type (main dataset)')

    plot_correlation_heatmap(
        df, FEATURE_COLUMNS_EXTEND,
        RESULTS_FIGURES_DIR / 'feature_correlation_heatmap.png',
        title='Feature correlation (main dataset, 13 features)')


if __name__ == '__main__':
    main()
