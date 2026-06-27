from baseline.static_detection import threshold_detector,fit_threshold, rule_based_detector
import pandas as pd
from ml.preprocessing import load_and_split
from ml.evaluation import model_evaluation
from config import RAW_DATA_FILE, METRICS_FILE


class BaselineWrapper:
    def __init__(self,baseline_fn):
        self.baseline_fn = baseline_fn
    def predict(self, X):
        return self.baseline_fn(X)
    

def main():
    _, _, _, X_train_raw, X_test_raw, y_train, _, y_test, _ = load_and_split(RAW_DATA_FILE)

    threshold = fit_threshold(X_train_raw, y_train)
    print(f'threshold fitted: {threshold}')

    threshold_model = BaselineWrapper(lambda X: threshold_detector(X, threshold))
    rule_based_model = BaselineWrapper(rule_based_detector)

    result = []

    for model_name, model in [
        ('threshold_based',threshold_model),
        ('rule_based',rule_based_model)
    ]:
        m = model_evaluation(model, X_test_raw, y_test, model_name=model_name)
        m['split'] = 'test'
        result.append(m)
        print(f'{model_name}: acc={m['accuracy']:.4f} f1={m['f1']:.4f}')

    new_df = pd.DataFrame(result)
    existing = pd.read_csv(METRICS_FILE)
    existing = existing[~existing['model'].isin(['threshold_based', 'rule_based'])]
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.to_csv(METRICS_FILE, index=False)
    print(f"\nAppended to {METRICS_FILE}")
    print(combined)


if __name__ == '__main__':
    main()