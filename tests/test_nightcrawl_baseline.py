import time
import pickle
import pytest

from nightcrawl import (
    TenantRegistry,
    JobStore,
    ScheduleStore,
    AuditLog,
    ResultCache,
    JOB_PENDING,
    JOB_RUNNING,
    JOB_DONE,
    JOB_FAILED,
    enqueue_job,
    run_due_jobs,
    get_job_result,
    retry_failed,
    get_default_tenants,
    get_default_jobs,
    get_default_schedules,
    get_default_audit,
    get_default_cache,
)
from nightcrawl.scheduler import register_handler, update_job_config


class TestTenantRegistry:

    def test_register_and_get(self):
        reg = TenantRegistry()
        reg.register("t1", "Acme", batch_enabled=True)
        record = reg.get("t1")
        assert record["tenant_id"] == "t1"
        assert record["name"] == "Acme"
        assert record["batch_enabled"] is True

    def test_list_ids(self):
        reg = TenantRegistry()
        reg.register("a", "A")
        reg.register("b", "B")
        assert set(reg.list_ids()) == {"a", "b"}

    def test_unknown_tenant_returns_none(self):
        reg = TenantRegistry()
        assert reg.get("missing") is None

    def test_is_batch_enabled(self):
        reg = TenantRegistry()
        reg.register("t1", "Acme", batch_enabled=True)
        reg.register("t2", "Beta", batch_enabled=False)
        assert reg.is_batch_enabled("t1") is True
        assert reg.is_batch_enabled("t2") is False


class TestJobStore:

    def test_create_and_get(self):
        store = JobStore()
        job_id = store.create_job("t1", "etl_export", {"input_path": "/data/in"})
        record = store.get(job_id)
        assert record["tenant_id"] == "t1"
        assert record["kind"] == "etl_export"
        assert record["state"] == JOB_PENDING

    def test_set_state_changes_state(self):
        store = JobStore()
        job_id = store.create_job("t1", "etl_export")
        store.set_state(job_id, JOB_RUNNING)
        assert store.get(job_id)["state"] == JOB_RUNNING

    def test_invalid_create_raises(self):
        store = JobStore()
        with pytest.raises(ValueError):
            store.create_job("", "etl_export")

    def test_list_for_tenant_filters(self):
        store = JobStore()
        store.create_job("t1", "etl_export")
        store.create_job("t1", "etl_export")
        store.create_job("t2", "etl_export")
        for_t1 = store.list_for_tenant("t1")
        assert len(for_t1) == 2
        for r in for_t1:
            assert r["tenant_id"] == "t1"

    def test_increment_attempts(self):
        store = JobStore()
        job_id = store.create_job("t1", "etl_export")
        assert store.increment_attempts(job_id) == 1
        assert store.increment_attempts(job_id) == 2


class TestScheduleStore:

    def test_add_and_get(self):
        store = ScheduleStore()
        store.add("s1", "t1", "digest_email", run_at=100.0)
        record = store.get("s1")
        assert record["tenant_id"] == "t1"
        assert record["run_at"] == 100.0

    def test_due_at(self):
        store = ScheduleStore()
        store.add("s1", "t1", "k", run_at=50.0)
        store.add("s2", "t1", "k", run_at=200.0)
        due = store.due_at(100.0)
        assert len(due) == 1
        assert due[0]["schedule_id"] == "s1"

    def test_mark_ran_recurring(self):
        store = ScheduleStore()
        store.add("s1", "t1", "k", run_at=100.0, recurring_seconds=60)
        store.mark_ran("s1", 100.0)
        record = store.get("s1")
        assert record["last_run"] == 100.0
        assert record["run_at"] == 160.0

    def test_legacy_export_roundtrip(self):
        store = ScheduleStore()
        store.add("s1", "t1", "k", run_at=100.0)
        blob = store.export_legacy()
        store.reset()
        fresh = ScheduleStore()
        count = fresh.import_legacy(blob)
        assert count == 1
        assert fresh.get("s1")["tenant_id"] == "t1"

    def test_export_returns_bytes(self):
        store = ScheduleStore()
        store.add("s1", "t1", "k", run_at=100.0)
        blob = store.export_legacy()
        assert isinstance(blob, bytes)


class TestAuditLog:

    def test_append_and_size(self):
        log = AuditLog()
        log.append("event_a", target="t1")
        log.append("event_b", target="t2")
        assert log.size() == 2

    def test_find_for_target(self):
        log = AuditLog()
        log.append("event_a", target="job-1")
        log.append("event_b", target="job-2")
        log.append("event_c", target="job-1")
        results = log.find_for_target("job-1")
        assert len(results) == 2


class TestResultCache:

    def test_put_and_get(self):
        cache = ResultCache()
        cache.put("k1", "value1")
        assert cache.get("k1") == "value1"

    def test_invalidate(self):
        cache = ResultCache()
        cache.put("k1", "value1")
        cache.invalidate("k1")
        assert cache.get("k1") is None

    def test_has(self):
        cache = ResultCache()
        cache.put("k1", "value1")
        assert cache.has("k1") is True
        assert cache.has("k2") is False


class TestGetJobResult:

    def test_get_returns_owned_job(self):
        get_default_tenants().register("t1", "Acme", batch_enabled=True)
        result = enqueue_job("t1", "etl_export", {})
        job_id = result["job_id"]
        out = get_job_result("t1", job_id)
        assert out["status"] == "ok"
        assert out["tenant_id"] == "t1"

    def test_get_unknown_returns_error(self):
        out = get_job_result("t1", "nonexistent")
        assert out["status"] == "error"
        assert out["reason"] == "not_found"


