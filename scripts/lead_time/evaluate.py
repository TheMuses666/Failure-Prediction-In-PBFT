from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import pandas as pd

from config import (
    DATA_RAW_DIR, RANDOM_SEEDS,
    FEATURE_COLUMNS_EXTEND, TARGET_COLUMN,
    RESULTS_TABLES_DIR, CONSENSUS_TIMEOUT_MS, CUTOFFS_MS
)
from utils.helpers import build_and_fit_all_candidates
from ml.evaluation import aggregate_metrics


def main():
    df = pd.read_csv(DATA_RAW_DIR / 'lead_time_snapshots.csv')
    print(f'Loaded {len(df)} snapshot rows, {df["round_uid"].nunique()} rounds')

    # One label per round (all 6 cutoff rows carry the same label; take the first)
    round_labels = df.groupby('round_uid')[TARGET_COLUMN].first()

    # ═══════════════════════════════════════════════════════════
    # ① Per-seed group split + per-cutoff training + batch predict
    # ═══════════════════════════════════════════════════════════
    pred_frames = []
    for seed in RANDOM_SEEDS:
        print(f'=== Seed {seed} ===')
        train_uids, test_uids = train_test_split(
            round_labels.index, test_size=0.2,
            stratify=round_labels.values, random_state=seed)

        for cutoff in CUTOFFS_MS:
            tr = df[(df.cutoff == cutoff) & (df.round_uid.isin(train_uids))]
            te = df[(df.cutoff == cutoff) & (df.round_uid.isin(test_uids))]

            fitted = build_and_fit_all_candidates(seed, tr[FEATURE_COLUMNS_EXTEND], tr[TARGET_COLUMN])

            for name, pipe in fitted.items():
                out = te[['round_uid', 'fault_type', TARGET_COLUMN]].copy()
                out['seed'] = seed
                out['model'] = name
                out['cutoff'] = cutoff
                out['pred'] = pipe.predict(te[FEATURE_COLUMNS_EXTEND])
                pred_frames.append(out)

    pred_df = pd.concat(pred_frames, ignore_index=True)
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════
    # ② Lead time on true failure rounds (label == 2)
    # ═══════════════════════════════════════════════════════════
    fail = pred_df[pred_df[TARGET_COLUMN] == 2]

    # Base index: one row per (seed, model, failure round)
    base = (fail[['seed', 'model', 'round_uid', 'fault_type']]
            .drop_duplicates()
            .set_index(['seed', 'model', 'round_uid']))

    # Earliest cutoff at which the model predicts label=2;
    # rounds that never alarm are absent from this Series
    earliest_alarm = (fail[fail['pred'] == 2]
                      .groupby(['seed', 'model', 'round_uid'])['cutoff'].min())

    base['alarm_cutoff'] = earliest_alarm          # aligned on index; NaN where missed
    base['detected'] = base['alarm_cutoff'].notna().astype(int)
    base['lead_time_ms'] = (CONSENSUS_TIMEOUT_MS - base['alarm_cutoff']).fillna(0)
    raw = base.reset_index()

    raw.to_csv(RESULTS_TABLES_DIR / 'lead_time_raw.csv', index=False)

    print('\n=== Lead Time (detected rounds only) ===')
    aggregate_metrics(
        raw[raw['detected'] == 1],
        groupby_cols=['model', 'fault_type'],
        value_cols=['lead_time_ms'],
        out_path=RESULTS_TABLES_DIR / 'lead_time_summary.csv',
    )

    # ═══════════════════════════════════════════════════════════
    # ③ Detection rate per (model, fault_type)
    # ═══════════════════════════════════════════════════════════
    detection_rate = raw.groupby(['model', 'fault_type']).agg(
        n_total=('detected', 'count'),
        n_detected=('detected', 'sum'),
    ).reset_index()
    detection_rate['detection_rate'] = detection_rate['n_detected'] / detection_rate['n_total']
    detection_rate.to_csv(RESULTS_TABLES_DIR / 'lead_time_detection_rate.csv', index=False)
    print('\n=== Detection Rate ===')
    print(detection_rate.to_string(index=False))

    # ═══════════════════════════════════════════════════════════
    # ④ False alarm on normal rounds, per (model, cutoff)
    # ═══════════════════════════════════════════════════════════
    normal = pred_df[pred_df['fault_type'] == 'normal'].copy()
    normal['pred_failure'] = (normal['pred'] == 2).astype(int)

    # FAR per seed first, then mean/std across seeds (feeds the shaded band in the plot)
    per_seed = (normal.groupby(['model', 'cutoff', 'seed'])['pred_failure']
                .mean().reset_index()
                .rename(columns={'pred_failure': 'false_alarm_rate'}))

    print('\n=== False Alarm Check ===')
    aggregate_metrics(
        per_seed,
        groupby_cols=['model', 'cutoff'],
        value_cols=['false_alarm_rate'],
        out_path=RESULTS_TABLES_DIR / 'lead_time_false_alarm.csv',
    )

    # ═══════════════════════════════════════════════════════════
    # ⑤ Macro-F1 per (model, cutoff)
    # ═══════════════════════════════════════════════════════════
    f1_records = []
    for (model, cutoff, seed), g in pred_df.groupby(['model', 'cutoff', 'seed']):
        f1_records.append({
            'model': model, 'cutoff': cutoff, 'seed': seed,
            'f1': f1_score(g[TARGET_COLUMN], g['pred'], average='macro'),
        })

    print('\n=== Macro-F1 by Cutoff ===')
    aggregate_metrics(
        f1_records,
        groupby_cols=['model', 'cutoff'],
        value_cols=['f1'],
        out_path=RESULTS_TABLES_DIR / 'lead_time_f1_by_cutoff.csv',
    )

    # ═══════════════════════════════════════════════════════════
    # ⑥ Early detection rate per (model, cutoff):
    #    fraction of true degraded/failure rounds flagged as degraded/failure
    # ═══════════════════════════════════════════════════════════
    faulty = pred_df[pred_df[TARGET_COLUMN].isin([1, 2])].copy()
    faulty['detected'] = faulty['pred'].isin([1, 2]).astype(int)
    det_per_seed = (faulty.groupby(['model', 'cutoff', 'seed'])['detected']
                    .mean().reset_index()
                    .rename(columns={'detected': 'detection_rate'}))

    print('\n=== Early Detection Rate by Cutoff ===')
    aggregate_metrics(
        det_per_seed,
        groupby_cols=['model', 'cutoff'],
        value_cols=['detection_rate'],
        out_path=RESULTS_TABLES_DIR / 'early_detection_rate_by_cutoff.csv',
    )


if __name__ == '__main__':
    main()
