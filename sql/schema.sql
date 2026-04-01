CREATE TABLE IF NOT EXISTS stg_customer (
  customer_id TEXT,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  status TEXT,
  signup_date TEXT
);

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_id TEXT PRIMARY KEY,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  status TEXT,
  signup_date TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_order (
  order_id TEXT,
  customer_id TEXT,
  amount REAL,
  order_date TEXT
);

CREATE TABLE IF NOT EXISTS fact_order (
  order_id TEXT PRIMARY KEY,
  customer_id TEXT,
  amount REAL,
  order_date TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS etl_batch_audit (
  run_id TEXT PRIMARY KEY,
  env_name TEXT,
  start_ts TEXT,
  end_ts TEXT,
  status TEXT
);

CREATE TABLE IF NOT EXISTS etl_file_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT,
  file_name TEXT,
  status TEXT,
  rows_read INTEGER,
  rows_loaded INTEGER,
  rows_rejected INTEGER,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS etl_reject_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  row_num INTEGER,
  column TEXT,
  reason TEXT,
  file_name TEXT
);

CREATE TABLE IF NOT EXISTS sf_record_status (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  object_name TEXT,
  status TEXT,
  error_message TEXT,
  payload TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
