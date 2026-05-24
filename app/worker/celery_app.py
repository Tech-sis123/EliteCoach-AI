from celery import Celery
from app.core.config import settings

broker_url = str(settings.REDIS_URL)
if broker_url.startswith("rediss://") and "ssl_cert_reqs" not in broker_url:
    broker_url += "?ssl_cert_reqs=none"

celery_app = Celery(
    "worker",
    broker=broker_url,
    backend=broker_url,
)

celery_app.conf.task_routes = {
    "app.worker.tasks.*": "main-queue",
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Autodiscover tasks
celery_app.autodiscover_tasks(["app.worker"])
