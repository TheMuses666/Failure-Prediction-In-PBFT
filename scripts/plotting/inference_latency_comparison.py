import time
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
from torch_geometric.loader import DataLoader

from config import (RAW_DATA_FILE, DATA_RAW_DIR, RESULTS_MODELS_DIR,
                    RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR,
                    FEATURE_COLUMNS_EXTEND, RANDOM_SEED)
from ml.preprocessing import load_and_split_trainval_ext, build_windows
from ml.models.gnn import GNNMonitor
from ml.models.bilstm import BiLSTMMonitor
from utils.helpers import build_and_fit_all_candidates
from baseline.static_detection import (fit_threshold, threshold_detector,
                                       rule_based_detector,
                                       fit_count_threshold, count_based_detector)


def timed_per_sample_us(fn, n_samples, repeats=5):
    """Best-of-N batch prediction time, averaged per sample, in microseconds."""
    best = float('inf')
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best / n_samples * 1e6


def main():
    latencies = {}

    # --- static baselines and tabular ML (main dataset test split) ---
    X_tv, X_test, y_tv, y_test = load_and_split_trainval_ext(
        feature_cols=FEATURE_COLUMNS_EXTEND, csv_path=RAW_DATA_FILE, seed=RANDOM_SEED)
    n = len(X_test)

    th = fit_threshold(X_tv, y_tv)
    latencies['threshold_based'] = timed_per_sample_us(
        lambda: threshold_detector(X_test, th), n)
    latencies['rule_based'] = timed_per_sample_us(
        lambda: rule_based_detector(X_test), n)
    ct = fit_count_threshold(X_tv, y_tv)
    latencies['count_based'] = timed_per_sample_us(
        lambda: count_based_detector(X_test, ct), n)

    for name, pipe in build_and_fit_all_candidates(RANDOM_SEED, X_tv, y_tv).items():
        latencies[name] = timed_per_sample_us(lambda p=pipe: p.predict(X_test), n)

    # --- GNN (N=7 graphs, batch inference) ---
    graphs = torch.load(DATA_RAW_DIR / 'graph_dataset_n7.pt', weights_only=False)
    gnn = GNNMonitor(node_dim=graphs[0].x.shape[1],
                     edge_dim=graphs[0].edge_attr.shape[1])
    try:
        gnn.load_state_dict(torch.load(RESULTS_MODELS_DIR / 'gnn.pt',
                                       weights_only=True))
    except (FileNotFoundError, RuntimeError):
        pass  # latency does not depend on the weight values
    gnn.eval()
    loader = DataLoader(graphs, batch_size=32)

    @torch.no_grad()
    def gnn_predict():
        for batch in loader:
            gnn(batch.x, batch.edge_index, batch.edge_attr, batch.batch).argmax(dim=1)

    latencies['gnn'] = timed_per_sample_us(gnn_predict, len(graphs))

    # --- BiLSTM (sequence windows, k=10, batch inference) ---
    seq_df = pd.read_csv(DATA_RAW_DIR / 'sequence_dataset.csv')
    X_win, _, _ = build_windows(seq_df, k=10, feature_cols=FEATURE_COLUMNS_EXTEND)
    X_win = torch.tensor(np.asarray(X_win), dtype=torch.float32)
    bilstm = BiLSTMMonitor(input_dim=len(FEATURE_COLUMNS_EXTEND))
    try:
        bilstm.load_state_dict(torch.load(RESULTS_MODELS_DIR / 'bilstm.pt',
                                          weights_only=True))
    except (FileNotFoundError, RuntimeError):
        pass
    bilstm.eval()

    @torch.no_grad()
    def bilstm_predict():
        for i in range(0, len(X_win), 32):
            bilstm(X_win[i:i + 32])

    latencies['bilstm'] = timed_per_sample_us(bilstm_predict, len(X_win))

    # --- save table + figure ---
    table = (pd.DataFrame(latencies.items(), columns=['model', 'latency_us'])
             .sort_values('latency_us'))
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(RESULTS_TABLES_DIR / 'inference_latency.csv', index=False)
    print(table.to_string(index=False))

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(table['model'], table['latency_us'], alpha=0.85)
    ax.bar_label(bars, fmt='%.1f')
    ax.set_yscale('log')
    ax.set_ylabel('Per-sample inference latency (µs, log scale)')
    ax.set_xlabel('Monitor')
    ax.set_title('Batch-averaged inference latency per consensus round (CPU)')
    plt.setp(ax.get_xticklabels(), rotation=20, ha='right')
    ax.grid(True, alpha=0.3, axis='y')

    fig.tight_layout()
    out_path = RESULTS_FIGURES_DIR / 'inference_latency_comparison.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Figure saved --> {out_path}')


if __name__ == '__main__':
    main()
