# Sample Run Walkthrough

1. Place files under `samples/input`:
   - `customers_20260328.csv`
   - `orders_20260328.txt`
2. Initialize DB schema and run pipeline.
3. Utility applies mapping from `configs/mappings/file_to_db.yml`.
4. Missing required `CustomerID` record is rejected to `etl_reject_records`.
5. Valid rows are loaded into staging/target tables.
6. Salesforce mappings from `db_to_salesforce.yml` build payloads for `Account` then `Order__c`.
7. Mock Salesforce returns per-record result and errors are saved to `sf_record_status`.
8. Processed files are moved to `samples/archive`.
