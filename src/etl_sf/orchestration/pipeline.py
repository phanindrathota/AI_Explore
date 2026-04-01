from __future__ import annotations

import uuid
from pathlib import Path

from etl_sf.audit.logger import configure_logging
from etl_sf.audit.repository import AuditRepository, FileAudit
from etl_sf.config.loader import load_environment_config, load_mappings
from etl_sf.database.engine import build_engine
from etl_sf.database.repository import DatabaseRepository
from etl_sf.ingestion.file_ingestor import FileIngestor
from etl_sf.mappings.interpreter import load_file_mappings, load_sf_mappings
from etl_sf.parsers.factory import ParserFactory
from etl_sf.salesforce.client import MockSalesforceClient
from etl_sf.salesforce.loader import SalesforceLoader
from etl_sf.transformations.rules import TransformEngine


class ETLPipeline:
    def __init__(self, config_root: Path, env_name: str) -> None:
        self.env = load_environment_config(config_root, env_name)
        mappings = load_mappings(config_root / "mappings")
        self.file_mappings = load_file_mappings(mappings.file_to_db_path)
        self.sf_mappings = load_sf_mappings(mappings.db_to_sf_path)

        self.engine = build_engine(self.env.database.url)
        self.db = DatabaseRepository(self.engine)
        self.audit = AuditRepository(self.engine)
        self.logger = configure_logging(self.env.logging_level, self.env.paths.logs_dir)
        self.ingestor = FileIngestor(self.env.paths.input_dir, self.env.paths.archive_dir, self.env.paths.error_dir)
        self.sf_loader = SalesforceLoader(self.db, MockSalesforceClient())

    def run(self) -> dict:
        run_id = str(uuid.uuid4())
        self.audit.start_batch(run_id, self.env.name)

        file_summary: dict[str, dict] = {}
        try:
            for mapping in self.file_mappings:
                for file in self.ingestor.list_files(mapping):
                    try:
                        raw = ParserFactory.read_file(file, mapping.parser_options)
                        transformed, rejects = TransformEngine.apply(raw, mapping.column_mappings)
                        self.db.write_dataframe(transformed, mapping.target_staging_table)
                        self.db.write_dataframe(transformed, mapping.target_table)
                        if not rejects.empty:
                            rejects["file_name"] = file.name
                            self.db.write_dataframe(rejects, "etl_reject_records")

                        self.audit.upsert_file_audit(
                            FileAudit(
                                run_id=run_id,
                                file_name=file.name,
                                status="SUCCESS",
                                rows_read=len(raw),
                                rows_loaded=len(transformed),
                                rows_rejected=len(rejects),
                            )
                        )
                        file_summary[file.name] = {
                            "rows_read": len(raw),
                            "rows_loaded": len(transformed),
                            "rows_rejected": len(rejects),
                        }
                        self.ingestor.archive(file)
                    except Exception as exc:
                        self.ingestor.move_to_error(file)
                        self.audit.upsert_file_audit(
                            FileAudit(run_id=run_id, file_name=file.name, status="FAILED", error_message=str(exc))
                        )
                        self.logger.exception("file-processing-failed", extra={"run_id": run_id})

            sf_summary = self.sf_loader.run(self.sf_mappings)
            self.audit.close_batch(run_id, "SUCCESS")
            return {"run_id": run_id, "files": file_summary, "salesforce": sf_summary}
        except Exception:
            self.audit.close_batch(run_id, "FAILED")
            self.logger.exception("batch-failed", extra={"run_id": run_id})
            raise
