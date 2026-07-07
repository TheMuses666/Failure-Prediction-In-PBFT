import pandas as pd
from src.plotting.plots import plot_grouped_curve
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR

TEST_SET_TO_N = {'n7_test': 7, 'n10': 10, 'n13': 13}


def main():
    tabular = pd.read_csv(RESULTS_TABLES_DIR / 'scalability_curve.csv')

    gnn = pd.read_csv(RESULTS_TABLES_DIR / 'model_metrics_gnn.csv')
    gnn['N'] = gnn['test_set'].map(TEST_SET_TO_N)
    gnn = gnn[['model', 'N', 'f1_mean', 'f1_std']]

    combined = pd.concat([tabular, gnn], ignore_index=True)

    plot_grouped_curve(
        df=combined,
        out_path=RESULTS_FIGURES_DIR / 'gnn_scalability_curve.png',
        x_col='N',
        y_col='f1_mean', std_col='f1_std',
        group_col='model',
        x_label='Total node count (N)',
        y_label='Macro F1',
        title='GNN vs tabular models: scale generalisation (trained on N=7 only)',
        x_ticks=[7, 10, 13],
        y_lim=(0.4, 1.0),
        markers={
            'decision_tree': 'o', 'random_forest': 's',
            'xgboost': '^', 'logistic_regression': 'D', 'gnn': '*',
        },
    )


if __name__ == '__main__':
    main()