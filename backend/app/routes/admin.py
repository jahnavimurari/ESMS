import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import current_user
from app.middleware.auth_guard import admin_required
from app.services.admin_service import AdminService

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# ------------------------------------------------------------------------------
# 1. User Administration
# ------------------------------------------------------------------------------
@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    """Lists registered users with pagination, search, and filtering."""
    search = request.args.get("search", type=str)
    if search:
        search = search.strip() or None

    role = request.args.get("role", type=str)
    if role:
        role = role.strip()
        if not role or role.upper() in ["ALL", ""]:
            role = None

    is_active_str = request.args.get("is_active", type=str)
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    is_active = None
    if is_active_str is not None:
        if is_active_str.lower() in ["true", "1"]:
            is_active = True
        elif is_active_str.lower() in ["false", "0"]:
            is_active = False

    result = AdminService.list_users(
        search=search,
        role=role,
        is_active=is_active,
        page=page,
        per_page=per_page
    )
    return jsonify({
        "success": True,
        "data": result
    }), 200

@admin_bp.route("/users/<uuid:user_id>", methods=["GET"])
@admin_required
def get_user_details(user_id):
    """Retrieves full details of a specific user account."""
    try:
        user_data = AdminService.get_user_details(user_id)
        return jsonify({
            "success": True,
            "data": user_data
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": str(err)
            }
        }), 404

@admin_bp.route("/users/<uuid:user_id>/role", methods=["PATCH", "PUT"])
@admin_required
def update_user_role(user_id):
    """Updates the authorization role of a user (Admin only)."""
    data = request.get_json(silent=True) or {}
    new_role = data.get("role")
    if not new_role:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Field 'role' is required."
            }
        }), 400

    try:
        updated = AdminService.update_user_role(user_id, new_role, actor_id=current_user.id)
        return jsonify({
            "success": True,
            "message": f"User role successfully updated to {new_role}.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "ROLE_UPDATE_REJECTED",
                "message": str(err)
            }
        }), 400

@admin_bp.route("/users/<uuid:user_id>/status", methods=["PATCH", "PUT"])
@admin_required
def update_user_status(user_id):
    """Activates or deactivates a user account (Admin only)."""
    data = request.get_json(silent=True) or {}
    if "is_active" not in data:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Field 'is_active' (boolean) is required."
            }
        }), 400

    is_active = bool(data["is_active"])
    try:
        updated = AdminService.update_user_status(user_id, is_active, actor_id=current_user.id)
        status_label = "activated" if is_active else "deactivated"
        return jsonify({
            "success": True,
            "message": f"User account has been {status_label}.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "STATUS_UPDATE_REJECTED",
                "message": str(err)
            }
        }), 400

# ------------------------------------------------------------------------------
# 2. Audit Log Viewer
# ------------------------------------------------------------------------------
@admin_bp.route("/audit-logs", methods=["GET"])
@admin_required
def list_audit_logs():
    """Returns paginated audit log entries with multi-filter query support."""
    user_id = request.args.get("user_id")
    action = request.args.get("action")
    target_entity = request.args.get("target_entity")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=25, type=int)

    result = AdminService.list_audit_logs(
        user_id=user_id,
        action=action,
        target_entity=target_entity,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page
    )
    return jsonify({
        "success": True,
        "data": result
    }), 200

# ------------------------------------------------------------------------------
# 3. System Administration Dashboard
# ------------------------------------------------------------------------------
@admin_bp.route("/system-stats", methods=["GET"])
@admin_required
def get_system_stats():
    """Returns real-time administrative telemetry, user counts, health checks, and activity logs."""
    stats = AdminService.get_system_stats()
    return jsonify({
        "success": True,
        "data": stats
    }), 200

