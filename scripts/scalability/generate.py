from config import FAULT_TYPES,NUM_NODES, DATA_RAW_DIR, SCALABILITY_NODE_COUNTS, BZY_ID_SCALABILITY
import pandas as pd
from utils.helpers import collect_rows

def main():
    for node in SCALABILITY_NODE_COUNTS:
        byz_ids = BZY_ID_SCALABILITY[node]
        rows =[]
        next_round_id = 1

        rows.extend(collect_rows(next_round_id, 200, 'normal',[], total_nodes=node))
        next_round_id += 200

        for fault_type in FAULT_TYPES:
            rows.extend(collect_rows(next_round_id, 200, fault_type, byz_ids, total_nodes=node))
            next_round_id += 200

        pd.DataFrame(rows).to_csv(DATA_RAW_DIR / f'scalability_n{node}.csv', index=False)

if __name__ == '__main__':
    main()