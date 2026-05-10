from __future__ import annotations
from nightcrawl.tenants import TenantRegistry
from nightcrawl.jobs import JobStore
from nightcrawl.schedule import ScheduleStore
from nightcrawl.audit import AuditLog
from nightcrawl.cache import ResultCache


_DEFAULT_TENANTS = None
_DEFAULT_JOBS = None
_DEFAULT_SCHEDULES = None
_DEFAULT_AUDIT = None
_DEFAULT_CACHE = None


def get_default_tenants() -> TenantRegistry:
    global _DEFAULT_TENANTS
    if _DEFAULT_TENANTS is None:
        _DEFAULT_TENANTS = TenantRegistry()
    return _DEFAULT_TENANTS


def get_default_jobs() -> JobStore:
    global _DEFAULT_JOBS
    if _DEFAULT_JOBS is None:
        _DEFAULT_JOBS = JobStore()
    return _DEFAULT_JOBS


def get_default_schedules() -> ScheduleStore:
    global _DEFAULT_SCHEDULES
    if _DEFAULT_SCHEDULES is None:
        _DEFAULT_SCHEDULES = ScheduleStore()
    return _DEFAULT_SCHEDULES


def get_default_audit() -> AuditLog:
    global _DEFAULT_AUDIT
    if _DEFAULT_AUDIT is None:
        _DEFAULT_AUDIT = AuditLog()
    return _DEFAULT_AUDIT


def get_default_cache() -> ResultCache:
    global _DEFAULT_CACHE
    if _DEFAULT_CACHE is None:
        _DEFAULT_CACHE = ResultCache()
    return _DEFAULT_CACHE


def reset_all_stores():
    global _DEFAULT_TENANTS, _DEFAULT_JOBS, _DEFAULT_SCHEDULES, _DEFAULT_AUDIT, _DEFAULT_CACHE
    TenantRegistry.reset()
    JobStore.reset()
    ScheduleStore.reset()
    AuditLog.reset()
    ResultCache.reset()
    _DEFAULT_TENANTS = None
    _DEFAULT_JOBS = None
    _DEFAULT_SCHEDULES = None
    _DEFAULT_AUDIT = None
    _DEFAULT_CACHE = None
