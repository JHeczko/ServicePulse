import os
import time
import json
from datetime import datetime
import httpx
import dramatiq
from dramatiq.brokers.redis import RedisBroker

from database.core.int_db import SessionLocal
from database.Service import Service
from database.Check import Check
from database.Incident import Incident

# 1. Konfiguracja brokera Dramatiq z Redisem
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
broker = RedisBroker(url=REDIS_URL)
dramatiq.set_broker(broker)


def log_json_event(event: str, service_id: int, status_code: int, response_time_ms: int):
    log_payload = {
        "event": event,
        "service_id": service_id,
        "status_code": status_code,
        "response_time_ms": response_time_ms
    }
    print(json.dumps(log_payload))


@dramatiq.actor
def ping_service_task(service_id: int):
    db = SessionLocal()
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
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

            except (httpx.RequestError, httpx.TimeoutException):
                response_time_ms = int((time.time() - start_time) * 1000)
                status_code = 0  # 0 symbolizuje błąd sieciowy w bazie
                is_available = False

        # ==== R4.0 & R5.0: ZAPIS WYNIKU SPRAWDZENIA (Check) ====
        new_check = Check(
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=service.user_id,
            service_id=service.id
        )
        db.add(new_check)

        # ==== R4.0: AUTOMATYCZNA DETEKCJA INCYDENTÓW ====
        active_incident = db.query(Incident).filter(
            Incident.service_id == service.id,
            Incident.ended_at.is_(None)
        ).first()

        if not is_available:
            if not active_incident:
                error_msg = f"Serwis zwrócił status {status_code}" if status_code > 0 else "Błąd połączenia / Timeout"
                new_incident = Incident(
                    error_message=error_msg,
                    user_id=service.user_id,
                    service_id=service.id,
                    started_at=datetime.now()
                )
                db.add(new_incident)
        else:
            if active_incident:
                active_incident.ended_at = datetime.now()

        db.commit()

        log_json_event("service_checked", service.id, status_code, response_time_ms)

    except Exception as e:
        db.rollback()
        # Logowanie błędów wewnętrznych workera, jeśli np. baza nawali
        print(json.dumps({"event": "worker_error", "message": str(e), "service_id": service_id}))
    finally:
        db.close()