from __future__ import annotations

import argparse
from pathlib import Path

from etl_sf.database.repository import DatabaseRepository
from etl_sf.orchestration.pipeline import ETLPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run metadata-driven ETL to Salesforce")
    parser.add_argument("--config-root", default="configs")
    parser.add_argument("--env", default="dev")
    parser.add_argument("--init-db", action="store_true", help="Initialize schema before run")
    parser.add_argument("--ddl", default="sql/schema.sql")
    args = parser.parse_args()

    pipeline = ETLPipeline(Path(args.config_root), args.env)
    if args.init_db:
        ddl = Path(args.ddl).read_text(encoding="utf-8")
        DatabaseRepository(pipeline.engine).init_schema(ddl)

    summary = pipeline.run()
    print(summary)


if __name__ == "__main__":
    main()
