from __future__ import annotations

import json
import logging
from pathlib import Path


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
        }
        if hasattr(record, "run_id"):
            payload["run_id"] = record.run_id
        return json.dumps(payload)


def configure_logging(level: str, logs_dir: Path) -> logging.Logger:
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("etl_sf")
    logger.setLevel(level)
    logger.handlers.clear()

    stream = logging.StreamHandler()
    stream.setFormatter(JsonFormatter())
    file_handler = logging.FileHandler(logs_dir / "etl_sf.log")
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(stream)
    logger.addHandler(file_handler)
    return logger
