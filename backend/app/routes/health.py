import time
from datetime import datetime, timezone
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from app.extension_registry import db
from app.utils.db_helpers import redact_database_url

health_bp = Blueprint("health", __name__, url_prefix="/api/health")

@health_bp.route("", methods=["GET"])
def health_check():
    """Basic service health check."""
    return jsonify({
        "success": True,
        "service": "Employee Success Management System API",
        "status": "healthy",
        "environment": current_app.config.get("ENV", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200

@health_bp.route("/db", methods=["GET"])
def db_health_check():
    """
    Verifies live connectivity to Neon PostgreSQL.
    Executes a simple 'SELECT 1' query and reports response latency.
    Never exposes passwords or sensitive credentials.
    """
    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    redacted_uri = redact_database_url(db_uri)

    if not db_uri or "YOUR_NEON" in db_uri or "placeholder" in db_uri:
        return jsonify({
            "success": False,
            "status": "unconfigured",
            "database": "Neon PostgreSQL",
            "message": "DATABASE_URL is not configured or still contains placeholder values. Please update your .env file with your Neon PostgreSQL connection string.",
            "configured_target": redacted_uri
        }), 503

    start_time = time.time()
    try:
        # Test connection execution
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1;")).scalar()

        latency_ms = round((time.time() - start_time) * 1000, 2)
        if result == 1:
            return jsonify({
                "success": True,
                "status": "connected",
                "database": "Neon PostgreSQL",
                "latency_ms": latency_ms,
                "message": "Successfully connected to Neon PostgreSQL database.",
                "target": redacted_uri
            }), 200
        else:
            return jsonify({
                "success": False,
                "status": "unexpected_result",
                "message": "Database connected but query returned unexpected result."
            }), 500

    except Exception as exc:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        error_type = exc.__class__.__name__
        return jsonify({
            "success": False,
            "status": "disconnected",
            "database": "Neon PostgreSQL",
            "latency_ms": latency_ms,
            "error_type": error_type,
            "message": "Failed to connect to Neon PostgreSQL database. Verify host, network credentials, and SSL requirements.",
            "target": redacted_uri
        }), 503
