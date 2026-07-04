from config import RESULTS_TABLES_DIR, FEATURE_COLUMNS_EXTEND  
from utils.helpers import train_default_pipeline_multiseed
from ml.preprocessing import load_and_split_trainval_ext
from ml.evaluation import aggregate_metrics

def main():
    records, per_class_records = train_default_pipeline_multiseed(
        feature_cols=FEATURE_COLUMNS_EXTEND, split_fuc=load_and_split_trainval_ext)

    summary = aggregate_metrics(
        records, ['model'], ['accuracy', 'precision', 'recall', 'f1'],
        out_path=RESULTS_TABLES_DIR / 'model_metrics_default_13.csv')  
    
if __name__ == '__main__':
    main()