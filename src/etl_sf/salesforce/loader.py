from __future__ import annotations

from collections import defaultdict, deque

from etl_sf.database.repository import DatabaseRepository
from etl_sf.mappings.interpreter import SalesforceMapping
from etl_sf.salesforce.client import SalesforceClient


class SalesforceLoader:
    def __init__(self, db: DatabaseRepository, client: SalesforceClient) -> None:
        self.db = db
        self.client = client

    def run(self, mappings: list[SalesforceMapping]) -> dict[str, dict[str, int]]:
        ordered = self._topological_sort(mappings)
        summary: dict[str, dict[str, int]] = {}

        for m in ordered:
            rows = self.db.fetch_rows(m.source_query)
            payload = [self._map_row(r, m.field_mappings) for r in rows]
            result = self.client.upsert(m.object_name, payload, external_id_field=m.external_id_field)
            summary[m.object_name] = {"success": result.success, "failed": result.failed}
            for err in result.errors:
                self.db.execute(
                    """
                    INSERT INTO sf_record_status(object_name, status, error_message, payload)
                    VALUES (:obj, 'FAILED', :err, :payload)
                    """,
                    {
                        "obj": m.object_name,
                        "err": err["error"],
                        "payload": str(err["record"]),
                    },
                )
        return summary

    @staticmethod
    def _map_row(row: dict, field_mappings: list[dict]) -> dict:
        out = {}
        for fm in field_mappings:
            if "source" in fm:
                out[fm["target"]] = row.get(fm["source"])
            else:
                out[fm["target"]] = fm.get("default")
        return out

    @staticmethod
    def _topological_sort(mappings: list[SalesforceMapping]) -> list[SalesforceMapping]:
        name_to_map = {m.object_name: m for m in mappings}
        graph = defaultdict(list)
        indegree = {m.object_name: 0 for m in mappings}
        for m in mappings:
            for dep in m.depends_on:
                graph[dep].append(m.object_name)
                indegree[m.object_name] += 1

        q = deque([n for n, d in indegree.items() if d == 0])
        order = []
        while q:
            node = q.popleft()
            order.append(name_to_map[node])
            for nxt in graph[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    q.append(nxt)
        if len(order) != len(mappings):
            raise ValueError("Cycle detected in Salesforce dependency graph")
        return order
