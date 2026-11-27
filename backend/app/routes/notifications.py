from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.services.notification_service import NotificationService

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

@notifications_bp.route("", methods=["GET"])
@jwt_required()
def get_notifications():
    """Lists notifications for current user with optional filtering and pagination."""
    try:
        unread_only = request.args.get("unread_only", "false").lower() in ("true", "1")
        category = request.args.get("category")
        page = max(request.args.get("page", 1, type=int), 1)
        limit = min(max(request.args.get("limit", 20, type=int), 1), 100)

        data = NotificationService.get_user_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            category=category,
            page=page,
            limit=limit
        )
        return jsonify({"success": True, "data": data}), 200
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@notifications_bp.route("/unread-count", methods=["GET"])
@jwt_required()
def get_unread_count():
    """Returns unread notification badge count."""
    try:
        count = NotificationService.get_unread_count(current_user.id)
        return jsonify({"success": True, "data": {"unread_count": count}}), 200
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@notifications_bp.route("/<int:notif_id>/read", methods=["PATCH"])
@jwt_required()
def mark_read(notif_id):
    """Marks a single notification as read."""
    try:
        notif = NotificationService.mark_as_read(notif_id, current_user.id)
        return jsonify({"success": True, "data": notif.to_dict()}), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": str(err)}}), 404
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@notifications_bp.route("/read-all", methods=["PATCH"])
@jwt_required()
def mark_all_read():
    """Marks all notifications as read for current user."""
    try:
        count = NotificationService.mark_all_as_read(current_user.id)
        return jsonify({"success": True, "data": {"marked_count": count}}), 200
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@notifications_bp.route("/<int:notif_id>", methods=["DELETE"])
@jwt_required()
def delete_notification(notif_id):
    """Deletes an in-app notification."""
    try:
        NotificationService.delete_notification(notif_id, current_user.id)
        return jsonify({"success": True, "message": "Notification deleted."}), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": str(err)}}), 404
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@notifications_bp.route("/announcements", methods=["POST"])
@jwt_required()
def create_announcement():
    """Admin / HR announcement broadcasting endpoint."""
    if current_user.role not in ["ADMIN", "HR"]:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": "Admin or HR role required."}}), 403

    payload = request.get_json() or {}
    title = payload.get("title", "").strip()
    message = payload.get("message", "").strip()
    priority = payload.get("priority", "NORMAL")
    target_role = payload.get("target_role")

    if not title or not message:
        return jsonify({"success": False, "error": {"code": "VALIDATION_ERROR", "message": "Title and message are required."}}), 400

    try:
        count = NotificationService.broadcast_announcement(
            title=title,
            message=message,
            priority=priority,
            target_role=target_role,
            current_user=current_user
        )
        return jsonify({"success": True, "data": {"recipients_count": count}, "message": f"Broadcast sent to {count} users."}), 201
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500

