from etl_sf.web.job_manager import JobManager


def test_job_manager_lifecycle():
    jm = JobManager()
    job = jm.create_job("dev")
    jm.update(job.job_id, status="RUNNING", event={"stage": "START"})
    jm.complete(job.job_id, {"ok": True})

    current = jm.get(job.job_id)
    assert current.status == "SUCCESS"
    assert current.result == {"ok": True}
    assert current.events[0]["stage"] == "START"
