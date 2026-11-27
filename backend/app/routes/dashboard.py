from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.middleware.auth_guard import admin_required, hr_required
from app.services.dashboard_service import DashboardService
from app.models.employee import Employee

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

# ------------------------------------------------------------------------------
# 1. Role-Specific Dashboards
# ------------------------------------------------------------------------------
@dashboard_bp.route("/admin", methods=["GET"])
@admin_required
def get_admin_dashboard():
    """Returns organizational command center metrics and visual charts for Admin users."""
    try:
        data = DashboardService.get_admin_dashboard()
        return jsonify({"success": True, "data": data}), 200
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@dashboard_bp.route("/hr", methods=["GET"])
@hr_required
def get_hr_dashboard():
    """Returns HR workforce operations, attendance, and leave approval metrics."""
    department_id = request.args.get("department_id", type=int)
    try:
        data = DashboardService.get_hr_dashboard(department_id=department_id)
        return jsonify({"success": True, "data": data}), 200
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@dashboard_bp.route("/employee", methods=["GET"])
@jwt_required()
def get_employee_dashboard():
    """Returns personal attendance, leave balances, tasks, and performance for the authenticated employee."""
    try:
        data = DashboardService.get_employee_dashboard(user_id=current_user.id)
        return jsonify({"success": True, "data": data}), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": str(err)}}), 404
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


# ------------------------------------------------------------------------------
# 2. Granular Analytics Endpoints (Scoped by RBAC)
# ------------------------------------------------------------------------------
@dashboard_bp.route("/attendance-trends", methods=["GET"])
@jwt_required()
def get_attendance_trends():
    """Returns daily attendance headcount and hours trends over N days (default 7)."""
    days = min(request.args.get("days", 7, type=int), 90)

    # RBAC Scoping: Employees see only their own trends
    if current_user.role == "EMPLOYEE":
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        employee_id = emp.id if emp else None
    else:
        employee_id = request.args.get("employee_id")

    trends = DashboardService.get_attendance_trends(days=days, employee_id=employee_id)
    return jsonify({"success": True, "data": trends}), 200


@dashboard_bp.route("/department-distribution", methods=["GET"])
@hr_required
def get_department_distribution():
    """Returns active employee headcount distribution across departments."""
    distribution = DashboardService.get_department_distribution()
    return jsonify({"success": True, "data": distribution}), 200


@dashboard_bp.route("/task-analytics", methods=["GET"])
@jwt_required()
def get_task_analytics():
    """Returns task status and priority distribution. Scoped to employee for EMPLOYEE role."""
    if current_user.role == "EMPLOYEE":
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        employee_id = emp.id if emp else None
    else:
        employee_id = request.args.get("employee_id")

    analytics = DashboardService.get_task_analytics(employee_id=employee_id)
    return jsonify({"success": True, "data": analytics}), 200


@dashboard_bp.route("/leave-analytics", methods=["GET"])
@jwt_required()
def get_leave_analytics():
    """Returns leave status and leave type distribution. Scoped to employee for EMPLOYEE role."""
    if current_user.role == "EMPLOYEE":
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        employee_id = emp.id if emp else None
    else:
        employee_id = request.args.get("employee_id")

    analytics = DashboardService.get_leave_analytics(employee_id=employee_id)
    return jsonify({"success": True, "data": analytics}), 200


@dashboard_bp.route("/performance-analytics", methods=["GET"])
@jwt_required()
def get_performance_analytics():
    """Returns performance rating distribution. Scoped to employee for EMPLOYEE role."""
    cycle_id = request.args.get("cycle_id", type=int)

    if current_user.role == "EMPLOYEE":
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        employee_id = emp.id if emp else None
    else:
        employee_id = request.args.get("employee_id")

    analytics = DashboardService.get_performance_analytics(cycle_id=cycle_id, employee_id=employee_id)
    return jsonify({"success": True, "data": analytics}), 200

