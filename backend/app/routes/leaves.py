from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from marshmallow import ValidationError
from app.extension_registry import db
from app.models.leave import LeaveRequest, LeaveType
from app.middleware.auth_guard import admin_required, hr_required, employee_required
from app.schemas.leave_schema import (
    leave_apply_schema,
    leave_update_schema,
    leave_review_schema,
    leave_type_create_schema,
    leave_type_update_schema
)
from app.services.leave_service import LeaveService

leave_bp = Blueprint("leaves", __name__, url_prefix="/api/leaves")

# ------------------------------------------------------------------------------
# Leave Types
# ------------------------------------------------------------------------------
@leave_bp.route("/types", methods=["GET"])
@jwt_required()
def list_leave_types():
    """Lists available leave types."""
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    types = LeaveService.list_leave_types(include_inactive=include_inactive)
    return jsonify({
        "success": True,
        "data": types
    }), 200

@leave_bp.route("/types", methods=["POST"])
@admin_required
def create_leave_type():
    """Admin creates a new leave type."""
    data = request.get_json(silent=True) or {}
    try:
        validated = leave_type_create_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid leave type data.",
                "details": err.messages
            }
        }), 400

    try:
        created = LeaveService.create_leave_type(validated)
        return jsonify({
            "success": True,
            "message": "Leave type created successfully.",
            "data": created
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "DUPLICATE_RESOURCE",
                "message": str(err)
            }
        }), 409

@leave_bp.route("/types/<int:type_id>", methods=["PUT"])
@admin_required
def update_leave_type(type_id):
    """Admin updates an existing leave type."""
    data = request.get_json(silent=True) or {}
    try:
        validated = leave_type_update_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid leave type data.",
                "details": err.messages
            }
        }), 400

    try:
        updated = LeaveService.update_leave_type(type_id, validated)
        return jsonify({
            "success": True,
            "message": "Leave type updated successfully.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "UPDATE_FAILED",
                "message": str(err)
            }
        }), 400

# ------------------------------------------------------------------------------
# Leave Applications & Balance
# ------------------------------------------------------------------------------
@leave_bp.route("", methods=["POST"])
@jwt_required()
def apply_leave():
    """Applies for leave for the authenticated employee."""
    data = request.get_json(silent=True) or {}
    try:
        validated = leave_apply_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid leave application payload.",
                "details": err.messages
            }
        }), 400

    try:
        result = LeaveService.apply_leave(
            user_id=current_user.id,
            leave_type_id=validated["leave_type_id"],
            start_date=validated["start_date"],
            end_date=validated["end_date"],
            reason=validated["reason"]
        )
        return jsonify({
            "success": True,
            "message": f"Leave application submitted for {result['total_days']} days.",
            "data": result
        }), 201
    except (ValueError, PermissionError) as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "LEAVE_APPLICATION_FAILED",
                "message": str(err)
            }
        }), 400

@leave_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my_leaves():
    """Retrieves personal leave history and balances."""
    status = request.args.get("status")
    year = request.args.get("year", type=int)
    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)

    try:
        history = LeaveService.get_my_leave_history(
            user_id=current_user.id,
            status=status,
            year=year,
            limit=limit,
            offset=offset
        )
        return jsonify({
            "success": True,
            "data": history
        }), 200
    except (ValueError, PermissionError) as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "QUERY_FAILED",
                "message": str(err)
            }
        }), 400

@leave_bp.route("/balance", methods=["GET"])
@jwt_required()
def get_my_balance():
    """Retrieves leave balance breakdowns for the authenticated employee."""
    year = request.args.get("year", type=int)
    try:
        emp = LeaveService.get_employee_for_user(current_user.id)
        balances = LeaveService.get_employee_balance(emp.id, year=year)
        return jsonify({
            "success": True,
            "data": balances
        }), 200
    except (ValueError, PermissionError) as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "BALANCE_QUERY_FAILED",
                "message": str(err)
            }
        }), 400

