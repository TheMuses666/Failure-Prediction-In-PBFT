import pandas as pd
from ml.preprocessing import load_and_split
from ml.models.decision_tree import train_decision_tree
from ml.models.random_forest import train_random_forest
from ml.models.xgboost_model import train_xgboost
from ml.evaluation import model_evaluation
from config import METRICS_FILE, RESULTS_FIGURES_DIR, RAW_DATA_FILE, RESULTS_MODELS_DIR
import joblib

def main():
    X_train, X_val, X_test,_,_, y_train, y_val, y_test, scaler = load_and_split(RAW_DATA_FILE)

    result = []
    for model_name, train_fc in [
        ('decision_tree',train_decision_tree),
        ('random_forest', train_random_forest),
        ('xgboost', train_xgboost)
    ]:
        print(f'Training {model_name}')
        model = train_fc(X_train, y_train)
        test_metrics = model_evaluation(model, X_test, y_test, model_name=model_name)
        test_metrics['split'] = 'test'
        val_metrics = model_evaluation(model, X_val, y_val, model_name=model_name)
        val_metrics['split'] = 'val'
        result.append(test_metrics)
        result.append(val_metrics)
        RESULTS_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"  test_acc={test_metrics['accuracy']:.4f}  test_f1={test_metrics['f1']:.4f}\n")
        joblib.dump(model, RESULTS_MODELS_DIR / f"{model_name}.joblib")
        
    joblib.dump(scaler, RESULTS_MODELS_DIR / "scaler.joblib")
    df = pd.DataFrame(result)
    RESULTS_FIGURES_DIR.mkdir(parents = True, exist_ok=True)
    df.to_csv(METRICS_FILE, index=False)
    print(f"\nSaved to {METRICS_FILE}")
    print(df)

if __name__ == '__main__':
    main()
