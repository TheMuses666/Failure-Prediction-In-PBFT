import pandas as pd
from utils.helpers import build_and_fit_all_candidates
from config import RAW_DATA_FILE, DATA_RAW_DIR, FEATURE_COLUMNS_EXTEND, RANDOM_SEEDS, TARGET_COLUMN, RESULTS_TABLES_DIR
from ml.preprocessing import load_and_split_trainval_ext
from sklearn.metrics import f1_score
from ml.evaluation import aggregate_metrics

def main():
    df_f1 = pd.read_csv(DATA_RAW_DIR / 'robustness_f1.csv')
    df_f3 = pd.read_csv(DATA_RAW_DIR / 'robustness_f3.csv')

    records = []
    for seed in RANDOM_SEEDS:
        X_trainval_raw, X_test_raw, y_trainval, y_test = load_and_split_trainval_ext(feature_cols=FEATURE_COLUMNS_EXTEND,csv_path=RAW_DATA_FILE, seed=seed)

        fitted = build_and_fit_all_candidates(X_tv=X_trainval_raw,y_tv=y_trainval, seed=seed)
        for f_count, X_test_raw, y_test in [
            (1, df_f1[FEATURE_COLUMNS_EXTEND], df_f1[TARGET_COLUMN]),
            (2, X_test_raw, y_test),
            (3, df_f3[FEATURE_COLUMNS_EXTEND], df_f3[TARGET_COLUMN]),
        ]:
            for name, pipe in fitted.items():
                f1 = f1_score(y_test, pipe.predict(X_test_raw), average='macro')
                records.append({'seed': seed, 'model': name, 'f': f_count, 'f1': f1})
    
    aggregate_metrics(records, ['model','f'], ['f1'],
                  out_path=RESULTS_TABLES_DIR / 'robustness_curve.csv')


if __name__ == '__main__':
    main()