import pandas as pd
from config import RAW_DATA_FILE, FEATURE_COLUMNS, RESULTS_TABLES_DIR, EXTENDED_DATA_FILE, AUXILIARY_COLUMNS, AUXILIARY_COUNTERS, RESULTS_FIGURES_DIR
from src.plotting.plots import plot_feature_distribution_by_group, plot_variance_comparison


def build_summary(csv_file, group_col, out_path, is_aux = False, figure_out_path = None, figure_title = None):
    df = pd.read_csv(csv_file)
    missing = set(FEATURE_COLUMNS) - set(df.columns)
    assert not missing, f'CSV Missing Features: {missing}'
    grouped = df.groupby(group_col)

    summary = pd.DataFrame({
        'n_rounds':       grouped.size(),
        'success_rate':   grouped['success'].mean(),
        'timeout_rate':   grouped['timeout'].mean(),
        'label_0_ratio':  grouped['label'].apply(lambda s: (s == 0).mean()),
        'label_1_ratio':  grouped['label'].apply(lambda s: (s == 1).mean()),
        'label_2_ratio':  grouped['label'].apply(lambda s: (s == 2).mean()),
    })

    for col in FEATURE_COLUMNS:
        summary[f'{col}_mean'] = grouped[col].mean()
        summary[f'{col}_std']  = grouped[col].std()

    if is_aux:
        for col in AUXILIARY_COUNTERS:
            summary[f'{col}_mean'] = grouped[col].mean()

    output_path = RESULTS_TABLES_DIR / out_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path)
    print(f'saved -> {output_path}')

    if figure_out_path is not None:
        plot_feature_distribution_by_group(
            df,
            FEATURE_COLUMNS,
            group_col,
            figure_out_path,
            figure_title
        )

    return summary

def main_corr(csv_file, feature_cols, out_path):
    df_main_for_corr = pd.read_csv(csv_file)
    corr = df_main_for_corr[feature_cols].corr()
    corr.to_csv(RESULTS_TABLES_DIR / out_path)
    print(f'CSV files saved --> {out_path}')

    
def main():
    # Normal dataset
    sum_main = build_summary(   
    RAW_DATA_FILE,
    'fault_type',
    'simulation_summary.csv',
    True, 
    RESULTS_FIGURES_DIR / 'feature_distribution_by_fault.png',
    'Feature distribution by fault type (main dataset)'
)

    # Extend dataset
    sum_ext = build_summary(    
    EXTENDED_DATA_FILE,
    'fault_subtype',
    'advanced_fault_summary.csv',
    True,
    RESULTS_FIGURES_DIR / 'feature_distribution_by_subtype.png',
    'Feature distribution by fault type (auxiliary dataset)',
)

    df_ext = pd.read_csv(EXTENDED_DATA_FILE)
    comparison = [  
    ('delay_gaussian', 'delay_lognormal', 'Delay: Phase 4 (Gaussian) vs Phase 4c (Lognormal)'),
    ('silent_all',     'silent_commit',   'Silent: Phase 4 (all) vs Phase 4c (commit-only)'),
]
    plot_variance_comparison(
        df_ext,
        FEATURE_COLUMNS,
        comparison,
        RESULTS_FIGURES_DIR / 'phase4c_variance_comparison.png',
        title='Phase 4 vs Phase 4c: feature variance comparison'
)

    main_corr(
        RAW_DATA_FILE,
        FEATURE_COLUMNS,
        'feature_correlation.csv'
    )

    print('=== Main ===')
    print(sum_main)

    print('\n=== Extended ===')
    print(sum_ext[['n_rounds', 'success_rate', 'timeout_rate']])

if __name__ == '__main__':
    main()