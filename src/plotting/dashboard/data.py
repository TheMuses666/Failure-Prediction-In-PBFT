from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from config import DATA_RAW_DIR as DATA_DIR
from config import LABEL_NAMES, RESULTS_FIGURES_DIR as FIGURES_DIR
from config import RESULTS_TABLES_DIR as TABLES_DIR

DATASET_FILES = {
    "Main consensus": "consensus_data.csv",
    "Advanced faults": "extended_robustness.csv",
    "Scalability N=10": "scalability_n10.csv",
    "Scalability N=13": "scalability_n13.csv",
    "Mixed-N train N=10": "mixed_n_train_n10.csv",
    "Mixed-N train N=13": "mixed_n_train_n13.csv",
    "Sequence episodes": "sequence_dataset.csv",
}

FIGURE_SECTIONS = {
    "Dataset": [
        "dataset_label_distribution.png",
        "dataset_fault_composition.png",
        "label_by_fault_type.png",
        "feature_distribution_by_fault.png",
        "feature_shift_by_network_size.png",
        "feature_correlation_heatmap.png",
    ],
    "Main results": [
        "model_comparison.png",
        "baseline_vs_ml.png",
        "per_class_f1.png",
        "detection_rate_by_fault_type.png",
        "failure_recall_by_fault_type.png",
    ],
    "Early prediction": [
        "lead_time_f1_by_cutoff.png",
        "early_detection_rate_by_cutoff.png",
        "lead_time_false_alarm.png",
        "lead_time_comparison.png",
    ],
    "Generalisation": [
        "scalability_curve.png",
        "robustness_curve.png",
        "mixed_n_curve.png",
        "ood_f1_by_fault_subtype.png",
        "ood_exposure_comparison.png",
    ],
    "Ablations": [
        "feature_ablation.png",
        "tuning_ablation.png",
        "auth_ablation_detection.png",
        "strict_ablation_detection.png",
        "strict_ablation_quorum.png",
    ],
    "Extensions": [
        "gnn_scalability_curve.png",
        "gnn_confusion_matrix.png",
        "graph_dataset_summary.png",
        "bilstm_horizon_comparison.png",
        "bilstm_per_class_f1.png",
    ],
    "Explanatory": [
        "pbft_round_timeline.png",
        "inference_latency_comparison.png",
        "learning_curve.png",
    ],
}

FIGURE_CAPTIONS = {
    "dataset_label_distribution.png": "Dataset label distribution",
    "dataset_fault_composition.png": "Fault composition by dataset",
    "label_by_fault_type.png": "Labels by fault type",
    "feature_distribution_by_fault.png": "Feature distributions by fault type",
    "feature_shift_by_network_size.png": "Feature shift across network sizes",
    "feature_correlation_heatmap.png": "Feature correlation heatmap",
    "model_comparison.png": "Model comparison",
    "baseline_vs_ml.png": "Static baselines vs ML models",
    "per_class_f1.png": "Per-class F1 score",
    "detection_rate_by_fault_type.png": "Detection rate by fault type",
    "failure_recall_by_fault_type.png": "Failure recall by fault type",
    "lead_time_f1_by_cutoff.png": "Lead-time F1 by prediction cutoff",
    "early_detection_rate_by_cutoff.png": "Early detection rate by cutoff",
    "lead_time_false_alarm.png": "Lead-time false alarm rate",
    "lead_time_comparison.png": "Lead-time comparison",
    "scalability_curve.png": "Scalability curve",
    "robustness_curve.png": "Robustness under Byzantine-count shift",
    "mixed_n_curve.png": "Mixed-N training exposure",
    "ood_f1_by_fault_subtype.png": "OOD F1 by fault subtype",
    "ood_exposure_comparison.png": "OOD exposure comparison",
    "feature_ablation.png": "Feature-set ablation",
    "tuning_ablation.png": "Tuning ablation",
    "auth_ablation_detection.png": "Authentication ablation detection",
    "strict_ablation_detection.png": "Strict validation detection",
    "strict_ablation_quorum.png": "Strict validation quorum effect",
    "gnn_scalability_curve.png": "GNN scalability curve",
    "gnn_confusion_matrix.png": "GNN confusion matrix",
    "graph_dataset_summary.png": "Graph dataset summary",
    "bilstm_horizon_comparison.png": "BiLSTM horizon comparison",
    "bilstm_per_class_f1.png": "BiLSTM per-class F1",
    "pbft_round_timeline.png": "PBFT round timeline",
    "inference_latency_comparison.png": "Inference latency comparison",
    "learning_curve.png": "Learning curve",
}
def _read_csv_cached(path_str: str, mtime: float) -> pd.DataFrame:
    return pd.read_csv(path_str)

def read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    # mtime participates in the cache key so regenerated CSVs are picked up
    # without restarting the app
    return _read_csv_cached(str(path), path.stat().st_mtime)

def table(name: str) -> pd.DataFrame | None:
    return read_csv(TABLES_DIR / name)

def dataset(name: str) -> pd.DataFrame | None:
    return read_csv(DATA_DIR / name)

def available_datasets() -> dict[str, pd.DataFrame]:
    loaded = {}
    for label, filename in DATASET_FILES.items():
        df = dataset(filename)
        if df is not None:
            loaded[label] = df
    return loaded

def figure_caption(filename: str) -> str:
    return FIGURE_CAPTIONS.get(filename, Path(filename).stem.replace("_", " ").title())

def label_counts_by_dataset(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in datasets.items():
        if "label" not in df.columns:
            continue
        counts = df["label"].map(LABEL_NAMES).value_counts()
        for label, count in counts.items():
            rows.append({"dataset": name, "label": label, "count": int(count)})
    return pd.DataFrame(rows)

def fault_counts_by_dataset(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in datasets.items():
        col = "fault_subtype" if "fault_subtype" in df.columns else "fault_type"
        if col not in df.columns:
            continue
        counts = df[col].fillna("unknown").value_counts()
        for fault, count in counts.items():
            rows.append({"dataset": name, "fault": str(fault), "count": int(count)})
    return pd.DataFrame(rows)

def best_metric(df: pd.DataFrame | None, metric_col: str = "f1_mean") -> tuple[str, float] | None:
    if df is None or metric_col not in df.columns or "model" not in df.columns or df.empty:
        return None
    row = df.sort_values(metric_col, ascending=False).iloc[0]
    return str(row["model"]), float(row[metric_col])

def metric_options(df: pd.DataFrame, preferred: list[str]) -> list[str]:
    options = [col for col in preferred if col in df.columns]
    if options:
        return options
    return list(df.select_dtypes(include="number").columns)
