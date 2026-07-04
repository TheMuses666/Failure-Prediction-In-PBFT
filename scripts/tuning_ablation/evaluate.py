import pandas as pd
from config import RESULTS_TABLES_DIR

def main():

    df_dafault = pd.read_csv(RESULTS_TABLES_DIR / 'model_metrics_default_multiseed.csv')
    df_tuned = pd.read_csv(RESULTS_TABLES_DIR / 'model_metrics_tuned.csv')

    df_dafault = df_dafault.add_prefix('default_').rename(columns={'default_model': 'model'})
    df_tuned = df_tuned.add_prefix('tuned_').rename(columns={'tuned_model':'model'})

    df_merged = df_dafault.merge(df_tuned, on='model')
    df_merged['delta_f1_mean'] = df_merged['tuned_f1_mean'] - df_merged['default_f1_mean']
    df_merged['delta_acc_mean'] = df_merged['tuned_accuracy_mean'] - df_merged['default_accuracy_mean']

    cols = ['model', 'default_f1_mean', 'default_f1_std',
        'tuned_f1_mean', 'tuned_f1_std', 'delta_f1_mean',
        'default_accuracy_mean', 'tuned_accuracy_mean', 'delta_acc_mean']

    df_save = df_merged[cols].sort_values('delta_f1_mean', ascending=False)

    df_save.to_csv(RESULTS_TABLES_DIR / 'ablation_tuning.csv', index=False)
    print(f'---- Ablation Tuning CSV Saved to {RESULTS_TABLES_DIR} ----')
    print(df_save.to_string(index=False))


if __name__ == '__main__':
    main()