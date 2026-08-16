# Easy Pallet – ISM Dashboard (Streamlit)

Dashboard operacional no estilo do Looker/Easy Pallet, construído com **Streamlit + Plotly**.

## Estrutura do Projeto

```
easy_pallet_app/
│
├── app.py                      ← Ponto de entrada principal (run this)
│
├── requirements.txt
│
├── components/
│   ├── data_loader.py          ← Funções de leitura de CSV (cached)
│   └── ui_components.py        ← Componentes reutilizáveis (cards, gráficos, filtros)
│
├── pages/
│   ├── painel_geral.py         ← Painel Geral (KPIs + Donut + Bar + Line)
│   ├── painel_montagem.py      ← Painel Montagem (Bar + Line + Tabela)
│   ├── painel_conferencia.py   ← Painel Conferência (Bar + Line + Tabela por Operador)
│   └── painel_erros.py         ← Painel Erros (Donut + Bar Stacked + Tabela)
│
└── data/                       ← Coloque seus CSVs aqui
    ├── pallets.csv
    ├── cargas.csv
    ├── conferencia.csv
    └── erros.csv
```

## Como Rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Formato dos CSVs

| Arquivo            | Colunas obrigatórias                                  |
|--------------------|-------------------------------------------------------|
| `pallets.csv`      | `date`, `type` (COMPLETO\|MISTO), `qty`               |
| `cargas.csv`       | `date`, `carga_id`, `status`, `duration_min`          |
| `conferencia.csv`  | `date`, `op`, `duration_sec`, `errors`                |
| `erros.csv`        | `date`, `carga_id`, `error_type`, `qty`               |

Datas no formato `YYYY-MM-DD`.

## Adicionando um Novo Painel

1. Crie `pages/painel_novo.py` com uma função `render()`  
2. Adicione a opção no `st.radio` em `app.py`  
3. Adicione a rota `elif "Novo" in page` em `app.py`  
4. Opcionalmente adicione um loader em `data_loader.py`
