from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
import time
import numpy as np
import pandas as pd

def model_evaluation(model, X_test, y_test, model_name=''):
    # Model Response Time
    start = time.perf_counter()
    y_pred = model.predict(X_test)
    elapsed = time.perf_counter() - start

    # Evaluation Metric
    acc = accuracy_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred, average="macro")
    precision = precision_score(y_test, y_pred, average="macro")
    f1 = f1_score(y_test, y_pred, average="macro")

    cm = confusion_matrix(y_test, y_pred)

    model_response_time = (elapsed / len(X_test)) * 1000

    return  {
        'model': model_name,
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion matrix': cm,
        'model_response_time_ms': model_response_time
    }


def evaluate_per_fault_type(
    model, X_test, y_test, test_fault_types, 
    fault_types_to_eval, model_name='',
):
    y_pred = model.predict(X_test)
    y_true = y_test.to_numpy() if hasattr(y_test, 'to_numpy') else np.asarray(y_test)
    ft_arr = test_fault_types.to_numpy() if hasattr(test_fault_types, 'to_numpy') else np.asarray(test_fault_types)
    
    records = []
    for ft in fault_types_to_eval:
        mask = ft_arr == ft
        if mask.sum() == 0:
            continue
        
        y_true_ft = y_true[mask]
        y_pred_ft = y_pred[mask]
        
        accuracy       = (y_true_ft == y_pred_ft).mean()
        detection_rate = (y_pred_ft != 0).mean()
        
        n_failure_true = (y_true_ft == 2).sum()
        if n_failure_true > 0:
            failure_recall = ((y_pred_ft == 2) & (y_true_ft == 2)).sum() / n_failure_true
        else:
            failure_recall = float('nan')
        
        records.append({
            'model': model_name,
            'fault_type': ft,
            'accuracy': float(accuracy),
            'detection_rate': float(detection_rate),
            'failure_recall': float(failure_recall),
            'support': int(mask.sum()),
        })
    return records


def aggregate_metrics(records, groupby_cols, value_cols, out_path=None, print_result=True):

    df = pd.DataFrame(records) if isinstance(records, list) else records
    
    summary = df.groupby(groupby_cols)[value_cols].agg(['mean', 'std'])
    summary.columns = [f'{col}_{stat}' for col, stat in summary.columns]
    summary = summary.reset_index()
    
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(out_path, index=False)
    
    if print_result:
        print(summary.to_string(index=False))
    
    return summary