import pandas as pd
from config import DATA_RAW_DIR, RESULTS_FIGURES_DIR, LABEL_NAMES
from src.plotting.plots import plot_grouped_bar

DATASETS = {
    'main': 'consensus_data.csv',
    'extended': 'extended_robustness.csv',
    'scal_n10': 'scalability_n10.csv',
    'scal_n13': 'scalability_n13.csv',
    'mixed_n10': 'mixed_n_train_n10.csv',
    'mixed_n13': 'mixed_n_train_n13.csv',
}


def load_datasets():
    return {name: pd.read_csv(DATA_RAW_DIR / fname)
            for name, fname in DATASETS.items()}


def plot_label_distribution(datasets):
    rows = []
    for name, df in datasets.items():
        for label_value, count in df['label'].value_counts().items():
            rows.append({'dataset': name,
                         'label': LABEL_NAMES[label_value],
                         'count': count})

    plot_grouped_bar(pd.DataFrame(rows),
                     RESULTS_FIGURES_DIR / 'dataset_label_distribution.png',
                     x_col='dataset', y_col='count', std_col=None,
                     group_col='label',
                     x_label='Dataset', y_label='Rounds',
                     title='Label distribution across datasets')


def plot_fault_composition(datasets):
    rows = []
    for name, df in datasets.items():
        fault = df['fault_subtype'].where(df['fault_subtype'] != 'base',
                                          df['fault_type'])
        for fault_name, count in fault.value_counts().items():
            rows.append({'dataset': name, 'fault': fault_name, 'count': count})

    plot_grouped_bar(pd.DataFrame(rows),
                     RESULTS_FIGURES_DIR / 'dataset_fault_composition.png',
                     x_col='fault', y_col='count', std_col=None,
                     group_col='dataset',
                     x_label='Fault type / subtype', y_label='Rounds',
                     title='Fault composition across datasets',
                     figsize=(14, 5), x_rotation=30)


def plot_label_by_fault(datasets):
    rows = []
    counts = datasets['main'].groupby(['fault_type', 'label']).size()
    for (fault_name, label_value), count in counts.items():
        rows.append({'fault_type': fault_name,
                     'label': LABEL_NAMES[label_value],
                     'count': count})

    plot_grouped_bar(pd.DataFrame(rows),
                     RESULTS_FIGURES_DIR / 'label_by_fault_type.png',
                     x_col='fault_type', y_col='count', std_col=None,
                     group_col='label',
                     x_label='Fault type', y_label='Rounds',
                     title='Label distribution within each fault type (main dataset)')


def main():
    datasets = load_datasets()
    plot_label_distribution(datasets)
    plot_fault_composition(datasets)
    plot_label_by_fault(datasets)


if __name__ == '__main__':
    main()
