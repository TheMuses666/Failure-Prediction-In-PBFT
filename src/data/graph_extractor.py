import torch
from torch_geometric.data import Data
from config import MESSAGE_TYPE_TO_ID
import torch
import numpy as np
import pandas as pd
from torch import nn
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.utils.class_weight import compute_class_weight
from torch_geometric.loader import DataLoader
from config import DATA_RAW_DIR, RANDOM_SEED, RESULTS_MODELS_DIR, RESULTS_TABLES_DIR
from ml.preprocessing import split_graphs
from ml.models.gnn import GNNMonitor

@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    y_true, y_pred = [], []
    for batch in loader:
        batch = batch.to(device)
        logits = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        preds = logits.argmax(dim=1)
        y_true.extend(batch.y.cpu().tolist())
        y_pred.extend(preds.cpu().tolist())

    return {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average='macro', zero_division=0),
        'recall': recall_score(y_true, y_pred, average='macro', zero_division=0),
        'f1': f1_score(y_true, y_pred, average='macro', zero_division=0),
    }

def build_graph(raw: dict, label:int) -> Data:
    nodes = raw['_nodes']
    round_id = raw['round_id']
    primary_id = raw['primary_id']
    commited_node_ids = set(raw['committed_node_ids'])

    node_features = []
    for n in nodes:
        is_primary = 1 if n.node_id == primary_id else 0
        has_committed = 1 if n.node_id in commited_node_ids else 0

        own_prepare_votes = sum(len(s) for s in n.prepare_log.get(round_id, {}).values())
        own_commit_votes = sum(len(s) for s in n.commit_log.get(round_id, {}).values())

        first_response = n.first_response_time.get(round_id, -1.0)

        phases = n.phase_times.get(round_id, {})
        if 'commit' in phases and 'prepare' in phases:
            phase_duration = phases['commit'] - phases['prepare']
        else:
            phase_duration = -1.0

        node_features.append([
            is_primary,
            has_committed,
            float(own_prepare_votes),
            float(own_commit_votes),
            float(first_response),
            float(phase_duration)
        ])
    x = torch.tensor(node_features, dtype=torch.float)

    net = raw['_network']
    this_round_msgs = [m for m in net.message_log if m.round_id == round_id]

    edge_index = []
    edge_features =[]
    for m in this_round_msgs:
        edge_index.append([m.sender_id, m.receiver_id])

        is_delivered = 1.0 if m.delivery_time is not None else 0.0
        latency = (m.delivery_time -m.send_time) if is_delivered else -1.0

        edge_features.append([
            float(MESSAGE_TYPE_TO_ID.get(m.message_type, -1)),
            latency,
            is_delivered,
            1.0 if m.is_corrupt else 0.0
        ])

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_features, dtype=torch.float)

    y = torch.tensor([label], dtype=torch.long)
    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
