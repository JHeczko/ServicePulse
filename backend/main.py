import fastapi
import uvicorn
from fastapi import FastAPI

app = FastAPI()


# =-=-=-=-=-= AUTH =-=-=-=-=-=

@app.post("/auth/register")
def register_user():
    return {}

@app.post("/auth/login")
def login_user():
    return {}

# =-=-=-=-=-= SERVICES =-=-=-=-=-=

# =-=-=-=-=-= HEALTH =-=-=-=-=-=
@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=13000)