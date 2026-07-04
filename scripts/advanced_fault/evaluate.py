import pandas as pd
from config import (RAW_DATA_FILE, EXTENDED_DATA_FILE, FEATURE_COLUMNS_EXTEND,
                    RANDOM_SEEDS, TARGET_COLUMN, RESULTS_TABLES_DIR)
from ml.preprocessing import load_and_split_trainval_ext
from utils.helpers import build_and_fit_all_candidates
from ml.evaluation import evaluate_per_fault_type, aggregate_metrics
from sklearn.metrics import f1_score, recall_score, confusion_matrix
import argparse
from sklearn.model_selection import train_test_split

def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train-on-extended', action='store_true')
    args = parser.parse_args()
    return args

def main():

    args = arg_parser()
    suffix = '_trainext' if args.train_on_extended else ''

    df_ext = pd.read_csv(EXTENDED_DATA_FILE)    
    f1_records = []
    subtype_records = []
    cm_sum = {}

    for seed in RANDOM_SEEDS:
        ext_tv, ext_test = train_test_split(
        df_ext, test_size=0.2,
        stratify=df_ext['fault_subtype'], random_state=seed)
        X_ext_test = ext_test[FEATURE_COLUMNS_EXTEND]
        y_ext_test = ext_test[TARGET_COLUMN]

        
        X_tv, X_test, y_tv, y_test = load_and_split_trainval_ext(
        feature_cols=FEATURE_COLUMNS_EXTEND, csv_path=RAW_DATA_FILE, seed=seed)
        if args.train_on_extended:
            X_tv = pd.concat([X_tv, ext_tv[FEATURE_COLUMNS_EXTEND]])
            y_tv = pd.concat([y_tv, ext_tv[TARGET_COLUMN]])
        fitted = build_and_fit_all_candidates(seed, X_tv, y_tv)

        for name, pipe in fitted.items():
            for dist, X_eval, y_eval in [('in_dist', X_test, y_test),('ood_extended',X_ext_test, y_ext_test)]:
                y_pred = pipe.predict(X_eval)
                f1_records.append({
                    'seed':seed, 'model': name, 'distribution': dist,
                    'f1': f1_score(y_eval, y_pred, average='macro'),
                    'recall':recall_score(y_eval, y_pred, average='macro')
                })
                cm = confusion_matrix(y_eval, y_pred, labels=[0, 1, 2])
                cm_sum[(name,dist)] = cm_sum.get((name,dist), 0) + cm
    
            subtypes = sorted(df_ext['fault_subtype'].unique())
            ft_records = evaluate_per_fault_type(
                pipe, X_ext_test, y_ext_test, ext_test['fault_subtype'], subtypes, model_name=name
            )
            for r in ft_records:
                r['seed'] = seed
            subtype_records.extend(ft_records)

            
    cm_rows = []
    for (name,dist), cm in cm_sum.items():
        for i in [0,1,2]:
            for j in [0,1,2]:
                cm_rows.append({'model':name, 'distribution':dist,'true_label':i,'pred_label':j, 'count': int(cm[i,j])})
    pd.DataFrame(cm_rows).to_csv(RESULTS_TABLES_DIR / f'ood_confusion{suffix}.csv', index=False)

    
    aggregate_metrics(f1_records, ['model', 'distribution'], ['f1', 'recall'],
                      out_path=RESULTS_TABLES_DIR / f'ood_f1{suffix}.csv')
    aggregate_metrics(subtype_records, ['model', 'fault_type'],
                      ['accuracy', 'detection_rate', 'failure_recall'],
                      out_path=RESULTS_TABLES_DIR / f'ood_per_subtype{suffix}.csv')

if __name__ == '__main__':
    main()

