import torch
import numpy as np
import pandas as pd
from torch import nn
from torch_geometric.loader import DataLoader
from config import DATA_RAW_DIR, RANDOM_SEEDS, RESULTS_MODELS_DIR, RESULTS_TABLES_DIR
from ml.preprocessing import split_graphs
from ml.models.gnn import GNNMonitor, train_gnn
from sklearn.utils.class_weight import compute_class_weight
from ml.evaluate_gnn import evaluate
from ml.evaluation import aggregate_metrics


def load_graphs(n):
    return torch.load(DATA_RAW_DIR / f'graph_dataset_n{n}.pt', weights_only=False)


def run_one_seed(seed, device):
    graphs_n7 = load_graphs(7)
    train, val, test = split_graphs(graphs_n7, seed=seed)

    torch.manual_seed(seed)

    train_loader = DataLoader(train, batch_size=32, shuffle=True)
    val_loader = DataLoader(val, batch_size=32)
    test_loader = DataLoader(test, batch_size=32)

    node_dim = train[0].x.shape[1]
    edge_dim = train[0].edge_attr.shape[1]
    model = GNNMonitor(node_dim=node_dim, edge_dim=edge_dim)

    train_labels = [int(g.y.item()) for g in train]
    class_weights = compute_class_weight('balanced', classes=np.unique(train_labels), y=train_labels)
    class_weights = torch.tensor(class_weights, dtype=torch.float)

    model = train_gnn(model, train_loader, val_loader, device, class_weights=class_weights)

    records = []
    test_metrics = evaluate(model, test_loader, device)
    records.append({'seed': seed, 'model': 'gnn', 'test_set': 'n7_test', **test_metrics})

    for n in [10, 13]:
        graphs_n = load_graphs(n)
        loader_n = DataLoader(graphs_n, batch_size=32)
        metrics_n = evaluate(model, loader_n, device)
        records.append({'seed': seed, 'model': 'gnn', 'test_set': f'n{n}', **metrics_n})

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
    torch.save(last_model.state_dict(), RESULTS_MODELS_DIR / 'gnn.pt')

    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    summary = aggregate_metrics(
        all_records, ['model', 'test_set'], ['accuracy', 'precision', 'recall', 'f1'],
        out_path=RESULTS_TABLES_DIR / 'model_metrics_gnn.csv'
    )
    print(summary)

if __name__ == '__main__':
    main()