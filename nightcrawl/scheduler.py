from __future__ import annotations
import time
import traceback
from nightcrawl.runtime import (
    get_default_jobs,
    get_default_schedules,
    get_default_audit,
    get_default_cache,
    get_default_tenants,
)
from nightcrawl.jobs import JOB_PENDING, JOB_RUNNING, JOB_DONE, JOB_FAILED


_HANDLERS = {}


def register_handler(kind: str, fn):
    _HANDLERS[kind] = fn


def enqueue_job(tenant_id: str, kind: str, config: dict | None = None) -> dict:
    tenants = get_default_tenants()
    if not tenants.is_batch_enabled(tenant_id):
        return {"status": "error", "reason": "tenant_not_enabled"}
    jobs = get_default_jobs()
    job_id = jobs.create_job(tenant_id, kind, config or {})
    audit = get_default_audit()
    audit.append("job_enqueued", actor=tenant_id, target=job_id,
                 extra={"kind": kind})
    return {"status": "ok", "job_id": job_id}


def run_due_jobs(now: float | None = None) -> list:
    if now is None:
        now = time.time()
    schedules = get_default_schedules()
    jobs = get_default_jobs()
    cache = get_default_cache()
    results = []
    for sched in schedules.due_at(now):
        sid = sched["schedule_id"]
        tenant_id = sched["tenant_id"]
        kind = sched["kind"]
        job_id = jobs.create_job(tenant_id, kind, {})
        outcome = _execute_job(job_id, kind)
        if outcome.get("ok"):
            cache.put(f"job:{job_id}", outcome.get("result"))
        schedules.mark_ran(sid, now)
        results.append({
            "schedule_id": sid,
            "job_id": job_id,
            "status": outcome.get("status"),
        })
    return results


def _execute_job(job_id: str, kind: str) -> dict:
    jobs = get_default_jobs()
    jobs.set_state(job_id, JOB_RUNNING)
    handler = _HANDLERS.get(kind)
    if handler is None:
        jobs.set_state(job_id, JOB_FAILED)
        jobs.set_error(job_id, f"no handler registered for kind={kind!r}")
        return {"ok": False, "status": JOB_FAILED}
    try:
        record = jobs.get(job_id)
        result = handler(record["config"])
        jobs.set_result(job_id, result)
        jobs.set_state(job_id, JOB_DONE)
        return {"ok": True, "status": JOB_DONE, "result": result}
    except Exception as exc:
        jobs.set_state(job_id, JOB_FAILED)
        jobs.set_error(job_id, traceback.format_exc())
        return {"ok": False, "status": JOB_FAILED, "error": str(exc)}


def get_job_result(requesting_tenant_id: str, job_id: str) -> dict:
    jobs = get_default_jobs()
    record = jobs.get(job_id)
    if record is None:
        return {"status": "error", "reason": "not_found"}
    return {
        "status": "ok",
        "job_id": job_id,
        "tenant_id": record.get("tenant_id"),
        "kind": record.get("kind"),
        "state": record.get("state"),
        "attempts": record.get("attempts"),
        "result": record.get("result"),
        "last_error": record.get("last_error"),
    }


def retry_failed(tenant_id: str | None = None) -> list:
    jobs = get_default_jobs()
    targets = jobs.list_failed()
    if tenant_id is not None:
        targets = [t for t in targets if t.get("tenant_id") == tenant_id]
    out = []
    for record in targets:
        job_id = record["job_id"]
        kind = record["kind"]
        jobs.increment_attempts(job_id)
        outcome = _execute_job(job_id, kind)
        out.append({"job_id": job_id, "status": outcome.get("status")})
    return out


def update_job_config(job_id: str, updates: dict) -> dict:
    jobs = get_default_jobs()
    ok = jobs.update_config(job_id, updates)
    if not ok:
        return {"status": "error", "reason": "not_found"}
    return {"status": "ok"}
