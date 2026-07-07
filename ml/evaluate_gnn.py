import torch
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


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