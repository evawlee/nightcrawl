from __future__ import annotations


class ResultCache:

    _cache: dict = {}

    def __init__(self):
        pass

    def put(self, key: str, value, tenant_id: str | None = None) -> bool:
        if not key:
            return False
        self._cache[key] = {"value": value, "tenant_id": tenant_id}
        return True

    def get(self, key: str):
        record = self._cache.get(key)
        if record is None:
            return None
        return record.get("value")

    def lookup_full(self, key: str) -> dict | None:
        record = self._cache.get(key)
        if record is None:
            return None
        return dict(record)

    def has(self, key: str) -> bool:
        return key in self._cache

    def invalidate(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def size(self) -> int:
        return len(self._cache)

    @classmethod
    def reset(cls):
        cls._cache = {}
