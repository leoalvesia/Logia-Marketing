from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "logia",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks",
        "app.tasks.feedback_tasks",
        "app.tasks.cost_monitor",
        "app.tasks.account_tasks",
        "app.tasks.business_alerts",
    ],
)

celery_app.conf.update(
    # ── Serialização ──────────────────────────────────────────────────────────
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    # ── Performance ───────────────────────────────────────────────────────────
    # prefetch=1 evita que um worker acumule várias tasks longas de uma vez,
    # garantindo distribuição justa entre workers.
    worker_prefetch_multiplier=1,
    task_acks_late=True,  # confirma task apenas após conclusão (evita perda em crash)
    # ── Roteamento de filas ───────────────────────────────────────────────────
    # Filas separadas permitem escalar workers por tipo de carga:
    #   celery worker -Q copy   --concurrency=4
    #   celery worker -Q art    --concurrency=2
    #   celery worker -Q research --concurrency=1
    task_routes={
        "app.tasks.generate_single_copy": {"queue": "copy"},
        "app.tasks.generate_all_copies": {"queue": "copy"},
        "app.tasks.generate_copy": {"queue": "copy"},
        "app.tasks.generate_art": {"queue": "art"},
        "app.tasks.run_daily_research": {"queue": "research"},
        "app.tasks.publish_post": {"queue": "copy"},
    },
    # ── Timeouts por tipo de task ─────────────────────────────────────────────
    # soft_time_limit: lança SoftTimeLimitExceeded (task pode limpar recursos)
    # time_limit:      mata o processo worker após o limite total
    task_annotations={
        "app.tasks.generate_single_copy": {
            "soft_time_limit": 55,
            "time_limit": 60,
        },
        "app.tasks.generate_all_copies": {
            "soft_time_limit": 55,
            "time_limit": 60,
        },
        "app.tasks.generate_art": {
            "soft_time_limit": 110,
            "time_limit": 120,
        },
        "app.tasks.run_daily_research": {
            "soft_time_limit": 280,
            "time_limit": 300,
        },
    },
    # ── Beat schedule ─────────────────────────────────────────────────────────
    beat_schedule={
        # Pesquisa diária de tendências às 6h (horário de Brasília)
        "daily-research": {
            "task": "app.tasks.run_daily_research",
            "schedule": crontab(hour=6, minute=0),
        },
        # Resumo NPS diário às 9h UTC
        "daily-nps-summary": {
            "task": "app.tasks.feedback_tasks.daily_nps_summary",
            "schedule": crontab(hour=9, minute=0),
        },
        # Relatório de custos de IA às 8h UTC (antes do resumo NPS)
        "daily-cost-report": {
            "task": "app.tasks.cost_monitor.daily_cost_report",
            "schedule": crontab(hour=8, minute=0),
        },
        # Hard delete de contas LGPD às 3h UTC (baixo tráfego)
        "hard-delete-expired-accounts": {
            "task": "app.tasks.account_tasks.hard_delete_expired_accounts",
            "schedule": crontab(hour=3, minute=0),
        },
        # Alertas de negócio — a cada hora
        "business-health-check": {
            "task": "app.tasks.business_alerts.business_health_check",
            "schedule": crontab(minute=0),  # todo início de hora
        },
        # Relatório semanal — segunda às 8h UTC
        "weekly-business-report": {
            "task": "app.tasks.business_alerts.weekly_business_report",
            "schedule": crontab(hour=8, minute=0, day_of_week=1),
        },
    },
)
