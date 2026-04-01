from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
from flask import Flask, redirect, render_template, request, send_file, url_for

app = Flask(__name__)

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "trade_logs.csv"

COLUMNS = [
    "date",
    "expiration_date",
    "ticker",
    "entry_price",
    "exit_price",
    "expected_return_pct",
    "profit_loss",
    "profit_loss_pct",
    "running_total_profits",
    "reason_for_trade",
]


def ensure_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)


def load_logs() -> pd.DataFrame:
    ensure_storage()
    df = pd.read_csv(DATA_FILE)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = "" if col in {"ticker", "reason_for_trade"} else 0

    for col in ["entry_price", "exit_price", "expected_return_pct", "profit_loss", "running_total_profits"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    if "profit_loss_pct" not in df.columns:
        df["profit_loss_pct"] = 0.0
    df["profit_loss_pct"] = pd.to_numeric(df["profit_loss_pct"], errors="coerce").fillna(0.0)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["expiration_date"] = pd.to_datetime(df["expiration_date"], errors="coerce")

    df = df.dropna(subset=["date"]).sort_values("date")
    return df


def save_logs(df: pd.DataFrame) -> None:
    ensure_storage()
    df_out = df.copy()
    if not df_out.empty:
        df_out["date"] = df_out["date"].dt.strftime("%Y-%m-%d")
        df_out["expiration_date"] = df_out["expiration_date"].dt.strftime("%Y-%m-%d")
    df_out.to_csv(DATA_FILE, index=False)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "Date": "date",
        "Expiration date": "expiration_date",
        "Ticker": "ticker",
        "Entry price": "entry_price",
        "Exit price": "exit_price",
        "Expected return %": "expected_return_pct",
        "Running total profits": "running_total_profits",
        "Reason for trade": "reason_for_trade",
    }
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = "" if col in {"ticker", "reason_for_trade"} else 0

    for col in ["entry_price", "exit_price", "expected_return_pct", "running_total_profits"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["expiration_date"] = pd.to_datetime(df["expiration_date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["profit_loss"] = df["exit_price"] - df["entry_price"]
    df["profit_loss_pct"] = df.apply(
        lambda row: ((row["exit_price"] - row["entry_price"]) / row["entry_price"] * 100)
        if row["entry_price"]
        else 0.0,
        axis=1,
    )

    if (df["running_total_profits"] == 0).all() and not df.empty:
        df["running_total_profits"] = df["profit_loss"].cumsum()

    return df[COLUMNS]


def build_summary(df: pd.DataFrame) -> Dict[str, List[Dict[str, object]]]:
    if df.empty:
        return {"year": [], "week": [], "day": []}

    temp = df.copy()
    temp["year"] = temp["date"].dt.year
    temp["week"] = temp["date"].dt.isocalendar().week
    temp["day"] = temp["date"].dt.date

    year = (
        temp.groupby("year", as_index=False)["profit_loss"]
        .sum()
        .sort_values("year", ascending=False)
        .to_dict("records")
    )
    week = (
        temp.groupby(["year", "week"], as_index=False)["profit_loss"]
        .sum()
        .sort_values(["year", "week"], ascending=[False, False])
        .to_dict("records")
    )
    day = (
        temp.groupby("day", as_index=False)["profit_loss"]
        .sum()
        .sort_values("day", ascending=False)
        .to_dict("records")
    )

    return {"year": year, "week": week, "day": day}


@app.route("/", methods=["GET"])
def index():
    df = load_logs()

    year_filter = request.args.get("year", "").strip()
    week_filter = request.args.get("week", "").strip()
    day_filter = request.args.get("day", "").strip()

    filtered = df.copy()
    if year_filter:
        filtered = filtered[filtered["date"].dt.year == int(year_filter)]
    if week_filter:
        filtered = filtered[filtered["date"].dt.isocalendar().week == int(week_filter)]
    if day_filter:
        filtered = filtered[filtered["date"].dt.strftime("%Y-%m-%d") == day_filter]

    records = []
    if not filtered.empty:
        rows = filtered.sort_values("date", ascending=False).to_dict("records")
        for row in rows:
            row["date"] = row["date"].strftime("%Y-%m-%d")
            row["expiration_date"] = row["expiration_date"].strftime("%Y-%m-%d")
            records.append(row)

    totals = {
        "trade_count": len(filtered),
        "profit_loss": float(filtered["profit_loss"].sum()) if not filtered.empty else 0.0,
        "avg_return_pct": float(filtered["profit_loss_pct"].mean()) if not filtered.empty else 0.0,
    }

    years = sorted(df["date"].dt.year.unique().tolist(), reverse=True) if not df.empty else []
    weeks = sorted(df["date"].dt.isocalendar().week.unique().tolist(), reverse=True) if not df.empty else []

    summary = build_summary(df)

    return render_template(
        "index.html",
        records=records,
        years=years,
        weeks=weeks,
        selected={"year": year_filter, "week": week_filter, "day": day_filter},
        totals=totals,
        summary=summary,
    )


@app.route("/add", methods=["POST"])
def add_trade():
    df = load_logs()

    entry = float(request.form.get("entry_price", 0) or 0)
    exit_price = float(request.form.get("exit_price", 0) or 0)
    pnl = exit_price - entry
    pnl_pct = (pnl / entry * 100) if entry else 0.0

    running_total = request.form.get("running_total_profits", "").strip()
    if running_total:
        running_total_value = float(running_total)
    else:
        current = float(df["running_total_profits"].iloc[-1]) if not df.empty else 0.0
        running_total_value = current + pnl

    new_row = pd.DataFrame(
        [
            {
                "date": pd.to_datetime(request.form.get("date"), errors="coerce"),
                "expiration_date": pd.to_datetime(request.form.get("expiration_date"), errors="coerce"),
                "ticker": request.form.get("ticker", "").strip().upper(),
                "entry_price": entry,
                "exit_price": exit_price,
                "expected_return_pct": float(request.form.get("expected_return_pct", 0) or 0),
                "profit_loss": pnl,
                "profit_loss_pct": pnl_pct,
                "running_total_profits": running_total_value,
                "reason_for_trade": request.form.get("reason_for_trade", "").strip(),
            }
        ]
    )

    merged = pd.concat([df, new_row], ignore_index=True)
    merged = merged.dropna(subset=["date", "expiration_date"])
    save_logs(merged)
    return redirect(url_for("index"))


@app.route("/upload", methods=["POST"])
def upload():
    uploaded = request.files.get("trade_file")
    if not uploaded or not uploaded.filename:
        return redirect(url_for("index"))

    if uploaded.filename.endswith(".csv"):
        incoming = pd.read_csv(uploaded)
    else:
        incoming = pd.read_excel(uploaded)

    incoming = normalize_columns(incoming)
    existing = load_logs()

    combined = pd.concat([existing, incoming], ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)

    if combined["running_total_profits"].eq(0).all() and not combined.empty:
        combined["running_total_profits"] = combined["profit_loss"].cumsum()

    save_logs(combined)
    return redirect(url_for("index"))


@app.route("/export", methods=["GET"])
def export_data():
    ensure_storage()
    return send_file(DATA_FILE, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
