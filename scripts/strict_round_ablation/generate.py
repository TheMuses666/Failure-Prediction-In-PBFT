from config import DATA_RAW_DIR, BYZ_IDS, STRICT_SCENARIOS
import pandas as pd
from collections import Counter
from utils.helpers import collect_rows

def main():
    for name, strict in STRICT_SCENARIOS:
        rows = collect_rows(
            start_id=1,
            n_rounds=200,
            fault_type='replay',
            byz_ids=BYZ_IDS,
            fault_subtype=f'replay_stale_{name}',
            replay_mode='stale',
            strict_round_validation=strict,
        )

        df = pd.DataFrame(rows)
        output_path = DATA_RAW_DIR / f'stale_{name}.csv'
        df.to_csv(output_path, index=False)
        print(f'{name}: saved {len(df)} rows -> {output_path.name}')
        print('  label distribution:', Counter(r['label'] for r in rows))
        print('  stale_replayed mean:', round(df['stale_replayed'].mean(), 2))
        print('  message_consistency mean:', round(df['message_consistency'].mean(), 4),
              ' min:', round(df['message_consistency'].min(), 4))

if __name__ == '__main__':
    main()