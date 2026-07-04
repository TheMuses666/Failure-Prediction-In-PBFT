import pandas as pd
from ml.preprocessing import load_and_split_trainval_ext
from utils.helpers import build_and_fit_all_candidates
from ml.evaluation import evaluate_per_fault_type, aggregate_metrics
from config import (DATA_RAW_DIR, RAW_DATA_FILE, FORGERY_INTENSITIES,
                    RESULTS_TABLES_DIR, RANDOM_SEEDS, FEATURE_COLUMNS_EXTEND, TARGET_COLUMN)
from baseline.static_detection import fit_threshold, BaselineWrapper, threshold_detector,rule_based_detector, fit_count_threshold, count_based_detector

def detection_analysis():
    dfs = [pd.read_csv(DATA_RAW_DIR / f'forgery_i{int(it*100)}.csv') for it in FORGERY_INTENSITIES]
    df_forgery = pd.concat(dfs, ignore_index=True)
    subtypes = sorted(df_forgery['fault_subtype'].unique())

    records = []
    for seed in RANDOM_SEEDS:
        X_tv, X_test, y_tv, y_test = load_and_split_trainval_ext(
            feature_cols=FEATURE_COLUMNS_EXTEND, csv_path=RAW_DATA_FILE, seed=seed)
        fitted = build_and_fit_all_candidates(seed, X_tv, y_tv)

        threshold = fit_threshold(X_tv, y_tv)
        count_thr = fit_count_threshold(X_tv,y_tv)
        static_models = {
            'threshold_based': BaselineWrapper(lambda X, t=threshold: threshold_detector(X, t)),
            'rule_based': BaselineWrapper(rule_based_detector),
            'count_based': BaselineWrapper(lambda X, t=count_thr: count_based_detector(X,t))
        }

        for name, pipe in {**fitted,**static_models}.items():
            ft_records = evaluate_per_fault_type(
                pipe,
                df_forgery[FEATURE_COLUMNS_EXTEND],
                df_forgery[TARGET_COLUMN],
                df_forgery['fault_subtype'],
                subtypes,
                model_name=name,
            )

            for r in ft_records:
                r['seed'] = seed
            records.extend(ft_records)

    aggregate_metrics(records, ['model', 'fault_type'],
                  ['accuracy', 'detection_rate', 'failure_recall'],
                  out_path=RESULTS_TABLES_DIR / 'auth_ablation_detection.csv')

def main():
    df_main = pd.read_csv(RAW_DATA_FILE)
    normal = df_main[df_main['fault_type'] == 'normal'] 

    dataset = [('normal',0.0, normal)]

    for intensity in FORGERY_INTENSITIES:
        df = pd.read_csv(DATA_RAW_DIR / f'forgery_i{int(intensity*100)}.csv')
        dataset.append((f'forgery_i{intensity}',intensity,df))

    records = []

    for name, it, df in dataset:
        records.append({
            'scenario':name,
            'intensity': it,
            'n_round':len(df),
            'forgery_mean': df['forged'].mean(),
            'label_0': int((df['label'] == 0).sum()),
            'label_1': int((df['label'] == 1).sum()),
            'label_2': int((df['label'] == 2).sum()),
            'agreement_time_mean': df['consensus_agreement_time'].mean(),
            'agreement_time_std': df['consensus_agreement_time'].std(),
            'phase_completion_mean': df['phase_completion_time'].mean(),
            'voting_consistency_mean': df['voting_consistency'].mean(),
        })

    output_path = RESULTS_TABLES_DIR / 'auth_ablation.csv'
    pd.DataFrame(records).to_csv(output_path, index=False)
    print(pd.DataFrame(records).round(3).to_string(index=False))

if __name__ == '__main__':
    detection_analysis()
    main()