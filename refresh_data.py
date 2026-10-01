"""
refresh_data.py – executa cada query de queries/*.sql contra o banco de produção
(via túnel SSH) e regrava o CSV correspondente em data/.

O nome do arquivo manda: queries/tab_orders.sql  ->  data/tab_orders.csv

Uso:
    python refresh_data.py                    # atualiza todos os CSVs
    python refresh_data.py tab_orders         # atualiza só os informados
    python refresh_data.py --list             # lista as queries encontradas
    python refresh_data.py --schemas          # mostra databases e schemas do servidor
    python refresh_data.py --allow-empty      # grava mesmo se a query voltar vazia

Cada CSV é escrito primeiro num arquivo temporário e só então substitui o
antigo, de modo que uma query que falhe nunca deixa um CSV pela metade.
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from psycopg2 import extensions as pg_ext
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sshtunnel import SSHTunnelForwarder

BASE_DIR = Path(__file__).parent
QUERIES_DIR = BASE_DIR / "queries"
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")

# Datas que o psycopg2 não conseguiu converter na query em execução.
_datas_invalidas: list[str] = []


def _env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        sys.exit(f"[ERRO] variável {key} ausente no .env")
    return value.strip()


def find_queries(names: list[str]) -> list[Path]:
    """Retorna os .sql a executar, ordenados. Sem filtro = todos."""
    found = sorted(QUERIES_DIR.glob("*.sql"))
    if not names:
        return found

    by_stem = {p.stem: p for p in found}
    selected, missing = [], []
    for name in names:
        stem = name.removesuffix(".sql")
        selected.append(by_stem[stem]) if stem in by_stem else missing.append(stem)
    if missing:
        sys.exit(f"[ERRO] query não encontrada em queries/: {', '.join(missing)}")
    return selected


def format_timedelta(td) -> str | None:
    """
    Formata um Timedelta como HH:MM:SS[.f] — o mesmo formato que o DBeaver
    exportava ("00:01:17", "00:00:08.6").

    Sem isso o pandas grava o repr nativo ("0 days 00:01:17"), que o
    parse_dates= do data_loader.py não consegue ler: a coluna fica como texto
    e as agregações das páginas quebram.
    """
    if pd.isna(td):
        return None
    total = td.total_seconds()
    sign = "-" if total < 0 else ""
    total = abs(total)
    whole = int(total)
    hours, rem = divmod(whole, 3600)
    minutes, seconds = divmod(rem, 60)
    out = f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"
    frac = round(total - whole, 6)
    if frac:                                   # fração só quando existe, sem zeros à direita
        out += f"{frac:.6f}"[1:].rstrip("0")
    return out


def register_safe_date_casters() -> None:
    """
    Impede que uma data inválida no banco derrube a query inteira.

    O datetime do Python só vai até o ano 9999; o Postgres vai até 294276.
    Um timestamp digitado errado — ex.: '92026-05-28', typo de '2026' — faz o
    psycopg2 estourar com "year 92026 is out of range" e a query toda falha.
    O DBeaver tolerava porque os tipos de data do Java têm alcance maior.

    Aqui o valor problemático vira NULL e a query continua. Os descartes são
    registrados em _datas_invalidas e reportados ao final — nunca em silêncio.
    """
    for base in (pg_ext.PYDATE, pg_ext.PYDATETIME, pg_ext.PYDATETIMETZ):
        def cast(value, cursor, _base=base):
            if value is None:
                return None
            try:
                return _base(value, cursor)
            except (ValueError, OverflowError):
                _datas_invalidas.append(value)
                return None

        pg_ext.register_type(pg_ext.new_type(base.values, f"SAFE_{base.name}", cast))


def has_data(csv_path: Path) -> bool:
    """True se o CSV existe e tem ao menos uma linha além do cabeçalho."""
    if not csv_path.exists():
        return False
    with csv_path.open(encoding="utf-8") as fh:
        next(fh, None)                    # cabeçalho
        return next(fh, None) is not None


def run_query(engine, sql_path: Path, allow_empty: bool = False) -> tuple[int, bool, list[str]]:
    """
    Executa uma query e substitui o CSV de destino.
    Retorna (nº de linhas, se o CSV foi gravado, datas inválidas descartadas).
    """
    _datas_invalidas.clear()
    df = pd.read_sql(sql_path.read_text(encoding="utf-8"), engine)
    descartadas = list(_datas_invalidas)

    # intervals do Postgres chegam como timedelta64 via psycopg2 — reformatar
    # posicionalmente, já que algumas queries repetem nomes de coluna
    for i, dtype in enumerate(df.dtypes):
        if dtype.kind == "m":
            df.isetitem(i, df.iloc[:, i].map(format_timedelta))

    destination = DATA_DIR / f"{sql_path.stem}.csv"

    # Resultado vazio sobre um CSV que tinha dados é quase sempre erro de query
    # (schema errado, filtro de data), não ausência real de dados. Preservar o
    # anterior em vez de zerar o painel em silêncio.
    if df.empty and not allow_empty and has_data(destination):
        return 0, False, descartadas

    tmp = destination.with_suffix(".csv.tmp")
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, destination)          # troca atômica: nunca deixa CSV parcial
    return len(df), True, descartadas


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    queries = find_queries(args)

    if "--list" in sys.argv:
        for q in sorted(QUERIES_DIR.glob("*.sql")):
            print(f"  {q.stem:<25} -> data/{q.stem}.csv")
        return 0

    DATA_DIR.mkdir(exist_ok=True)
    print(f"Abrindo túnel SSH para {_env('SSH_HOST')}…")

    with SSHTunnelForwarder(
        (_env("SSH_HOST"), int(_env("SSH_PORT"))),
        ssh_username=_env("SSH_USER"),
        ssh_password=_env("SSH_PASSWORD"),
        remote_bind_address=(_env("DB_HOST"), int(_env("DB_PORT"))),
    ) as tunnel:
        register_safe_date_casters()
        # URL.create escapa usuário e senha. Montar a URL por concatenação quebra
        # quando a senha tem @ : / ou # — o parser corta no primeiro @ e trata o
        # resto da senha como nome de host.
        url = URL.create(
            "postgresql+psycopg2",
            username=_env("DB_USER"),
            password=_env("DB_PASSWORD"),
            host="127.0.0.1",
            port=tunnel.local_bind_port,
            database=_env("DB_NAME"),
        )
        engine = create_engine(
            url,
            # search_path replica o schema ativo que o DBeaver definia: algumas queries
            # referenciam tabelas sem prefixo (ex.: "FROM daily_operations"), e sem isso
            # elas resolvem para public.* e voltam vazias em vez de dar erro.
            connect_args={
                "sslmode": "require",
                "options": f"-c search_path={_env('DB_SCHEMA')},public",
            },
        )
        if "--schemas" in sys.argv:
            print(f"Conectado em {_env('DB_NAME')}.\n")
            print("Databases no servidor:")
            print(pd.read_sql(
                "SELECT datname FROM pg_database WHERE NOT datistemplate ORDER BY 1",
                engine).to_string(index=False))
            print(f"\nSchemas dentro de {_env('DB_NAME')} (com nº de tabelas):")
            print(pd.read_sql(
                "SELECT table_schema, COUNT(*) AS tabelas FROM information_schema.tables "
                "WHERE table_schema NOT IN ('pg_catalog', 'information_schema') "
                "GROUP BY 1 ORDER BY 1", engine).to_string(index=False))
            engine.dispose()
            return 0

        print(f"Conectado em {_env('DB_NAME')}. {len(queries)} query(s) a executar.\n")

        allow_empty = "--allow-empty" in sys.argv
        failures, empties, datas_ruins = [], [], {}
        for i, sql_path in enumerate(queries, 1):
            label = f"[{i}/{len(queries)}] {sql_path.stem}"
            started = time.monotonic()
            try:
                rows, written, descartadas = run_query(engine, sql_path, allow_empty)
                aviso = f"  [{len(descartadas)} data(s) inválida(s) -> NULL]" if descartadas else ""
                if descartadas:
                    datas_ruins[sql_path.stem] = descartadas
                if written:
                    print(f"{label:<35} {rows:>7} linhas  "
                          f"{time.monotonic() - started:5.1f}s{aviso}")
                else:
                    empties.append(sql_path.stem)
                    print(f"{label:<35} VAZIA — CSV anterior preservado{aviso}")
            except Exception as exc:
                failures.append(sql_path.stem)
                # SQLAlchemy embrulha o erro do driver; .orig traz a mensagem real do Postgres
                cause = getattr(exc, "orig", exc)
                detail = " ".join(str(cause).strip().splitlines()[:4])
                # CSV antigo é preservado — o painel continua abrindo com o dado anterior
                print(f"{label:<35} FALHOU: {detail}")

        engine.dispose()

    if datas_ruins:
        print("\nAVISO — datas inválidas no banco, gravadas como NULL:")
        for stem, valores in datas_ruins.items():
            amostra = ", ".join(sorted(set(valores))[:3])
            print(f"  {stem}: {len(valores)} ocorrência(s) — {amostra}")
        print("  São dados digitados errados na origem. Corrija no banco para recuperá-los.")

    if failures:
        print(f"\n{len(failures)} query(s) falharam (CSV anterior mantido): {', '.join(failures)}")
    if empties:
        print(f"\n{len(empties)} query(s) voltaram vazias (CSV anterior mantido): {', '.join(empties)}"
              "\nVerifique o schema/filtros da query. Se o vazio for legítimo, use --allow-empty.")
    if failures or empties:
        return 1

    print(f"\nOK — {len(queries)} CSV(s) atualizados em data/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
