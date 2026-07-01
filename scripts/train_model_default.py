import pandas as pd

from utils.helpers import train_default_pipeline_multiseed
from ml.preprocessing import load_and_split_trainval_ext
from ml.evaluation import aggregate_metrics 
from config import RESULTS_TABLES_DIR, FEATURE_COLUMNS

def main():

    records, per_class_records = train_default_pipeline_multiseed(feature_cols=FEATURE_COLUMNS,split_fuc=load_and_split_trainval_ext)

    summary = aggregate_metrics(
    records, ['model'], ['accuracy', 'precision', 'recall', 'f1'],
    out_path=RESULTS_TABLES_DIR / 'model_metrics_default_multiseed.csv'
    )
    print(summary)


if __name__ == '__main__':
    main()