import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_router, service_router

app = FastAPI(
    title="ServicePulse API",
    description="Backend to monitor defined services",
    version="1.0.0"
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