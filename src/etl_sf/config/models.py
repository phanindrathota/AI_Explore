from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    backoff_seconds: int = 5


class AppPaths(BaseModel):
    input_dir: Path
    archive_dir: Path
    error_dir: Path
    logs_dir: Path


class DatabaseConfig(BaseModel):
    url: str
    schema: str = "main"


class SalesforceConfig(BaseModel):
    auth_mode: str = "mock"
    instance_url: str | None = None
    username: str | None = None
    password_env: str | None = None
    token_env: str | None = None
    api_version: str = "58.0"
    use_bulk_api: bool = True


class RuntimeConfig(BaseModel):
    batch_size: int = 1000
    dry_run: bool = False
    incremental_mode: bool = True
    enabled_objects: dict[str, bool] = Field(default_factory=dict)


class EnvironmentConfig(BaseModel):
    name: str
    paths: AppPaths
    database: DatabaseConfig
    salesforce: SalesforceConfig
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    logging_level: str = "INFO"


class MappingBundle(BaseModel):
    file_to_db_path: Path
    db_to_sf_path: Path


class JobContext(BaseModel):
    env: EnvironmentConfig
    mappings: MappingBundle
    run_id: str
    extras: dict[str, Any] = Field(default_factory=dict)
