from __future__ import annotations

from pathlib import Path

import pandas as pd


class ParserFactory:
    @staticmethod
    def read_file(path: Path, options: dict) -> pd.DataFrame:
        suffix = path.suffix.lower()
        if suffix in {".csv", ".txt", ".dat"}:
            return pd.read_csv(
                path,
                delimiter=options.get("delimiter", ","),
                quotechar=options.get("quotechar", '"'),
                encoding=options.get("encoding", "utf-8"),
                header=0 if options.get("has_header", True) else None,
            )
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path, sheet_name=options.get("sheet_name", 0))
        raise ValueError(f"Unsupported file type: {suffix}")
