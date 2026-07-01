from baseline.static_detection import threshold_detector,fit_threshold, rule_based_detector
import pandas as pd
from ml.preprocessing import load_and_split_trainval_raw
from ml.evaluation import model_evaluation
from sklearn.metrics import classification_report
from config import RAW_DATA_FILE, RANDOM_SEEDS, RESULTS_TABLES_DIR


class BaselineWrapper:
    def __init__(self,baseline_fn):
        self.baseline_fn = baseline_fn
    def predict(self, X):
        return self.baseline_fn(X)
    

def main():
    result = []
    per_class_record = []

    for seed in RANDOM_SEEDS:
        X_trainval_raw, X_test_raw, y_trainval, y_test = load_and_split_trainval_raw(
        RAW_DATA_FILE, seed=seed
    )

        threshold = fit_threshold(X_trainval_raw, y_trainval)
        print(f'threshold fitted: {threshold}')

        threshold_model = BaselineWrapper(lambda X, t=threshold: threshold_detector(X, t))
        rule_based_model = BaselineWrapper(rule_based_detector)

    

        for model_name, model in [
            ('threshold_based',threshold_model),
            ('rule_based',rule_based_model)
        ]:
            m = model_evaluation(model, X_test_raw, y_test, model_name=model_name)
            m['split'] = 'test'
            result.append({
                'seed':seed,
                'model': model_name,
                **m
            })
            print(f'{model_name}: acc={m['accuracy']:.4f} f1={m['f1']:.4f}')

            # per_class
            y_pred = model.predict(X_test_raw)
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            for class_label, score in report.items():
                if isinstance(score, dict):
                    per_class_record.append({
                        'seed': seed,
                        'model': model_name,
                        'class':class_label,
                        'precision': score['precision'],
                        'recall': score['recall'],
                        'f1': score['f1-score'],     
                        'support': score['support'],
                    })

    new_df = pd.DataFrame(result)
    # Calculate Mean and STD
    summary = new_df.groupby('model')[['accuracy','precision','recall','f1']].agg(['mean','std'])
    summary.columns = ['_'.join(col) for col in summary.columns]
    summary = summary.reset_index()

    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(RESULTS_TABLES_DIR / "baseline_metrics_multiseed.csv", index=False)
    pd.DataFrame(per_class_record).to_csv(
        RESULTS_TABLES_DIR / "baseline_per_class_multiseed.csv", index=False
    )

    print("\n=== Baseline Summary ===")
    print(summary)

if __name__ == '__main__':
    main()