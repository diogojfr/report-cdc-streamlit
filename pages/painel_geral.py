"""
pages/painel_geral.py – Painel Geral (overview dashboard)

KPIs  : Caixas | Pallets Completos | Pallets Mistos
        Cargas Finalizadas | Tempo Médio Montagem | Tempo Médio Conferência

Charts: Donut – % Pallets por Tipo
        Bar   – Pallets por Dia
        Line  – Cargas Finalizadas por Dia
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
from components.data_loader import load_pallets, load_cargas, load_conferencia

BLUE     = "#105dc6"   # azul da marca (#003276) clareado para ficar legivel no tema dark
BLUE_LT  = "#478ceb"
RED      = "#c62828"

COLORS = [RED, BLUE]
COLORS_BAR = [BLUE, RED]

# def render():
# ── Data ──────────────────────────────────────────────────────────────────
# need_pallets  = csv_uploader("Upload pallets.csv", "pallets.csv",
#                                 ["date", "TIPO_PALETE", "CAIXAS"])
# need_cargas   = csv_uploader("Upload cargas.csv",  "cargas.csv",
#                                 ["date", "carga_id", "status", "duration_min"])

# if not (need_pallets and need_cargas):
    # st.stop()

df_pallets = load_pallets()
df_cargas  = load_cargas()
df_conferencia = load_conferencia()

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


# ── Header ────────────────────────────────────────────────────────────────
# page_header("Painel Geral", period=period)
# page_header("Painel Geral")

# ── KPI calculations ──────────────────────────────────────────────────────
total_caixas      = int(df_pallets["CAIXAS"].sum())
pallets_completos = int(df_pallets[df_pallets["TIPO_PALETE"] == "COMPLETO"]["CAIXAS"].count())
pallets_mistos    = int(df_pallets[df_pallets["TIPO_PALETE"] == "MISTO"]["CAIXAS"].count())

# cargas_fin        = int(df_cargas[df_cargas["load_status_name"] == "Finalizado"]["load_id"].nunique())
cargas_fin        = int(df_pallets["TRANSPORTE"].nunique())
# tempo_medio_mont  = df_cargas["loading_time"].mean() if "loading_time" in df_cargas else 0
raw_tempo_medio_mont  = df_pallets["TEMPO_MONTAGEM"].mean() if "TEMPO_MONTAGEM" in df_pallets else 0
if pd.isna(raw_tempo_medio_mont):
    tempo_medio_mont = "00:00:00"
else:
    # TEMPO_MONTAGEM is in minutes; format as hh:mm:ss
    total_seconds_mont = int(raw_tempo_medio_mont * 60)
    h_mont = total_seconds_mont // 3600
    m_mont = (total_seconds_mont % 3600) // 60
    s_mont = total_seconds_mont % 60
    tempo_medio_mont = f"{h_mont:02d}:{m_mont:02d}:{s_mont:02d}"

if "tempo_conferencia" in df_conferencia and not df_conferencia["tempo_conferencia"].dropna().empty:

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
    tempo_medio_por_conferente_d["TEMPO MÉDIO CONFERÊNCIA"] = pd.to_timedelta(tempo_medio_por_conferente_d["TEMPO MÉDIO CONFERÊNCIA"], errors="coerce")
    mean_td = tempo_medio_por_conferente_d["TEMPO MÉDIO CONFERÊNCIA"].mean()
    if pd.isna(mean_td):
        tempo_medio_conf = "00:00:00"
    else:
        total_seconds_conf = int(mean_td.total_seconds())
        h_conf = total_seconds_conf // 3600
        m_conf = (total_seconds_conf % 3600) // 60
        s_conf = total_seconds_conf % 60
        tempo_medio_conf = f"{h_conf:02d}:{m_conf:02d}:{s_conf:02d}"

else:
    tempo_medio_conf = "00:00:00"

# df_pallets["FIM_CONFERENCIA"] = pd.to_datetime(df_pallets["FIM_CONFERENCIA"])
# df_pallets["INICIO_CONFERENCIA"] = pd.to_datetime(df_pallets["INICIO_CONFERENCIA"])
# tmp  = df_pallets["FIM_CONFERENCIA"] - df_pallets["INICIO_CONFERENCIA"]
# tempo_medio_conf  = tmp.mean()
# tempo_conf = df_pallets["FIM_CONFERENCIA"] - df_pallets["INICIO_CONFERENCIA"]
# tempo_medio_conf   = tempo_conf.mean().total_seconds() / 60 

# ── Row 1: three KPI cards ─────────────────────────────────────────────────
metric_row([
    {"label": "Caixas",           "value": f"{total_caixas:,}"},
    {"label": "Pallets Completos","value": f"{pallets_completos:,}"},
    {"label": "Pallets Mistos",   "value": f"{pallets_mistos:,}"},
])

st.markdown("<div style='height:16px'/>", unsafe_allow_html=True)

# ── Row 2: three KPI cards ─────────────────────────────────────────────────
metric_row([
    {"label": "Cargas Finalizadas",              "value": cargas_fin},
    {"label": "Tempo Médio Montagem",             "value": tempo_medio_mont},
    {"label": "Tempo Médio Conferência",          "value": tempo_medio_conf},
])

st.markdown("<div style='height:24px'/>", unsafe_allow_html=True)

# ── Charts row ────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Percentual de Pallets por Tipo</div>',
                unsafe_allow_html=True)
    TIPO_PALETE_totals = df_pallets.groupby("TIPO_PALETE")["CAIXAS"].count().reset_index()
    fig = donut_chart(
        labels=TIPO_PALETE_totals["TIPO_PALETE"].tolist(),
        values=TIPO_PALETE_totals["CAIXAS"].tolist(),
        colors=COLORS,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Caixas por Dia</div>',
                unsafe_allow_html=True)
    daily = (
        df_pallets.groupby(["DATA_ENTREGA", "TIPO_PALETE"])["CAIXAS"]
        .sum()
        .reset_index()
    )
    fig2 = bar_chart(daily, x="DATA_ENTREGA", y="CAIXAS", color="TIPO_PALETE", barmode="group", colors=COLORS)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Bottom chart: Cargas por Dia ───────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Cargas Finalizadas por Dia</div>',
            unsafe_allow_html=True)
daily_cargas = (
    df_cargas[df_cargas["load_status_name"] == "Finalizado"]
    .groupby("delivery_date")["load_id"]
    .nunique()
    .reset_index()
    .rename(columns={"load_id": "CARGAS", 'delivery_date': 'DATA_ENTREGA'})
)
fig3 = line_chart(daily_cargas, x="DATA_ENTREGA", y="CARGAS")
st.plotly_chart(fig3, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── Detail table ──────────────────────────────────────────────────────────
# with st.expander("🔍 Ver dados detalhados – Cargas"):
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Dados detalhados – Cargas</div>',
            unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
df_cargas_display = df_cargas[['load_id','client_name','integration_id',
                               'load_code','delivery_date', 'locality_name',
                               'vehicle_name','assembled_percentage','checked_percentage',
                               'loaded_percentage','load_status_name','load_weight',
                               'quantity_boxes','checker','loading_time']]
df_cargas_display = df_cargas_display.rename(columns={
    'load_id': 'ID Carga',
    'client_name': 'Cliente',
    'integration_id': 'Transporte',
    'load_code': 'Código Carga',
    'delivery_date': 'Data de Entrega',
    'locality_name': 'Localidade',
    'vehicle_name': 'Veículo',
    'assembled_percentage': 'Percentual de Montagem',
    'checked_percentage': 'Percentual de Verificação',
    'loaded_percentage': 'Percentual de Carregamento',
    'load_status_name': 'Status',
    'load_weight': 'Peso (kg)',
    'quantity_boxes': 'Caixas',
    'checker': 'Conferente',
    'loading_time': 'Tempo de Carregamento (horas)'
})

df_cargas_display["Data de Entrega"] = df_cargas_display["Data de Entrega"].dt.date

# Download button for the cargos table
st.download_button(
    label="📥 Baixar Tabela",
    data=_df_to_excel_bytes(df_cargas_display),
    file_name="dados_cargas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

styled_table(df_cargas_display)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:16px'/>", unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Dados detalhados – Listas</div>', unsafe_allow_html=True)

df_pallets["DATA_ENTREGA"] = df_pallets["DATA_ENTREGA"].dt.date

# Download button for the pallets/listas table
st.download_button(
    label="📥 Baixar Tabela",
    data=_df_to_excel_bytes(df_pallets),
    file_name="dados_listas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# df_pallets_display = df_pallets[['DATA_ENTREGA', 'MONTADOR', 'CAIXAS', 'TIPO_PALETE', 'TEMPO_MONTAGEM', 'CONFERENTE']]
# df_pallets_display = df_pallets_display.rename(columns={
#     'DATA_ENTREGA': 'Data de Entrega',
#     'MONTADOR': 'Montador',
#     'CAIXAS': 'Caixas',
#     'TIPO_PALETE': 'Tipo de Pallet',
#     'TEMPO_MONTAGEM': 'Tempo de Montagem (min)',
#     'CONFERENTE': 'Conferente'
# })
styled_table(df_pallets)
st.markdown('</div>', unsafe_allow_html=True)
