"""
data_loader.py – helpers to read CSV files and return DataFrames.
Each page calls the function it needs; all heavy work lives here.
"""
import pandas as pd
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


@st.cache_data(show_spinner=False)
def load_csv(filename: str, **kwargs) -> pd.DataFrame:
    """Generic cached CSV loader. Pass any pandas read_csv kwargs."""
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()          # return empty DF if file not uploaded yet
    return pd.read_csv(path, **kwargs)


# ── Page-specific loaders (rename / coerce columns here) ──────────────────────

def load_pallets() -> pd.DataFrame:
    """Expects: data/pallets.csv  with columns date, type, qty"""
    # df = load_csv("pallets.csv", parse_dates=["date"])
    df = load_csv("tab_orders.csv", parse_dates=["DATA_ENTREGA"])
    return df


def load_cargas() -> pd.DataFrame:
    """Expects: data/cargas.csv  with columns date, carga_id, status, duration_min"""
    df = load_csv("tab_loads.csv", parse_dates=["delivery_date"])
    return df


def load_conferencia() -> pd.DataFrame:
    """Expects: data/conferencia.csv  with columns date, op, duration_sec, errors"""
    df = load_csv("conf_registros.csv", parse_dates=["data_entrega","tempo_conferencia"])
    return df


def load_erros() -> pd.DataFrame:
    """Expects: data/erros.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("tab_errors.csv", parse_dates=["DATA_ENTREGA"])
    return df

def load_caixa_hora() -> pd.DataFrame:
    """Expects: data/caixa_hora.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("caixa_hora.csv", parse_dates=["DATA_ENTREGA"])
    return df

def load_tempo_montagem() -> pd.DataFrame:
    """Expects: data/tempo_montagem.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("tempo_medio_montagem.csv", parse_dates=["date"])
    return df

def load_tempo_conferencia_dia() -> pd.DataFrame:
    """Expects: data/tempo_conferencia.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("media_conf_dia.csv", parse_dates=["date"])
    return df

def load_montagem_transporte() -> pd.DataFrame:
    """Expects: data/montagem_transporte.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("montagem_transporte.csv", parse_dates=["DATA_ENTREGA"])
    return df

def load_erros_percentual() -> pd.DataFrame:
    """Expects: data/tab_errors_percent.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("tab_percent_errors.csv", sep=",")
    return df

def load_duracao_operacao() -> pd.DataFrame:
    """Expects: data/duracao_operacao.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("tab_duracao_operacao.csv", parse_dates=["data_operacao"])
    return df

def load_op_perfil() -> pd.DataFrame:
    """Expects: data/op_perfil.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("tab_op_perfil.csv", parse_dates=["data_operacao"])
    return df

def load_horas_trabalhadas() -> pd.DataFrame:
    """Expects: data/horas_trabalhadas.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("tab_horas_trabalhadas.csv", parse_dates=["data_operacao"])
    return df

def load_operacao_perfil() -> pd.DataFrame:
    """Expects: data/operacao_perfil.csv  with columns date, carga_id, error_type, qty"""
    df = load_csv("tab_op_perfil.csv", parse_dates=["data_operacao"])
    return df

def load_erros_dia() -> pd.DataFrame:
    """Expects: data/erros_dia.csv  with columns date, corrects boxes and wrong boxes per day"""
    df = load_csv("tab_erros_dia.csv", parse_dates=["delivery_date"])
    return df