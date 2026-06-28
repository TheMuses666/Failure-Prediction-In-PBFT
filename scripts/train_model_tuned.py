import joblib
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler

from ml.preprocessing import load_and_split_trainval_raw
from ml.tuning import tune_model
from ml.evaluation import model_evaluation
from ml.models.logistic_regression import build_logistic_regression
from ml.models.random_forest import build_random_forest
from ml.models.decision_tree import build_decision_tree
from ml.models.xgboost_model import build_xgboost
from config import RANDOM_SEED, RANDOM_SEEDS, PARAM_GRIDS, RESULTS_MODELS_DIR, RAW_DATA_FILE, RESULTS_TABLES_DIR

def make_pipeline(estimator):
    return Pipeline([
        ('scaler', MinMaxScaler()),
        ('clf', estimator),
    ])


def prefix_grid(grid):
    return {f'clf__{k}': v for k, v in grid.items()}


def strip_prefix(params):
    return {k.removeprefix('clf__'): v for k, v in params.items()}


def main():

    records = []
    cv_records = []
    best_params_records =[]
    per_class_records =[]

    for seed in RANDOM_SEEDS:
        print(f'==== Seed: {seed} ====')
        X_trainval, X_test, y_trainval, y_test = load_and_split_trainval_raw(
            RAW_DATA_FILE, seed=seed
        )

        sample_weight = compute_sample_weight('balanced', y_trainval)

        candidates = [
            ('decision_tree',  build_decision_tree(seed),     PARAM_GRIDS['decision_tree']),
            ('random_forest',  build_random_forest(seed),     PARAM_GRIDS['random_forest']),
            ('xgboost',        build_xgboost(seed),              PARAM_GRIDS['xgboost']),
            ('logistic_regression', build_logistic_regression(seed), PARAM_GRIDS['logistic_regression']),
        ]

        for name, estimator, grid in candidates:
            print(f"Tuning {name}...")
            pipe = make_pipeline(estimator)
            prefixed_grid = prefix_grid(grid)
            sw = sample_weight if name == 'xgboost' else None

            best_model, best_params, cv_results = tune_model(
                pipe, prefixed_grid, X_trainval, y_trainval, seed=seed, sample_weight=sw, sample_weight_param='clf__sample_weight'
            )
            test_metrics = model_evaluation(best_model, X_test, y_test, model_name=name)
            clean_params = strip_prefix(best_params)
            print(f"  best_params: {clean_params}")
            print(f"  test_f1: {test_metrics['f1']:.4f}")

            records.append({
                'seed': seed,
                'model': name,
                'accuracy': test_metrics['accuracy'],
                'precision': test_metrics['precision'],
                'recall': test_metrics['recall'],
                'f1': test_metrics['f1']
            })
        
            if seed == RANDOM_SEED:
                # Save the Pipeline (scaler bundled inside)
                RESULTS_MODELS_DIR.mkdir(parents=True, exist_ok=True)
                joblib.dump(best_model, RESULTS_MODELS_DIR / f"{name}_tuned.joblib")

                # Save the Model CV Records
                df_cv = pd.DataFrame(cv_results)
                df_cv['model'] = name
                cv_records.append(df_cv)

            y_pred = best_model.predict(X_test)
            report = classification_report(y_test, y_pred, output_dict=True)
            for class_label, score in report.items():
                if isinstance(score, dict):
                    per_class_records.append({
                        'model': name,
                        'class': class_label,
                        'seed': seed,
                        'precision': score['precision'],
                        'recall': score['recall'],
                        'f1': score['f1-score'],
                        'support': score['support'],
                    })
            
                

            # Save the Best Params of Model
            best_params_records.append({
                'model': name,
                'seed':seed,
                **clean_params
            })



    df = pd.DataFrame(records)
    summary = df.groupby('model').agg(['mean','std'])

    summary.columns = ['_'.join(col) for col in summary.columns]
    summary = summary.reset_index()

    summary = summary.drop(columns=['seed_mean','seed_std'])

    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(RESULTS_TABLES_DIR / "model_metrics_tuned.csv", index=False)
    pd.concat(cv_records, ignore_index=True).to_csv(
        RESULTS_TABLES_DIR / "cv_results.csv", index=False
    )
    pd.DataFrame(best_params_records).to_csv(
        RESULTS_TABLES_DIR / "best_hyperparameters.csv", index=False
    )
    pd.DataFrame(per_class_records).to_csv(
        RESULTS_TABLES_DIR / "per_class_report.csv", index=False
    )
    print("\n=== Summary ===")
    print(summary)

if __name__ == '__main__':
    main()