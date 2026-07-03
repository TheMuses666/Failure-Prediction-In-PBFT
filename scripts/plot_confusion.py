import pandas as pd
from config import RESULTS_TABLES_DIR, RESULTS_FIGURES_DIR, LABEL_NAMES
from src.plotting.plots import plot_confusion_heatmap

def main():
    df = pd.read_csv(RESULTS_TABLES_DIR / 'ood_confusion.csv')
    label_names = [LABEL_NAMES[i] for i in [0, 1, 2]]
    for model in df['model'].unique():
        plot_confusion_heatmap(
            df[df['model'] == model],
            RESULTS_FIGURES_DIR / f'confusion_matrix_{model}.png',
            label_names, title=model)

if __name__ == '__main__':
    main()