import pandas as pd
from utils.helpers import build_and_fit_all_candidates
from config import RAW_DATA_FILE, DATA_RAW_DIR, FEATURE_COLUMNS_EXTEND, RANDOM_SEEDS, TARGET_COLUMN, RESULTS_TABLES_DIR, SCALABILITY_NODE_COUNTS, NUM_NODES
from ml.preprocessing import load_and_split_trainval_ext
from sklearn.metrics import f1_score
from ml.evaluation import aggregate_metrics

def main():
    ood_nodes_scenarios = []
    for n in SCALABILITY_NODE_COUNTS:
        df = pd.read_csv(DATA_RAW_DIR / f'scalability_n{n}.csv')
        ood_nodes_scenarios.append((n,df[FEATURE_COLUMNS_EXTEND], df[TARGET_COLUMN]))

    records = []
    for seed in RANDOM_SEEDS:
        X_trainval_raw, X_test_raw, y_trainval, y_test = load_and_split_trainval_ext(feature_cols=FEATURE_COLUMNS_EXTEND, csv_path=RAW_DATA_FILE, seed=seed)

        fitted = build_and_fit_all_candidates(seed, X_trainval_raw, y_trainval)

        all_scenarios = [(NUM_NODES, X_test_raw, y_test)] + ood_nodes_scenarios

        for n_count, X_eval, y_eval in all_scenarios:
            for name, pipe in fitted.items():
                f1 = f1_score(y_eval, pipe.predict(X_eval), average='macro')
                records.append({'seed':seed, 'model':name, 'N':n_count, 'f1': f1})

    aggregate_metrics(records, ['model','N'], ['f1'],
                  out_path=RESULTS_TABLES_DIR / 'scalability_curve.csv')


if __name__  == '__main__':
    main()