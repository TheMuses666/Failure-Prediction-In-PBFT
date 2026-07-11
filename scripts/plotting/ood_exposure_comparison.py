import pandas as pd
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR
from src.plotting.plots import plot_grouped_bar

ARMS = {
    'main_only': 'ood_f1.csv',
    'extended_exposure': 'ood_f1_trainext.csv',
}


def main():
    frames = []
    for arm, fname in ARMS.items():
        df = pd.read_csv(RESULTS_TABLES_DIR / fname)
        df = df[df['distribution'] == 'ood_extended'].copy()
        df['arm'] = arm
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)

    plot_grouped_bar(combined, RESULTS_FIGURES_DIR / 'ood_exposure_comparison.png',
                     x_col='model', y_col='f1_mean', std_col='f1_std',
                     group_col='arm',
                     x_label='Model', y_label='Macro-F1 on extended OOD test set',
                     title='OOD performance: main-only training vs extended exposure',
                     y_lim=(0.5, 1.0), figsize=(9, 5), x_rotation=15)


if __name__ == '__main__':
    main()
