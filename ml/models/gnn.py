import torch
from torch import nn
from torch_geometric.nn import GINEConv, global_mean_pool
from ml.evaluate_gnn import evaluate

class GNNMonitor(nn.Module):
    def __init__(self, node_dim, edge_dim, hidden_dim = 32, num_classes = 3):
        super().__init__()
        self.node_encoder = nn.Linear(node_dim, hidden_dim)
        self.edge_encoder = nn.Linear(edge_dim, hidden_dim)

        self.conv1 = GINEConv(nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        ))
        self.conv2 = GINEConv(nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        ))

        self.classifier = nn.Linear(hidden_dim, num_classes)

    def forward(self, x, edge_index, edge_attr, batch):
        x = self.node_encoder(x)
        e = self.edge_encoder(edge_attr)

        x = self.conv1(x, edge_index, e).relu()
        x = self.conv2(x, edge_index, e).relu()

        x = global_mean_pool(x, batch)
        return self.classifier(x)
    

def train_gnn(model, train_loader, val_loader, device, epochs=100, lr=1e-3, class_weights=None):
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    weight = class_weights.to(device) if class_weights is not None else None
    criterion = nn.CrossEntropyLoss(weight = weight)

    best_val_f1 = -1.0
    best_state = None

    for epoch in range(epochs):
        model.train()
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            logits = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            loss = criterion(logits, batch.y)
            loss.backward()
            optimizer.step()

        val_metrics = evaluate(model, val_loader, device)
        if val_metrics['f1'] > best_val_f1:
            best_val_f1 = val_metrics['f1']
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

        if (epoch + 1) % 10 == 0:
            print(f'Epoch {epoch + 1}/{epochs}, val_f1={val_metrics['f1']:.3f}')

    model.load_state_dict(best_state)
    return model