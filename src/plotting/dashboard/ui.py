from __future__ import annotations

from io import BytesIO

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

from config import CHART_COLORS, DASHBOARD_PALETTE as PALETTE, LABEL_NAMES
from .data import FIGURES_DIR, figure_caption

# Single source of truth for figure geometry: every Altair chart and every
# PNG card reads from here, so spacing stays uniform across the whole app.
CHART_SPEC = {
    "height": 380,
    "padding": {"top": 36, "right": 34, "bottom": 42, "left": 46},
}

def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --primary: {PALETTE["primary"]};
            --text: {PALETTE["text"]};
            --warm: {PALETTE["warm"]};
            --soft: {PALETTE["soft"]};
            --line: {PALETTE["line"]};
            --muted: {PALETTE["muted"]};
            --sidebar: {PALETTE["sidebar"]};
            --paper: {PALETTE["paper"]};
        }}

        .stApp {{
            background: var(--primary);
            color: var(--text);
        }}

        [data-testid="stHeader"] {{
            background: var(--primary);
            border-bottom: 1px solid var(--line);
        }}

        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {{
            display: flex;
            visibility: visible;
        }}

        [data-testid="stHeader"] [data-testid="stBaseButton-headerNoPadding"] {{
            display: inline-flex;
            visibility: visible;
            opacity: 1;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            margin: 0.75rem;
            background: var(--soft);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(68, 68, 68, 0.06);
            z-index: 999999;
        }}

        [data-testid="stHeader"] [data-testid="stBaseButton-headerNoPadding"]:hover {{
            background: var(--warm);
            border-color: var(--muted);
        }}

        [data-testid="stHeader"] [data-testid="stBaseButton-headerNoPadding"] svg {{
            color: var(--text);
            opacity: 0.88;
        }}

        .block-container {{
            max-width: 1280px;
            margin: 0 auto;
            padding-top: 2rem;
        }}

        [data-testid="stSidebar"] {{
            background: var(--sidebar);
            border-right: 1px solid var(--line);
        }}

        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 1rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }}

        [data-testid="stSidebar"] * {{
            color: var(--text);
        }}

        .sidebar-section {{
            font-size: 0.72rem;
            font-weight: 600;
            opacity: 0.76;
            margin: 0.4rem 0 0.35rem;
        }}

        .sidebar-footnote {{
            border-top: 1px solid var(--line);
            margin-top: 1.25rem;
            padding-top: 1rem;
            font-size: 0.76rem;
            line-height: 1.45;
            opacity: 0.74;
        }}

        [data-testid="stSidebar"] [data-testid="stRadio"] > label {{
            display: none;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] {{
            gap: 0.12rem;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label {{
            min-height: 2rem;
            border-radius: 6px;
            padding: 0.18rem 0.45rem;
            margin: 0.04rem 0;
            transition: background 120ms ease, border-color 120ms ease;
            border: 1px solid transparent;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba(236, 236, 234, 0.72);
            border-color: var(--line);
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
            background: var(--primary);
            border-color: var(--line);
            box-shadow: 0 1px 2px rgba(68, 68, 68, 0.05);
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{
            display: none;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label p {{
            font-size: 0.84rem;
            font-weight: 500;
            opacity: 0.72;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {{
            opacity: 1;
            font-weight: 650;
        }}

        h1, h2, h3, h4, h5, p, span, label, div {{
            color: var(--text);
        }}

        h1 {{
            font-size: 2.1rem;
            letter-spacing: 0;
            margin-bottom: 0.25rem;
        }}

        h2 {{
            border-bottom: 1px solid var(--line);
            padding-bottom: 0.45rem;
            margin-top: 1.8rem;
        }}

        div[data-testid="stMetric"] {{
            background: var(--soft);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1rem 0.8rem;
        }}

        div[data-testid="stMetric"] label {{
            color: var(--text);
            opacity: 0.78;
        }}

        div[data-testid="stMetricValue"] {{
            color: var(--text);
        }}

        .hero {{
            background: linear-gradient(180deg, var(--soft), var(--primary));
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.3rem 1.4rem;
            margin-bottom: 1rem;
        }}

        .hero .caption {{
            color: var(--text);
            opacity: 0.76;
            font-size: 0.98rem;
            line-height: 1.55;
            max-width: 960px;
        }}

        .section-note {{
            background: var(--warm);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin: 0.5rem 0 1rem;
            color: var(--text);
        }}

        .missing {{
            border: 1px dashed var(--muted);
            border-radius: 8px;
            padding: 1rem;
            background: var(--soft);
            color: var(--text);
        }}

        div[data-testid="stSelectbox"] > div,
        div[data-testid="stMultiSelect"] > div {{
            background: var(--primary);
            border-color: var(--line);
        }}

        div[data-baseweb="select"] > div {{
            background: var(--primary);
            border-color: var(--line);
            box-shadow: none;
        }}

        span[data-baseweb="tag"],
        div[data-baseweb="tag"] {{
            background: var(--line);
            color: var(--text);
            border: 1px solid var(--muted);
            border-radius: 6px;
        }}

        span[data-baseweb="tag"] span,
        div[data-baseweb="tag"] span {{
            color: var(--text);
        }}

        [data-testid="stVegaLiteChart"],
        [data-testid="stImageContainer"],
        [data-testid="stDataFrame"] {{
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--soft);
            overflow: hidden;
            margin-bottom: 1rem;
        }}

        [data-testid="stVegaLiteChart"] {{
            border: 0;
            box-sizing: border-box;
            box-shadow: inset 0 0 0 1px var(--line);
        }}

        [data-testid="stImageContainer"] {{
            padding: 1rem;
            /* matplotlib PNGs are rendered on white paper; a white card
               makes the figure blend instead of floating as a white patch */
            background: var(--paper);
        }}

        [data-testid="stDataFrame"] div {{
            color: var(--text);
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.35rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            background: var(--soft);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.45rem 0.9rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_missing(label: str, command: str | None = None) -> None:
    detail = f"<br><code>{command}</code>" if command else ""
    st.markdown(
        f'<div class="missing">Missing <strong>{label}</strong>.{detail}</div>',
        unsafe_allow_html=True,
    )

def show_note(text: str) -> None:
    st.markdown(f'<div class="section-note">{text}</div>', unsafe_allow_html=True)

def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[idx : idx + 2], 16) for idx in (0, 2, 4))

def padded_figure_bytes(path_str: str, mtime: float, padding: int, background: str) -> bytes:
    with Image.open(path_str) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")
        canvas = Image.new(
            "RGBA",
            (image.width + padding * 2, image.height + padding * 2),
            (*hex_to_rgb(background), 255),
        )
        canvas.alpha_composite(image, (padding, padding))
        output = BytesIO()
        canvas.convert("RGB").save(output, format="PNG")
        return output.getvalue()

def show_figure(filename: str, caption: str | None = None) -> None:
    path = FIGURES_DIR / filename
    if path.exists():
        image = padded_figure_bytes(str(path), path.stat().st_mtime, 40, PALETTE["paper"])
        st.image(image, caption=caption or figure_caption(filename), width="stretch")
    else:
        show_missing(filename)

def compact_number(value: int | float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(int(value))

def metric_row(items: list[tuple[str, str, str | None]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label, value, help=help_text)

def chart_theme(chart: alt.Chart) -> alt.Chart:
    return (
        chart.properties(
            background=PALETTE["soft"],
            padding=CHART_SPEC["padding"],
            # default autosize 'pad' ADDS the configured padding outside the
            # container width, overflowing the card; 'fit' + contains='padding'
            # keeps the total canvas (padding included) inside the container
            autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        )
        .configure(
            background=PALETTE["soft"],
        )
        .configure_axis(
            labelColor=PALETTE["text"],
            titleColor=PALETTE["text"],
            gridColor=PALETTE["line"],
            domainColor=PALETTE["line"],
            tickColor=PALETTE["line"],
            labelFontSize=12,
            titleFontSize=13,
            titlePadding=12,
        )
        .configure_legend(
            labelColor=PALETTE["text"],
            titleColor=PALETTE["text"],
            orient="bottom",
            symbolStrokeWidth=0,
        )
        .configure_title(color=PALETTE["text"], anchor="start", fontSize=15, offset=22)
        .configure_view(stroke=PALETTE["line"], strokeWidth=1, fill=PALETTE["soft"])
    )

def axis_title(col: str) -> str:
    return col.replace("_", " ")

def encoded_x(df: pd.DataFrame, x: str) -> alt.X:
    dtype = df[x].dtype
    if pd.api.types.is_numeric_dtype(dtype):
        values = sorted(df[x].unique())
        # tick exactly at the measured x values instead of a dense auto grid
        axis = alt.Axis(values=values) if len(values) <= 12 else alt.Axis()
        scale = alt.Scale(nice=False)
        if values:
            low, high = float(values[0]), float(values[-1])
            span = high - low
            pad = span * 0.05 if span else 1.0
            scale = alt.Scale(domain=[low - pad, high + pad], nice=False)
        return alt.X(f"{x}:Q", title=axis_title(x), axis=axis, scale=scale)
    return alt.X(f"{x}:N", title=axis_title(x), sort=None, axis=alt.Axis(labelAngle=-25))

def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str | None = None,
) -> None:
    if df.empty or x not in df.columns or y not in df.columns:
        return

    encodings = {
        "x": encoded_x(df, x),
        # lines encode position, not length, so the domain may hug the data;
        # bars keep zero=True (they encode length)
        "y": alt.Y(f"{y}:Q", title=axis_title(y),
                   scale=alt.Scale(zero=False, nice=True)),
        "tooltip": [alt.Tooltip(col, type="nominal") for col in df.columns if col != y]
        + [alt.Tooltip(y, type="quantitative", format=".3f")],
    }
    if color and color in df.columns:
        encodings["color"] = alt.Color(
            f"{color}:N",
            scale=alt.Scale(range=CHART_COLORS),
            legend=alt.Legend(title=color),
        )

    mark_args = {
        "point": alt.OverlayMarkDef(filled=True, size=60),
        "strokeWidth": 2.5,
    }
    if not color or color not in df.columns:
        mark_args["color"] = CHART_COLORS[0]

    chart = (
        alt.Chart(df)
        .mark_line(**mark_args)
        .encode(**encodings)
        .properties(height=CHART_SPEC["height"], title=title)
    )
    st.altair_chart(chart_theme(chart), width="stretch")

def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str | None = None,
    y_domain: list[float] | None = None,
    height: int | None = None,
) -> None:
    if df.empty or x not in df.columns or y not in df.columns:
        return

    encodings = {
        "x": alt.X(f"{x}:N", title=axis_title(x), sort="-y", axis=alt.Axis(labelAngle=-25)),
        "y": alt.Y(
            f"{y}:Q",
            title=axis_title(y),
            scale=alt.Scale(domain=y_domain) if y_domain else alt.Undefined,
        ),
        "tooltip": [alt.Tooltip(col, type="nominal") for col in df.columns if col != y]
        + [alt.Tooltip(y, type="quantitative", format=",.3f")],
    }
    grouped = bool(color and color in df.columns and color != x)
    if color and color in df.columns:
        encodings["color"] = alt.Color(
            f"{color}:N",
            scale=alt.Scale(range=CHART_COLORS),
            # colouring by the x column itself: the axis already names the
            # bars, so a legend would just repeat it
            legend=alt.Legend(title=color) if grouped else None,
        )
        if grouped:
            encodings["xOffset"] = alt.XOffset(f"{color}:N")

    mark_args = {"cornerRadiusTopLeft": 3, "cornerRadiusTopRight": 3}
    if not color or color not in df.columns:
        mark_args["color"] = CHART_COLORS[0]
    mark_args["size"] = 28 if grouped else 42

    chart = (
        alt.Chart(df)
        .mark_bar(**mark_args)
        .encode(**encodings)
        .properties(height=height or CHART_SPEC["height"], title=title)
    )
    st.altair_chart(chart_theme(chart), width="stretch")

def fault_composition_chart(df: pd.DataFrame, height: int | None = None) -> None:
    required = {"dataset", "fault", "count"}
    if df.empty or not required.issubset(df.columns):
        return

    view = df.copy()
    view["dataset"] = view["dataset"].astype(str)
    view["fault"] = view["fault"].astype(str)
    fault_order = list(
        dict.fromkeys(
            [
                "normal", "silent", "delay", "replay", "equivocation",
                "forgery", "silent_prepare", "silent_commit", "silent_all",
                "delay_gaussian", "delay_lognormal", "replay_stale",
            ]
            + sorted(view["fault"].unique())
        )
    )

    chart = (
        alt.Chart(view)
        .mark_bar(size=22, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(
                "fault:N",
                title="fault",
                sort=fault_order,
                axis=alt.Axis(labelAngle=-35, labelLimit=140),
            ),
            y=alt.Y("count:Q", title="count"),
            color=alt.Color(
                "dataset:N",
                scale=alt.Scale(range=CHART_COLORS),
                legend=alt.Legend(title="dataset", orient="bottom"),
            ),
            xOffset=alt.XOffset("dataset:N"),
            tooltip=[
                alt.Tooltip("dataset:N", title="dataset"),
                alt.Tooltip("fault:N", title="fault"),
                alt.Tooltip("count:Q", title="count", format=",d"),
            ],
        )
        .properties(height=height or 380, title="Fault composition")
    )
    st.altair_chart(chart_theme(chart), width="stretch")

def label_name(value: object) -> str:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return str(value)
    return LABEL_NAMES.get(numeric, str(value))

def confusion_heatmap(df: pd.DataFrame, title: str | None = None) -> None:
    required = {"true_label", "pred_label", "count"}
    if df.empty or not required.issubset(df.columns):
        return

    view = df.copy()
    view["true"] = view["true_label"].map(label_name)
    view["predicted"] = view["pred_label"].map(label_name)
    view["text_color"] = view["count"].apply(
        lambda count: PALETTE["primary"] if count > view["count"].max() * 0.55 else PALETTE["text"]
    )
    label_order = [LABEL_NAMES[index] for index in sorted(LABEL_NAMES)]

    base = alt.Chart(view).encode(
        x=alt.X("predicted:N", title="predicted label", sort=label_order),
        y=alt.Y("true:N", title="true label", sort=label_order),
        tooltip=[
            alt.Tooltip("true:N", title="true"),
            alt.Tooltip("predicted:N", title="predicted"),
            alt.Tooltip("count:Q", title="count", format=",d"),
        ],
    )
    heatmap = base.mark_rect(cornerRadius=3).encode(
        color=alt.Color(
            "count:Q",
            scale=alt.Scale(range=[PALETTE["primary"], CHART_COLORS[1]]),
            legend=alt.Legend(title="count"),
        )
    )
    labels = base.mark_text(fontSize=13, fontWeight=600).encode(
        text=alt.Text("count:Q", format=",d"),
        color=alt.Color("text_color:N", scale=None, legend=None),
    )
    chart = (heatmap + labels).properties(height=320, title=title)
    st.altair_chart(chart_theme(chart), width="stretch")

def feature_boxplot(
    df: pd.DataFrame,
    feature: str,
    label: str = "label",
    title: str | None = None,
) -> None:
    if df.empty or feature not in df.columns or label not in df.columns:
        return

    view = df[[feature, label]].dropna().copy()
    view["label_name"] = view[label].map(label_name)
    label_order = [LABEL_NAMES[index] for index in sorted(LABEL_NAMES)]
    chart = (
        alt.Chart(view)
        .mark_boxplot(size=48, extent=1.5)
        .encode(
            x=alt.X("label_name:N", title="label", sort=label_order),
            y=alt.Y(f"{feature}:Q", title=axis_title(feature), scale=alt.Scale(zero=False)),
            color=alt.Color(
                "label_name:N",
                title="label",
                sort=label_order,
                scale=alt.Scale(range=CHART_COLORS),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("label_name:N", title="label"),
                alt.Tooltip(f"{feature}:Q", title=axis_title(feature), format=",.3f"),
            ],
        )
        .properties(height=CHART_SPEC["height"], title=title)
    )
    st.altair_chart(chart_theme(chart), width="stretch")

def correlation_heatmap(
    df: pd.DataFrame,
    features: list[str],
    title: str | None = None,
) -> None:
    usable = [feature for feature in features if feature in df.columns]
    if df.empty or len(usable) < 2:
        return

    correlation = df[usable].corr(numeric_only=True).round(3)
    view = (
        correlation.rename_axis("feature_y")
        .reset_index()
        .melt(id_vars="feature_y", var_name="feature_x", value_name="correlation")
    )
    base = alt.Chart(view).encode(
        x=alt.X("feature_x:N", title=None, sort=usable, axis=alt.Axis(labelAngle=-35)),
        y=alt.Y("feature_y:N", title=None, sort=usable),
        tooltip=[
            alt.Tooltip("feature_y:N", title="feature"),
            alt.Tooltip("feature_x:N", title="compared with"),
            alt.Tooltip("correlation:Q", format=".3f"),
        ],
    )
    cells = base.mark_rect(cornerRadius=2).encode(
        color=alt.Color(
            "correlation:Q",
            title="correlation",
            scale=alt.Scale(domain=[-1, 0, 1], range=[CHART_COLORS[0], PALETTE["primary"], CHART_COLORS[1]]),
        )
    )
    labels = base.mark_text(fontSize=11).encode(
        text=alt.Text("correlation:Q", format=".2f"),
        color=alt.condition(
            "abs(datum.correlation) >= 0.58",
            alt.value(PALETTE["paper"]),
            alt.value(PALETTE["text"]),
        ),
    )
    chart = (cells + labels).properties(height=460, title=title)
    st.altair_chart(chart_theme(chart), width="stretch")

def metric_long(df: pd.DataFrame, metrics: list[str], id_cols: list[str]) -> pd.DataFrame:
    value_cols = [metric for metric in metrics if metric in df.columns]
    if not value_cols:
        return pd.DataFrame()
    return df.melt(
        id_vars=[col for col in id_cols if col in df.columns],
        value_vars=value_cols,
        var_name="metric",
        value_name="value",
    )
