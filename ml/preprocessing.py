import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from config import RAW_DATA_FILE, FEATURE_COLUMNS, TARGET_COLUMN, RANDOM_SEED


def load_and_split(csv_path=RAW_DATA_FILE):
    df = pd.read_csv(csv_path)
    X = df[FEATURE_COLUMNS]
    y= df[TARGET_COLUMN]

    X_trainval, X_test, y_trainval, y_test = train_test_split(X,y, test_size=0.2, random_state=RANDOM_SEED, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_trainval,y_trainval, test_size=0.125, random_state=RANDOM_SEED, stratify=y_trainval)
    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)
    return X_train, X_val, X_test, y_train, y_val, y_test