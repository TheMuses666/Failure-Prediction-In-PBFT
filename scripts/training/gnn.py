import torch
from torch_geometric.loader import DataLoader
from config import DATA_RAW_DIR, RANDOM_SEED
from ml.preprocessing import split_graphs
from ml.models.gnn import GNNMonitor

def load_graphs(n):
    return torch.load(DATA_RAW_DIR / f'graph_dataset_n{n}.pt', weights_only=False)


def main():
    graphs_n7 = load_graphs(7)
    train, val, test = split_graphs(graphs_n7, seed=RANDOM_SEED)

    train_loader = DataLoader(train, batch_size=32, shuffle=True)
    val_loader = DataLoader(val, batch_size=32)
    test_loader = DataLoader(test, batch_size=32)

    node_dim = train[0].x.shape[1]
    edge_dim = train[0].edge_attr.shape[1]
    model = GNNMonitor(node_dim=node_dim, edge_dim=edge_dim)

    print(f'train={len(train)} val={len(val)} test={len(test)}')
    print(f'node_dim={node_dim} edge_dim={edge_dim}')
    print(model)


if __name__ == '__main__':
    main()