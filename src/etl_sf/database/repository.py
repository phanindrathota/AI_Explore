from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass
class WriteResult:
    table: str
    row_count: int


class DatabaseRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def init_schema(self, ddl_sql: str) -> None:
        statements = [s.strip() for s in ddl_sql.split(";") if s.strip()]
        with self.engine.begin() as conn:
            for st in statements:
                conn.execute(text(st))

    def write_dataframe(self, df: pd.DataFrame, table: str, if_exists: str = "append") -> WriteResult:
        df.to_sql(table, self.engine, if_exists=if_exists, index=False)
        return WriteResult(table=table, row_count=len(df))

    def fetch_rows(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.engine.begin() as conn:
            rows = conn.execute(text(query), params or {})
            return [dict(r._mapping) for r in rows]

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> None:
        with self.engine.begin() as conn:
            conn.execute(text(sql), params or {})
