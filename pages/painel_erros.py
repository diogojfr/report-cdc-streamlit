"""
pages/painel_erros.py – Error / exception panel

Charts: Bar  – Erros por Tipo
        Line – Erros por Dia
        Table – Detalhe de erros
"""
import streamlit as st
import pandas as pd
from io import BytesIO


from components.ui_components import (
    page_header, date_filter, metric_row,
    bar_chart, line_chart, donut_chart, styled_table, csv_uploader,
)

def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Return a DataFrame converted to Excel bytes for Streamlit download."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    return output.getvalue()
from components.data_loader import (
    load_pallets,
    load_cargas,
    load_conferencia,
    load_caixa_hora,
    load_montagem_transporte,
    load_erros,
    load_erros_dia,
)

GREEN    = "#2e7d32"
GREEN_LT = "#66bb6a"
RED      = "#c62828"

COLORS = [RED, GREEN]
COLORS_BAR = [GREEN, RED]

df_pallets = load_pallets()
df_cargas  = load_cargas()
df_conferencia = load_conferencia()
df_caixa_hora = load_caixa_hora()
df_montagem_transporte = load_montagem_transporte()
df_erros = load_erros()
df_erros_dia = load_erros_dia()

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

if not df_erros.empty and "DATA_ENTREGA" in df_erros.columns:
    mask_erros = (df_erros["DATA_ENTREGA"].dt.date >= start) & (df_erros["DATA_ENTREGA"].dt.date <= end)
    df_erros = df_erros[mask_erros]

if not df_erros_dia.empty and "delivery_date" in df_erros_dia.columns:
    mask_erros_dia = (df_erros_dia["delivery_date"].dt.date >= start) & (df_erros_dia["delivery_date"].dt.date <= end)
    df_erros_dia = df_erros_dia[mask_erros_dia]



# ── Charts ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Percentual de Caixas Erradas</div>', unsafe_allow_html=True)
    if not df_erros_dia.empty and "delivery_date" in df_erros_dia.columns:
        df_erros_dia["delivery_date"] = pd.to_datetime(df_erros_dia["delivery_date"]).dt.date
        correct = int(df_erros_dia["caixas_corretas"].sum()) if "caixas_corretas" in df_erros_dia.columns else 0
        wrong = int(df_erros_dia["caixas_erradas"].sum()) if "caixas_erradas" in df_erros_dia.columns else 0
        labels = ["CORRETO", "ERROS"]
        values = [correct, wrong]

        if correct + wrong > 0:
            fig = donut_chart(
                labels=labels,
                values=values,
                colors=COLORS_BAR,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Nenhum dado de caixas disponível para o período selecionado.")
    else:
        st.write("Dados de erros por dia indisponíveis")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Produtos com Mais Erros</div>', unsafe_allow_html=True)
    if not df_erros.empty and "PRODUTO" in df_erros.columns:
        produtos = (
            df_erros.groupby("PRODUTO").size().reset_index(name="TOTAL")
            .sort_values("TOTAL", ascending=True)
        )
        fig = bar_chart(produtos, x="TOTAL", y="PRODUTO", orientation="h")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Dados de erros indisponíveis")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Table ────────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Dados Detalhados - Erros</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
if not df_erros.empty:
    df_erros["DATA_ENTREGA"] = df_erros["DATA_ENTREGA"].dt.date

    # Download button for the cargos table
    st.download_button(
        label="📥 Baixar Tabela",
        data=_df_to_excel_bytes(df_erros),
        file_name="dados_erros.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    styled_table(df_erros)
else:
    st.write("Dados de erros indisponíveis")
st.markdown('</div>', unsafe_allow_html=True)


# ── Additional Analysis ───────────────────────────────────────────────────
col3, col4, col5 = st.columns(3)

with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Erros por Tipo</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if not df_erros.empty and "TIPO_ERRO" in df_erros.columns:
        tipo_erros = (
            df_erros.groupby("TIPO_ERRO").size().reset_index(name="TOTAL")
            .sort_values("TOTAL", ascending=False)
        )
        fig = bar_chart(tipo_erros, x="TIPO_ERRO", y="TOTAL", orientation="v")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Dados de erros indisponíveis")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Erros Informados pelos Conferentes</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if not df_erros.empty and "INFORMANTE" in df_erros.columns and "PERFIL_OFENSOR" in df_erros.columns:
        montadores = df_erros[df_erros["PERFIL_OFENSOR"] == "Montador"]
        if not montadores.empty:
            informantes = (
                montadores.groupby("INFORMANTE").size().reset_index(name="TOTAL")
                .sort_values("TOTAL", ascending=False)
                .rename(columns={"INFORMANTE": "CONFERENTE"})
            )
            # st.metric(label="Total Informantes", value=len(informantes))
            styled_table(informantes)
        else:
            st.write("Nenhum dado para Montadores")
    else:
        st.write("Dados de erros indisponíveis")
    st.markdown('</div>', unsafe_allow_html=True)

with col5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Erros por Montador</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if not df_erros.empty and "OFENSOR" in df_erros.columns and "PERFIL_OFENSOR" in df_erros.columns:
        montadores = df_erros[df_erros["PERFIL_OFENSOR"] == "Montador"]
        if not montadores.empty:
            ofensores = (
                montadores.groupby("OFENSOR").size().reset_index(name="TOTAL")
                .sort_values("TOTAL", ascending=False)
                .rename(columns={"OFENSOR": "MONTADOR"})
            )
            styled_table(ofensores)
        else:
            st.write("Nenhum dado para Montadores")
    else:
        st.write("Dados de erros indisponíveis")
    st.markdown('</div>', unsafe_allow_html=True)

