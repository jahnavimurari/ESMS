from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from marshmallow import ValidationError
from app.middleware.auth_guard import admin_required, hr_required, employee_required
from app.schemas.attendance_schema import (
    attendance_check_in_schema,
    attendance_check_out_schema,
    attendance_correction_schema
)
from app.services.attendance_service import AttendanceService

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

@attendance_bp.route("/check-in", methods=["POST"])
@jwt_required()
def check_in():
    """Starts an active attendance shift for the authenticated employee."""
    data = request.get_json(silent=True) or {}
    try:
        validated = attendance_check_in_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid check-in payload.",
                "details": err.messages
            }
        }), 400

    try:
        session = AttendanceService.check_in(current_user.id, notes=validated.get("notes"))
        return jsonify({
            "success": True,
            "message": f"Check-in recorded for Shift {session['shift_number']}.",
            "data": session
        }), 201
    except (ValueError, PermissionError) as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "CHECKIN_FAILED",
                "message": str(err)
            }
        }), 400

@attendance_bp.route("/check-out", methods=["POST"])
@jwt_required()
def check_out():
    """Ends the active attendance shift for the authenticated employee."""
    data = request.get_json(silent=True) or {}
    try:
        validated = attendance_check_out_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid check-out payload.",
                "details": err.messages
            }
        }), 400

    try:
        session = AttendanceService.check_out(current_user.id, notes=validated.get("notes"))
        return jsonify({
            "success": True,
            "message": f"Check-out recorded. Shift {session['shift_number']} duration: {session['total_hours']} hours.",
            "data": session
        }), 200
    except (ValueError, PermissionError) as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "CHECKOUT_FAILED",
                "message": str(err)
            }
        }), 400

@attendance_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my_attendance():
    """Retrieves attendance history and current shift status for the authenticated employee."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)

    try:
        data = AttendanceService.get_my_attendance(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        return jsonify({
            "success": True,
            "data": data
        }), 200
    except (ValueError, PermissionError) as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "ATTENDANCE_QUERY_FAILED",
                "message": str(err)
            }
        }), 400

@attendance_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_summary():
    """
    Returns high-level attendance summary.
    - HR / ADMIN: returns company-wide stats.
    - EMPLOYEE: returns their personal attendance summary.
    """
    work_date = request.args.get("work_date")
    dept_id = request.args.get("department_id", type=int)

    if current_user.role == "EMPLOYEE":
        # Personal summary
        try:
            my_data = AttendanceService.get_my_attendance(current_user.id)
            return jsonify({
                "success": True,
                "data": my_data["today"]
            }), 200
        except ValueError as err:
            return jsonify({
                "success": False,
                "error": {
                    "code": "SUMMARY_FAILED",
                    "message": str(err)
                }
            }), 400

    # HR / Admin summary
    summary = AttendanceService.get_summary(work_date=work_date, department_id=dept_id)
    return jsonify({
        "success": True,
        "data": summary
    }), 200

@attendance_bp.route("", methods=["GET"])
@hr_required
def list_attendance():
    """Lists organization-wide attendance records with filters (HR or Admin)."""
    search = request.args.get("search")
    dept_id = request.args.get("department_id", type=int)
    status = request.args.get("status")
    work_date = request.args.get("work_date")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)

    result = AttendanceService.list_attendance(
        search=search,
        department_id=dept_id,
        status=status,
        work_date=work_date,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return jsonify({
        "success": True,
        "data": result
    }), 200

@attendance_bp.route("/<int:attendance_id>", methods=["GET"])
@jwt_required()
def get_attendance_detail(attendance_id):
    """Retrieves specific attendance record details."""
    try:
        record = AttendanceService.get_attendance_by_id(attendance_id)
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": str(err)
            }
        }), 404

    # Authorization: Employees can only view their own records
    if current_user.role == "EMPLOYEE":
        if record.employee.user_id != current_user.id:
            return jsonify({
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You are not authorized to view another employee's attendance record."
                }
            }), 403

    return jsonify({
        "success": True,
        "data": record.to_dict()
    }), 200

@attendance_bp.route("/<int:attendance_id>", methods=["PUT"])
@hr_required
def correct_attendance(attendance_id):
    """Performs authorized correction of an attendance record (HR or Admin)."""
    data = request.get_json(silent=True) or {}
    try:
        validated = attendance_correction_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid correction payload.",
                "details": err.messages
            }
        }), 400

    try:
        corrected = AttendanceService.correct_attendance(
            attendance_id=attendance_id,
            data=validated,
            admin_user_id=current_user.id
        )
        return jsonify({
            "success": True,
            "message": "Attendance record corrected successfully.",
            "data": corrected
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "CORRECTION_FAILED",
                "message": str(err)
            }
        }), 400

