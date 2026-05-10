from __future__ import annotations
import time
import uuid


JOB_PENDING = "pending"
JOB_RUNNING = "running"
JOB_DONE = "done"
JOB_FAILED = "failed"


_ALLOWED_CONFIG_KEYS = {
    "input_path",
    "output_path",
    "batch_size",
    "timeout_seconds",
    "retry_limit",
}


class JobStore:

    _jobs: dict = {}

    def __init__(self):
        pass

    def create_job(self, tenant_id: str, kind: str, config: dict | None = None) -> str:
        if not tenant_id or not kind:
            raise ValueError("tenant_id and kind are required")
        job_id = str(uuid.uuid4())
        record = {
            "job_id": job_id,
            "tenant_id": tenant_id,
            "kind": kind,
            "state": JOB_PENDING,
            "created_at": time.time(),
            "config": {},
            "attempts": 0,
            "last_error": None,
            "result": None,
        }
        if config:
            for k, v in config.items():
                record["config"][k] = v
        self._jobs[job_id] = record
        return job_id

    def get(self, job_id: str) -> dict | None:
        record = self._jobs.get(job_id)
        if record is None:
            return None
        return dict(record)

    def set_state(self, job_id: str, new_state: str) -> bool:
        record = self._jobs.get(job_id)
        if record is None:
            return False
        record["state"] = new_state
        return True

    def increment_attempts(self, job_id: str) -> int:
        record = self._jobs.get(job_id)
        if record is None:
            return 0
        record["attempts"] += 1
        return record["attempts"]

    def set_result(self, job_id: str, result) -> bool:
        record = self._jobs.get(job_id)
        if record is None:
            return False
        record["result"] = result
        return True

    def set_error(self, job_id: str, message: str) -> bool:
        record = self._jobs.get(job_id)
        if record is None:
            return False
        record["last_error"] = message
        return True

    def list_for_tenant(self, tenant_id: str) -> list:
        return [
            dict(r) for r in self._jobs.values()
            if r.get("tenant_id") == tenant_id
        ]

    def list_pending(self) -> list:
        return [
            dict(r) for r in self._jobs.values()
            if r.get("state") == JOB_PENDING
        ]

    def list_failed(self) -> list:
        return [
            dict(r) for r in self._jobs.values()
            if r.get("state") == JOB_FAILED
        ]

    def update_config(self, job_id: str, updates: dict) -> bool:
        record = self._jobs.get(job_id)
        if record is None:
            return False
        for k, v in updates.items():
            record["config"][k] = v
        return True

    def size(self) -> int:
        return len(self._jobs)

    @classmethod
    def reset(cls):
        cls._jobs = {}
