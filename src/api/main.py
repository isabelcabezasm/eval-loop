import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.generate import router as generate_router
from api.health import router as health_router

STATIC_FILES_DIRECTORY_ENV_VAR = "STATIC_FILES_DIRECTORY"
API_PORT_ENV_VAR = "API_PORT"
DEFAULT_API_PORT = 8080


def get_api_port() -> int:
    """Get the API port from environment variable or use default."""
    return int(os.getenv(API_PORT_ENV_VAR, DEFAULT_API_PORT))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup: Write API configuration to file for frontend to read
    port = get_api_port()
    config_file = Path(".api-config.json")
    _ = config_file.write_text(
        json.dumps({"port": port, "baseUrl": f"http://127.0.0.1:{port}/api/"})
    )
    yield
    # Shutdown: cleanup if needed


app = FastAPI(title="Q&A backend", version="0.1.0", lifespan=lifespan)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8007",
        "http://localhost:8007",
        "http://127.0.0.1:5173",  # Vite default dev port
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router, prefix="/api")
app.include_router(health_router, prefix="/api")


if static_directory := os.getenv(STATIC_FILES_DIRECTORY_ENV_VAR):
    static_path = Path(static_directory)

    # Mount static assets (JS, CSS, etc.)
    app.mount(
        "/assets",
        StaticFiles(directory=static_path / "assets"),
        name="assets",
    )

    # Serve index.html for all other routes (SPA fallback)
    # Explicitly exclude /api/* and /assets/* paths to prevent conflicts
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't serve SPA for API or asset requests
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            raise HTTPException(status_code=404, detail="Not found")

        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(
            status_code=404,
            detail=(
                "Frontend not built. "
                "Set STATIC_FILES_DIRECTORY to the built frontend."
            ),
        )


if __name__ == "__main__":
    import uvicorn

    port = get_api_port()
    uvicorn.run("main:app", port=port)