# ------------------------------------------------------------------------------
# HR & Admin Listing & Summaries
# ------------------------------------------------------------------------------
@leave_bp.route("", methods=["GET"])
@hr_required
def list_leaves():
    """Lists company-wide leave requests with filters (HR/Admin)."""
    search = request.args.get("search")
    dept_id = request.args.get("department_id", type=int)
    lt_id = request.args.get("leave_type_id", type=int)
    status = request.args.get("status")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)

    result = LeaveService.list_leaves(
        search=search,
        department_id=dept_id,
        leave_type_id=lt_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return jsonify({
        "success": True,
        "data": result
    }), 200

@leave_bp.route("/summary", methods=["GET"])
@hr_required
def get_leave_summary():
    """Provides organizational KPI summary for leave operations."""
    year = request.args.get("year", type=int)
    summary = LeaveService.get_summary(year=year)
    return jsonify({
        "success": True,
        "data": summary
    }), 200

# ------------------------------------------------------------------------------
# Request Actions & Details
# ------------------------------------------------------------------------------
@leave_bp.route("/<int:leave_id>", methods=["GET"])
@jwt_required()
def get_leave_detail(leave_id):
    """Retrieves specific leave request details."""
    req = db.session.get(LeaveRequest, leave_id)
    if not req:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Leave request {leave_id} not found."
            }
        }), 404

    # RBAC check for employee
    if current_user.role == "EMPLOYEE":
        if req.employee.user_id != current_user.id:
            return jsonify({
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You are not authorized to view another employee's leave request."
                }
            }), 403

    return jsonify({
        "success": True,
        "data": req.to_dict()
    }), 200

@leave_bp.route("/<int:leave_id>", methods=["PUT"])
@jwt_required()
def update_leave(leave_id):
    """Allows an employee to update their own PENDING request."""
    data = request.get_json(silent=True) or {}
    try:
        validated = leave_update_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid update payload.",
                "details": err.messages
            }
        }), 400

    try:
        updated = LeaveService.update_pending_leave(leave_id, current_user.id, validated)
        return jsonify({
            "success": True,
            "message": "Leave request updated successfully.",
            "data": updated
        }), 200
    except (ValueError, PermissionError) as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "UPDATE_FAILED",
                "message": str(err)
            }
        }), 400

@leave_bp.route("/<int:leave_id>/approve", methods=["PATCH"])
@hr_required
def approve_leave(leave_id):
    """Approves a PENDING leave request (HR or Admin)."""
    data = request.get_json(silent=True) or {}
    try:
        validated = leave_review_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid review payload.",
                "details": err.messages
            }
        }), 400

    try:
        approved = LeaveService.approve_leave(
            leave_id=leave_id,
            reviewer_user_id=current_user.id,
            comments=validated.get("comments")
        )
        return jsonify({
            "success": True,
            "message": "Leave request approved successfully.",
            "data": approved
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "APPROVAL_FAILED",
                "message": str(err)
            }
        }), 400

@leave_bp.route("/<int:leave_id>/reject", methods=["PATCH"])
@hr_required
def reject_leave(leave_id):
    """Rejects a PENDING leave request (HR or Admin)."""
    data = request.get_json(silent=True) or {}
    try:
        validated = leave_review_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid review payload.",
                "details": err.messages
            }
        }), 400

    try:
        rejected = LeaveService.reject_leave(
            leave_id=leave_id,
            reviewer_user_id=current_user.id,
            comments=validated.get("comments")
        )
        return jsonify({
            "success": True,
            "message": "Leave request rejected.",
            "data": rejected
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "REJECTION_FAILED",
                "message": str(err)
            }
        }), 400

@leave_bp.route("/<int:leave_id>/cancel", methods=["PATCH"])
@jwt_required()
def cancel_leave(leave_id):
    """Cancels a leave request."""
    try:
        cancelled = LeaveService.cancel_leave(
            leave_id=leave_id,
            user_id=current_user.id,
            user_role=current_user.role
        )
        return jsonify({
            "success": True,
            "message": "Leave request cancelled successfully.",
            "data": cancelled
        }), 200
    except (ValueError, PermissionError) as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "CANCELLATION_FAILED",
                "message": str(err)
            }
        }), 400
