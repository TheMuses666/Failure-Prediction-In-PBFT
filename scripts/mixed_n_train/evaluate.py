import pandas as pd
from sklearn.metrics import f1_score

from config import (RAW_DATA_FILE, DATA_RAW_DIR, FEATURE_COLUMNS_EXTEND, SCALABILITY_NODE_COUNTS,
                     RANDOM_SEEDS, TARGET_COLUMN, RESULTS_TABLES_DIR, NUM_NODES)
from ml.preprocessing import load_and_split_trainval_ext
from utils.helpers import build_and_fit_all_candidates
from ml.evaluation import aggregate_metrics
from baseline.static_detection import (
    fit_threshold, threshold_detector,
    fit_count_threshold, count_based_detector,
    rule_based_detector, BaselineWrapper,
)

def main():
    mixed_pool = pd.concat([
        pd.read_csv(DATA_RAW_DIR / f'mixed_n_train_n{node}.csv') for node in SCALABILITY_NODE_COUNTS
    ], ignore_index=True)
    X = mixed_pool[FEATURE_COLUMNS_EXTEND]
    y = mixed_pool[TARGET_COLUMN]

    odd_scenarios = []
    
    records = []
    for n in SCALABILITY_NODE_COUNTS:
        df = pd.read_csv(DATA_RAW_DIR / f'scalability_n{n}.csv')
        odd_scenarios.append((n, df[FEATURE_COLUMNS_EXTEND], df[TARGET_COLUMN]))

    for seed in RANDOM_SEEDS:
        X_train_n7, X_test_n7, y_train_n7, y_test_n7 = load_and_split_trainval_ext(feature_cols=FEATURE_COLUMNS_EXTEND, csv_path=RAW_DATA_FILE, seed=seed)

        arms = {
            'baseline': (X_train_n7, y_train_n7),
            'mixed':(
                pd.concat([X_train_n7, X], ignore_index=True),
                pd.concat([y_train_n7, y], ignore_index=True)
            )
        }

        all_scenarios = [(NUM_NODES, X_test_n7, y_test_n7)] + odd_scenarios

        for arm_name, (X_train, y_train) in arms.items():
            fitted = build_and_fit_all_candidates(seed, X_train, y_train)
            threshold = fit_threshold(X_train, y_train)
            count_threshold = fit_count_threshold(X_train, y_train)

            static_models = {           
                'threshold_based': BaselineWrapper(lambda X, t=threshold: threshold_detector(X, t)),
                'count_based': BaselineWrapper(lambda X, t=count_threshold: count_based_detector(X, t)),
                'rule_based': BaselineWrapper(rule_based_detector),
            }

            for n_nodes, X_test, y_test in all_scenarios:
                   for model, pipe in {**fitted,**static_models}.items():
                    y_pred = pipe.predict(X_test)
                    f1 = f1_score(y_test, y_pred, average='macro')
                    records.append({
                        'seed': seed,
                        'arms': arm_name,
                        'N': n_nodes,
                        'model': model,
                         'f1': f1
                    })
    
    aggregate_metrics(records,['arms','model','N'],['f1'], RESULTS_TABLES_DIR / 'mixed_n_curve.csv')

if __name__ == '__main__':
    main()