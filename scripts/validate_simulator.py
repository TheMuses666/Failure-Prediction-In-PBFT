import pandas as pd
from pathlib import Path
from config import RAW_DATA_FILE, FEATURE_COLUMNS, RESULTS_TABLES_DIR

df = pd.read_csv(RAW_DATA_FILE)

missing = set(FEATURE_COLUMNS) - set(df.columns)
assert not missing, f'CSV Missing Features: {missing}'

grouped = df.groupby('fault_type')

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

out_path = Path(RESULTS_TABLES_DIR / 'simulation_summary.csv')
out_path.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(out_path)
print(summary)
print(f'saved -> {out_path}')
