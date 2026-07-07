import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from config import RAW_DATA_FILE, FEATURE_COLUMNS, TARGET_COLUMN, RANDOM_SEED

# For defualt ML training
def load_and_split(csv_path=RAW_DATA_FILE):
    """Load the main dataset and create scaled train, validation, and test splits."""
    df = pd.read_csv(csv_path)
    X = df[FEATURE_COLUMNS]
    y= df[TARGET_COLUMN]

    X_trainval, X_test_raw, y_trainval, y_test = train_test_split(X,y, test_size=0.2, random_state=RANDOM_SEED, stratify=y)
    X_train_raw, X_val, y_train, y_val = train_test_split(X_trainval,y_trainval, test_size=0.125, random_state=RANDOM_SEED, stratify=y_trainval)
    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test_raw)
    return X_train, X_val, X_test, X_train_raw, X_test_raw, y_train, y_val, y_test, scaler


# For tunning ML training
def load_and_split_trainval(csv_path=RAW_DATA_FILE, seed=RANDOM_SEED):
    """Load the main dataset and create a scaled trainval/test split for tuning."""

    df = pd.read_csv(csv_path)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_trainval_raw, X_test_raw, y_trainval, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=seed)

    scaler = MinMaxScaler()
    X_trainval = scaler.fit_transform(X_trainval_raw)
    X_test = scaler.transform(X_test_raw)

    return X_trainval, X_test, y_trainval, y_test, scaler

# Multi-seed for baseline raw data
def load_and_split_trainval_raw(csv_path=RAW_DATA_FILE, seed=RANDOM_SEED):
    """Load the main dataset and return raw trainval/test splits for pipelines."""
    df = pd.read_csv(csv_path)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    X_trainval_raw, X_test_raw, y_trainval, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed
    )
    return X_trainval_raw, X_test_raw, y_trainval, y_test

# Multi-seed for extend features
def load_and_split_trainval_ext(feature_cols = FEATURE_COLUMNS,target_cols = TARGET_COLUMN,csv_path=RAW_DATA_FILE, seed=RANDOM_SEED):
    """Load selected feature columns and return raw trainval/test splits."""
    df = pd.read_csv(csv_path)
    X = df[feature_cols]
    y = df[target_cols]
    X_trainval_raw, X_test_raw, y_trainval, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed
    )
    return X_trainval_raw, X_test_raw, y_trainval, y_test

def split_graphs(graphs, seed=RANDOM_SEED):
    """Stratified 70/10/20 train/val/test split for a list of PyG Data graphs."""
    labels = [int(g.y.item()) for g in graphs]

    trainval, test, y_trainval, _ = train_test_split(
        graphs, labels, test_size=0.2, random_state=seed, stratify=labels
    )
    train, val = train_test_split(
        trainval, test_size=0.125, random_state=seed, stratify=y_trainval
    )
    return train, val, test


def build_windows(df, k, feature_cols):
    X_list, y_list, sid_list = [], [], []

    for seq_id, group in df.groupby('seq_id'):
        group = group.sort_values('position')
        features = group[feature_cols].values
        labels = group[TARGET_COLUMN].values

        for t in range(k-1,len(group)):

            X_list.append(features[t-k+1:t+1])
            y_list.append(labels[t])
            sid_list.append(seq_id)
    return (np.stack(X_list).astype(np.float32),
            np.array(y_list),
            np.array(sid_list))

def split_by_sequence(df, seed, ratio=(0.7, 0.1, 0.2)):
    """Split the DataFrame into train/val/test sets based on unique seq_id."""
    seq_meta = df.groupby('seq_id')['fault_type'].first()

    trainval_ids, test_ids = train_test_split(
        seq_meta.index, test_size=ratio[2],
        random_state=seed, stratify=seq_meta.values)
    
    n_val = round(len(seq_meta) * ratio[1])  
    train_ids, val_ids = train_test_split(
        trainval_ids, test_size=n_val,
        random_state=seed, stratify=seq_meta.loc[trainval_ids].values)

    train_df = df[df['seq_id'].isin(train_ids)]
    val_df = df[df['seq_id'].isin(val_ids)]
    test_df = df[df['seq_id'].isin(test_ids)]

    return train_df, val_df, test_df
