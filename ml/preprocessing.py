import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from config import RAW_DATA_FILE, FEATURE_COLUMNS, TARGET_COLUMN, RANDOM_SEED

# For defualt ML training
def load_and_split(csv_path=RAW_DATA_FILE):
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
    df = pd.read_csv(csv_path)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    X_trainval_raw, X_test_raw, y_trainval, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed
    )
    return X_trainval_raw, X_test_raw, y_trainval, y_test

# Multi-seed for extend features
def load_and_split_trainval_ext(feature_cols = FEATURE_COLUMNS,target_cols = TARGET_COLUMN,csv_path=RAW_DATA_FILE, seed=RANDOM_SEED):
    df = pd.read_csv(csv_path)
    X = df[feature_cols]
    y = df[target_cols]
    X_trainval_raw, X_test_raw, y_trainval, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed
    )
    return X_trainval_raw, X_test_raw, y_trainval, y_test
