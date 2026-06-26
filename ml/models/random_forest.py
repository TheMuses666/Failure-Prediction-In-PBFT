from sklearn.ensemble import RandomForestClassifier
from config import RANDOM_SEED

def train_random_forest(X_train, y_train):
    model = RandomForestClassifier(random_state=RANDOM_SEED)
    model.fit(X_train, y_train)

    return model
