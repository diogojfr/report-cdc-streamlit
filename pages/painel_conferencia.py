"""
pages/painel_conferencia.py – Conference / QC panel

Charts: Bar  – Conferências por Operador
        Line – Tempo Médio Conferência por Dia
        Table – Detalhe por Operador
"""
import streamlit as st
import pandas as pd
from io import BytesIO

from components.ui_components import (
    page_header, date_filter, metric_row,
    bar_chart, line_chart, styled_table, csv_uploader,
)
from components.data_loader import load_cargas, load_pallets, load_conferencia, load_caixa_hora, load_montagem_transporte

def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Return a DataFrame converted to Excel bytes for Streamlit download."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    return output.getvalue()

df_pallets = load_pallets()
df_cargas  = load_cargas()
df_conferencia = load_conferencia()
df_caixa_hora = load_caixa_hora()
df_montagem_transporte = load_montagem_transporte()

# ── Sidebar filters ───────────────────────────────────────────────────────
# Use a single date picker for all charts (same period applied across datasets)
df_pallets, period = date_filter(df_pallets, col="DATA_ENTREGA", key_prefix="period")
start, end = period

# Apply the same date range to other tables
if not df_cargas.empty and "delivery_date" in df_cargas.columns:
    mask_cargas = (df_cargas["delivery_date"].dt.date >= start) & (df_cargas["delivery_date"].dt.date <= end)
    df_cargas = df_cargas[mask_cargas]

if not df_conferencia.empty and "data_entrega" in df_conferencia.columns:
    mask_conf = (df_conferencia["data_entrega"].dt.date >= start) & (df_conferencia["data_entrega"].dt.date <= end)
    df_conferencia = df_conferencia[mask_conf]

if not df_caixa_hora.empty and "DATA_ENTREGA" in df_caixa_hora.columns:
    mask_caixa_hora = (df_caixa_hora["DATA_ENTREGA"].dt.date >= start) & (df_caixa_hora["DATA_ENTREGA"].dt.date <= end)
    df_caixa_hora = df_caixa_hora[mask_caixa_hora]

if not df_montagem_transporte.empty and "DATA_ENTREGA" in df_montagem_transporte.columns:
    mask_montagem = (df_montagem_transporte["DATA_ENTREGA"].dt.date >= start) & (df_montagem_transporte["DATA_ENTREGA"].dt.date <= end)
    df_montagem_transporte = df_montagem_transporte[mask_montagem]



# ── Charts ────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Caixas por Conferente</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    caixas_por_conferente = (
        df_pallets.groupby("CONFERENTE")["CAIXAS"].sum().reset_index()
        .sort_values("CAIXAS", ascending=False)
    )
    styled_table(caixas_por_conferente)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Paletes por Conferente</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    paletes_por_conferente = (
        df_pallets.groupby("CONFERENTE").size().reset_index(name="PALETES")
        .sort_values("PALETES", ascending=False)
    )
    styled_table(paletes_por_conferente)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:24px'/>", unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Transportes por Conferente</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    transporte_por_conferente = (
        df_pallets.groupby("CONFERENTE")["TRANSPORTE"].nunique().reset_index(name="TOTAL_CARGAS")
        .sort_values("TOTAL_CARGAS", ascending=False)
    )
    styled_table(transporte_por_conferente)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Tempo Médio Conferência por Conferente</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    tempo_medio_por_conferente = df_conferencia.groupby("conferente")["tempo_conferencia"].mean().reset_index()

    def _format_duration(v):
        if pd.isna(v):
            return ""
        if hasattr(v, "time"):
            return v.time().strftime("%H:%M:%S")
        if isinstance(v, pd.Timedelta):
            return str(v).split(".")[0]
        return str(v)

    tempo_medio_por_conferente["tempo_conferencia"] = (
        tempo_medio_por_conferente["tempo_conferencia"].apply(_format_duration)
    )

    tempo_medio_por_conferente_d = tempo_medio_por_conferente.rename(columns={
        'conferente': 'CONFERENTE',
        'tempo_conferencia': 'TEMPO MÉDIO CONFERÊNCIA'
    })
    styled_table(tempo_medio_por_conferente_d)
    st.markdown('</div>', unsafe_allow_html=True)


# ── Additional table: raw conferencia data ───────────────────────────────────
st.markdown("<div style='height:24px'/>", unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Dados de Conferência</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
# Show a subset of columns to keep the table readable
cols = [c for c in ["data_entrega", "conferente", "caixas", "tempo_conferencia"] if c in df_conferencia.columns]
if cols:
    df_display = df_conferencia[cols].copy()

    def _format_duration(v):
        if pd.isna(v):
            return ""
        if hasattr(v, "time"):
            return v.time().strftime("%H:%M:%S")
        if isinstance(v, pd.Timedelta):
            return str(v).split(".")[0]
        return str(v)

    if "tempo_conferencia" in df_display.columns:
        df_display["tempo_conferencia"] = df_display["tempo_conferencia"].apply(_format_duration)

    # Rename displayed columns to upper case for consistency
    df_display["data_entrega"] = df_display["data_entrega"].dt.date
    df_display = df_display.rename(columns=str.upper)

    # Download button for the cargos table
    st.download_button(
        label="📥 Baixar Tabela",
        data=_df_to_excel_bytes(df_display.sort_values(cols[0].upper(), ascending=False)),
        file_name="dados_conferencia.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    styled_table(df_display.sort_values(cols[0].upper(), ascending=False))
else:
    st.write("Nenhum dado disponível para exibir.")
st.markdown('</div>', unsafe_allow_html=True)


