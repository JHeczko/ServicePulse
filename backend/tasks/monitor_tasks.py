import os
import time
from datetime import datetime
import httpx
import dramatiq
from dramatiq.brokers.redis import RedisBroker

from database.core.int_db import SessionLocal
from database.Service import Service
from database.Check import Check
from database.Incident import Incident
from utils.logger import logger

# 1. Dramatiq broker configuration with Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
broker = RedisBroker(url=REDIS_URL)
dramatiq.set_broker(broker)


@dramatiq.actor
def ping_service_task(service_id: int):
    db = SessionLocal()
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            logger.warning(
                "Service not found in database for checking",
                service_id=service_id
            )
            return

        start_time = time.time()
        status_code = 0
        response_time_ms = 0
        is_available = False

        with httpx.Client() as client:
            try:
                response = client.get(service.url, timeout=10.0)
                response_time_ms = int((time.time() - start_time) * 1000)
                status_code = response.status_code

                if status_code < 400:
                    is_available = True

            except (httpx.RequestError, httpx.TimeoutException) as network_exc:
                response_time_ms = int((time.time() - start_time) * 1000)
                status_code = 0  # 0 symbolizes a network failure/timeout in the DB
                is_available = False
                logger.warning(
                    "Network request failed during service ping",
                    service_id=service.id,
                    url=service.url,
                    error=str(network_exc)
                )

        # ==== SAVE CHECK RESULT ====
        new_check = Check(
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=service.user_id,
            service_id=service.id
        )
        db.add(new_check)

        # ==== AUTOMATIC INCIDENT DETECTION ====
        active_incident = db.query(Incident).filter(
            Incident.service_id == service.id,
            Incident.ended_at.is_(None)
        ).first()

        if not is_available:
            if not active_incident:
                error_msg = f"Service returned status code {status_code}" if status_code > 0 else "Connection error / Timeout"
                new_incident = Incident(
                    error_message=error_msg,
                    user_id=service.user_id,
                    service_id=service.id,
                    started_at=datetime.now()
                )
                db.add(new_incident)

                logger.error(
                    "New incident detected! Service is down",
                    service_id=service.id,
                    status_code=status_code,
                    error_message=error_msg
                )
        else:
            if active_incident:
                active_incident.ended_at = datetime.now()

                logger.info(
                    "Incident resolved. Service is back online",
                    service_id=service.id,
                    incident_id=active_incident.id,
                    downtime_duration_ms=int((datetime.now() - active_incident.started_at).total_seconds() * 1000)
                )

        db.commit()

        logger.info(
            "Service check executed successfully",
            service_id=service.id,
            status_code=status_code,
            response_time_ms=response_time_ms,
            is_available=is_available
        )

    except Exception as e:
        db.rollback()
        logger.critical(
            "Worker internal error processing service task",
            service_id=service_id,
            error=str(e)
        )
    finally:
        db.close()