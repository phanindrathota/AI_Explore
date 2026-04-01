from sqlalchemy import create_engine

from etl_sf.database.repository import DatabaseRepository
from etl_sf.mappings.interpreter import SalesforceMapping
from etl_sf.salesforce.client import MockSalesforceClient
from etl_sf.salesforce.loader import SalesforceLoader


def test_salesforce_loader_dependency_and_failure_capture():
    engine = create_engine("sqlite:///:memory:", future=True)
    db = DatabaseRepository(engine)
    db.init_schema(
        """
        CREATE TABLE dim_customer (customer_id TEXT, first_name TEXT, last_name TEXT, email TEXT, status TEXT);
        CREATE TABLE sf_record_status (id INTEGER PRIMARY KEY AUTOINCREMENT, object_name TEXT, status TEXT, error_message TEXT, payload TEXT);
        INSERT INTO dim_customer VALUES ('C1', 'Ada', 'Lovelace', NULL, 'ACTIVE');
        """
    )

    mappings = [
        SalesforceMapping(
            source_query="SELECT customer_id, first_name, last_name, email, status FROM dim_customer",
            object_name="Account",
            operation="upsert",
            external_id_field="External_Customer_Id__c",
            batch_size=100,
            field_mappings=[
                {"source": "customer_id", "target": "External_Customer_Id__c"},
                {"source": "first_name", "target": "FirstName"},
                {"source": "email", "target": "PersonEmail"},
            ],
            depends_on=[],
        )
    ]

    loader = SalesforceLoader(db, MockSalesforceClient())
    summary = loader.run(mappings)
    failures = db.fetch_rows("SELECT * FROM sf_record_status")

    assert summary["Account"]["failed"] == 1
    assert len(failures) == 1
