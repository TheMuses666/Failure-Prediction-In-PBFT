from sklearn.tree import DecisionTreeClassifier
from config import RANDOM_SEED

def train_decision_tree(X_train, y_train):
    model = DecisionTreeClassifier(random_state=RANDOM_SEED)
    model.fit(X_train, y_train)
    return model