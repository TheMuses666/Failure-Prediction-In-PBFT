from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
import time
import numpy as np

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
