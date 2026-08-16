"""
pages/painel_montagem.py – Assembly panel

Charts: Bar  – Montagens por Operador
        Line – Tempo Médio por Dia
        Table – Top 10 cargas mais lentas
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

# page_header("Painel Montagem", period=period)


# ── Charts ────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Caixas por Montador</div>', unsafe_allow_html=True)
    caixas_por_montador = df_pallets.groupby("MONTADOR")["CAIXAS"].sum().reset_index()
    fig = bar_chart(caixas_por_montador, x="CAIXAS", y="MONTADOR", orientation="h", category_orders={"MONTADOR": caixas_por_montador.sort_values("CAIXAS", ascending=False)["MONTADOR"].tolist()})
    st.plotly_chart(fig, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Paletes por Montador</div>', unsafe_allow_html=True)
    paletes_por_montador = df_pallets.groupby("MONTADOR").size().reset_index(name="PALETES")
    fig = bar_chart(paletes_por_montador, x="PALETES", y="MONTADOR", orientation="h", category_orders={"MONTADOR": paletes_por_montador.sort_values("PALETES", ascending=False)["MONTADOR"].tolist()})
    st.plotly_chart(fig, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:24px'/>", unsafe_allow_html=True)

col5, col6 = st.columns(2)

with col5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Tabela - Caixas por Montador</div>', unsafe_allow_html=True)
    st.download_button(
        label="📥 Baixar Tabela",
        data=_df_to_excel_bytes(caixas_por_montador),
        file_name="caixas_por_montador.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    styled_table(caixas_por_montador)
    st.markdown('</div>', unsafe_allow_html=True)

with col6:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Tabela - Paletes por Montador</div>', unsafe_allow_html=True)
    st.download_button(
        label="📥 Baixar Tabela",
        data=_df_to_excel_bytes(paletes_por_montador),
        file_name="paletes_por_montador.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    styled_table(paletes_por_montador)
    st.markdown('</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Tempo Médio Montagem por Montador</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    tempo_montagem_mean = df_pallets.groupby("MONTADOR")["TEMPO_MONTAGEM"].mean().reset_index()
    tempo_montagem_mean["TEMPO_MONTAGEM"] = round(tempo_montagem_mean["TEMPO_MONTAGEM"], 2)
    styled_table(tempo_montagem_mean)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Caixa Hora Médio por Montador</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    caixa_hora_mean = df_caixa_hora.groupby("MONTADOR")["CAIXA_HORA"].mean().reset_index()
    caixa_hora_mean["CAIXA_HORA"] = round(caixa_hora_mean["CAIXA_HORA"], 2)
    styled_table(caixa_hora_mean)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:24px'/>", unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Tempo de Montagem Detalhado por Transporte</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
df_montagem_transporte_display = df_montagem_transporte[['TRANSPORTE','DATA_ENTREGA',
                                                         'TOTAL_PALETES_MISTOS','LISTA',
                                                         'MONTADOR','CAIXAS','TEMPO_MONTAGEM_POR_USUARIO', 
                                                         'TEMPO_MONTAGEM_POR_TRANSPORTE']]
df_montagem_transporte_display["DATA_ENTREGA"] = df_montagem_transporte_display["DATA_ENTREGA"].dt.date

# Download button for the cargos table
st.download_button(
    label="📥 Baixar Tabela",
    data=_df_to_excel_bytes(df_montagem_transporte_display),
    file_name="dados_montagem_por_transporte.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

styled_table(df_montagem_transporte_display)
st.markdown('</div>', unsafe_allow_html=True)


# ── Caixa Hora Table ─────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Caixa Hora por Data de Entrega</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
if not df_caixa_hora.empty:
    df_caixa_hora["CAIXA_HORA"] = round(df_caixa_hora["CAIXA_HORA"], 2)
    df_caixa_hora["DATA_ENTREGA"] = df_caixa_hora["DATA_ENTREGA"].dt.date

    # Download button for the cargos table
    st.download_button(
        label="📥 Baixar Tabela",
        data=_df_to_excel_bytes(df_caixa_hora),
        file_name="dados_caixa_hora_data_entrega.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    styled_table(df_caixa_hora)
else:
    st.write("Dados de caixa hora indisponíveis")
st.markdown('</div>', unsafe_allow_html=True)
