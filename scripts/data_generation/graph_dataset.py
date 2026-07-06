import torch
from config import (
    FAULT_TYPES, NORMAL_ROUNDS, ROUNDS_PER_FAULT, BYZ_IDS,
    SCALABILITY_NODE_COUNTS, BZY_ID_SCALABILITY, DATA_RAW_DIR, NUM_NODES,
)

from utils.helpers import collect_graphs



def main():
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    graph_n7 = []
    next_round_id = 1

    graph_n7.extend(collect_graphs(next_round_id, NORMAL_ROUNDS, 'normal', []))
    next_round_id += NORMAL_ROUNDS

    for fault_type in FAULT_TYPES:
        graph_n7.extend(collect_graphs(next_round_id, ROUNDS_PER_FAULT, fault_type, BYZ_IDS))
        next_round_id += ROUNDS_PER_FAULT
    torch.save(graph_n7, DATA_RAW_DIR / 'graph_dataset_n7.pt')
    print(f"Saved {len(graph_n7)} graphs for n=7 to {DATA_RAW_DIR / 'graph_dataset_n7.pt'}")

    for node in SCALABILITY_NODE_COUNTS:
        byz_ids = BZY_ID_SCALABILITY[node]
        next_round_id = 1
        graphs = []

        graphs.extend(collect_graphs(next_round_id, 200, 'normal', [], total_nodes=node))
        next_round_id += 200

        for fault_type in FAULT_TYPES:
            graphs.extend(collect_graphs(next_round_id, ROUNDS_PER_FAULT, fault_type, byz_ids, total_nodes=node))
            next_round_id += ROUNDS_PER_FAULT
        
        torch.save(graphs, DATA_RAW_DIR / f'graph_dataset_n{node}.pt')
        print(f"Saved {len(graphs)} graphs for n={node} to {DATA_RAW_DIR / f'graph_dataset_n{node}.pt'}")


if __name__ == '__main__':
    main()