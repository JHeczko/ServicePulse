import time
from contextlib import asynccontextmanager

import uvicorn
import redis
import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from routes import auth_router, service_router
from sqlalchemy import text

from database.core import SessionLocal
from database import Service
from tasks import ping_service_task, register_worker_heartbeat
from utils.logger import logger



scheduler = BackgroundScheduler()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, socket_timeout=2.0)

def push_to_queue(service_id: int):
    try:
        logger.info(
            "Pushing service to Dramatiq queue",
            service_id=service_id,
            action="scheduler_push",
        )
        ping_service_task.send(service_id)
    except Exception as e:
        logger.error(
            "Failed to send task to Dramatiq",
            service_id=service_id,
            error=str(e),
        )

def trigger_worker_heartbeat():
    try:
        register_worker_heartbeat.send()
    except Exception as e:
        logger.error("Failed to send heartbeat task to Dramatiq broker", error=str(e))

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info("APScheduler background runner started")

    db = SessionLocal()
    # adding every saved service to the queue loaded from DB
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
            "All scheduler jobs loaded successfully",
            total_services=len(services),
            status="active",
        )

    except Exception as e:
        logger.critical(
            "Critical error initializing services on startup",
            error=str(e),
        )
        raise e
    finally:
        db.close()


    # adding health check
    scheduler.add_job(
        trigger_worker_heartbeat,
        trigger="interval",
        minutes=1,
        id="worker_heartbeat_generator",
        replace_existing=True
    )
    logger.info("Worker heartbeat generator scheduled successfully (1m interval)")

    yield

    # ==== APP CLOSE ====
    scheduler.shutdown()
    logger.info("Scheduler shut down safely")


app = FastAPI(
    title="ServicePulse API",
    description="Backend to monitor defined services",
    version="1.0.0",
    lifespan=lifespan,
)

# =-=-=-=-=-= CORS =-=-=-=-=-=
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =-=-=-=-=-= ROUTERS =-=-=-=-=-=
app.include_router(auth_router)
app.include_router(service_router)


# =-=-=-=-=-= BASIC ENDPOINTS =-=-=-=-=-=
@app.get("/")
def root():
    return {"message": "ServicePulse API is running perfectly!"}


@app.get("/health")
def health_check(response: Response):
    components = {
        "database": "unknown",
        "redis": "unknown",
        "worker": "unknown"
    }

    # 1. DATABASE CHECK
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        components["database"] = "ok"
    except Exception as e:
        components["database"] = "down"
        logger.critical("Health check failure: Database unreachable", error=str(e))
    finally:
        db.close()

    # 2. REDIS CHECK
    try:
        if redis_client.ping():
            components["redis"] = "ok"
    except Exception as e:
        components["redis"] = "down"
        logger.critical("Health check failure: Redis unreachable", error=str(e))

    # 3. DRAMATIQ WORKER CHECK
    try:
        last_heartbeat = redis_client.get("worker:heartbeat")
        if last_heartbeat:
            last_heartbeat_time = float(last_heartbeat)
            if time.time() - last_heartbeat_time < 90:
                components["worker"] = "ok"
            else:
                components["worker"] = "stale"
                logger.warning("Health check warning: Worker heartbeat is stale")
        else:
            components["worker"] = "down"
            logger.error("Health check failure: No worker heartbeat found in Redis")
    except Exception as e:
        components["worker"] = "down"
        logger.critical("Health check failure: Could not read worker heartbeat", error=str(e))

    all_ok = all(status_val == "ok" for status_val in components.values())

    if all_ok:
        overall_status = "ok"
        response.status_code = status.HTTP_200_OK
    else:
        overall_status = "error"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall_status,
        "components": components
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=13000)