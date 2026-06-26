import pandas as pd
from ml.preprocessing import load_and_split
from ml.models.decision_tree import train_decision_tree
from ml.models.random_forest import train_random_forest
from ml.models.xgboost_model import train_xgboost
from ml.evaluation import model_evaluation
from config import METRICS_FILE, RESULTS_FIGURES_DIR, RAW_DATA_FILE

def main():
    X_train, X_val, X_test, y_train, y_val, y_test = load_and_split(RAW_DATA_FILE)

    result = []
    for model_name, train_fc in [
        ('decision tree',train_decision_tree),
        ('random forest', train_random_forest),
        ('xgboost', train_xgboost)
    ]:
        print(f'Training {model_name}')
        model = train_fc(X_train, y_train)
        metrics = model_evaluation(model, X_test, y_test, model_name=model_name)
        result.append(metrics)
        print(f"  acc={metrics['accuracy']:.4f}  f1={metrics['f1']:.4f}")

    
    df = pd.DataFrame(result)
    RESULTS_FIGURES_DIR.mkdir(parents = True, exist_ok=True)
    df.to_csv(METRICS_FILE, index=False)
    print(f"\nSaved to {METRICS_FILE}")
    print(df)

if __name__ == '__main__':
    main()
