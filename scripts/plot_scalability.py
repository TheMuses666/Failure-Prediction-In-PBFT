import pandas as pd
from src.plotting.plots import plot_grouped_curve
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR

plot_grouped_curve(
    df = pd.read_csv(RESULTS_TABLES_DIR / 'scalability_curve.csv'),
    out_path=RESULTS_FIGURES_DIR / 'scalability_curve.png',
    x_col='N',                       
    y_col='f1_mean', std_col='f1_std',
    group_col='model',
    x_label='Total node count (N)',  
    y_label='Macro F1',
    title='Scalability with respect to network size',
    x_ticks=[7, 10, 13],             
    y_lim=(0.5, 1.0),
    markers={
        'decision_tree': 'o', 'random_forest': 's',
        'xgboost': '^', 'logistic_regression': 'D',
    },
)