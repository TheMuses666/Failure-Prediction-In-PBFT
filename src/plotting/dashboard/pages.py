from __future__ import annotations

import pandas as pd
import streamlit as st

from config import FEATURE_COLUMNS_EXTEND
from .data import (
    FIGURE_SECTIONS,
    FIGURES_DIR,
    TABLES_DIR,
    available_datasets,
    best_metric,
    dataset,
    fault_counts_by_dataset,
    label_counts_by_dataset,
    metric_options,
    table,
)
from .ui import (
    bar_chart,
    compact_number,
    confusion_heatmap,
    correlation_heatmap,
    fault_composition_chart,
    feature_boxplot,
    label_name,
    line_chart,
    metric_row,
    show_figure,
    show_missing,
    show_note,
)

def page_overview() -> None:
    datasets = available_datasets()
    figures = list(FIGURES_DIR.glob("*.png")) if FIGURES_DIR.exists() else []
    tables = list(TABLES_DIR.glob("*.csv")) if TABLES_DIR.exists() else []
    main_df = dataset("consensus_data.csv")
    tuned = table("model_metrics_tuned.csv")
    default_13 = table("model_metrics_default_13.csv")
    best = best_metric(tuned)
    best_default_13 = best_metric(default_13)

    st.markdown(
        """
        <div class="hero">
            <h1>PBFT Failure Prediction Dashboard</h1>
            <div class="caption">
            A compact research console for inspecting deterministic PBFT fault-injection datasets,
            early degradation prediction results, scale generalisation, ablations, and neural extensions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_row([
        ("Datasets", str(len(datasets)), "CSV datasets found in data/raw"),
        ("Result tables", str(len(tables)), "CSV summaries found in results/tables"),
        ("Figures", str(len(figures)), "PNG figures found in results/figures"),
        ("Main rows", compact_number(len(main_df)) if main_df is not None else "0", "Rows in consensus_data.csv"),
    ])

    if best:
        st.markdown("### Current headline")
        headline = (
            f"Best tuned macro-F1 in the tuned 11-feature result table: {best[0]} at {best[1]:.3f}."
        )
        if best_default_13:
            headline += (
                f" The 13-feature default result is a separate comparison: "
                f"{best_default_13[0]} at {best_default_13[1]:.3f}."
            )
        headline += " Open the sidebar navigation to inspect the evidence behind each claim."
        show_note(headline)

    st.markdown("### Research question")
    st.write(
        "Can round-level observable features predict PBFT consensus degradation "
        "and failure earlier, and more reliably, than static threshold or rule-based monitors?"
    )

    st.markdown("### Result map")
    cols = st.columns(3)
    cols[0].markdown("**Detection**\n\nML vs static baselines, per-class F1, confusion matrices.")
    cols[1].markdown("**Early warning**\n\nLead-time cutoffs, false alarms, next-round BiLSTM prediction.")
    cols[2].markdown("**Generalisation**\n\nScale shift, robustness, OOD faults, mixed-N exposure, GNN.")

    st.markdown("### Deployment cost")
    show_note(
        "Every monitor predicts in well under a millisecond per round; "
        "the linear and tree monitors are even cheaper than the pandas-based static rules. "
        "Static report figures are available in the Figures page."
    )

def page_dataset() -> None:
    st.title("Dataset")
    datasets = available_datasets()
    if not datasets:
        show_missing("data/raw/*.csv", "python -m scripts.data_generation.main_dataset")
        return

    labels = label_counts_by_dataset(datasets)
    faults = fault_counts_by_dataset(datasets)

    metric_row([
        ("Loaded datasets", str(len(datasets)), None),
        ("Total CSV rows", compact_number(sum(len(df) for df in datasets.values())), None),
        ("Main labels", str(datasets.get("Main consensus", pd.DataFrame()).get("label", pd.Series(dtype=int)).nunique()), None),
        ("Fault views", str(faults["fault"].nunique()) if not faults.empty else "0", None),
    ])

    tabs = st.tabs(["Composition", "Feature Evidence", "Raw Tables"])
    with tabs[0]:
        show_note("Use these charts to explain what the experiments are trained and evaluated on.")
        if not labels.empty:
            st.subheader("Label distribution")
            selected_labels = st.multiselect(
                "Labels",
                sorted(labels["label"].unique()),
                default=sorted(labels["label"].unique()),
                key="dataset-label-filter",
            )
            label_view = labels[labels["label"].isin(selected_labels)]
            bar_chart(
                label_view,
                "dataset",
                "count",
                "label",
                "Label distribution by dataset",
                height=520,
            )
            st.dataframe(labels, width="stretch")
        if not faults.empty:
            st.subheader("Fault composition")
            dataset_filter = st.multiselect(
                "Datasets for fault composition",
                sorted(faults["dataset"].unique()),
                default=sorted(faults["dataset"].unique())[:4],
                key="fault-dataset-filter",
            )
            fault_view = faults[faults["dataset"].isin(dataset_filter)]
            fault_composition_chart(fault_view)

    with tabs[1]:
        main_df = datasets.get("Main consensus")
        if main_df is None:
            show_missing("consensus_data.csv")
        else:
            available_features = [
                feature for feature in FEATURE_COLUMNS_EXTEND if feature in main_df.columns
            ]
            show_note(
                "These views are calculated directly from the main dataset. "
                "Use the distribution view to inspect class separation and the heatmap to spot redundant signals."
            )
            feature = st.selectbox(
                "Feature distribution",
                available_features,
                index=available_features.index("quorum_margin")
                if "quorum_margin" in available_features else 0,
                key="dataset-feature-distribution",
            )
            feature_boxplot(
                main_df,
                feature,
                title=f"{feature.replace('_', ' ').title()} by outcome label",
            )

            correlation_features = st.multiselect(
                "Correlation features",
                available_features,
                default=available_features[:8],
                max_selections=10,
                key="dataset-correlation-features",
            )
            if len(correlation_features) >= 2:
                correlation_heatmap(
                    main_df,
                    correlation_features,
                    "Feature correlation matrix",
                )
            else:
                show_note("Select at least two features to draw the correlation matrix.")

    with tabs[2]:
        selected = st.selectbox("Dataset", list(datasets.keys()))
        df = datasets[selected]
        st.dataframe(df.head(200), width="stretch")

def page_main_results() -> None:
    st.title("Main Results")
    tuned = table("model_metrics_tuned.csv")
    default = table("model_metrics_default_multiseed.csv")
    if default is None:
        default = table("model_metrics_default_13.csv")
    baseline = table("baseline_metrics_multiseed.csv")
    per_class = table("per_class_report.csv")
    confusion = table("ood_confusion.csv")

    if tuned is None and default is None:
        show_missing("main model metrics", "python -m scripts.training.default")
        return

    tuned_col, baseline_col = st.columns(2, gap="large")
    with tuned_col:
        st.subheader("Tuned models")
        if tuned is not None:
            metrics = metric_options(tuned, ["accuracy_mean", "precision_mean", "recall_mean", "f1_mean"])
            if metrics:
                metric = st.selectbox("Tuned metric", metrics, index=min(3, len(metrics) - 1))
                bar_chart(tuned, "model", metric, "model", title=f"Tuned models by {metric}", y_domain=[0, 1.0])
            st.dataframe(tuned, width="stretch")
        else:
            show_missing("model_metrics_tuned.csv")

    with baseline_col:
        st.subheader("Static baselines")
        if baseline is not None:
            metrics = metric_options(baseline, ["accuracy_mean", "precision_mean", "recall_mean", "f1_mean"])
            if metrics:
                metric = st.selectbox("Baseline metric", metrics, index=min(3, len(metrics) - 1))
                bar_chart(
                    baseline,
                    "model",
                    metric,
                    "model",
                    title=f"Static baselines by {metric}",
                    y_domain=[0, 1.0],
                )
            st.dataframe(baseline, width="stretch")
        else:
            show_missing("baseline_metrics_multiseed.csv")

    st.subheader("Per-class evidence")
    if per_class is not None and {"model", "class", "f1"}.issubset(per_class.columns):
        per_class_view = per_class[~per_class["class"].astype(str).str.contains("avg", case=False)].copy()
        per_class_view["class_name"] = per_class_view["class"].map(label_name)
        per_class_view = (
            per_class_view.groupby(["model", "class_name"], as_index=False)
            .agg(f1_mean=("f1", "mean"))
        )
        models = st.multiselect(
            "Per-class models",
            sorted(per_class_view["model"].unique()),
            default=sorted(per_class_view["model"].unique()),
            key="main-per-class-models",
        )
        bar_chart(
            per_class_view[per_class_view["model"].isin(models)],
            "class_name",
            "f1_mean",
            "model",
            "Per-class F1",
            y_domain=[0, 1.0],
        )
    else:
        show_missing("per_class_report.csv")

    st.subheader("Confusion matrix")
    if confusion is not None:
        conf_view = confusion.copy()
        if "distribution" in conf_view.columns:
            conf_view = conf_view[conf_view["distribution"] == "in_dist"]
        models = sorted(conf_view["model"].unique()) if "model" in conf_view.columns else []
        if models:
            model = st.selectbox("Confusion model", models, index=models.index("xgboost") if "xgboost" in models else 0)
            confusion_heatmap(conf_view[conf_view["model"] == model], f"In-distribution confusion matrix: {model}")
        else:
            show_missing("confusion matrix rows")
    else:
        show_missing("ood_confusion.csv")

def page_early_prediction() -> None:
    st.title("Early Prediction")
    show_note(
        "This page separates within-round lead-time experiments from temporal next-round prediction."
    )
    f1_cutoff = table("lead_time_f1_by_cutoff.csv")
    detection = table("early_detection_rate_by_cutoff.csv")
    false_alarm = table("lead_time_false_alarm.csv")
    summary = table("lead_time_summary.csv")

    tabs = st.tabs(["Cutoff Curves", "Lead Time", "Tables"])
    with tabs[0]:
        st.subheader("Macro-F1 by cutoff")
        if f1_cutoff is not None:
            models = st.multiselect(
                "Models",
                sorted(f1_cutoff["model"].unique()),
                default=sorted(f1_cutoff["model"].unique()),
                key="lead-time-f1-models",
            )
            line_chart(
                f1_cutoff[f1_cutoff["model"].isin(models)],
                "cutoff",
                "f1_mean",
                "model",
                "Macro-F1 by prediction cutoff",
            )

        st.subheader("Detection rate by cutoff")
        if detection is not None:
            y_col = "detection_rate_mean"
            if y_col in detection.columns:
                models = st.multiselect(
                    "Detection models",
                    sorted(detection["model"].unique()),
                    default=sorted(detection["model"].unique()),
                    key="lead-time-detection-models",
                )
                line_chart(
                    detection[detection["model"].isin(models)],
                    "cutoff",
                    y_col,
                    "model",
                    "Early degraded/failure detection rate",
                )

    with tabs[1]:
        if summary is not None:
            st.subheader("Lead time by fault type")
            models = st.multiselect(
                "Lead-time models",
                sorted(summary["model"].unique()),
                default=sorted(summary["model"].unique()),
                key="lead-time-summary-models",
            )
            summary_view = summary[summary["model"].isin(models)]
            bar_chart(
                summary_view,
                "fault_type",
                "lead_time_ms_mean",
                "model",
                "Mean lead time by fault type",
            )

        if false_alarm is not None:
            st.subheader("False alarm rate by cutoff")
            models = st.multiselect(
                "False-alarm models",
                sorted(false_alarm["model"].unique()),
                default=sorted(false_alarm["model"].unique()),
                key="lead-time-false-alarm-models",
            )
            false_alarm_view = false_alarm[false_alarm["model"].isin(models)]
            line_chart(
                false_alarm_view,
                "cutoff",
                "false_alarm_rate_mean",
                "model",
                "False alarm rate by cutoff",
            )

        if summary is not None:
            st.dataframe(summary, width="stretch")

    with tabs[2]:
        for name, df in {
            "lead_time_f1_by_cutoff.csv": f1_cutoff,
            "early_detection_rate_by_cutoff.csv": detection,
            "lead_time_false_alarm.csv": false_alarm,
            "lead_time_summary.csv": summary,
        }.items():
            st.subheader(name)
            if df is not None:
                st.dataframe(df, width="stretch")
            else:
                show_missing(name)

def page_generalisation() -> None:
    st.title("Generalisation")
    tabs = st.tabs(["Scale", "OOD", "Robustness", "Mixed-N"])
    with tabs[0]:
        scal = table("scalability_curve.csv")
        if scal is not None:
            models = st.multiselect(
                "Scale models",
                sorted(scal["model"].unique()),
                default=sorted(scal["model"].unique()),
                key="scale-models",
            )
            line_chart(
                scal[scal["model"].isin(models)],
                "N",
                "f1_mean",
                "model",
                "Macro-F1 under network-size shift",
            )
            st.dataframe(scal, width="stretch")

    with tabs[1]:
        ood = table("ood_f1.csv")
        ext = table("ood_f1_trainext.csv")
        subtype = table("ood_per_subtype.csv")
        if ood is not None:
            st.subheader("Main-only OOD")
            models = st.multiselect(
                "Main-only OOD models",
                sorted(ood["model"].unique()),
                default=sorted(ood["model"].unique()),
                key="ood-main-models",
            )
            bar_chart(
                ood[ood["model"].isin(models)],
                "model",
                "f1_mean",
                "distribution",
                "Main-only training: in-distribution vs OOD F1",
                y_domain=[0, 1.0],
            )
            st.dataframe(ood, width="stretch")
        if ext is not None:
            st.subheader("Extended-exposure OOD")
            models = st.multiselect(
                "Extended-exposure OOD models",
                sorted(ext["model"].unique()),
                default=sorted(ext["model"].unique()),
                key="ood-extended-models",
            )
            bar_chart(
                ext[ext["model"].isin(models)],
                "model",
                "f1_mean",
                "distribution",
                "Extended exposure: in-distribution vs OOD F1",
                y_domain=[0, 1.0],
            )
            st.dataframe(ext, width="stretch")
        if subtype is not None:
            st.subheader("OOD subtype detection")
            models = st.multiselect(
                "Subtype models",
                sorted(subtype["model"].unique()),
                default=sorted(subtype["model"].unique()),
                key="ood-subtype-models",
            )
            subtype_view = subtype[subtype["model"].isin(models)]
            bar_chart(
                subtype_view,
                "fault_type",
                "detection_rate_mean",
                "model",
                "Detection rate by advanced-fault subtype",
                y_domain=[0, 1.0],
            )
            st.dataframe(subtype, width="stretch")

    with tabs[2]:
        rob = table("robustness_curve.csv")
        if rob is not None:
            line_chart(rob, "f", "f1_mean", "model", "Macro-F1 under Byzantine-count shift")
            st.dataframe(rob, width="stretch")

    with tabs[3]:
        mixed = table("mixed_n_curve.csv")
        if mixed is not None:
            mixed = mixed.copy()
            mixed["series"] = mixed["model"] + " (" + mixed["arms"] + ")"
            arms = st.multiselect(
                "Training arms",
                sorted(mixed["arms"].unique()),
                default=sorted(mixed["arms"].unique()),
            )
            mixed_view = mixed[mixed["arms"].isin(arms)]
            line_chart(mixed_view, "N", "f1_mean", "series", "Mixed-N exposure effect")
            st.dataframe(mixed, width="stretch")

def page_ablations() -> None:
    st.title("Ablations")
    tabs = st.tabs(["Feature and Tuning", "Security Assumptions", "Tables"])
    with tabs[0]:
        df = table("ablation_feature_set.csv")
        if df is not None:
            # wide table (f1_mean_<feature_set> columns) -> long form
            mean_cols = [col for col in df.columns if col.startswith("f1_mean_")]
            if mean_cols and "model" in df.columns:
                long_df = df.melt(
                    id_vars=["model"], value_vars=mean_cols,
                    var_name="feature_set", value_name="f1_mean",
                )
                long_df["feature_set"] = long_df["feature_set"].str.removeprefix("f1_mean_")
                bar_chart(long_df, "feature_set", "f1_mean", "model",
                          "Feature-set ablation (macro-F1)")
            st.dataframe(df, width="stretch")

        df = table("ablation_tuning.csv")
        if df is not None:
            # wide table (default_f1_mean / tuned_f1_mean) -> long form
            arm_cols = [col for col in ("default_f1_mean", "tuned_f1_mean")
                        if col in df.columns]
            if arm_cols and "model" in df.columns:
                long_df = df.melt(
                    id_vars=["model"], value_vars=arm_cols,
                    var_name="setting", value_name="f1_mean",
                )
                long_df["setting"] = long_df["setting"].str.removesuffix("_f1_mean")
                bar_chart(long_df, "model", "f1_mean", "setting",
                          "Default vs tuned (macro-F1)")
            st.dataframe(df, width="stretch")

    with tabs[1]:
        df = table("auth_ablation_detection.csv")
        if df is not None:
            if "fault_type" in df.columns:
                df = df.copy()
                df["intensity"] = df["fault_type"].astype(str).str.removeprefix("forgery_i").astype(float)
                line_chart(df, "intensity", "detection_rate_mean", "model", "Forgery detection by intensity")
            st.dataframe(df, width="stretch")

        strict_df = table("strict_ablation_detection.csv")
        if strict_df is not None:
            strict_view = strict_df.copy()
            if "fault_type" in strict_view.columns:
                strict_view["scenario"] = strict_view["fault_type"].map({
                    "replay_stale_strict_on": "strict on",
                    "replay_stale_strict_off": "strict off",
                }).fillna(strict_view["fault_type"])
                bar_chart(
                    strict_view,
                    "scenario",
                    "detection_rate_mean",
                    "model",
                    "Stale replay detection by validation setting",
                )

    with tabs[2]:
        for filename in [
            "auth_ablation.csv",
            "strict_ablation_sim.csv",
            "strict_ablation_quorum.csv",
            "strict_ablation_detection.csv",
        ]:
            st.subheader(filename)
            df = table(filename)
            if df is not None:
                st.dataframe(df, width="stretch")
            else:
                show_missing(filename)

def page_extensions() -> None:
    st.title("GNN and BiLSTM")
    tabs = st.tabs(["GNN", "BiLSTM"])
    with tabs[0]:
        gnn = table("model_metrics_gnn.csv")
        if gnn is not None:
            metric_row([
                ("GNN rows", str(len(gnn)), None),
                ("Best GNN F1", f"{gnn['f1_mean'].max():.3f}" if "f1_mean" in gnn else "-", None),
                ("Test sets", str(gnn["test_set"].nunique()) if "test_set" in gnn else "-", None),
            ])
            if "test_set" in gnn.columns and "f1_mean" in gnn.columns:
                gnn_view = gnn.copy()
                gnn_view["N"] = gnn_view["test_set"].map({"n7_test": 7, "n10": 10, "n13": 13})
                if gnn_view["N"].notna().any():
                    line_chart(gnn_view.dropna(subset=["N"]), "N", "f1_mean", "model", "GNN scale generalisation")
                else:
                    bar_chart(gnn_view, "test_set", "f1_mean", "model", "GNN test-set F1")
            st.dataframe(gnn, width="stretch")

    with tabs[1]:
        bilstm = table("model_metrics_bilstm.csv")
        if bilstm is not None:
            metric_row([
                ("BiLSTM rows", str(len(bilstm)), None),
                ("Best next-round F1", f"{bilstm[bilstm['horizon'] == 1]['f1_mean'].max():.3f}" if "horizon" in bilstm else "-", None),
                ("Windows", ", ".join(map(str, sorted(bilstm["k"].unique()))) if "k" in bilstm else "-", None),
            ])
            metrics = metric_options(bilstm, ["f1_mean", "f1_degraded_mean", "f1_failure_mean", "accuracy_mean"])
            metric = st.selectbox("BiLSTM metric", metrics, key="bilstm-metric")
            model_filter = st.multiselect(
                "BiLSTM comparison models",
                sorted(bilstm["model"].unique()),
                default=sorted(bilstm["model"].unique()),
                key="bilstm-model-filter",
            )
            bilstm_view = bilstm[bilstm["model"].isin(model_filter)].copy()
            bilstm_view["setting"] = (
                "k=" + bilstm_view["k"].astype(str)
                + ", h=" + bilstm_view["horizon"].astype(str)
            )
            bar_chart(bilstm_view, "setting", metric, "model", f"Temporal model comparison by {metric}")
            st.dataframe(bilstm, width="stretch")

def page_figures() -> None:
    st.title("Figure Gallery")
    available = sorted(path.name for path in FIGURES_DIR.glob("*.png")) if FIGURES_DIR.exists() else []
    if not available:
        show_missing("results/figures/*.png")
        return

    section = st.selectbox("Section", list(FIGURE_SECTIONS.keys()) + ["All figures"])
    if section == "All figures":
        chosen = st.multiselect("Figures", available, default=available[:4])
    else:
        defaults = [name for name in FIGURE_SECTIONS[section] if name in available]
        chosen = st.multiselect("Figures", available, default=defaults)

    for filename in chosen:
        show_figure(filename)
