from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from etl_sf.config.models import EnvironmentConfig, MappingBundle


class ConfigError(RuntimeError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_environment_config(config_root: Path, env_name: str) -> EnvironmentConfig:
    base = _load_yaml(config_root / "base.yml")
    env_overrides = _load_yaml(config_root / "environments" / f"{env_name.lower()}.yml")
    merged = _deep_merge(base, env_overrides)
    merged["name"] = env_name.upper()
    _resolve_env_vars(merged)
    return EnvironmentConfig.model_validate(merged)


def load_mappings(mapping_root: Path) -> MappingBundle:
    return MappingBundle(
        file_to_db_path=mapping_root / "file_to_db.yml",
        db_to_sf_path=mapping_root / "db_to_salesforce.yml",
    )


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _resolve_env_vars(data: Any) -> Any:
    if isinstance(data, dict):
        for k, v in data.items():
            data[k] = _resolve_env_vars(v)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            data[i] = _resolve_env_vars(v)
    elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
        env_key = data[2:-1]
        return os.getenv(env_key, "")
    return data
