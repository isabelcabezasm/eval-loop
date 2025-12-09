import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.generate import router as generate_router
from api.health import router as health_router

STATIC_FILES_DIRECTORY_ENV_VAR = "STATIC_FILES_DIRECTORY"

app = FastAPI(title="Q&A backend", version="0.1.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8007", "http://localhost:8007"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router, prefix="/api")
app.include_router(health_router, prefix="/api")

if static_directory := os.getenv(STATIC_FILES_DIRECTORY_ENV_VAR):
    static_path = Path(static_directory)
    
    # Mount static assets (JS, CSS, etc.)
    app.mount("/assets", StaticFiles(directory=static_path / "assets"), name="assets")
    
    # Serve index.html for all other routes (SPA fallback)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not built. Set STATIC_FILES_DIRECTORY to the built frontend."}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", port=8080)
