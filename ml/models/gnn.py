from torch import nn
from torch_geometric.nn import GINEConv, global_mean_pool

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