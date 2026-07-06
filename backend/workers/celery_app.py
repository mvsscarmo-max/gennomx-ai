from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

# VLAEG phase G (Gatilho): scheduled ingestion. Hour configurable via settings when present.
CT_INGEST_HOUR = getattr(settings, "CLINICALTRIALS_INGEST_HOUR_UTC", 3)

celery_app = Celery(
    "gennomx",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "workers.tasks.ingest",
        "workers.tasks.process",
        "workers.tasks.retention",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "workers.tasks.ingest.*": {"queue": "ingest"},
        "workers.tasks.process.*": {"queue": "process"},
        "workers.tasks.retention.*": {"queue": "process"},
        "workers.tasks.ai.*": {"queue": "ai"},
    },
    task_default_queue="ingest",
    task_queues={
        "ingest": {"exchange": "ingest", "routing_key": "ingest"},
        "process": {"exchange": "process", "routing_key": "process"},
        "ai": {"exchange": "ai", "routing_key": "ai"},
    },
    broker_connection_retry_on_startup=True,
    task_soft_time_limit=3600,  # 1 hour soft limit
    task_time_limit=7200,  # 2 hour hard limit
    worker_max_tasks_per_child=50,  # restart worker after 50 tasks (memory management)
    # VLAEG phase G (Gatilho): scheduled triggers. Operated by `celery -A workers.celery_app beat`.
    # Declared in docs/09_DEPLOY_E_OPERACAO.md §0.1.
    beat_schedule={
        "clinicaltrials-daily-incremental": {
            "task": "workers.tasks.ingest.run_clinicaltrials_ingest",
            "schedule": crontab(hour=CT_INGEST_HOUR, minute=0),
            "kwargs": {"job_type": "incremental"},
            "options": {"queue": "ingest"},
        },
        "pubmed-daily-incremental": {
            "task": "workers.tasks.ingest.run_pubmed_ingest",
            "schedule": crontab(hour=getattr(settings, "PUBMED_INGEST_HOUR_UTC", 3), minute=15),
            "kwargs": {"job_type": "incremental"},
            "options": {"queue": "ingest"},
        },
        "openfda-daily-incremental": {
            "task": "workers.tasks.ingest.run_openfda_ingest",
            "schedule": crontab(hour=getattr(settings, "OPENFDA_INGEST_HOUR_UTC", 3), minute=30),
            "kwargs": {"job_type": "incremental"},
            "options": {"queue": "ingest"},
        },
        "dailymed-daily-incremental": {
            "task": "workers.tasks.ingest.run_dailymed_ingest",
            "schedule": crontab(hour=getattr(settings, "DAILYMED_INGEST_HOUR_UTC", 3), minute=45),
            "kwargs": {"job_type": "incremental"},
            "options": {"queue": "ingest"},
        },
        "opentargets-weekly": {
            "task": "workers.tasks.ingest.run_opentargets_ingest",
            "schedule": crontab(
                hour=getattr(settings, "OPEN_TARGETS_INGEST_HOUR_UTC", 4),
                minute=0,
                day_of_week="mon",
            ),
            "kwargs": {"job_type": "incremental"},
            "options": {"queue": "ingest"},
        },
        "ema-weekly": {
            "task": "workers.tasks.ingest.run_ema_ingest",
            "schedule": crontab(
                hour=getattr(settings, "EMA_INGEST_HOUR_UTC", 4), minute=15, day_of_week="mon"
            ),
            "kwargs": {"job_type": "incremental"},
            "options": {"queue": "ingest"},
        },
        "governance-retention-weekly": {
            "task": "workers.tasks.retention.run_retention_cycle",
            "schedule": crontab(hour=4, minute=0, day_of_week="sun"),
            "kwargs": {"dry_run": False, "batch_size": 1000},
            "options": {"queue": "process"},
        },
        "governance-freshness-daily": {
            "task": "workers.tasks.process.mark_stale_assertions",
            "schedule": crontab(hour=2, minute=30),
            "options": {"queue": "process"},
        },
    },
)
