"""
pages/painel_operacoes.py – Painel Operações (operations dashboard)

Tabela: Duração das Operações
"""
import streamlit as st
import pandas as pd
from io import BytesIO

from components.ui_components import (
    page_header, date_filter, metric_row,
    donut_chart, bar_chart, line_chart,
    styled_table, csv_uploader,
)


def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Return a DataFrame converted to Excel bytes for Streamlit download."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    return output.getvalue()
from components.data_loader import load_pallets, load_cargas, load_conferencia, load_duracao_operacao, load_horas_trabalhadas, load_op_perfil

GREEN    = "#2e7d32"
GREEN_LT = "#66bb6a"
RED      = "#c62828"

COLORS = [RED, GREEN]
COLORS_BAR = [GREEN, RED]

# def render():
# ── Data ──────────────────────────────────────────────────────────────────
# need_pallets  = csv_uploader("Upload pallets.csv", "pallets.csv",
#                                 ["date", "TIPO_PALETE", "CAIXAS"])
# need_cargas   = csv_uploader("Upload cargas.csv",  "cargas.csv",
#                                 ["date", "carga_id", "status", "duration_min"])

# if not (need_pallets and need_cargas):
#     st.stop()

df_pallets = load_pallets()
df_cargas  = load_cargas()
df_conferencia = load_conferencia()
df_operacaoes = load_duracao_operacao()
df_horas_trabalhadas = load_horas_trabalhadas()
df_op_perfil = load_op_perfil()

# ── Sidebar filters ───────────────────────────────────────────────────────
# Use a single date picker for all charts (same period applied across datasets)
df_operacaoes, period = date_filter(df_operacaoes, col="data_operacao", key_prefix="period")
start, end = period

# Apply the same date range to other tables
if not df_cargas.empty and "delivery_date" in df_cargas.columns:
    mask_cargas = (df_cargas["delivery_date"].dt.date >= start) & (df_cargas["delivery_date"].dt.date <= end)
    df_cargas = df_cargas[mask_cargas]

if not df_conferencia.empty and "data_entrega" in df_conferencia.columns:
    mask_conf = (df_conferencia["data_entrega"].dt.date >= start) & (df_conferencia["data_entrega"].dt.date <= end)
    df_conferencia = df_conferencia[mask_conf]

if not df_pallets.empty and "DATA_ENTREGA" in df_pallets.columns:
    mask_pallets = (df_pallets["DATA_ENTREGA"].dt.date >= start) & (df_pallets["DATA_ENTREGA"].dt.date <= end)
    df_pallets = df_pallets[mask_pallets]

if not df_horas_trabalhadas.empty and "data_operacao" in df_horas_trabalhadas.columns:
    mask_horas = (df_horas_trabalhadas["data_operacao"].dt.date >= start) & (df_horas_trabalhadas["data_operacao"].dt.date <= end)
    df_horas_trabalhadas = df_horas_trabalhadas[mask_horas]

if not df_op_perfil.empty and "data_operacao" in df_op_perfil.columns:
    mask_op_perfil = (df_op_perfil["data_operacao"].dt.date >= start) & (df_op_perfil["data_operacao"].dt.date <= end)
    df_op_perfil = df_op_perfil[mask_op_perfil]


