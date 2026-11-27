from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.middleware.auth_guard import admin_required, hr_required, employee_required
from app.services.settings_service import SettingsService

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

# ------------------------------------------------------------------------------
# 1. Organization Settings & Profile
# ------------------------------------------------------------------------------
@settings_bp.route("/organization", methods=["GET"])
@jwt_required()
def get_organization_settings():
    """Returns organization profile and global settings."""
    settings = SettingsService.get_organization_settings()
    return jsonify({
        "success": True,
        "data": settings
    }), 200

@settings_bp.route("/organization", methods=["PUT"])
@hr_required
def update_organization_settings():
    """Updates organization profile and settings (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        updated = SettingsService.update_organization_settings(data, user_id=current_user.id)
        return jsonify({
            "success": True,
            "message": "Organization settings updated successfully.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

# ------------------------------------------------------------------------------
# 2. Designations
# ------------------------------------------------------------------------------
@settings_bp.route("/designations", methods=["GET"])
@jwt_required()
def list_designations():
    """Lists company job designations."""
    department_id = request.args.get("department_id", type=int)
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    designations = SettingsService.list_designations(department_id=department_id, include_inactive=include_inactive)
    return jsonify({
        "success": True,
        "data": designations
    }), 200

@settings_bp.route("/designations", methods=["POST"])
@hr_required
def create_designation():
    """Creates a new job designation (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        created = SettingsService.create_designation(data)
        return jsonify({
            "success": True,
            "message": "Designation created successfully.",
            "data": created
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

@settings_bp.route("/designations/<int:designation_id>", methods=["PUT"])
@hr_required
def update_designation(designation_id):
    """Updates a job designation (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        updated = SettingsService.update_designation(designation_id, data)
        return jsonify({
            "success": True,
            "message": "Designation updated successfully.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

@settings_bp.route("/designations/<int:designation_id>", methods=["DELETE"])
@hr_required
def delete_designation(designation_id):
    """Deletes a job designation (Admin/HR only)."""
    try:
        SettingsService.delete_designation(designation_id)
        return jsonify({
            "success": True,
            "message": "Designation deleted successfully."
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": str(err)
            }
        }), 404

# ------------------------------------------------------------------------------
# 3. Holiday Calendar
# ------------------------------------------------------------------------------
@settings_bp.route("/holidays", methods=["GET"])
@jwt_required()
def list_holidays():
    """Lists holidays for a given year or all upcoming."""
    year = request.args.get("year", type=int)
    holidays = SettingsService.list_holidays(year=year)
    return jsonify({
        "success": True,
        "data": holidays
    }), 200

@settings_bp.route("/holidays", methods=["POST"])
@hr_required
def create_holiday():
    """Creates a holiday entry (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        created = SettingsService.create_holiday(data)
        return jsonify({
            "success": True,
            "message": "Holiday created successfully.",
            "data": created
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

@settings_bp.route("/holidays/<int:holiday_id>", methods=["PUT"])
@hr_required
def update_holiday(holiday_id):
    """Updates a holiday entry (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        updated = SettingsService.update_holiday(holiday_id, data)
        return jsonify({
            "success": True,
            "message": "Holiday updated successfully.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

@settings_bp.route("/holidays/<int:holiday_id>", methods=["DELETE"])
@hr_required
def delete_holiday(holiday_id):
    """Deletes a holiday entry (Admin/HR only)."""
    try:
        SettingsService.delete_holiday(holiday_id)
        return jsonify({
            "success": True,
            "message": "Holiday deleted successfully."
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": str(err)
            }
        }), 404

# ------------------------------------------------------------------------------
# 4. Work Shifts & Attendance Rules
# ------------------------------------------------------------------------------
@settings_bp.route("/shifts", methods=["GET"])
@jwt_required()
def list_shifts():
    """Lists company work shifts and attendance timing rules."""
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    shifts = SettingsService.list_shifts(include_inactive=include_inactive)
    return jsonify({
        "success": True,
        "data": shifts
    }), 200

@settings_bp.route("/shifts", methods=["POST"])
@hr_required
def create_shift():
    """Creates a new shift configuration (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        created = SettingsService.create_shift(data)
        return jsonify({
            "success": True,
            "message": "Work shift created successfully.",
            "data": created
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

@settings_bp.route("/shifts/<int:shift_id>", methods=["PUT"])
@hr_required
def update_shift(shift_id):
    """Updates a shift configuration (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        updated = SettingsService.update_shift(shift_id, data)
        return jsonify({
            "success": True,
            "message": "Work shift updated successfully.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

@settings_bp.route("/shifts/<int:shift_id>", methods=["DELETE"])
@hr_required
def delete_shift(shift_id):
    """Deletes a shift configuration (Admin/HR only)."""
    try:
        SettingsService.delete_shift(shift_id)
        return jsonify({
            "success": True,
            "message": "Work shift deleted successfully."
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": str(err)
            }
        }), 404

# ------------------------------------------------------------------------------
# 5. Employee Categories
# ------------------------------------------------------------------------------
@settings_bp.route("/categories", methods=["GET"])
@jwt_required()
def list_categories():
    """Lists employee categories (Full-Time, Contractor, Intern, etc.)."""
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    categories = SettingsService.list_categories(include_inactive=include_inactive)
    return jsonify({
        "success": True,
        "data": categories
    }), 200

@settings_bp.route("/categories", methods=["POST"])
@hr_required
def create_category():
    """Creates a new employee category (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        created = SettingsService.create_category(data)
        return jsonify({
            "success": True,
            "message": "Employee category created successfully.",
            "data": created
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

@settings_bp.route("/categories/<int:category_id>", methods=["PUT"])
@hr_required
def update_category(category_id):
    """Updates an employee category (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        updated = SettingsService.update_category(category_id, data)
        return jsonify({
            "success": True,
            "message": "Employee category updated successfully.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

# ------------------------------------------------------------------------------
# 6. Leave Policies Configuration
# ------------------------------------------------------------------------------
@settings_bp.route("/leave-policies", methods=["GET"])
@jwt_required()
def list_leave_policies():
    """Lists company leave policies and annual entitlements."""
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    policies = SettingsService.list_leave_policies(include_inactive=include_inactive)
    return jsonify({
        "success": True,
        "data": policies
    }), 200

@settings_bp.route("/leave-policies/<int:leave_type_id>", methods=["PUT"])
@hr_required
def update_leave_policy(leave_type_id):
    """Updates leave policy rules and entitlements (Admin/HR only)."""
    data = request.get_json(silent=True) or {}
    try:
        updated = SettingsService.update_leave_policy(leave_type_id, data)
        return jsonify({
            "success": True,
            "message": "Leave policy updated successfully.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(err)
            }
        }), 400

# ------------------------------------------------------------------------------
# 7. User Preferences
# ------------------------------------------------------------------------------
@settings_bp.route("/preferences", methods=["GET"])
@jwt_required()
def get_user_preferences():
    """Returns the current user's personal display and notification preferences."""
    pref = SettingsService.get_user_preferences(current_user.id)
    return jsonify({
        "success": True,
        "data": pref
    }), 200

@settings_bp.route("/preferences", methods=["PUT"])
@jwt_required()
def update_user_preferences():
    """Updates the current user's personal display and notification preferences."""
    data = request.get_json(silent=True) or {}
    updated = SettingsService.update_user_preferences(current_user.id, data)
    return jsonify({
        "success": True,
        "message": "Preferences updated successfully.",
        "data": updated
    }), 200

