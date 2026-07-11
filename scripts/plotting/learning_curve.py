from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

from config import (RAW_DATA_FILE, RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR,
                    FEATURE_COLUMNS_EXTEND, RANDOM_SEEDS)
from ml.preprocessing import load_and_split_trainval_ext
from ml.evaluation import aggregate_metrics
from utils.helpers import build_and_fit_all_candidates
from src.plotting.plots import plot_grouped_curve

TRAIN_SIZES = [120, 240, 480, 720, 960]

MARKERS = {
    'decision_tree': 'o',
    'random_forest': 's',
    'xgboost': '^',
    'logistic_regression': 'D',
}


def main():
    records = []
    for seed in RANDOM_SEEDS:
        print(f'=== Seed {seed} ===')
        X_tv, X_test, y_tv, y_test = load_and_split_trainval_ext(
            feature_cols=FEATURE_COLUMNS_EXTEND, csv_path=RAW_DATA_FILE, seed=seed)

        for size in TRAIN_SIZES:
            if size < len(X_tv):
                X_sub, _, y_sub, _ = train_test_split(
                    X_tv, y_tv, train_size=size, stratify=y_tv, random_state=seed)
            else:
                X_sub, y_sub = X_tv, y_tv

            for name, pipe in build_and_fit_all_candidates(seed, X_sub, y_sub).items():
                records.append({
                    'seed': seed, 'model': name, 'train_size': size,
                    'f1': f1_score(y_test, pipe.predict(X_test), average='macro'),
                })

    aggregate_metrics(records, ['model', 'train_size'], ['f1'],
                      out_path=RESULTS_TABLES_DIR / 'learning_curve.csv')

    import pandas as pd
    df = pd.read_csv(RESULTS_TABLES_DIR / 'learning_curve.csv')
    plot_grouped_curve(
        df=df,
        out_path=RESULTS_FIGURES_DIR / 'learning_curve.png',
        x_col='train_size',
        y_col='f1_mean',
        std_col='f1_std',
        group_col='model',
        x_label='Training set size (rounds)',
        y_label='Macro-F1 (test split)',
        title='Learning curve on the main dataset (5 seeds)',
        x_ticks=TRAIN_SIZES,
        y_lim=(0.7, 1.0),
        markers=MARKERS,
    )


if __name__ == '__main__':
    main()
