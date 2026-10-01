"""
refresh_data.py – executa cada query de queries/*.sql contra o banco de produção
(via túnel SSH) e regrava o CSV correspondente em data/.

O nome do arquivo manda: queries/tab_orders.sql  ->  data/tab_orders.csv

Uso:
    python refresh_data.py                    # atualiza todos os CSVs
    python refresh_data.py tab_orders         # atualiza só os informados
    python refresh_data.py --list             # lista as queries encontradas

Cada CSV é escrito primeiro num arquivo temporário e só então substitui o
antigo, de modo que uma query que falhe nunca deixa um CSV pela metade.
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder

BASE_DIR = Path(__file__).parent
QUERIES_DIR = BASE_DIR / "queries"
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")


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


def run_query(engine, sql_path: Path) -> int:
    """Executa uma query e substitui o CSV de destino. Retorna nº de linhas."""
    df = pd.read_sql(sql_path.read_text(encoding="utf-8"), engine)

    destination = DATA_DIR / f"{sql_path.stem}.csv"
    tmp = destination.with_suffix(".csv.tmp")
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, destination)          # troca atômica: nunca deixa CSV parcial
    return len(df)


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
        engine = create_engine(
            f"postgresql+psycopg2://{_env('DB_USER')}:{_env('DB_PASSWORD')}"
            f"@127.0.0.1:{tunnel.local_bind_port}/{_env('DB_NAME')}",
            connect_args={"sslmode": "require"},
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

        failures = []
        for i, sql_path in enumerate(queries, 1):
            label = f"[{i}/{len(queries)}] {sql_path.stem}"
            started = time.monotonic()
            try:
                rows = run_query(engine, sql_path)
                print(f"{label:<35} {rows:>7} linhas  {time.monotonic() - started:5.1f}s")
            except Exception as exc:
                failures.append(sql_path.stem)
                # SQLAlchemy embrulha o erro do driver; .orig traz a mensagem real do Postgres
                cause = getattr(exc, "orig", exc)
                detail = " ".join(str(cause).strip().splitlines()[:4])
                # CSV antigo é preservado — o painel continua abrindo com o dado anterior
                print(f"{label:<35} FALHOU: {detail}")

        engine.dispose()

    if failures:
        print(f"\n{len(failures)} query(s) falharam (CSV anterior mantido): {', '.join(failures)}")
        return 1

    print(f"\nOK — {len(queries)} CSV(s) atualizados em data/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
