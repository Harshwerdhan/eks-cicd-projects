from fastapi import FastAPI
import os

app = FastAPI(title="user-service")

@app.get("/")
def root():
    return {"service": "user-service", "status": "ok", "env": os.environ.get("APP_ENV", "dev")}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ready")
def ready():
    return {"status": "ready"}