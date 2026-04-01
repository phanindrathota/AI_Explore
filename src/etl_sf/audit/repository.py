from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass
class FileAudit:
    run_id: str
    file_name: str
    status: str
    rows_read: int = 0
    rows_loaded: int = 0
    rows_rejected: int = 0
    error_message: str | None = None


class AuditRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def start_batch(self, run_id: str, env_name: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO etl_batch_audit(run_id, env_name, start_ts, status)
                    VALUES (:run_id, :env_name, :start_ts, 'RUNNING')
                    """
                ),
                {"run_id": run_id, "env_name": env_name, "start_ts": datetime.utcnow()},
            )

    def close_batch(self, run_id: str, status: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE etl_batch_audit
                    SET end_ts = :end_ts, status = :status
                    WHERE run_id = :run_id
                    """
                ),
                {"run_id": run_id, "status": status, "end_ts": datetime.utcnow()},
            )

    def upsert_file_audit(self, event: FileAudit) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO etl_file_audit
                    (run_id, file_name, status, rows_read, rows_loaded, rows_rejected, error_message)
                    VALUES (:run_id, :file_name, :status, :rows_read, :rows_loaded, :rows_rejected, :error_message)
                    """
                ),
                event.__dict__,
            )
