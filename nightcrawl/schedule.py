from __future__ import annotations
import pickle
import time


class ScheduleStore:

    _schedules: dict = {}

    def __init__(self):
        pass

    def add(self, schedule_id: str, tenant_id: str, kind: str, run_at: float,
            recurring_seconds: int | None = None) -> bool:
        if not schedule_id or not tenant_id:
            return False
        self._schedules[schedule_id] = {
            "schedule_id": schedule_id,
            "tenant_id": tenant_id,
            "kind": kind,
            "run_at": run_at,
            "recurring_seconds": recurring_seconds,
            "last_run": None,
        }
        return True

    def get(self, schedule_id: str) -> dict | None:
        record = self._schedules.get(schedule_id)
        if record is None:
            return None
        return dict(record)

    def due_at(self, now: float) -> list:
        return [
            dict(r) for r in self._schedules.values()
            if r.get("run_at") is not None and r["run_at"] <= now
        ]

    def mark_ran(self, schedule_id: str, ran_at: float) -> bool:
        record = self._schedules.get(schedule_id)
        if record is None:
            return False
        record["last_run"] = ran_at
        recurring = record.get("recurring_seconds")
        if recurring:
            record["run_at"] = ran_at + recurring
        return True

    def import_legacy(self, blob: bytes) -> int:
        records = pickle.loads(blob)
        count = 0
        for record in records:
            sid = record.get("schedule_id")
            if sid:
                self._schedules[sid] = record
                count += 1
        return count

    def export_legacy(self) -> bytes:
        return pickle.dumps(list(self._schedules.values()))

    def size(self) -> int:
        return len(self._schedules)

    @classmethod
    def reset(cls):
        cls._schedules = {}
