from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from etl_sf.config.loader import load_environment_config
from etl_sf.database.engine import build_engine
from etl_sf.database.repository import DatabaseRepository
from etl_sf.orchestration.pipeline import ETLPipeline
from etl_sf.web.job_manager import JobManager, run_in_background

app = FastAPI(title="Real-Time ETL + Salesforce Control Plane", version="1.0.0")
manager = JobManager()


def _get_pipeline(env: str) -> ETLPipeline:
    return ETLPipeline(Path("configs"), env)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html>
<head>
  <title>ETL Salesforce Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; }
    button { padding: 8px 14px; margin-right: 6px; }
    #events { white-space: pre-wrap; background: #111; color: #0f0; padding: 12px; height: 300px; overflow: auto; }
    .panel { margin-bottom: 20px; }
  </style>
</head>
<body>
  <h1>Real-Time ETL + Salesforce Dashboard</h1>

  <div class="panel">
    <label>Environment:</label>
    <select id="env">
      <option>dev</option><option>qa</option><option>uat</option><option>prod</option>
    </select>
    <button onclick="runJob()">Run Pipeline</button>
    <button onclick="loadJobs()">Refresh Jobs</button>
  </div>

  <div class="panel">
    <h3>Jobs</h3>
    <ul id="jobs"></ul>
  </div>

  <div class="panel">
    <h3>Live Events</h3>
    <div id="events"></div>
  </div>

<script>
let ws = null;
function log(msg){
  const box = document.getElementById('events');
  box.textContent += msg + "\n";
  box.scrollTop = box.scrollHeight;
}
async function runJob(){
  const env = document.getElementById('env').value;
  const r = await fetch(`/api/jobs/run?env=${env}`, {method:'POST'});
  const data = await r.json();
  log(`Started job ${data.job_id} on ${env}`);
  connect(data.job_id);
  loadJobs();
}
function connect(jobId){
  if(ws){ws.close();}
  ws = new WebSocket(`ws://${location.host}/ws/jobs/${jobId}`);
  ws.onmessage = (e)=>log(e.data);
  ws.onclose = ()=>log("socket closed");
}
async function loadJobs(){
  const r = await fetch('/api/jobs');
  const data = await r.json();
  const ul = document.getElementById('jobs');
  ul.innerHTML = '';
  for (const j of data.jobs){
    const li = document.createElement('li');
    li.textContent = `${j.job_id} | ${j.env} | ${j.status} | ${j.updated_at}`;
    li.onclick = ()=>connect(j.job_id);
    ul.appendChild(li);
  }
}
loadJobs();
</script>
</body>
</html>
"""


@app.get("/api/environments")
def list_envs() -> dict:
    envs = ["dev", "qa", "uat", "prod"]
    data = {}
    for e in envs:
        cfg = load_environment_config(Path("configs"), e)
        data[e] = {
            "database": cfg.database.url,
            "batch_size": cfg.runtime.batch_size,
            "dry_run": cfg.runtime.dry_run,
        }
    return {"environments": data}


@app.get("/api/mappings")
def mappings_preview() -> dict:
    root = Path("configs/mappings")
    return {
        "file_to_db": (root / "file_to_db.yml").read_text(encoding="utf-8"),
        "db_to_salesforce": (root / "db_to_salesforce.yml").read_text(encoding="utf-8"),
    }


@app.get("/api/jobs")
def list_jobs() -> dict:
    return {"jobs": [j.__dict__ for j in manager.list_jobs()]}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    return manager.get(job_id).__dict__


@app.post("/api/jobs/run")
def run_job(env: str = Query("dev")) -> dict:
    job = manager.create_job(env)

    def _runner() -> None:
        manager.update(job.job_id, status="RUNNING", event={"stage": "RUNNING"})
        try:
            pipeline = _get_pipeline(env)
            result = pipeline.run(progress=lambda evt: manager.update(job.job_id, event=evt))
            manager.complete(job.job_id, result)
        except Exception as exc:
            manager.fail(job.job_id, str(exc))

    run_in_background(_runner)
    return {"job_id": job.job_id, "status": job.status}


@app.get("/api/audits")
def get_audits(env: str = Query("dev"), limit: int = Query(20)) -> dict:
    pipeline = _get_pipeline(env)
    db = DatabaseRepository(build_engine(pipeline.env.database.url))
    try:
        batches = db.fetch_rows(
            "SELECT run_id, env_name, start_ts, end_ts, status FROM etl_batch_audit ORDER BY start_ts DESC LIMIT :limit",
            {"limit": limit},
        )
        files = db.fetch_rows(
            "SELECT run_id, file_name, status, rows_read, rows_loaded, rows_rejected FROM etl_file_audit ORDER BY id DESC LIMIT :limit",
            {"limit": limit},
        )
    except Exception:
        batches, files = [], []
    return {"batch_audit": batches, "file_audit": files}


@app.websocket("/ws/jobs/{job_id}")
async def jobs_ws(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    queue = await manager.subscribe(job_id)
    try:
        while True:
            event = await asyncio.wait_for(queue.get(), timeout=25)
            await websocket.send_json(event)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        manager.unsubscribe(job_id, queue)


def run_web() -> None:
    import uvicorn

    uvicorn.run("etl_sf.web.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run_web()
