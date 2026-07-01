from sklearn.ensemble import RandomForestClassifier
from config import RANDOM_SEED

def build_random_forest(seed = RANDOM_SEED):
    return RandomForestClassifier(class_weight='balanced', random_state=seed)

def train_random_forest(X_train, y_train,seed = RANDOM_SEED):
    model = build_random_forest(seed)
    model.fit(X_train, y_train)
    return model
