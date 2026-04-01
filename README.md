# Metadata-Driven File → Database → Salesforce Utility

Production-oriented reusable ETL/ELT utility for loading heterogeneous raw files into a database and then pushing curated data to Salesforce using configuration and mapping metadata.

## 1) High-Level Architecture

```mermaid
flowchart LR
  A[Raw Files\nCSV/TXT/XLSX] --> B[Ingestion + Parser]
  B --> C[Transformation Engine\n(file->db mapping)]
  C --> D[Staging Tables]
  D --> E[Validation + DQ Rules]
  E --> F[Target Tables / Views]
  F --> G[SF Mapping Engine\n(db->sf mapping)]
  G --> H[Salesforce Loader\nBulk/REST abstraction]
  H --> I[Salesforce Objects]
  B --> J[Archive/Error Folders]
  C --> K[Reject/Error Tables]
  H --> L[SF Status Tables]
  M[Config + Env Overrides] --> B
  M --> C
  M --> G
  N[Audit + Structured Logs] --> O[Ops Dashboard / Reports]
  B --> N
  C --> N
  H --> N
```

### Components
- **Ingestion Layer:** file discovery, parser selection, schema checks, archival/error routing.
- **Transformation Layer:** metadata-driven column mapping, type conversion, cleansing, required checks.
- **Database Layer:** staging/target writes, reject handling, batch/file audit.
- **Salesforce Layer:** dependency-aware loading, upsert with external IDs, response capture.
- **Configuration Framework:** base + environment override config and externalized mappings.
- **Audit/Monitoring:** JSON logs, batch/file counters, failure reason tables.

## 2) Project Structure

```text
src/etl_sf/
  ingestion/
  parsers/
  mappings/
  transformations/
  database/
  salesforce/
  audit/
  config/
  orchestration/
configs/
  base.yml
  environments/{dev,qa,uat,prod}.yml
  mappings/{file_to_db.yml,db_to_salesforce.yml}
sql/schema.sql
samples/input
samples/archive
samples/error
tests/
```

## 3) Core Capabilities

- Metadata-driven onboarding (new file/object mostly config-only)
- Supports CSV/TXT/XLSX parsers
- Header-based file mapping
- Staging + target loads
- Reject tracking with failure reason
- Dependency-based Salesforce sequencing
- Record-level Salesforce failure capture
- Multi-environment configuration (DEV/QA/UAT/PROD)
- Dry-run knob in runtime config

## 4) Database Design

`sql/schema.sql` includes:
- **Staging:** `stg_customer`, `stg_order`
- **Target:** `dim_customer`, `fact_order`
- **Audit:** `etl_batch_audit`, `etl_file_audit`
- **Error/Reject:** `etl_reject_records`
- **Salesforce Status:** `sf_record_status`

## 5) Salesforce Integration Design

- **Strategy:** Metadata defines source query + field mappings + operation
- **Upsert Key:** `external_id_field` per object mapping
- **Sequencing:** `depends_on` graph with topological sort
- **Bulk-ready:** Loader abstraction isolates API implementation; mock client included, real client can swap in
- **Error Capture:** Failed records inserted into `sf_record_status`

## 6) End-to-End Control Flow

1. Load merged environment config (`base.yml` + env override).
2. Load file-to-db and db-to-sf mapping metadata.
3. Start batch audit record.
4. For each file mapping:
   - Find matching files.
   - Parse by extension/options.
   - Transform + validate fields.
   - Write valid rows to staging + target.
   - Write rejects to reject table.
   - Write file audit + archive or error move.
5. Read target data and send to Salesforce in dependency order.
6. Write Salesforce record-level failures.
7. Close batch audit as success/failure.

## 7) Reprocessing and Idempotency

- Failed files moved to `/samples/error` for controlled replay.
- Batch and file audit rows provide traceability.
- External ID upserts avoid duplicate Salesforce records.
- Incremental/full mode controlled by mapping metadata.
- Can add high-watermark strategy with per-object watermark table for strict incremental loads.

## 8) Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 9) Run

Initialize schema + run DEV pipeline:

```bash
python -m etl_sf.main --config-root configs --env dev --init-db --ddl sql/schema.sql
```

Run only pipeline:

```bash
python -m etl_sf.main --config-root configs --env dev
```

## 10) Testing

```bash
pytest
```

## 11) Mapping Guide (Quick)

### File-to-DB mapping fields
- `file_pattern`, `target_staging_table`, `target_table`
- `parser_options` (delimiter/encoding/header)
- `column_mappings[]` with `source`, `target`, `dtype`, `required`, `default`, `transform`

### DB-to-SF mapping fields
- `source_query`, `object_name`, `operation`, `external_id_field`, `batch_size`
- `depends_on[]` for sequencing
- `field_mappings[]` with source/default to target SF field

## 12) Troubleshooting

- **No files picked up:** verify `paths.input_dir` and mapping `file_pattern`.
- **Parser errors:** validate delimiter, quotechar, encoding in mapping.
- **Unexpected rejects:** inspect `etl_reject_records` for row and reason.
- **Salesforce failures:** inspect `sf_record_status` payload + error.
- **Wrong environment settings:** verify selected `--env` and override YAML.

## 13) Bonus Integration Patterns

- Scheduler: cron/Airflow/GitHub Actions invoking CLI.
- Notifications: add post-run hook (Slack/Teams/Email).
- Lightweight UI: FastAPI page triggering `ETLPipeline.run()` and rendering audits.
- Dry-run: set `runtime.dry_run` and short-circuit write operations.
- Reconciliation report: compare source counts vs target vs SF success.
