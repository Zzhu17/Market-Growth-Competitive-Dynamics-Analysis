#!/usr/bin/env python
"""Materialize marts from SQL into parquet (primary) and CSV (published)."""
from __future__ import annotations

from pathlib import Path
import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = REPO_ROOT / "sql"
MARTS_DIR = REPO_ROOT / "data" / "marts"
PUBLISHED_DIR = REPO_ROOT / "data" / "published"

MARTS = {
    "marts_market_trends": SQL_DIR / "marts_market_trends.sql",
    "marts_growth_contribution": SQL_DIR / "marts_growth_contribution.sql",
}


def _run_query(con: duckdb.DuckDBPyConnection, sql_path: Path):
    sql = sql_path.read_text(encoding="utf-8")
    return con.execute(sql).df()


def _write(df, name: str) -> None:
    MARTS_DIR.mkdir(parents=True, exist_ok=True)
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

    parquet_path = MARTS_DIR / f"{name}.parquet"
    csv_path = PUBLISHED_DIR / f"{name}.csv"

    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)

    print(f"wrote {parquet_path}")
    print(f"wrote {csv_path}")


def main() -> int:
    con = duckdb.connect()
    for name, sql_path in MARTS.items():
        if not sql_path.exists():
            raise FileNotFoundError(f"missing SQL: {sql_path}")
        df = _run_query(con, sql_path)
        _write(df, name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
