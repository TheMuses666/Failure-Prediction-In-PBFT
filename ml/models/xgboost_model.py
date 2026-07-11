from xgboost import XGBClassifier
from config import RANDOM_SEED

def build_xgboost(seed = RANDOM_SEED):
    # n_jobs=1: GridSearchCV already parallelises across folds/candidates;
    # letting XGBoost also spawn one thread per core oversubscribes the CPU
    # and crashes loky workers (TerminatedWorkerError) on many-core machines.
    return XGBClassifier(random_state=seed, n_jobs=1)

def train_xgboost(X_train, y_train, seed = RANDOM_SEED):
    model = build_xgboost(seed)
    model.fit(X_train, y_train)
    return model