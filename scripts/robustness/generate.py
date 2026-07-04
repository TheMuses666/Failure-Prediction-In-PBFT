from config import FAULT_TYPES,NUM_NODES, DATA_RAW_DIR, ROBUSTNESS_BYZANTINE_COUNTS
import pandas as pd
from utils.helpers import collect_rows


def main():
    for fault_num in ROBUSTNESS_BYZANTINE_COUNTS:
        byz_ids = list(range(NUM_NODES - fault_num, NUM_NODES))
        rows = []
        next_round_id = 1

        rows.extend(collect_rows(next_round_id, 200, 'normal', []))
        next_round_id +=200

        for fault_type in FAULT_TYPES:
            rows.extend(collect_rows(next_round_id, 200, fault_type, byz_ids))
            next_round_id += 200

        df = pd.DataFrame(rows)
        output_path = DATA_RAW_DIR / f'robustness_f{fault_num}.csv'
        df.to_csv(output_path, index=False)

if __name__ == '__main__':
    main()