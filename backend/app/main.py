from fastapi import FastAPI

app = FastAPI(title="DataHandler API")


@app.get("/health")
async def healthcheck():
    return {
        "status": "ok",
        "service": "backend",
    }


@app.get("/")
async def root():
    return {
        "message": "DataHandler backend is running",
        "docs": "/docs",
    }
