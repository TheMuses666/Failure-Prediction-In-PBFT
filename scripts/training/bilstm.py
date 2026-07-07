import torch
import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import TensorDataset, DataLoader
from ml.preprocessing import split_by_sequence, build_windows
from ml.models.bilstm import BiLSTMMonitor, train_bilstm, evaluate_bilstm
from sklearn.preprocessing import MinMaxScaler  
from ml.evaluation import aggregate_metrics
from config import DATA_RAW_DIR, RANDOM_SEEDS, RESULTS_MODELS_DIR, RESULTS_TABLES_DIR, FEATURE_COLUMNS_EXTEND

K = 5

def run_one_seed(seed, device):
    df = pd.read_csv(DATA_RAW_DIR / 'sequence_dataset.csv')
    tr, va, te = split_by_sequence(df, seed=seed)

    scaler = MinMaxScaler().fit(tr[FEATURE_COLUMNS_EXTEND])
    tr, va, te = tr.copy(), va.copy(), te.copy()
    for part in (tr, va, te):
        part[FEATURE_COLUMNS_EXTEND] = scaler.transform(part[FEATURE_COLUMNS_EXTEND])

    X_tr, y_tr, _ = build_windows(tr, K, FEATURE_COLUMNS_EXTEND)
    X_va, y_va, _ = build_windows(va, K, FEATURE_COLUMNS_EXTEND)
    X_te, y_te, _ = build_windows(te, K, FEATURE_COLUMNS_EXTEND)

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
    records.append({'seed': seed, 'model': 'bilstm', 'k': K, 'test_set': 'test', **test_metrics})

    return records, model

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    all_records = []
    last_model = None
    for seed in RANDOM_SEEDS:
        print(f'=== seed {seed} ===')
        records, last_model = run_one_seed(seed, device)
        all_records.extend(records)

    RESULTS_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(last_model.state_dict(), RESULTS_MODELS_DIR / 'bilstm.pt')

    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    summary = aggregate_metrics(
        all_records, ['model', 'test_set'], ['accuracy', 'precision', 'recall', 'f1'],
        out_path=RESULTS_TABLES_DIR / 'model_metrics_bilstm.csv'
    )
    print(summary)

if __name__ == '__main__':
    main()