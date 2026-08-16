"""
ui_components.py – reusable Streamlit building blocks.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date


# ── ISM color palette ─────────────────────────────────────────────────────────
GREEN    = "#2e7d32"
GREEN_LT = "#66bb6a"
RED      = "#c62828"
RED_LT   = "#ef9a9a"
GRAY     = "#64748b"
BG       = "#ffffff"

CHART_COLORS = [GREEN, RED, "#42a5f5", "#ffa726", "#ab47bc", "#26c6da"]
# CHART_COLORS = [RED, GREEN, "#42a5f5", "#ffa726", "#ab47bc", "#26c6da"]

# ── Header ────────────────────────────────────────────────────────────────────
def page_header(title: str, period: tuple[date, date] | None = None):
    """Renders the top brand bar with title and optional period badge."""
    period_html = ""
    if period:
        start, end = period
        period_html = (
            f'<span class="period-badge">'
            f'Período: {start.strftime("%d/%m/%Y")} a {end.strftime("%d/%m/%Y")}'
            f'</span>'
        )

    st.markdown(
        f"""
        <div class="brand-bar">
            <h2 style="margin:0;font-size:1.35rem;font-weight:700;color:#1e293b;">{title}</h2>
            {period_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Date range filter ─────────────────────────────────────────────────────────
def date_filter(df: pd.DataFrame, col: str = "date", key_prefix: str = "") -> tuple[pd.DataFrame, tuple]:
    """Sidebar date-range picker; returns filtered df and (start, end) tuple."""
    if df.empty or col not in df.columns:
        return df, (date.today(), date.today())

    min_d = df[col].min().date()
    max_d = df[col].max().date()

    with st.sidebar:
        st.markdown("#### 🗓 Filtro de Período")
        start = st.date_input("De", value=min_d, min_value=min_d, max_value=max_d, key=f"date_start_{key_prefix}" if key_prefix else "date_start")
        end   = st.date_input("Até", value=max_d, min_value=min_d, max_value=max_d, key=f"date_end_{key_prefix}" if key_prefix else "date_end")

    mask = (df[col].dt.date >= start) & (df[col].dt.date <= end)
    return df[mask], (start, end)


# ── Metric row ────────────────────────────────────────────────────────────────
def metric_row(metrics: list[dict]):
    """
    Render a row of metric cards.
    metrics: [{"label": str, "value": str|int|float, "delta": str|None}, ...]
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.metric(
                label=m.get("label", ""),
                value=m.get("value", "—"),
                delta=m.get("delta"),
            )


# ── Chart helpers ─────────────────────────────────────────────────────────────
def _chart_defaults(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="DM Sans, sans-serif",
        font_color=GRAY,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=True, zeroline=True),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=True),
        xaxis_zeroline=True, 
        yaxis_zeroline=True
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def donut_chart(labels: list, values: list, title: str = "", colors: list = CHART_COLORS) -> go.Figure:
    """Green/Red donut matching the ISM style."""
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker_colors=colors,
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=9.5, family="DM Sans, sans-serif", color="#ffffff"),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="DM Sans, sans-serif",
        font_color=GRAY,
        legend=dict(orientation="v", x=1.05),
        margin=dict(l=0, r=80, t=10, b=0),
        annotations=[dict(text=f"<b>{title}</b>", x=0.5, y=0.5, showarrow=False,
                          font_size=13, font_color="#ffffff")] if title else [],
    )
    return fig



def bar_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None,
              barmode: str = "group", orientation: str = "v", category_orders: dict | None = None, colors: list = CHART_COLORS) -> go.Figure:
    fig = px.bar(df, x=x, y=y, color=color, barmode=barmode,
                 color_discrete_sequence=colors, orientation=orientation, category_orders=category_orders)
    # Show values on bars for easier reading
    if orientation == "h":
        fig.update_traces(texttemplate="%{x}", textposition="outside", textfont_color="white")
        # Hide horizontal grid lines which can look like a line through the bars
        fig.update_yaxes(showgrid=False)
        fig.update_xaxes(showgrid=False)
        fig.update_layout(
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
    else:
        fig.update_traces(texttemplate="%{y}", textposition="outside", textfont_color="white")
        fig.update_layout(font_color=GRAY)
    # Remove bar borders/lines for a cleaner look
    fig.update_traces(marker_line_width=0)
    return _chart_defaults(fig)


def line_chart(df: pd.DataFrame, x: str, y: str | list[str],
               color: str | None = None) -> go.Figure:
    fig = px.line(df, x=x, y=y, color=color, color_discrete_sequence=CHART_COLORS,
                  markers=True)
    fig.update_traces(line=dict(width=5))  # Set line width to 5
    return _chart_defaults(fig)


def styled_table(df: pd.DataFrame):
    """Render a Streamlit dataframe with consistent styling."""
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


# ── Card wrapper ──────────────────────────────────────────────────────────────
def card(title: str, content_fn, *args, **kwargs):
    """Wrap any content in a white rounded card."""
    st.markdown(
        f'<div class="card"><div class="card-title">{title}</div></div>',
        unsafe_allow_html=True,
    )
    content_fn(*args, **kwargs)


# ── Upload helper (shown when CSV is missing) ─────────────────────────────────
def csv_uploader(label: str, filename: str, expected_cols: list[str]) -> bool:
    """
    Show an uploader for `filename`. Returns True once the file is saved to data/.
    """
    from pathlib import Path
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    dest = data_dir / filename
    if dest.exists():
        return True

    st.info(f"📂 Faça upload do arquivo **{filename}** para este painel.")
    st.caption(f"Colunas esperadas: `{'`, `'.join(expected_cols)}`")
    uploaded = st.file_uploader(label, type="csv", key=filename)
    if uploaded:
        dest.write_bytes(uploaded.read())
        st.success("Arquivo carregado! Recarregue a página.")
        st.rerun()
    return False
