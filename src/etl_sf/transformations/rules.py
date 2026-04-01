from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


class TransformEngine:
    @staticmethod
    def apply(df: pd.DataFrame, column_mappings: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
        out = pd.DataFrame()
        rejects: list[dict[str, Any]] = []

        for mapping in column_mappings:
            src = mapping.get("source")
            tgt = mapping["target"]
            default = mapping.get("default")
            dtype = mapping.get("dtype", "str")
            required = mapping.get("required", False)
            transform = mapping.get("transform")

            series = df[src] if src in df.columns else pd.Series([default] * len(df))
            if default is not None:
                series = series.fillna(default)
            if transform == "trim":
                series = series.astype(str).str.strip()
            if transform == "upper":
                series = series.astype(str).str.upper()
            if transform == "date_iso":
                series = pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d")

            casted = TransformEngine._cast(series, dtype)
            out[tgt] = casted

            if required:
                missing_idx = casted[casted.isna() | (casted.astype(str).str.strip() == "")].index
                for idx in missing_idx:
                    rejects.append({"row_num": int(idx), "column": tgt, "reason": "required field missing"})

        reject_df = pd.DataFrame(rejects)
        if not reject_df.empty:
            bad_rows = reject_df["row_num"].unique().tolist()
            out_valid = out.drop(index=bad_rows)
        else:
            out_valid = out
        return out_valid, reject_df

    @staticmethod
    def _cast(series: pd.Series, dtype: str) -> pd.Series:
        if dtype == "int":
            return pd.to_numeric(series, errors="coerce").astype("Int64")
        if dtype == "float":
            return pd.to_numeric(series, errors="coerce")
        if dtype == "date":
            return pd.to_datetime(series, errors="coerce").dt.date
        if dtype == "timestamp":
            return pd.to_datetime(series, errors="coerce")
        if dtype == "bool":
            return series.astype(str).str.lower().isin({"true", "1", "y", "yes"})
        if dtype == "str":
            return series.astype(str)
        raise ValueError(f"Unsupported dtype {dtype} at {datetime.utcnow().isoformat()}")
