import torch
import numpy as np
import pandas as pd
from utils.helpers import build_and_fit_all_candidates
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import TensorDataset, DataLoader
from ml.preprocessing import split_by_sequence, build_windows
from ml.models.bilstm import BiLSTMMonitor, train_bilstm, evaluate_bilstm
from sklearn.preprocessing import MinMaxScaler  
from ml.evaluation import aggregate_metrics
from config import DATA_RAW_DIR, RANDOM_SEEDS, RESULTS_MODELS_DIR, RESULTS_TABLES_DIR, FEATURE_COLUMNS_EXTEND

def run_one_seed(seed, device, horizon, k):
    df = pd.read_csv(DATA_RAW_DIR / 'sequence_dataset.csv')
    tr, va, te = split_by_sequence(df, seed=seed)

    scaler = MinMaxScaler().fit(tr[FEATURE_COLUMNS_EXTEND])
    tr, va, te = tr.copy(), va.copy(), te.copy()
    for part in (tr, va, te):
        part[FEATURE_COLUMNS_EXTEND] = scaler.transform(part[FEATURE_COLUMNS_EXTEND])

    X_tr, y_tr, _ = build_windows(tr, k, FEATURE_COLUMNS_EXTEND, horizon)
    X_va, y_va, _ = build_windows(va, k, FEATURE_COLUMNS_EXTEND, horizon)
    X_te, y_te, _ = build_windows(te, k, FEATURE_COLUMNS_EXTEND, horizon)

    torch.manual_seed(seed)

    def make_loader(X, y, shuffle=False):
        ds = TensorDataset(torch.from_numpy(X), torch.from_numpy(y.astype(np.int64)))
        return DataLoader(ds, batch_size=32, shuffle=shuffle)

    train_loader = make_loader(X_tr, y_tr, shuffle=True)
    val_loader = make_loader(X_va, y_va)
    test_loader = make_loader(X_te, y_te)

    model = BiLSTMMonitor(input_dim=len(FEATURE_COLUMNS_EXTEND))

    class_weights = compute_class_weight('balanced', classes=np.unique(y_tr), y=y_tr)
    class_weights = torch.tensor(class_weights, dtype=torch.float)

    model = train_bilstm(model, train_loader, val_loader, device, class_weights=class_weights)

    records = []
    test_metrics = evaluate_bilstm(model, test_loader, device)
    records.append({'seed': seed, 'model': 'bilstm', 'k': k, 'test_set': 'test','horizon': horizon, **test_metrics})

    X_tr_last = X_tr[:, -1, :]
    X_te_last = X_te[:, -1, :]

    fitted = build_and_fit_all_candidates(seed, X_tr_last, y_tr)
    for name, pipe in fitted.items():
        pred = pipe.predict(X_te_last)
        per_class = f1_score(y_te, pred, average=None, labels=[0, 1, 2], zero_division=0)
        records.append({
            'seed': seed, 'model': name, 'k': k, 'test_set': 'test', 'horizon': horizon,
            'accuracy': accuracy_score(y_te, pred),
            'precision': precision_score(y_te, pred, average='macro', zero_division=0),
            'recall': recall_score(y_te, pred, average='macro', zero_division=0),
            'f1': f1_score(y_te, pred, average='macro', zero_division=0),
            'f1_normal': per_class[0],
            'f1_degraded': per_class[1],
            'f1_failure': per_class[2],
        })

    return records, model

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    all_records = []
    last_model = None
    for seed in RANDOM_SEEDS:
        for k in (5,10):
            for horizon in (0, 1):
                print(f'=== seed {seed} horizon {horizon} K {k} ===')
                records, last_model = run_one_seed(seed, device, horizon,k)
                all_records.extend(records)

    RESULTS_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(last_model.state_dict(), RESULTS_MODELS_DIR / 'bilstm.pt')

    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    summary = aggregate_metrics(
        all_records, ['model','k','horizon', 'test_set'], ['accuracy', 'precision', 'recall', 'f1', 'f1_normal', 'f1_degraded', 'f1_failure'],
        out_path=RESULTS_TABLES_DIR / 'model_metrics_bilstm.csv'
    )
    print(summary)

if __name__ == '__main__':
    main()