import pandas as pd
from config import RAW_DATA_FILE, FEATURE_COLUMNS, RESULTS_TABLES_DIR, EXTENDED_DATA_FILE, AUXILIARY_COLUMNS, AUXILIARY_COUNTERS


def build_summary(csv_file, group_col, out_path, is_aux = False):
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
    return summary

# Normal dataset
sum_main = build_summary(RAW_DATA_FILE,'fault_type','simulation_summary.csv',True)

# Extend dataset
sum_ext = build_summary(EXTENDED_DATA_FILE,'fault_subtype','advanced_fault_summary.csv',True)

print('=== Main ===')
print(sum_main)

print('\n=== Extended ===')
print(sum_ext[['n_rounds', 'success_rate', 'timeout_rate']])