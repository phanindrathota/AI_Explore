from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SalesforceResult:
    success: int
    failed: int
    errors: list[dict[str, Any]]


class SalesforceClient:
    def upsert(self, object_name: str, records: list[dict[str, Any]], external_id_field: str | None = None) -> SalesforceResult:
        raise NotImplementedError


class MockSalesforceClient(SalesforceClient):
    def upsert(self, object_name: str, records: list[dict[str, Any]], external_id_field: str | None = None) -> SalesforceResult:
        errors: list[dict[str, Any]] = []
        success = 0
        for rec in records:
            if any(v is None for v in rec.values()):
                errors.append({"object": object_name, "record": rec, "error": "null field"})
            else:
                success += 1
        return SalesforceResult(success=success, failed=len(errors), errors=errors)
