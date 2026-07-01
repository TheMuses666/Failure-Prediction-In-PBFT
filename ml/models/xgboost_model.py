from xgboost import XGBClassifier
from config import RANDOM_SEED

def build_xgboost(seed = RANDOM_SEED):
    return XGBClassifier(random_state=seed)

def train_xgboost(X_train, y_train, seed = RANDOM_SEED):
    model = build_xgboost(seed)
    model.fit(X_train, y_train)
    return model