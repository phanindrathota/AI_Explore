# Implementation Notes

## Security
- Do not hardcode Salesforce secrets.
- Use env var references in config (`${SF_USERNAME}` pattern supported).
- For production use secret manager integration (Vault/AWS/Azure Key Vault).

## Extensibility
- Add a new inbound file by appending a new `file_mappings` entry.
- Add a new Salesforce object by appending `salesforce_mappings` entry and dependencies.
- Add new transforms by extending `TransformEngine`.
- Add new parser by extending `ParserFactory`.

## Performance Guidance
- Use chunked `pandas.read_csv(..., chunksize=...)` for very large files.
- Partition large staging tables and index business keys.
- Replace mock Salesforce client with Bulk API 2.0 implementation.

## Enterprise Hardening To Add
- SCD handling in target tables.
- Data quality rules in metadata DSL.
- Hash-based dedup keys.
- Checkpoint/watermark table.
- Distributed execution via Spark for high volume.
