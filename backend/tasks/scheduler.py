from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from database.core import SessionLocal
from database.Service import Service
from tasks import ping_service_task, register_worker_heartbeat
from utils.logger import logger

scheduler = BackgroundScheduler()


def push_to_queue(service_id: int):
    db = SessionLocal()
    try:
        service_exists = db.query(Service).filter(Service.id == service_id).first() is not None

        if not service_exists:
            logger.warning(
                "Detected zombie job for deleted service. Removing from local scheduler memory.",
                service_id=service_id,
                action="scheduler_cleanup"
            )
            try:
                scheduler.remove_job(f"service_{service_id}")
            except Exception:
                pass
            return

        logger.info(
            "Pushing service to Dramatiq queue",
            service_id=service_id,
            action="scheduler_push",
        )
        ping_service_task.send(service_id)

    except Exception as e:
        logger.error(
            "Failed to process scheduler task",
            service_id=service_id,
            error=str(e),
        )
    finally:
        db.close()


def trigger_worker_heartbeat():
    try:
        register_worker_heartbeat.send()
    except Exception as e:
        logger.error("Failed to send heartbeat task to Dramatiq broker", error=str(e))


def init_scheduler():
    db = SessionLocal()
    try:
        services = db.query(Service).all()
        for service in services:
            scheduler.add_job(
                push_to_queue,
                trigger="interval",
                seconds=service.interval,
                id=f"service_{service.id}",
                args=[service.id],
                replace_existing=True,
            )
        logger.info(
            "All scheduler jobs loaded successfully from database",
            total_services=len(services),
            status="active",
        )
    except Exception as e:
        logger.critical("Critical error initializing services on startup", error=str(e))
        raise e
    finally:
        db.close()

    # Rejestracja cyklicznego sprawdzania workerów
    scheduler.add_job(
        trigger_worker_heartbeat,
        trigger="interval",
        minutes=1,
        id="worker_heartbeat_generator",
        next_run_time=datetime.now(),
        replace_existing=True
    )
    logger.info("Worker heartbeat generator scheduled successfully (1m interval)")

    scheduler.start()
    logger.info("APScheduler background runner started safely")