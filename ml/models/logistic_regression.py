from sklearn.linear_model import LogisticRegression
from config import RANDOM_SEED

def build_logistic_regression(seed = RANDOM_SEED):
    return LogisticRegression(class_weight='balanced',max_iter=1000,random_state=seed)

def train_logistic_regression(X_train, y_train, seed = RANDOM_SEED):
    model = build_logistic_regression(seed)
    model.fit(X_train, y_train)
    return model
