from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, current_user
from app.middleware.auth_guard import admin_required, hr_required
from app.services.reports_service import ReportsService

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

def _build_filter_summary(args):
    """Helper to convert query arguments into a human-readable filter summary for exports."""
    parts = []
    for k, v in args.items():
        if k not in ["format", "page", "limit"] and v:
            parts.append(f"{k}={v}")
    return ", ".join(parts) if parts else "None (All records)"

def _send_export_response(report_data, base_filename, default_format="csv"):
    export_format = request.args.get("format", default_format).lower().strip()
    filter_summary = _build_filter_summary(request.args)
    try:
        content_bytes, content_type, ext = ReportsService.export_data(
            report_data, export_format=export_format, filter_summary=filter_summary
        )
        filename = f"{base_filename}_{ext}.{ext}"
        return Response(
            content_bytes,
            mimetype=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type
            }
        )
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "INVALID_FORMAT", "message": str(err)}}), 400
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "EXPORT_ERROR", "message": str(err)}}), 500


# ------------------------------------------------------------------------------
# 1. Employee Reports
# ------------------------------------------------------------------------------
@reports_bp.route("/employees", methods=["GET"])
@hr_required
def get_employee_report():
    """Generates employee directory report (Admin & HR only)."""
    try:
        filters = {
            "department_id": request.args.get("department_id", type=int),
            "status": request.args.get("status"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date")
        }
        data = ReportsService.get_employee_report_data(filters=filters, current_user=current_user)
        return jsonify({"success": True, "data": data}), 200
    except PermissionError as err:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": str(err)}}), 403
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@reports_bp.route("/employees/export", methods=["GET"])
@hr_required
def export_employee_report():
    """Exports employee directory report to CSV, Excel, or PDF."""
    try:
        filters = {
            "department_id": request.args.get("department_id", type=int),
            "status": request.args.get("status"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date")
        }
        data = ReportsService.get_employee_report_data(filters=filters, current_user=current_user)
        return _send_export_response(data, "employee_directory_report")
    except PermissionError as err:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": str(err)}}), 403
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


# ------------------------------------------------------------------------------
# 2. Attendance Reports
# ------------------------------------------------------------------------------
@reports_bp.route("/attendance", methods=["GET"])
@jwt_required()
def get_attendance_report():
    """Generates attendance report (Scoped to self for EMPLOYEE; org-wide for Admin/HR)."""
    try:
        filters = {
            "employee_id": request.args.get("employee_id"),
            "department_id": request.args.get("department_id", type=int),
            "status": request.args.get("status"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date")
        }
        data = ReportsService.get_attendance_report_data(filters=filters, current_user=current_user)
        return jsonify({"success": True, "data": data}), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": str(err)}}), 404
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@reports_bp.route("/attendance/export", methods=["GET"])
@jwt_required()
def export_attendance_report():
    """Exports attendance report to CSV, Excel, or PDF."""
    try:
        filters = {
            "employee_id": request.args.get("employee_id"),
            "department_id": request.args.get("department_id", type=int),
            "status": request.args.get("status"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date")
        }
        data = ReportsService.get_attendance_report_data(filters=filters, current_user=current_user)
        return _send_export_response(data, "attendance_report")
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


# ------------------------------------------------------------------------------
# 3. Leave Reports
# ------------------------------------------------------------------------------
@reports_bp.route("/leaves", methods=["GET"])
@jwt_required()
def get_leave_report():
    """Generates leave requests report (Scoped to self for EMPLOYEE; org-wide for Admin/HR)."""
    try:
        filters = {
            "employee_id": request.args.get("employee_id"),
            "department_id": request.args.get("department_id", type=int),
            "leave_type_id": request.args.get("leave_type_id", type=int),
            "status": request.args.get("status"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date")
        }
        data = ReportsService.get_leave_report_data(filters=filters, current_user=current_user)
        return jsonify({"success": True, "data": data}), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": str(err)}}), 404
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@reports_bp.route("/leaves/export", methods=["GET"])
@jwt_required()
def export_leave_report():
    """Exports leave requests report to CSV, Excel, or PDF."""
    try:
        filters = {
            "employee_id": request.args.get("employee_id"),
            "department_id": request.args.get("department_id", type=int),
            "leave_type_id": request.args.get("leave_type_id", type=int),
            "status": request.args.get("status"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date")
        }
        data = ReportsService.get_leave_report_data(filters=filters, current_user=current_user)
        return _send_export_response(data, "leave_report")
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


# ------------------------------------------------------------------------------
# 4. Task Reports
# ------------------------------------------------------------------------------
@reports_bp.route("/tasks", methods=["GET"])
@jwt_required()
def get_task_report():
    """Generates task tracking report (Scoped to self for EMPLOYEE; org-wide for Admin/HR)."""
    try:
        filters = {
            "employee_id": request.args.get("employee_id"),
            "department_id": request.args.get("department_id", type=int),
            "priority": request.args.get("priority"),
            "status": request.args.get("status"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date")
        }
        data = ReportsService.get_task_report_data(filters=filters, current_user=current_user)
        return jsonify({"success": True, "data": data}), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": str(err)}}), 404
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@reports_bp.route("/tasks/export", methods=["GET"])
@jwt_required()
def export_task_report():
    """Exports task tracking report to CSV, Excel, or PDF."""
    try:
        filters = {
            "employee_id": request.args.get("employee_id"),
            "department_id": request.args.get("department_id", type=int),
            "priority": request.args.get("priority"),
            "status": request.args.get("status"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date")
        }
        data = ReportsService.get_task_report_data(filters=filters, current_user=current_user)
        return _send_export_response(data, "task_report")
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


# ------------------------------------------------------------------------------
# 5. Performance Reports
# ------------------------------------------------------------------------------
@reports_bp.route("/performance", methods=["GET"])
@jwt_required()
def get_performance_report():
    """Generates performance review report (Scoped to self for EMPLOYEE; org-wide for Admin/HR)."""
    try:
        filters = {
            "employee_id": request.args.get("employee_id"),
            "department_id": request.args.get("department_id", type=int),
            "cycle_id": request.args.get("cycle_id", type=int),
            "status": request.args.get("status")
        }
        data = ReportsService.get_performance_report_data(filters=filters, current_user=current_user)
        return jsonify({"success": True, "data": data}), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": str(err)}}), 404
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500


@reports_bp.route("/performance/export", methods=["GET"])
@jwt_required()
def export_performance_report():
    """Exports performance review report to CSV, Excel, or PDF."""
    try:
        filters = {
            "employee_id": request.args.get("employee_id"),
            "department_id": request.args.get("department_id", type=int),
            "cycle_id": request.args.get("cycle_id", type=int),
            "status": request.args.get("status")
        }
        data = ReportsService.get_performance_report_data(filters=filters, current_user=current_user)
        return _send_export_response(data, "performance_report")
    except Exception as err:
        return jsonify({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(err)}}), 500

