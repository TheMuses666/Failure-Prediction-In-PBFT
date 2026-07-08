from config import SEQUENCE_CONST, FAULT_TYPES, DATA_RAW_DIR, FEATURE_COLUMNS_EXTEND
import numpy as np
import pandas as pd
from collections import Counter
from src.simulation.pbft import run_pbft_simulation
from src.simulation.round_result import build_round_result
from src.data.feature_extractor import extract_features
from src.data.label_generator import generate_label

def generate_episode(seq_id, fault_type, onset, T):
    ep_seed = SEQUENCE_CONST['seq_base_seed'] + seq_id*1000

    if fault_type == 'normal':
        raws = run_pbft_simulation(n_rounds =T, fault_type='normal',byzantine_node_ids=[],seed=ep_seed, start_round=1)
    else:
        raws_a = run_pbft_simulation(n_rounds = onset - 1, fault_type='normal',byzantine_node_ids=[],seed=ep_seed, start_round=1)
        raws_b = run_pbft_simulation(n_rounds =T - onset + 1, fault_type=fault_type,byzantine_node_ids=[4,5],seed=ep_seed+1234, start_round=onset)
        raws = raws_a + raws_b

    rows = []
    for position,raw in enumerate(raws, start=1):
        rr = build_round_result(raw)
        features = extract_features(rr)
        label = generate_label(rr, features)
        rows.append({
            'seq_id': seq_id,
            'position': position,
            'fault_type': fault_type,
            'onset': onset,
            **features,
            'label': label,
        })

    return rows

def main():
    rng = np.random.default_rng(seed=SEQUENCE_CONST['seq_base_seed'])
    all_rows = []
    seq_id = 0

    for i in range(SEQUENCE_CONST['n_fault']):
        fault_type = FAULT_TYPES[i% len(FAULT_TYPES)]
        onset = rng.integers(SEQUENCE_CONST['onset_min'], SEQUENCE_CONST['onset_max'] + 1)
        rows = generate_episode(seq_id, fault_type, onset, SEQUENCE_CONST['t'])
        all_rows.extend(rows)
        seq_id += 1

    for i in range(SEQUENCE_CONST['n_normal']):
        fault_type = 'normal'
        onset = -1
        rows = generate_episode(seq_id, 'normal', onset, SEQUENCE_CONST['t'])
        all_rows.extend(rows)
        seq_id += 1

    df = pd.DataFrame(all_rows)
    T = SEQUENCE_CONST['t']
    n_seq = SEQUENCE_CONST['n_fault'] + SEQUENCE_CONST['n_normal']
    assert len(df) == n_seq * T, f"expected {n_seq * T} rows, got {len(df)}"

    print("total rows:", len(df))
    print("sequences per fault_type:")
    print(df.groupby('fault_type')['seq_id'].nunique())
    print("label distribution:", Counter(df['label']))

    fault = df[df['fault_type'] != 'normal']
    print("labels BEFORE onset:", Counter(fault[fault['position'] < fault['onset']]['label']))
    print("labels AFTER onset: ", Counter(fault[fault['position'] >= fault['onset']]['label']))

    n_unique = len(df[FEATURE_COLUMNS_EXTEND].drop_duplicates())
    print(f"unique feature rows: {n_unique} / {len(df)}")
    df.to_csv(DATA_RAW_DIR / 'sequence_dataset.csv', index=False)
if __name__ == '__main__':
    main()
