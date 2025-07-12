from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from celery.result import AsyncResult

from .settings import get_settings
from .tasks import celery_app, create_report

settings = get_settings()
app = FastAPI(title=settings.api_title, version=settings.api_version)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/report", response_class=PlainTextResponse)
def request_report(topic: str, keywords: str = "", num_results: int = 10):
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    task = create_report.delay(topic, kw_list, num_results)
    return task.id


@app.get("/status/{task_id}")
def check_status(task_id: str):
    task = AsyncResult(task_id, app=celery_app)
    return {"state": task.state, "ready": task.ready()}


@app.get("/result/{task_id}", response_class=PlainTextResponse)
def get_result(task_id: str):
    task = AsyncResult(task_id, app=celery_app)
    if task.state != "SUCCESS":
        return PlainTextResponse(f"Not ready: {task.state}", status_code=202)
    return task.result
