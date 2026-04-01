from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class FileMapping:
    file_pattern: str
    target_staging_table: str
    target_table: str
    parser_options: dict[str, Any]
    column_mappings: list[dict[str, Any]]
    primary_key: list[str]
    load_mode: str = "incremental"


@dataclass
class SalesforceMapping:
    source_query: str
    object_name: str
    operation: str
    external_id_field: str | None
    batch_size: int
    field_mappings: list[dict[str, Any]]
    depends_on: list[str]


def load_file_mappings(path: Path) -> list[FileMapping]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [FileMapping(**item) for item in data.get("file_mappings", [])]


def load_sf_mappings(path: Path) -> list[SalesforceMapping]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [SalesforceMapping(**item) for item in data.get("salesforce_mappings", [])]
