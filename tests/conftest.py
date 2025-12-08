"""Root conftest.py for loading environment variables from .env file."""

from pathlib import Path

from dotenv import load_dotenv


def pytest_configure():
    """Load environment variables from .env file before running tests."""
    # Get the project root directory (parent of tests directory)
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    if env_file.exists():
        _ = load_dotenv(env_file)
