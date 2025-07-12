from celery import Celery
from .settings import get_settings
from .agent import generate_report

settings = get_settings()
celery_app = Celery(
    "market_research_tasks",
    broker=settings.broker_url,
    backend=settings.result_backend,
)


@celery_app.task(bind=True)
def create_report(self, topic: str, extra_keywords: list = None, n: int = 10):
    """Celery task that wraps the async agent."""
    report = celery_app.loop.run_until_complete(
        generate_report(topic, extra_keywords, n)
    )
    return report
