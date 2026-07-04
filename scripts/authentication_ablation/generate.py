from config import FORGERY_INTENSITIES, DATA_RAW_DIR, BYZ_IDS
import pandas as pd
from collections import Counter
from utils.helpers import collect_rows

def main():

    for intensity in FORGERY_INTENSITIES:
        rows = collect_rows(
            start_id=1,
            n_rounds=200,
            fault_type='forgery',
            byz_ids=BYZ_IDS,
            fault_subtype=f'forgery_i{intensity}',
            fault_intensity = intensity
        )

        df = pd.DataFrame(rows)
        output_path = DATA_RAW_DIR / f'forgery_i{int(intensity*100)}.csv'
        df.to_csv(output_path, index=False)
        print(f'intensity={intensity}: saved {len(df)} rows -> {output_path.name}')
        print('  label distribution:', Counter(r['label'] for r in rows))

if __name__ == '__main__':
    main()