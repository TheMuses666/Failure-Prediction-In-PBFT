import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_sample_weight

from ml.preprocessing import load_and_split_trainval
from ml.tuning import tune_model
from ml.evaluation import model_evaluation
from config import RANDOM_SEED, RANDOM_SEEDS, PARAM_GRIDS, RESULTS_MODELS_DIR, RAW_DATA_FILE, RESULTS_TABLES_DIR


def main():

    records = []
    cv_records = []
    best_params_records =[]
    per_class_records =[]

    for seed in RANDOM_SEEDS:
        print(f'==== Seed: {seed} ====')
        X_trainval, X_test, y_trainval, y_test, scaler = load_and_split_trainval(
            RAW_DATA_FILE, seed=seed
        )

        sample_weight = compute_sample_weight('balanced', y_trainval)

        candidates = [
            ('decision_tree',  DecisionTreeClassifier(random_state=seed, class_weight = 'balanced'),     PARAM_GRIDS['decision_tree']),
            ('random_forest',  RandomForestClassifier(random_state=seed, class_weight = 'balanced'),     PARAM_GRIDS['random_forest']),
            ('xgboost',        XGBClassifier(random_state=seed),              PARAM_GRIDS['xgboost']),
        ]

        for name, estimator, grid in candidates:
            print(f"Tuning {name}...")
            sw = sample_weight if name == 'xgboost' else None
            best_model, best_params, cv_results = tune_model(
                estimator, grid, X_trainval, y_trainval, seed=seed, sample_weight=sw
            )
            test_metrics = model_evaluation(best_model, X_test, y_test, model_name=name)
            print(f"  best_params: {best_params}")
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
                # Save the Model
                RESULTS_MODELS_DIR.mkdir(parents=True, exist_ok=True)
                joblib.dump(scaler, RESULTS_MODELS_DIR / "scaler_tuned.joblib")
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
                **best_params
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