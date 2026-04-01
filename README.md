# Trade Log Portal

A Flask-based portal to track and analyze trading logs with:

- Manual trade entry
- Excel/CSV upload
- Persistent local storage (`data/trade_logs.csv`)
- Color-coded P/L and trade reasons
- Year-wise, week-wise, and day-wise summaries
- CSV export

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Expected upload columns

- Date
- Expiration date
- Ticker
- Entry price
- Exit price
- Expected return % (optional)
- Running total profits (optional)
- Reason for trade

`profit_loss` is calculated automatically as `Exit price - Entry price`.
