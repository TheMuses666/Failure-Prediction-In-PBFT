import torch
import numpy as np
import matplotlib.pyplot as plt
from config import DATA_RAW_DIR, RESULTS_FIGURES_DIR, LABEL_NAMES

NODE_COUNTS = [7, 10, 13]


def main():
    stats = {}
    for n in NODE_COUNTS:
        graphs = torch.load(DATA_RAW_DIR / f'graph_dataset_n{n}.pt',
                            weights_only=False)
        labels = [int(g.y.item()) for g in graphs]
        stats[n] = {
            'n_graphs': len(graphs),
            'avg_nodes': np.mean([g.x.shape[0] for g in graphs]),
            'avg_edges': np.mean([g.edge_index.shape[1] for g in graphs]),
            'label_counts': {lbl: labels.count(lbl) for lbl in [0, 1, 2]},
        }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: label distribution per network size
    x = np.arange(len(NODE_COUNTS))
    width = 0.25
    for i, lbl in enumerate([0, 1, 2]):
        counts = [stats[n]['label_counts'][lbl] for n in NODE_COUNTS]
        ax1.bar(x + (i - 1) * width, counts, width, label=LABEL_NAMES[lbl])
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'N={n}\n({stats[n]["n_graphs"]} graphs)'
                         for n in NODE_COUNTS])
    ax1.set_ylabel('Graphs')
    ax1.set_title('Label distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # Right: average node / edge counts per network size
    avg_nodes = [stats[n]['avg_nodes'] for n in NODE_COUNTS]
    avg_edges = [stats[n]['avg_edges'] for n in NODE_COUNTS]
    b1 = ax2.bar(x - 0.2, avg_nodes, 0.4, label='avg nodes')
    b2 = ax2.bar(x + 0.2, avg_edges, 0.4, label='avg edges')
    ax2.bar_label(b1, fmt='%.0f')
    ax2.bar_label(b2, fmt='%.0f')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'N={n}' for n in NODE_COUNTS])
    ax2.set_ylabel('Count per graph')
    ax2.set_title('Graph size')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')

    fig.suptitle('Graph dataset summary')
    fig.tight_layout()
    out_path = RESULTS_FIGURES_DIR / 'graph_dataset_summary.png'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Figure saved --> {out_path}')


if __name__ == '__main__':
    main()
