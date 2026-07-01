import pandas as pd

from utils.helpers import train_default_pipeline_multiseed
from ml.preprocessing import load_and_split_trainval_ext
from config import RESULTS_TABLES_DIR, FEATURE_COLUMNS

def main():

    records, per_class_records = train_default_pipeline_multiseed(feature_cols=FEATURE_COLUMNS,split_fuc=load_and_split_trainval_ext)

    df = pd.DataFrame(records)
    summary = df.groupby('model').agg(['mean', 'std'])
    summary.columns = ['_'.join(c) for c in summary.columns]
    summary = summary.reset_index().drop(columns=['seed_mean', 'seed_std'])

    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(RESULTS_TABLES_DIR / 'model_metrics_default_multiseed.csv', index=False)
    pd.DataFrame(per_class_records).to_csv(
        RESULTS_TABLES_DIR / 'per_class_report_default.csv', index=False
    )
    print(summary)


if __name__ == '__main__':
    main()