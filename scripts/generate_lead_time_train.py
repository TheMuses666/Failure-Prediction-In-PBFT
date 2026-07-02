import pandas as pd
from src.simulation.pbft import run_pbft_simulation
from src.simulation.round_result import build_round_result
from src.data.feature_extractor import extract_features, compute_features_at_time
from src.data.label_generator import generate_label
from config import FAULT_TYPES, CUTOFFS_MS, BYZ_IDS, DATA_RAW_DIR, NORMAL_ROUNDS, ROUNDS_PER_FAULT

rows = []

def process(raws, fault_type):
    for raw in raws:
        rr = build_round_result(raw)
        # label：整轮特征，只算一次
        label = generate_label(rr, extract_features(rr))
        for cutoff in CUTOFFS_MS:
            feats = compute_features_at_time(rr, cutoff)
            rows.append({
                'round_uid': f'{fault_type}_{rr["round_id"]}',
                'fault_type': fault_type,
                'cutoff': cutoff,
                **feats,          # 13 个特征
                'label': label,
            })

def main():

    for fault_type in FAULT_TYPES:
        print(f'Simulating {fault_type}')
        raws = run_pbft_simulation(
            n_rounds=ROUNDS_PER_FAULT,
            fault_type=fault_type,
            byzantine_node_ids=BYZ_IDS,
            start_round=1,
        )
        process(raws, fault_type)

    # 加 200 个 normal round 用于 false alarm 检查
    print('Simulating normal')
    raws_normal = run_pbft_simulation(
        n_rounds=NORMAL_ROUNDS,
        fault_type='normal',
        byzantine_node_ids=[],
        start_round=1,
    )
    process(raws_normal, 'normal')

    pd.DataFrame(rows).to_csv(DATA_RAW_DIR / 'lead_time_snapshots.csv', index=False)

if __name__ == '__main__':
    main()