import pandas as pd
from sklearn.metrics import confusion_matrix

from config import RESULTS_TABLES_DIR, DATA_RAW_DIR,RANDOM_SEEDS, FEATURE_COLUMNS_EXTEND,FAULT_TYPES_TO_EVAL
from ml.preprocessing import load_and_split_trainval_ext
from utils.helpers import build_and_fit_all_candidates
from ml.evaluation import evaluate_per_fault_type, aggregate_metrics

def main():
    records = []
    cm_records = []
    for seed in RANDOM_SEEDS:
        X_trainval_raw, X_test_raw, y_trainval, y_test = load_and_split_trainval_ext(csv_path=(DATA_RAW_DIR / 'consensus_data.csv'), seed=seed,feature_cols=FEATURE_COLUMNS_EXTEND)
        test_fault_types = pd.read_csv(DATA_RAW_DIR / 'consensus_data.csv').loc[X_test_raw.index, 'fault_type']
        fitted = build_and_fit_all_candidates(seed,X_trainval_raw,y_trainval)
        for name,pipe in fitted.items():
            ft_records = evaluate_per_fault_type(pipe, X_test_raw,y_test,test_fault_types,FAULT_TYPES_TO_EVAL, model_name=name)
            for r in ft_records:
                r['seed'] = seed
            records.extend(ft_records)

            cm = confusion_matrix(y_test, pipe.predict(X_test_raw), labels=[0,1,2])

            cm_records.append((name, cm))

    aggregate_metrics(records, ['model', 'fault_type'],
    ['accuracy', 'detection_rate', 'failure_recall'],
    out_path=RESULTS_TABLES_DIR / 'per_fault_type.csv',
    )


if __name__ == '__main__':
    main()