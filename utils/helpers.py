from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import classification_report

from config import RAW_DATA_FILE, RANDOM_SEEDS, TARGET_COLUMN,assert_feature_schema
from ml.models.decision_tree import build_decision_tree
from ml.models.random_forest import build_random_forest
from ml.models.xgboost_model import build_xgboost
from ml.models.logistic_regression import build_logistic_regression
from ml.evaluation import model_evaluation
from src.simulation.pbft import run_pbft_simulation
from src.simulation.round_result import build_round_result
from src.data.feature_extractor import extract_features
from src.data.label_generator import generate_label

def make_pipeline(estimator):
    return Pipeline([('scaler', MinMaxScaler()), ('clf', estimator)])

def train_default_pipeline_multiseed(
    feature_cols,
    split_fuc,
    csv_path=RAW_DATA_FILE,
    seeds=RANDOM_SEEDS,
    label_col=TARGET_COLUMN,
):
    records = []
    per_class_records = []

    for seed in seeds:
        X_trainval, X_test, y_trainval, y_test = split_fuc(
            feature_cols = feature_cols, target_cols = label_col,csv_path = csv_path, seed=seed
        )
        fitted = build_and_fit_all_candidates(seed, X_trainval, y_trainval)


        for name, pipe in fitted.items():
            m = model_evaluation(pipe, X_test, y_test, model_name=name)
            records.append({'seed': seed, 'model': name,
                            'accuracy': m['accuracy'],
                            'precision': m['precision'],
                            'recall': m['recall'],
                            'f1': m['f1']})
            # per-class
            y_pred = pipe.predict(X_test)
            rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            for cls, sc in rep.items():
                if isinstance(sc, dict):
                    per_class_records.append({
                        'seed': seed, 'model': name, 'class': cls,
                        'precision': sc['precision'], 'recall': sc['recall'],
                        'f1': sc['f1-score'], 'support': sc['support'],
                    })
    
    return records, per_class_records

def build_and_fit_all_candidates(seed, X_tv, y_tv):
    sample_weight = compute_sample_weight('balanced', y_tv)
    candidates = [
        ('decision_tree',       build_decision_tree(seed)),
        ('random_forest',       build_random_forest(seed)),
        ('xgboost',             build_xgboost(seed)),
        ('logistic_regression', build_logistic_regression(seed)),
    ]

    fitted = {}
    for name, estimator in candidates:
        pipe = make_pipeline(estimator)
        if name == 'xgboost':
            pipe.fit(X_tv, y_tv, clf__sample_weight=sample_weight)
        else:
            pipe.fit(X_tv, y_tv)
        fitted[name] = pipe
    return fitted


def collect_rows(start_id, n_rounds, fault_type, byz_ids, fault_subtype='base', **sim_kwargs):
    raws = run_pbft_simulation(
        start_round=start_id,
        fault_type=fault_type,
        byzantine_node_ids=byz_ids,
        n_rounds=n_rounds,
        **sim_kwargs
    )
    rows_chunk = []
    for raw in raws:
        rr = build_round_result(raw)
        features = extract_features(rr)
        assert_feature_schema(features)
        label = generate_label(rr, features)
        rows_chunk.append({
            'round_id':rr['round_id'],
            'fault_type': rr['fault_type'],
            'fault_subtype': fault_subtype,
            'byzantine_node_ids': rr['byzantine_node_ids'],
            'success': rr['success'],
            'timeout': rr['timeout'],
            **features,
            'label':label,
        })
    return rows_chunk