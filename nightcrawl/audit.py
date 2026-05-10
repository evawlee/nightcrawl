from __future__ import annotations
import time


class AuditLog:

    _entries: list = []

    def __init__(self):
        pass

    def append(self, event: str, actor: str | None = None, target: str | None = None,
               extra: dict | None = None) -> dict:
        entry = {
            "event": event,
            "actor": actor,
            "target": target,
            "extra": dict(extra) if extra else {},
            "at": time.time(),
        }
        self._entries.append(entry)
        return dict(entry)

    def find_for_target(self, target: str) -> list:
        return [dict(e) for e in self._entries if e.get("target") == target]

    def find_by_event(self, event: str) -> list:
        return [dict(e) for e in self._entries if e.get("event") == event]

    def all_entries(self) -> list:
        return [dict(e) for e in self._entries]

    def size(self) -> int:
        return len(self._entries)

    @classmethod
    def reset(cls):
        cls._entries = []
