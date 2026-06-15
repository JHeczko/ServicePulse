import logging
import sys

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_router, service_router

from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

from database.core.int_db import SessionLocal
from database.Service import Service
from tasks import ping_service_task

# WŁĄCZENIE LOGÓW - teraz zobaczysz każdy błąd APSchedulera w konsoli!
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def push_to_queue(service_id: int):
    try:
        logger.info(f"[SCHEDULER] Popycham serwis ID {service_id} do kolejki Dramatiq...")
        ping_service_task.send(service_id)
    except Exception as e:
        logger.error(f"[SCHEDULER] Nie udało się wysłać zadania do Dramatiq: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startujemy scheduler w tle
    scheduler.start()

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
                replace_existing=True
            )
        logger.info(f"Scheduler uruchomiony produkcyjnie. Załadowano {len(services)} serwisów z bazy.")
    except Exception as e:
        logger.error(f"Błąd podczas ładowania serwisów na starcie: {e}")
    finally:
        db.close()

    yield
    # ==== ZAMKNIĘCIE APLIKACJI ====
    scheduler.shutdown()
    logger.info("Scheduler wyłączony bezpiecznie.")

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

@app.get("/")
def root():
    return {"message": "ServicePulse API is running perfectly!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=13000)