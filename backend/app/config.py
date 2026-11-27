import os
from datetime import timedelta
from dotenv import load_dotenv
from app.utils.db_helpers import normalize_database_url

# Load environment variables from root or backend directory (override ensures .env takes precedence over stale shell variables)
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(basedir, ".env"), override=True)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-jwt-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 60)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 7)))
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # Database configuration
    RAW_DATABASE_URL = os.getenv("DATABASE_URL", "")
    RAW_DIRECT_URL = os.getenv("DATABASE_DIRECT_URL", "")
    # Default to placeholder structure if unconfigured so SQLAlchemy engine initializes lazily
    _normalized_url = normalize_database_url(RAW_DATABASE_URL)
    _normalized_direct_url = normalize_database_url(RAW_DIRECT_URL)

    # DATABASE_URL for pooled application runtime queries (pgBouncer)
    SQLALCHEMY_DATABASE_URI = _normalized_url if _normalized_url else "postgresql+psycopg://placeholder:placeholder@localhost/placeholder"
    # DATABASE_DIRECT_URL for direct unpooled migration runs (Alembic)
    MIGRATION_DATABASE_URI = _normalized_direct_url if _normalized_direct_url else SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Neon PostgreSQL connection pool settings
    # pool_pre_ping prevents dead connection errors on serverless idle resume
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # CORS configuration
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ORIGINS = [
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = False
    TESTING = True
    # Test database configuration: uses TEST_DATABASE_URL if provided, else isolated file-based db for multi-request persistence
    RAW_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
    _test_url = normalize_database_url(RAW_DATABASE_URL)
    _test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_esms.db")).replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = _test_url if _test_url else f"sqlite:///{_test_db_path}"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False}
    } if not _test_url else {"pool_pre_ping": True}

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
