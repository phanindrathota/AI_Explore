from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class JobState:
    job_id: str
    env: str
    status: str = "PENDING"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    events: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobState] = {}
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._lock = threading.Lock()

    def create_job(self, env: str) -> JobState:
        job = JobState(job_id=str(uuid.uuid4()), env=env)
        with self._lock:
            self._jobs[job.job_id] = job
            self._subscribers[job.job_id] = []
        return job

    def update(self, job_id: str, status: str | None = None, event: dict[str, Any] | None = None) -> None:
        with self._lock:
            job = self._jobs[job_id]
            if status:
                job.status = status
            if event:
                job.events.append(event)
            job.updated_at = datetime.utcnow().isoformat()
            subscribers = list(self._subscribers.get(job_id, []))

        for q in subscribers:
            try:
                q.put_nowait({"job_id": job_id, "status": job.status, "event": event})
            except asyncio.QueueFull:
                continue

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "SUCCESS"
            job.result = result
            job.updated_at = datetime.utcnow().isoformat()
            subscribers = list(self._subscribers.get(job_id, []))
        for q in subscribers:
            q.put_nowait({"job_id": job_id, "status": "SUCCESS", "result": result})

    def fail(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "FAILED"
            job.error = error
            job.updated_at = datetime.utcnow().isoformat()
            subscribers = list(self._subscribers.get(job_id, []))
        for q in subscribers:
            q.put_nowait({"job_id": job_id, "status": "FAILED", "error": error})

    def get(self, job_id: str) -> JobState:
        return self._jobs[job_id]

    def list_jobs(self) -> list[JobState]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        with self._lock:
            self._subscribers.setdefault(job_id, []).append(q)
        return q

    def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        with self._lock:
            if job_id in self._subscribers and queue in self._subscribers[job_id]:
                self._subscribers[job_id].remove(queue)


def run_in_background(func: Callable[[], None]) -> None:
    thread = threading.Thread(target=func, daemon=True)
    thread.start()
