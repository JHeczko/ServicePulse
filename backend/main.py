import os
import time
from contextlib import asynccontextmanager

import redis
import uvicorn
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database.core import SessionLocal
from routes import auth_router, service_router
from tasks.scheduler import init_scheduler, scheduler  # Import z Twojego pakietu
from utils.logger import logger

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, socket_timeout=2.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cały setup schedulera zamknięty w jednej czytelnej funkcji
    init_scheduler()
    yield
    # Bezpieczne zamknięcie przy gaszeniu kontenera
    scheduler.shutdown()
    logger.info("Scheduler shut down safely")


app = FastAPI(
    title="ServicePulse API",
    description="Backend to monitor defined services",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(service_router)


@app.get("/")
def root():
    return {"message": "ServicePulse API is running perfectly!"}


@app.get("/health")
def health_check(response: Response):
    components = {"database": "unknown", "redis": "unknown", "worker": "unknown"}

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
            if time.time() - float(last_heartbeat) < 90:
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
    response.status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if all_ok else "error",
        "components": components
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=13000)