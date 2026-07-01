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


def plot_grouped_curve(
    df,               
    out_path,         
    x_col,              
    y_col,                
    std_col,               
    group_col,            
    x_label,             
    y_label,              
    title=None,
    vline_x=None,         
    vline_label=None,      
    x_ticks=None,         
    y_lim=(0.5, 1.0),
    markers=None,         
):
    fig, ax = plt.subplots(figsize=(7, 5))
    
    for group_name in df[group_col].unique():
        sub = df[df[group_col] == group_name].sort_values(x_col)
        
        m = markers[group_name] if markers else 'o'
        line, = ax.plot(sub[x_col], sub[y_col], marker=m, label=group_name)
        
        ax.fill_between(
            sub[x_col],
            sub[y_col] - sub[std_col],
            sub[y_col] + sub[std_col],
            alpha=0.2,
            color=line.get_color(),   
        )
    
    if vline_x is not None:
        ax.axvline(x=vline_x, color='red', linestyle='--', alpha=0.5)
        if vline_label:
            ax.text(vline_x + 0.05, y_lim[0] + 0.35, vline_label,
                    color='red', fontsize=9)
    
    if x_ticks:
        ax.set_xticks(x_ticks)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_ylim(y_lim)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower left')
    if title:
        ax.set_title(title)
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Figure saved --> {out_path}')


def plot_grouped_bar(
    df, out_path,
    x_col,           # e.g. 'fault_type'
    y_col,           # e.g. 'detection_rate_mean'
    std_col,         # e.g. 'detection_rate_std'
    group_col,       # e.g. 'model'
    x_label,
    y_label,
    title=None,
    y_lim=None,
    figsize=(9, 5),
):

    import numpy as np
    
    df_plot = df.dropna(subset=[y_col]).copy()
    
    x_categories = sorted(df_plot[x_col].unique())
    groups = sorted(df_plot[group_col].unique())
    
    n_groups = len(groups)
    bar_width = 0.8 / n_groups
    x_positions = np.arange(len(x_categories))
    
    fig, ax = plt.subplots(figsize=figsize)
    
    for i, group_name in enumerate(groups):
        offsets = x_positions + (i - n_groups/2 + 0.5) * bar_width
        
        # 从 df 拿该 group 每个 x 的值
        means, stds = [], []
        for xc in x_categories:
            row = df_plot[(df_plot[group_col] == group_name) & (df_plot[x_col] == xc)]
            if len(row) == 0:
                means.append(np.nan)
                stds.append(0)
            else:
                means.append(row[y_col].values[0])
                stds.append(row[std_col].values[0] if std_col else 0)
        
        ax.bar(offsets, means, bar_width, yerr=stds, label=group_name,
               capsize=3, alpha=0.85)
    
    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_categories, rotation=0)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if y_lim:
        ax.set_ylim(y_lim)
    if title:
        ax.set_title(title)
    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3, axis='y')
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Figure saved --> {out_path}')