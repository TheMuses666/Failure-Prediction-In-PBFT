import pandas as pd
from ml.preprocessing import load_and_split_trainval_ext
from utils.helpers import build_and_fit_all_candidates, run_ood_detection
from ml.evaluation import evaluate_per_fault_type, aggregate_metrics
from src.simulation.pbft import run_pbft_simulation
from config import (DATA_RAW_DIR, RAW_DATA_FILE, RESULTS_TABLES_DIR, RANDOM_SEEDS,
                    FEATURE_COLUMNS_EXTEND, TARGET_COLUMN, BYZ_IDS, STRICT_SCENARIOS)
from baseline.static_detection import (fit_threshold, BaselineWrapper, threshold_detector,
                                       rule_based_detector, fit_count_threshold,
                                       count_based_detector)


def sim_analysis():
    records, dfs = [], {}
    for name, strict in STRICT_SCENARIOS:
        df = pd.read_csv(DATA_RAW_DIR / f'stale_{name}.csv')
        dfs[name] = df
        records.append({
            'scenario': name,
            'n_rounds': len(df),
            'stale_replayed_mean': df['stale_replayed'].mean(),
            'label_0': int((df['label'] == 0).sum()),
            'label_1': int((df['label'] == 1).sum()),
            'label_2': int((df['label'] == 2).sum()),
            'success_rate': df['success'].mean(),
            'message_consistency_mean': df['message_consistency'].mean(),
            'message_consistency_below_warning': int((df['message_consistency'] < 0.8).sum()),
            'prepare_count_std_mean': df['prepare_count_std'].mean(),
            'vote_deviation_mean': df['vote_deviation'].mean(),
            'agreement_time_mean': df['consensus_agreement_time'].mean(),
            'agreement_time_std': df['consensus_agreement_time'].std(),
            'voting_consistency_mean': df['voting_consistency'].mean(),
        })

    output_path = RESULTS_TABLES_DIR / 'strict_ablation_sim.csv'
    pd.DataFrame(records).to_csv(output_path, index=False)
    print(pd.DataFrame(records).round(3).to_string(index=False))

    merged = dfs['strict_on'].merge(dfs['strict_off'], on='round_id', suffixes=('_on', '_off'))
    diff = merged[merged['label_on'] != merged['label_off']]
    print(f'\npaired label check: {len(diff)} / {len(merged)} rounds differ')
    same_failures = set(dfs['strict_on'].loc[dfs['strict_on']['label'] == 2, 'round_id']) \
            == set(dfs['strict_off'].loc[dfs['strict_off']['label'] == 2, 'round_id'])
    print(f'label=2 rounds identical across arms: {same_failures}')


def quorum_analysis():
    records = []
    for name, strict in STRICT_SCENARIOS:
        raws = run_pbft_simulation(
            n_rounds=200, 
            fault_type='replay',
            byzantine_node_ids=BYZ_IDS, replay_mode='stale',
            strict_round_validation=strict
        )
        wrong_prep_q = wrong_com_q = 0
        max_wrong_prep = max_wrong_com = 0

        for raw in raws:
            rid = raw['round_id']
            expected = f'req_{rid}'
            q = raw['_nodes'][0].quorum_size

            for n in raw['_nodes']:
                for content, senders in n.prepare_log.get(rid,{}).items():
                    if content != expected:
                        max_wrong_prep = max(max_wrong_prep, len(senders))
                        if len(senders)>=q:
                            wrong_prep_q +=1
                for content, senders in n.commit_log.get(rid, {}).items():
                    if content != expected:
                        max_wrong_com = max(max_wrong_com, len(senders))
                        if len(senders) >= q:
                            wrong_com_q +=1

        records.append({
            'scenario': name,
            'quorum_size': q,
            'wrong_content_prepare_quorums': wrong_prep_q,
            'wrong_content_commit_quorums': wrong_com_q,
            'max_wrong_content_prepare_votes': max_wrong_prep,
            'max_wrong_content_commit_votes': max_wrong_com,
        })

    output_path = RESULTS_TABLES_DIR / 'strict_ablation_quorum.csv'
    pd.DataFrame(records).to_csv(output_path, index=False)
    print(pd.DataFrame(records).to_string(index=False))

def detection_analysis():
    df_all = pd.concat([pd.read_csv(DATA_RAW_DIR / f'stale_{name}.csv') for name, _ in STRICT_SCENARIOS], ignore_index=True)
    run_ood_detection(df_all, 'fault_subtype', RESULTS_TABLES_DIR / 'strict_ablation_detection.csv')
    
if __name__ == '__main__':
    sim_analysis()
    quorum_analysis()
    detection_analysis()
