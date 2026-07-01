from sklearn.tree import DecisionTreeClassifier
from config import RANDOM_SEED

def build_decision_tree(seed = RANDOM_SEED):
    return DecisionTreeClassifier(class_weight='balanced', random_state=seed)

def train_decision_tree(X_train, y_train,seed = RANDOM_SEED):
    model = build_decision_tree(seed)
    model.fit(X_train, y_train)
    return model