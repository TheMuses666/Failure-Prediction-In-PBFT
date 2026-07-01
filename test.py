import pandas as pd
from config import RAW_DATA_FILE

df = pd.read_csv(RAW_DATA_FILE)

# Check 1: 跟 label 的相关性（>0.9 就该警惕）
print("Correlation with label:")
print(df[['quorum_margin','prepare_count_std','voting_consistency','label']].corr()['label'])

# Check 2: 看 quorum_margin 按 label 的分布
print("\nquorum_margin by label:")
print(df.groupby('label')['quorum_margin'].describe())

# Check 3: 看 prepare_count_std 按 fault_type 的分布
print("\nprepare_count_std by fault_type:")
print(df.groupby('fault_type')['prepare_count_std'].describe())