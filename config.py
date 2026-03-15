import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = "groq"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LOG_FILES = {
    "nginx_access": os.path.join(DATA_DIR, "nginx-access.log"),
    "nginx_error": os.path.join(DATA_DIR, "nginx-error.log"),
    "app_error": os.path.join(DATA_DIR, "app-error.log"),
}

LOG_CHUNK_SIZE = 8000
CONFIDENCE_THRESHOLD = 0.6

FALLBACK_SOURCES = [
    {
        "url": "https://docs.sqlalchemy.org/en/20/core/pooling.html",
        "domain": "SQLAlchemy",
        "topic": "connection pool",
    },
    {
        "url": "https://www.postgresql.org/docs/current/runtime-config-connection.html",
        "domain": "PostgreSQL",
        "topic": "max_connections",
    },
    {
        "url": "https://docs.gunicorn.org/en/stable/settings.html",
        "domain": "Gunicorn",
        "topic": "worker timeout",
    },
]