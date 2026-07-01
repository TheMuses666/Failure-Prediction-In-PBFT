import pandas as pd

from ml.preprocessing import load_and_split_trainval_ext
from utils.helpers import train_default_pipeline_multiseed
from config import RANDOM_SEEDS, RAW_DATA_FILE, RESULTS_TABLES_DIR, FEATURE_COLUMNS, FEATURE_COLUMNS_EXTEND

def main():
    all_records = []
    for feature_set_name, cols in [('11_features', FEATURE_COLUMNS),('12_quorum_only',  FEATURE_COLUMNS + ['quorum_margin']),
    ('12_prepare_only', FEATURE_COLUMNS + ['prepare_count_std']),
    ('13_features', FEATURE_COLUMNS_EXTEND),]:
        
        records, _ = train_default_pipeline_multiseed(feature_cols=cols,split_fuc=load_and_split_trainval_ext)
        for r in records:
            r['feature_set'] = feature_set_name
        
        all_records.extend(records)

    df = pd.DataFrame(all_records)
    
    summary = df.groupby(['model', 'feature_set'])[['f1', 'accuracy']].agg(['mean', 'std'])
    print('--- after groupby ---')
    print(summary)
    print(summary.columns.tolist())


    pivoted = summary['f1'].unstack('feature_set')
    pivoted.columns = [f'f1_{metric}_{fs}' for metric, fs in pivoted.columns]
    # Both
    pivoted['delta_both'] = pivoted['f1_mean_13_features'] - pivoted['f1_mean_11_features']
    # Quprum Margin
    pivoted['delta_quorum'] = pivoted['f1_mean_12_quorum_only'] - pivoted['f1_mean_11_features']
    # Prepare_count_std
    pivoted['delta_prepare'] = pivoted['f1_mean_12_prepare_only'] - pivoted['f1_mean_11_features']

    pivoted = pivoted.reset_index().sort_values('delta_both', ascending=False)
    print('--- after unstack ---')
    print(pivoted)
    print(pivoted.columns.tolist())


    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    pivoted.to_csv(RESULTS_TABLES_DIR / 'ablation_feature_set.csv', index=False)
    print(pivoted.to_string(index=False))



    


if __name__ == '__main__':
    main()