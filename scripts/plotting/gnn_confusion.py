import torch
import pandas as pd
from sklearn.metrics import confusion_matrix
from torch_geometric.loader import DataLoader
from config import (DATA_RAW_DIR, RESULTS_MODELS_DIR, RESULTS_TABLES_DIR,
                    RESULTS_FIGURES_DIR, RANDOM_SEEDS, LABEL_NAMES)
from ml.preprocessing import split_graphs
from ml.models.gnn import GNNMonitor
from src.plotting.plots import plot_confusion_heatmap


@torch.no_grad()
def predict(model, loader, device):
    model.eval()
    y_true, y_pred = [], []
    for batch in loader:
        batch = batch.to(device)
        logits = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        y_true.extend(batch.y.cpu().tolist())
        y_pred.extend(logits.argmax(dim=1).cpu().tolist())
    return y_true, y_pred


def main():
    device = torch.device('cpu')

    graphs_n7 = torch.load(DATA_RAW_DIR / 'graph_dataset_n7.pt', weights_only=False)
    # gnn.pt holds the model from the last seed in RANDOM_SEEDS;
    # rebuild the matching n7 test split with that same seed
    seed = RANDOM_SEEDS[-1]
    _, _, test_n7 = split_graphs(graphs_n7, seed=seed)

    model = GNNMonitor(node_dim=graphs_n7[0].x.shape[1],
                       edge_dim=graphs_n7[0].edge_attr.shape[1])
    model.load_state_dict(torch.load(RESULTS_MODELS_DIR / 'gnn.pt',
                                     weights_only=True))

    eval_sets = {'n7_test': test_n7}
    for n in [10, 13]:
        eval_sets[f'n{n}'] = torch.load(DATA_RAW_DIR / f'graph_dataset_n{n}.pt',
                                        weights_only=False)

    cm_rows = []
    for dist, graphs in eval_sets.items():
        y_true, y_pred = predict(model, DataLoader(graphs, batch_size=32), device)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
        for i in [0, 1, 2]:
            for j in [0, 1, 2]:
                cm_rows.append({'model': 'gnn', 'distribution': dist,
                                'true_label': i, 'pred_label': j,
                                'count': int(cm[i, j])})

    cm_df = pd.DataFrame(cm_rows)
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    cm_df.to_csv(RESULTS_TABLES_DIR / 'gnn_confusion.csv', index=False)

    label_names = [LABEL_NAMES[i] for i in [0, 1, 2]]
    plot_confusion_heatmap(
        cm_df, RESULTS_FIGURES_DIR / 'gnn_confusion_matrix.png',
        label_names, title=f'GNN (seed {seed})')


if __name__ == '__main__':
    main()
