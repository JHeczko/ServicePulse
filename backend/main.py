from contextlib import asynccontextmanager

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_router, service_router
from sqlalchemy import text

from database.core.int_db import SessionLocal
from database.Service import Service
from tasks import ping_service_task
from utils.logger import logger

scheduler = BackgroundScheduler()


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info("APScheduler background runner started")

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
            "All scheduler jobs loaded successfully",
            total_services=len(services),
            status="active",
        )
    except Exception as e:
        logger.error(
            "Critical error initializing services on startup",
            error=str(e),
        )
    finally:
        db.close()

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
def health_check():
    database_status = "ok"
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        database_status = "down"
        logger.critical(
            "Health check detected database failure", error=str(e)
        )
    finally:
        db.close()

    overall_status = "ok" if database_status == "ok" else "error"

    return {
        "status": overall_status,
        "database": database_status,
        "worker": "ok",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=13000)