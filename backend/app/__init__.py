import os
from flask import Flask, jsonify
from app.config import config_by_name
from app.extension_registry import db, migrate, jwt, cors, ma

def create_app(config_name=None):
    """Application factory for Employee Success Management System."""
    if not config_name:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)

    # Initialize extensions
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config.get("CORS_ORIGINS", ["http://localhost:5173"]),
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    db.init_app(app)
    
    # Import all models to register them on db.metadata
    from app import models as app_models

    # Direct database URL can be supplied for migrations
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    # Register JWT callbacks and handlers
    from app.utils.jwt_handlers import register_jwt_callbacks
    register_jwt_callbacks(jwt)

    # Register blueprints
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.employees import employee_bp
    from app.routes.attendance import attendance_bp
    from app.routes.leaves import leave_bp
    from app.routes.tasks import task_bp
    from app.routes.performance import performance_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.reports import reports_bp
    from app.routes.notifications import notifications_bp
    from app.routes.settings import settings_bp
    from app.routes.admin import admin_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(admin_bp)

    # Register CLI commands
    from app.cli import create_admin_command
    app.cli.add_command(create_admin_command)

    # Global JSON error handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested API resource was not found."
            }
        }), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred."
            }
        }), 500

    return app

