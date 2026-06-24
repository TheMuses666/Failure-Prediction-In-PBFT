import matplotlib.pyplot as plt
import seaborn as sns
import math
import numpy as np
import pandas as pd

def plot_feature_distribution_by_group(df, feature_cols, group_cols, out_path, title=None):

    n_features = len(feature_cols)
    n_cols = 4
    n_rows = math.ceil(n_features / n_cols)

    fig, axes = plt.subplots(n_rows,n_cols, figsize = (n_cols*4, n_rows*3))
    axes = axes.flatten()

    for i, feature in enumerate(feature_cols):
        sns.boxplot(data=df, x=group_cols, y=feature, ax=axes[i])
        axes[i].set_title(feature, fontsize = 12)
        axes[i].set_xlabel('')
        axes[i].tick_params(axis = 'x',rotation=30)

    for j in range(n_features, len(axes)):
        axes[j].set_visible(False)

    if title:
        fig.suptitle(title, fontsize = 16)

    fig.tight_layout()
    out_path.parent.mkdir(parents = True, exist_ok = True)
    fig.savefig(out_path, dpi=150, bbox_inches = 'tight')
    plt.close(fig)
    print(f'Figure saved --> {out_path}')


def plot_variance_comparison(df, feature_cols, comparisons, out_path, title = None):
    n_feature = len(feature_cols)
    n_comparisons = len(comparisons)

    fig, axes = plt.subplots(n_comparisons, 1, figsize=(12, n_comparisons * 4))
    if n_comparisons == 1:
        axes = [axes]


    for i, (base, advanced, label) in enumerate(comparisons):
        base_std = df[df['fault_subtype'] == base][feature_cols].std()
        adv_std = df[df['fault_subtype'] == advanced][feature_cols].std()

        x = np.arange(n_feature)
        width = 0.35

        axes[i].bar(x - width/2, base_std, width, label=base)
        axes[i].bar(x + width/2, adv_std,  width, label=advanced)
        axes[i].set_xticks(x)
        axes[i].set_xticklabels(feature_cols, rotation=45, ha='right', fontsize=9)
        axes[i].set_ylabel('Std')
        axes[i].set_title(label)
        axes[i].legend()

    if title:
        fig.suptitle(title, fontsize = 14)

    fig.tight_layout()
    out_path.parent.mkdir(parents = True, exist_ok = True)
    fig.savefig(out_path, dpi = 150, bbox_inches = 'tight')
    plt.close(fig)
    print(f'Figure Saved --> {out_path}')

