import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.generate import router as generate_router
from api.health import router as health_router

STATIC_FILES_DIRECTORY_ENV_VAR = "STATIC_FILES_DIRECTORY"

app = FastAPI(title="Q&A backend", version="0.1.0")

if static_directory := os.getenv(STATIC_FILES_DIRECTORY_ENV_VAR):
    app.mount("/static", StaticFiles(directory=Path(static_directory)))

app.include_router(generate_router, prefix="/api")
app.include_router(health_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", port=8080)
