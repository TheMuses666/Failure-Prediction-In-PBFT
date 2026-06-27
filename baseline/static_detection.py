import numpy as np
from config import (LABEL_NORMAL, LABEL_DEGRADED, LABEL_FAILURE, FEATURE_COLUMNS,
                    QUORUM,
                    NORMAL_LATENCY_THRESHOLD_MAX,
                    DEGRADED_LATENCY_THRESHOLD_MAX,
                    DROP_RATE_WARNING,
                    MESSAGE_CONSISTENCY_WARNING          
                )
import pandas as pd


def fit_threshold(X_train_raw: pd.DataFrame, y_train: pd.Series) -> dict:
    normal_agreement = X_train_raw.loc[y_train == LABEL_NORMAL,'consensus_agreement_time' ]
    mean = normal_agreement.mean()
    std = normal_agreement.std()
    return{
        'mean': mean,
        'std':std,
        'degraded': mean + std*2,
        'failure': mean + 3*std
    }

def threshold_detector(X_test_raw: pd.DataFrame, thresholds: dict) -> np.ndarray:
    preds = []
    for _, row in X_test_raw.iterrows():
        if row['timeout_frequency'] > 0:
            preds.append(LABEL_FAILURE)

        elif row['consensus_agreement_time'] > thresholds['failure']:
            preds.append(LABEL_FAILURE)

        elif row['consensus_agreement_time'] > thresholds['degraded']:
            preds.append(LABEL_DEGRADED)
        
        else:
            preds.append(LABEL_NORMAL)

    return np.array(preds)

def rule_based_detector(X_test_raw: pd.DataFrame) -> np.ndarray:
    preds = []
    for _, row in X_test_raw.iterrows():
        if ((row['timeout_frequency'] > 0) 
            or (row['voting_consistency'] < QUORUM)
            ):
            preds.append(LABEL_FAILURE)
        elif ((row['message_latency'] >= NORMAL_LATENCY_THRESHOLD_MAX and row['consensus_agreement_time'] < DEGRADED_LATENCY_THRESHOLD_MAX)
              or (row['message_drop_rate'] >= DROP_RATE_WARNING)
              or (row['message_consistency'] < MESSAGE_CONSISTENCY_WARNING)
              ):
            preds.append(LABEL_DEGRADED)
        else:
            preds.append(LABEL_NORMAL)

    return np.array(preds)

# Smoke Test
if __name__ == '__main__':
    X_train_fake = pd.DataFrame({
        "consensus_agreement_time": [30, 35, 28, 200, 180],
        "timeout_frequency":        [0,  0,  0,  1,   1],
    })
    y_train_fake = pd.Series([0, 0, 0, 2, 2])

    threshold = fit_threshold(X_train_fake,y_train_fake)
    print(f'threshold: {threshold}')

    X_test_fake = pd.DataFrame({
        "consensus_agreement_time": [25, 60, 500, 40],
        "timeout_frequency":        [0,  0,  0,   1],
    })
    expected = ["normal", "degraded or failure", "failure", "failure (timeout)"]

    preds = threshold_detector(X_test_fake, threshold)
    for i, (p, e) in enumerate(zip(preds, expected)):
        print(f"row {i}: pred={p}  expected={e}")
    X_test_rule = pd.DataFrame({
        "message_latency":      [20,  60,  20,  20,  20],   # 第1行 >= 50 → degraded
        "timeout_frequency":    [0,   0,   0,   0,   0],
        "voting_consistency":   [1.0, 1.0, 0.5, 1.0, 1.0],  # 第2行 < QUORUM → failure
        "message_drop_rate":    [0,   0,   0,   0.5, 0],    # 第3行 >= 0.3 → degraded
        "message_consistency":  [1.0, 1.0, 1.0, 1.0, 0.5],  # 第4行 < 0.8 → degraded
        "consensus_agreement_time": [30, 60, 30, 30, 30],
    })
    preds_rule = rule_based_detector(X_test_rule)
    print("rule preds:", preds_rule, "expected: [0, 1, 2, 1, 1]")