from src.simulation.pbft import run_pbft_simulation
from src.simulation.round_result import build_round_result
from src.data.feature_extractor import extract_features
from src.data.label_generator import generate_label
from config import assert_feature_schema, FAULT_TYPES, RAW_DATA_FILE, DATA_RAW_DIR, EXTENDED_DATA_FILE
import pandas as pd
from collections import Counter

n_normal = 400
n_fault = 200
BYZ_ID = [4,5]

N_FORGERY = 200
N_PHASE4C = 100

# (fault_subtype, n_rounds, fault_type, sim_kwargs)
extended_configs = [
    ('forgery',         N_FORGERY,  'forgery',      {}),
    ('silent_prepare',  N_PHASE4C,  'silent',       {'silent_mode': 'prepare'}),
    ('silent_commit',   N_PHASE4C,  'silent',       {'silent_mode': 'commit'}),
    ('silent_all',      N_PHASE4C,  'silent',       {'silent_mode': 'all'}),
    ('delay_gaussian',  N_PHASE4C,  'delay',        {'delay_distribution': 'gaussian'}),
    ('delay_lognormal', N_PHASE4C,  'delay',        {'delay_distribution': 'lognormal'}),
    ('replay_stale',    N_PHASE4C,  'replay',       {'replay_mode': 'stale'}),
]


rows = []
next_round_id = 1

def collect_rows(start_id, n_rounds, fault_type, byz_ids, fault_subtype='base', **sim_kwargs):
    raws = run_pbft_simulation(
        start_round=start_id,
        fault_type=fault_type,
        byzantine_node_ids=byz_ids,
        n_rounds=n_rounds,
        **sim_kwargs
    )
    rows_chunk = []
    for raw in raws:
        rr = build_round_result(raw)
        features = extract_features(rr)
        assert_feature_schema(features)
        label = generate_label(rr, features)
        rows_chunk.append({
            'round_id':rr['round_id'],
            'fault_type': rr['fault_type'],
            'fault_subtype': fault_subtype,
            'byzantine_node_ids': rr['byzantine_node_ids'],
            'success': rr['success'],
            'timeout': rr['timeout'],
            **features,
            'label':label,
        })
    return rows_chunk

rows.extend(collect_rows(next_round_id,n_normal,'normal', []))
next_round_id +=n_normal

for fault_type in FAULT_TYPES:
    rows.extend(collect_rows(next_round_id, n_fault, fault_type, BYZ_ID))
    next_round_id+=n_fault

assert len(set(r['round_id'] for r in rows)) == len(rows), "round_id duplicates!"
print("total rows:", len(rows))
print("label distribution:", Counter(r['label'] for r in rows))
print("fault_type distribution:", Counter(r['fault_type'] for r in rows))
print("unique round_ids:", len(set(r['round_id'] for r in rows)))

DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)  # 确保 data/raw/ 文件夹存在
df = pd.DataFrame(rows)
df.to_csv(RAW_DATA_FILE, index=False)
print(f"saved {len(df)} rows to {RAW_DATA_FILE}")


# ===== Extended robustness dataset =====

extended_rows = []
new_next_round_id = 1

for subtype, n, ft, extra in extended_configs:
    extended_rows.extend(collect_rows(
        start_id=new_next_round_id,
        n_rounds=n,
        fault_type=ft,
        byz_ids=BYZ_ID,
        fault_subtype=subtype,
        **extra
    ))
    new_next_round_id += n

assert len(set(r['round_id'] for r in extended_rows)) == len(extended_rows), "extended round_id duplicates!"
print("extended rows:", len(extended_rows))
print("extended fault_subtype:", Counter(r['fault_subtype'] for r in extended_rows))
print("extended label:", Counter(r['label'] for r in extended_rows))

df_ext = pd.DataFrame(extended_rows)
df_ext.to_csv(EXTENDED_DATA_FILE, index=False)
print(f"saved {len(df_ext)} rows to {EXTENDED_DATA_FILE}")