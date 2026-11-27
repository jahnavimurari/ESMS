from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from marshmallow import ValidationError
from app.middleware.auth_guard import hr_required
from app.schemas.task_schema import (
    task_create_schema,
    task_update_schema,
    task_status_schema,
    task_assign_schema,
    task_cancel_schema
)
from app.services.task_service import TaskService

task_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")

# ------------------------------------------------------------------------------
# Task Creation & Listing
# ------------------------------------------------------------------------------
@task_bp.route("", methods=["POST"])
@hr_required
def create_task():
    """HR or Admin creates a new task."""
    data = request.get_json(silent=True) or {}
    try:
        validated = task_create_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid task data.",
                "details": err.messages
            }
        }), 400

    try:
        task = TaskService.create_task(
            creator_user_id=current_user.id,
            data=validated,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Task created successfully.",
            "data": task
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": str(err)
            }
        }), 400

@task_bp.route("", methods=["GET"])
@jwt_required()
def list_tasks():
    """Lists tasks with role-based filtering, overdue tracking, search, and pagination."""
    filters = {
        "status": request.args.get("status"),
        "priority": request.args.get("priority"),
        "category": request.args.get("category"),
        "assigned_to": request.args.get("assigned_to"),
        "department_id": request.args.get("department_id"),
        "overdue": request.args.get("overdue"),
        "search": request.args.get("search"),
        "page": request.args.get("page", 1),
        "per_page": request.args.get("per_page", 20)
    }

    try:
        result = TaskService.list_tasks(current_user=current_user, filters=filters)
        return jsonify({
            "success": True,
            "data": result["items"],
            "pagination": result["pagination"]
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": str(err)
            }
        }), 400

@task_bp.route("/my", methods=["GET"])
@jwt_required()
def list_my_tasks():
    """Returns assigned tasks for the currently authenticated employee."""
    filters = {
        "status": request.args.get("status"),
        "priority": request.args.get("priority"),
        "category": request.args.get("category"),
        "overdue": request.args.get("overdue"),
        "search": request.args.get("search"),
        "page": request.args.get("page", 1),
        "per_page": request.args.get("per_page", 20)
    }

    try:
        result = TaskService.list_my_tasks(current_user=current_user, filters=filters)
        return jsonify({
            "success": True,
            "data": result["items"],
            "pagination": result["pagination"]
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": str(err)
            }
        }), 400

@task_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_task_summary():
    """Calculates KPI summary metrics (total, in_progress, review, completed, overdue, etc.)."""
    dept_id = request.args.get("department_id")
    department_id = int(dept_id) if dept_id and dept_id.isdigit() else None

    try:
        summary = TaskService.get_task_summary(current_user=current_user, department_id=department_id)
        return jsonify({
            "success": True,
            "data": summary
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": str(err)
            }
        }), 400

# ------------------------------------------------------------------------------
# Task Details, Updates, Lifecycle, and History
# ------------------------------------------------------------------------------
@task_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task_detail(task_id: int):
    """Retrieves single task details with RBAC enforcement."""
    try:
        task = TaskService.get_task_by_id(task_id=task_id, current_user=current_user)
        return jsonify({
            "success": True,
            "data": task
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": str(err)
            }
        }), 404
    except PermissionError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": str(err)
            }
        }), 403

@task_bp.route("/<int:task_id>", methods=["PUT"])
@hr_required
def update_task(task_id: int):
    """HR or Admin updates task configurations."""
    data = request.get_json(silent=True) or {}
    try:
        validated = task_update_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid task update data.",
                "details": err.messages
            }
        }), 400

    try:
        task = TaskService.update_task(
            task_id=task_id,
            current_user=current_user,
            data=validated,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Task updated successfully.",
            "data": task
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": str(err)
            }
        }), 400
    except PermissionError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": str(err)
            }
        }), 403

@task_bp.route("/<int:task_id>/status", methods=["PATCH"])
@jwt_required()
def update_task_status(task_id: int):
    """Updates task lifecycle status (TODO, IN_PROGRESS, REVIEW, COMPLETED, BLOCKED, CANCELLED)."""
    data = request.get_json(silent=True) or {}
    try:
        validated = task_status_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid status update data.",
                "details": err.messages
            }
        }), 400

    try:
        task = TaskService.update_task_status(
            task_id=task_id,
            current_user=current_user,
            new_status=validated["status"],
            comment=validated.get("comment"),
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": f"Task status updated to '{task['status']}'.",
            "data": task
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": str(err)
            }
        }), 400
    except PermissionError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": str(err)
            }
        }), 403

@task_bp.route("/<int:task_id>/assign", methods=["PATCH"])
@hr_required
def assign_task(task_id: int):
    """HR or Admin reassigns a task to another active employee."""
    data = request.get_json(silent=True) or {}
    try:
        validated = task_assign_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid assignment data.",
                "details": err.messages
            }
        }), 400

    try:
        task = TaskService.assign_task(
            task_id=task_id,
            current_user=current_user,
            new_assignee_id=validated["assigned_to"],
            comment=validated.get("comment"),
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": f"Task reassigned to {task['assignee_name']}.",
            "data": task
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": str(err)
            }
        }), 400
    except PermissionError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": str(err)
            }
        }), 403

@task_bp.route("/<int:task_id>/cancel", methods=["PATCH"])
@hr_required
def cancel_task(task_id: int):
    """HR or Admin cancels a task with an audit trail."""
    data = request.get_json(silent=True) or {}
    try:
        validated = task_cancel_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid cancellation data.",
                "details": err.messages
            }
        }), 400

    try:
        task = TaskService.cancel_task(
            task_id=task_id,
            current_user=current_user,
            reason=validated.get("reason"),
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Task cancelled successfully.",
            "data": task
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": str(err)
            }
        }), 400
    except PermissionError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": str(err)
            }
        }), 403

@task_bp.route("/<int:task_id>/history", methods=["GET"])
@jwt_required()
def get_task_history(task_id: int):
    """Retrieves full audit timeline for the task."""
    try:
        history = TaskService.get_task_history(task_id=task_id, current_user=current_user)
        return jsonify({
            "success": True,
            "data": history
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": str(err)
            }
        }), 404
    except PermissionError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": str(err)
            }
        }), 403

