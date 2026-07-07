from torch import nn
import torch
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
class BiLSTMMonitor(nn.Module):
    def __init__(self, input_dim = 13, hidden_dim = 64, num_classes = 3):
        super().__init__()
        self.lstm = nn.LSTM(input_size = input_dim, hidden_size=hidden_dim, batch_first = True, bidirectional = True)
        self.classifier = nn.Linear(hidden_dim * 2, num_classes)  # *2 for bidirectional

    def forward(self, x):
        out, (h_n, c_n) = self.lstm(x)
        final_notebook = torch.cat([h_n[-2], h_n[-1]], dim=-1)   
        logits = self.classifier(final_notebook)
        return logits


@torch.no_grad()
def evaluate_bilstm(model, loader, device):
    model.eval()
    y_true, y_pred = [], []
    for xb, yb in loader:
        xb = xb.to(device)
        logits = model(xb)
        preds = logits.argmax(dim=1)
        y_true.extend(yb.tolist())
        y_pred.extend(preds.cpu().tolist())
    return {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average='macro', zero_division=0),
        'recall': recall_score(y_true, y_pred, average='macro', zero_division=0),
        'f1': f1_score(y_true, y_pred, average='macro', zero_division=0),
    }


def train_bilstm(model, train_loader, val_loader, device, epochs=100, lr=1e-3, class_weights=None):
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    weight = class_weights.to(device) if class_weights is not None else None
    criterion = nn.CrossEntropyLoss(weight = weight)

    best_val_f1 = -1.0
    best_state = None

    for epoch in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()

        val_metrics = evaluate_bilstm(model, val_loader, device)
        if val_metrics['f1'] > best_val_f1:
            best_val_f1 = val_metrics['f1']
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

        if (epoch + 1) % 10 == 0:
            print(f'Epoch {epoch + 1}/{epochs}, val_f1={val_metrics['f1']:.3f}')

    model.load_state_dict(best_state)
    return model