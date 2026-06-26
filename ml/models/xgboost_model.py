from xgboost import XGBClassifier
from config import RANDOM_SEED

def train_xgboost(X_train, y_train):
    model = XGBClassifier(random_state = RANDOM_SEED)
    model.fit(X_train, y_train)
    return model