# ── KPI: Duração média das operações ───────────────────────────────────────
if "DURAÇÃO" in df_operacaoes.columns and not df_operacaoes["DURAÇÃO"].dropna().empty:
    raw_durations = df_operacaoes["DURAÇÃO"].astype(str).str.strip().str.replace('"', '', regex=False)
    durations = pd.to_timedelta(raw_durations, errors="coerce")
    mean_duration = durations.mean()
    if pd.isna(mean_duration):
        mean_duration_text = "N/A"
    else:
        total_seconds = int(mean_duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        mean_duration_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
else:
    mean_duration_text = "N/A"

# ── KPI: Média de horas trabalhadas ─────────────────────────────────────────
if "horas" in df_horas_trabalhadas.columns and not df_horas_trabalhadas["horas"].dropna().empty:
    raw_horas = df_horas_trabalhadas["horas"].astype(str).str.strip().str.replace('"', '', regex=False)
    horas_timedelta = pd.to_timedelta(raw_horas, errors="coerce")
    mean_horas = horas_timedelta.mean()
    if pd.isna(mean_horas):
        mean_horas_text = "N/A"
    else:
        total_seconds_hours = int(mean_horas.total_seconds())
        hours_h = total_seconds_hours // 3600
        minutes_h = (total_seconds_hours % 3600) // 60
        seconds_h = total_seconds_hours % 60
        mean_horas_text = f"{hours_h:02d}:{minutes_h:02d}:{seconds_h:02d}"
else:
    mean_horas_text = "N/A"

# ── KPI: Médias de durações do perfil das operações ─────────────────────────
def _calc_mean_duration(df, col):
    if col in df.columns and not df[col].dropna().empty:
        raw_dur = df[col].astype(str).str.strip().str.replace('"', '', regex=False)
        dur_td = pd.to_timedelta(raw_dur, errors="coerce")
        mean_dur = dur_td.mean()
        if pd.isna(mean_dur):
            return "N/A"
        else:
            total_seconds = int(mean_dur.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return "N/A"

mean_montagem_text = _calc_mean_duration(df_op_perfil, "DURAÇÃO DA MONTAGEM")
mean_conferencia_text = _calc_mean_duration(df_op_perfil, "DURAÇÃO DA CONFERENCIA")
mean_empilhamento_text = _calc_mean_duration(df_op_perfil, "DURAÇÃO DO EMPILHAMENTO")

metric_row([
    {"label": "Duração Média das Operações", "value": mean_duration_text},
    {"label": "Média Horas Trabalhadas", "value": mean_horas_text},
    {"label": "Média Duração Montagem", "value": mean_montagem_text},
    {"label": "Média Duração Conferência", "value": mean_conferencia_text},
    {"label": "Média Duração Empilhamento", "value": mean_empilhamento_text}
])

# ── Tabela: Perfil das Operações ─────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Dados detalhados – Duração por Perfil</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if not df_op_perfil.empty:
    df_op_perfil_display = df_op_perfil.copy()
    if "data_operacao" in df_op_perfil_display.columns:
        df_op_perfil_display["data_operacao"] = df_op_perfil_display["data_operacao"].dt.date

    # Rename columns for display
    df_op_perfil_display = df_op_perfil_display.rename(columns={
        'INÍCIO DA OPERAÇÃO': 'INÍCIO DA OPERAÇÃO',
        'PRIMEIRA MONTAGEM': 'PRIMEIRA MONTAGEM',
        'ULTIMA MONTAGEM': 'ÚLTIMA MONTAGEM',
        'DURAÇÃO DA MONTAGEM': 'DURAÇÃO DA MONTAGEM',
        'PRIMEIRA CONFERENCIA': 'PRIMEIRA CONFERÊNCIA',
        'ULTIMA CONFERENCIA': 'ÚLTIMA CONFERÊNCIA',
        'DURAÇÃO DA CONFERENCIA': 'DURAÇÃO DA CONFERÊNCIA',
        'PRIMEIRO EMPILHAMENTO': 'PRIMEIRO EMPILHAMENTO',
        'ULTIMO EMPILHAMENTO': 'ÚLTIMO EMPILHAMENTO',
        'DURAÇÃO DO EMPILHAMENTO': 'DURAÇÃO DO EMPILHAMENTO',
        'data_operacao': 'DATA DA OPERAÇÃO'
    })

    st.download_button(
        label="📥 Baixar Tabela",
        data=_df_to_excel_bytes(df_op_perfil_display),
        file_name="dados_perfil_operacoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    styled_table(df_op_perfil_display)
else:
    st.info("Nenhum dado disponível em perfil das operações para o período selecionado.")

st.markdown('</div>', unsafe_allow_html=True)

# ── Gráfico: Comparação de durações por data ───────────────────────────────
if not df_op_perfil.empty:
    df_perfil_chart = df_op_perfil.copy()
    df_perfil_chart["data_operacao"] = pd.to_datetime(df_perfil_chart["data_operacao"]).dt.date

    # Convert durations to timedelta
    df_perfil_chart["DURAÇÃO DA MONTAGEM_td"] = pd.to_timedelta(
        df_perfil_chart["DURAÇÃO DA MONTAGEM"].astype(str).str.strip().str.replace('"', '', regex=False),
        errors="coerce"
    )
    df_perfil_chart["DURAÇÃO DA CONFERENCIA_td"] = pd.to_timedelta(
        df_perfil_chart["DURAÇÃO DA CONFERENCIA"].astype(str).str.strip().str.replace('"', '', regex=False),
        errors="coerce"
    )
    df_perfil_chart["DURAÇÃO DO EMPILHAMENTO_td"] = pd.to_timedelta(
        df_perfil_chart["DURAÇÃO DO EMPILHAMENTO"].astype(str).str.strip().str.replace('"', '', regex=False),
        errors="coerce"
    )

    # Group by data_operacao and calculate mean durations
    grouped = df_perfil_chart.groupby("data_operacao").agg({
        "DURAÇÃO DA MONTAGEM_td": "mean",
        "DURAÇÃO DA CONFERENCIA_td": "mean",
        "DURAÇÃO DO EMPILHAMENTO_td": "mean"
    }).reset_index()

    # Melt to long format for plotting
    melted = grouped.melt(id_vars="data_operacao", var_name="Tipo", value_name="Duração")
    melted["Tipo"] = melted["Tipo"].str.replace("_td", "").str.replace("DURAÇÃO DA ", "").str.replace("DURAÇÃO DO ", "")
    melted["Horas"] = (melted["Duração"].dt.total_seconds() / 3600.0).round(2)

    fig_comp = bar_chart(melted, x="data_operacao", y="Horas", color="Tipo", barmode="group")
    fig_comp.update_layout(
        title="Comparação de Durações por Data",
        xaxis_title="Data",
        yaxis_title="Horas",
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# ── Gráfico: Duração das operações por data ─────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Duração total das Operações por Data</div>',
            unsafe_allow_html=True)
# st.markdown('</div>', unsafe_allow_html=True)

if not df_operacaoes.empty and "data_operacao" in df_operacaoes.columns and "DURAÇÃO" in df_operacaoes.columns:
    df_operacaoes_chart = df_operacaoes.copy()
    df_operacaoes_chart["DURAÇÃO_TIMEDTA"] = pd.to_timedelta(
        df_operacaoes_chart["DURAÇÃO"].astype(str).str.strip().str.replace('"', '', regex=False),
        errors="coerce"
    )
    df_operacaoes_chart = df_operacaoes_chart.dropna(subset=["DURAÇÃO_TIMEDTA"])
    if not df_operacaoes_chart.empty:
        df_operacaoes_chart["data_operacao"] = pd.to_datetime(df_operacaoes_chart["data_operacao"]).dt.date
        daily_duration = (
            df_operacaoes_chart
            .groupby("data_operacao")
            ["DURAÇÃO_TIMEDTA"]
            .sum()
            .reset_index()
        )
        daily_duration["duration_hours"] = (daily_duration["DURAÇÃO_TIMEDTA"].dt.total_seconds() / 3600.0).round(2)
        fig_duracao = bar_chart(daily_duration, x="data_operacao", y="duration_hours", color=None)
        fig_duracao.update_layout(
            xaxis_title="Data",
            yaxis_title="Horas",
        )
        st.plotly_chart(fig_duracao, use_container_width=True)

# ── Gráfico: Média de horas trabalhadas por data ─────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Média de Horas Trabalhadas por Data</div>',
            unsafe_allow_html=True)
if not df_horas_trabalhadas.empty and "data_operacao" in df_horas_trabalhadas.columns and "horas" in df_horas_trabalhadas.columns:
    df_horas_chart = df_horas_trabalhadas.copy()
    df_horas_chart["horas_timedelta"] = pd.to_timedelta(
        df_horas_chart["horas"].astype(str).str.strip().str.replace('"', '', regex=False),
        errors="coerce"
    )
    df_horas_chart = df_horas_chart.dropna(subset=["horas_timedelta"])
    if not df_horas_chart.empty:
        df_horas_chart["data_operacao"] = pd.to_datetime(df_horas_chart["data_operacao"]).dt.date
        daily_mean_horas = (
            df_horas_chart
            .groupby("data_operacao")
            ["horas_timedelta"]
            .mean()
            .reset_index()
        )
        daily_mean_horas["mean_hours"] = (daily_mean_horas["horas_timedelta"].dt.total_seconds() / 3600.0).round(2)
        fig_mean_horas = bar_chart(daily_mean_horas, x="data_operacao", y="mean_hours", color=None)
        fig_mean_horas.update_layout(
            xaxis_title="Data",
            yaxis_title="Horas",
        )
        st.plotly_chart(fig_mean_horas, use_container_width=True)

# ── Detail table ──────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Dados detalhados – Duração das Operações</div>',
            unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Rename columns for display
df_operacaoes_display = df_operacaoes.rename(columns={
    'INÍCIO DA OPERAÇÃO': 'INÍCIO_DA_OPERAÇÃO',
    'INÍCIO DO INTERVALO': 'INÍCIO_DO_INTERVALO',
    'FIM DO INTERVALO': 'FIM_DO_INTERVALO',
    'FIM DA OPERAÇÃO': 'FIM_DA_OPERAÇÃO',
    'ULTIMO EMPILHAMENTO': 'ULTIMO_EMPILHAMENTO',
    'DURAÇÃO': 'DURAÇÃO',
    'data_operacao': 'DATA_DA_OPERAÇÃO'
})
df_operacaoes_display = df_operacaoes_display[["DATA_DA_OPERAÇÃO", "INÍCIO_DA_OPERAÇÃO", "FIM_DA_OPERAÇÃO", "ULTIMO_EMPILHAMENTO", "DURAÇÃO"]]
# Download button for the operations table
st.download_button(
    label="📥 Baixar Tabela",
    data=_df_to_excel_bytes(df_operacaoes_display),
    file_name="dados_duracao_operacao.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

styled_table(df_operacaoes_display)
st.markdown('</div>', unsafe_allow_html=True)

# ── Additional table: Horas Trabalhadas ─────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Dados detalhados – Horas Trabalhadas</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if not df_horas_trabalhadas.empty:
    df_horas_trabalhadas_display = df_horas_trabalhadas.copy()
    if "data_operacao" in df_horas_trabalhadas_display.columns:
        df_horas_trabalhadas_display["data_operacao"] = df_horas_trabalhadas_display["data_operacao"].dt.date

    df_horas_trabalhadas_display = df_horas_trabalhadas_display.rename(columns={
        'locality_name': 'UNIDADE',
        'start_of_operation': 'INÍCIO_DA_OPERAÇÃO',
        'data_operacao': 'DATA_DA_OPERAÇÃO',
        'assembler_name': 'MONTADOR',
        'inicio': 'PRIMEIRA_MONTAGEM',
        'fim': 'ÚLTIMA_MONTAGEM',
        'horas': 'HORAS_TRABALHADAS'
    })

    df_horas_trabalhadas_display = df_horas_trabalhadas_display[["DATA_DA_OPERAÇÃO", "UNIDADE", "MONTADOR", "INÍCIO_DA_OPERAÇÃO", "PRIMEIRA_MONTAGEM", "ÚLTIMA_MONTAGEM", "HORAS_TRABALHADAS"]]

    st.download_button(
        label="📥 Baixar Tabela",
        data=_df_to_excel_bytes(df_horas_trabalhadas_display),
        file_name="dados_horas_trabalhadas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    styled_table(df_horas_trabalhadas_display)
else:
    st.info("Nenhum dado disponível em horas_trabalhadas para o período selecionado.")

st.markdown('</div>', unsafe_allow_html=True)

