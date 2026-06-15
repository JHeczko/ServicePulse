import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_router, service_router

from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.core.int_db import SessionLocal
from database.Service import Service
from tasks import ping_service_task

scheduler = AsyncIOScheduler()

def push_to_queue(service_id: int):
    ping_service_task.send(service_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
        print(f"[INFO] Scheduler uruchomiony. Załadowano {len(services)} serwisów.")
    finally:
        db.close()

    yield
    # ==== ZAMKNIĘCIE APLIKACJI ====
    scheduler.shutdown()
    print("[INFO] Scheduler wyłączony.")
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

# =-=-=-=-=-= SERVICES =-=-=-=-=-=
app.include_router(auth_router)
app.include_router(service_router)

@app.get("/")
def root():
    return {"message": "ServicePulse API is running perfectly!"}


# =-=-=-=-=-= HEALTH =-=-=-=-=-=
@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=13000)