from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from marshmallow import ValidationError
from app.middleware.auth_guard import admin_required, hr_required, employee_required
from app.schemas.employee_schema import (
    employee_create_schema,
    employee_update_schema,
    employee_status_schema,
    department_create_schema,
    department_update_schema
)
from app.services.employee_service import EmployeeService

employee_bp = Blueprint("employees", __name__, url_prefix="/api/employees")

# ------------------------------------------------------------------------------
# Department Endpoints
# ------------------------------------------------------------------------------
@employee_bp.route("/departments", methods=["GET"])
@jwt_required()
def list_departments():
    """Returns all organizational departments."""
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    departments = EmployeeService.list_departments(include_inactive=include_inactive)
    return jsonify({
        "success": True,
        "data": departments
    }), 200

@employee_bp.route("/departments", methods=["POST"])
@hr_required
def create_department():
    """Creates a new organizational department (HR or Admin)."""
    data = request.get_json(silent=True) or {}
    try:
        validated = department_create_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid department data.",
                "details": err.messages
            }
        }), 400

    try:
        department = EmployeeService.create_department(validated)
        return jsonify({
            "success": True,
            "message": "Department created successfully.",
            "data": department
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "DUPLICATE_RESOURCE",
                "message": str(err)
            }
        }), 409

@employee_bp.route("/departments/<int:department_id>", methods=["PUT"])
@hr_required
def update_department(department_id):
    """Updates an existing department (HR or Admin)."""
    data = request.get_json(silent=True) or {}
    try:
        validated = department_update_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid department data.",
                "details": err.messages
            }
        }), 400

    try:
        department = EmployeeService.update_department(department_id, validated)
        return jsonify({
            "success": True,
            "message": "Department updated successfully.",
            "data": department
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "DEPARTMENT_ERROR",
                "message": str(err)
            }
        }), 400

# ------------------------------------------------------------------------------
# Employee Endpoints
# ------------------------------------------------------------------------------
@employee_bp.route("", methods=["GET"])
@jwt_required()
def list_employees():
    """
    Lists employees.
    - ADMIN & HR: can filter, paginate and see all records.
    - EMPLOYEE: can only retrieve their own record in the listing.
    """
    if current_user.role == "EMPLOYEE":
        try:
            emp = EmployeeService.get_employee_by_user_id(current_user.id)
            return jsonify({
                "success": True,
                "data": {
                    "total": 1,
                    "items": [emp.to_dict()],
                    "limit": 1,
                    "offset": 0
                }
            }), 200
        except ValueError:
            return jsonify({
                "success": True,
                "data": {
                    "total": 0,
                    "items": [],
                    "limit": 1,
                    "offset": 0
                }
            }), 200

    # For HR and ADMIN
    search = request.args.get("search")
    dept_id = request.args.get("department_id", type=int)
    status = request.args.get("status")
    role = request.args.get("role")
    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)

    result = EmployeeService.list_employees(
        search=search,
        department_id=dept_id,
        status=status,
        role=role,
        limit=limit,
        offset=offset
    )

    return jsonify({
        "success": True,
        "data": result
    }), 200

@employee_bp.route("", methods=["POST"])
@hr_required
def create_employee():
    """Creates a new employee record and linked user account (HR or Admin)."""
    data = request.get_json(silent=True) or {}
    try:
        validated = employee_create_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid employee payload.",
                "details": err.messages
            }
        }), 400

    try:
        employee = EmployeeService.create_employee(validated)
        return jsonify({
            "success": True,
            "message": "Employee created successfully.",
            "data": employee
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "EMPLOYEE_CREATION_FAILED",
                "message": str(err)
            }
        }), 409

@employee_bp.route("/<string:employee_id>", methods=["GET"])
@jwt_required()
def get_employee(employee_id):
    """
    Retrieves full details of a specific employee.
    - ADMIN & HR: can view any employee.
    - EMPLOYEE: can only view their own profile.
    """
    try:
        emp = EmployeeService.get_employee_by_id(employee_id)
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": str(err)
            }
        }), 404

    # RBAC check for EMPLOYEE role
    if current_user.role == "EMPLOYEE" and str(emp.user_id) != str(current_user.id):
        return jsonify({
            "success": False,
            "error": {
                "code": "UNAUTHORIZED_ACCESS",
                "message": "Employees are only permitted to view their own profile."
            }
        }), 403

    return jsonify({
        "success": True,
        "data": emp.to_dict()
    }), 200

@employee_bp.route("/<string:employee_id>", methods=["PUT"])
@hr_required
def update_employee(employee_id):
    """Updates an employee's details (HR or Admin)."""
    data = request.get_json(silent=True) or {}
    try:
        validated = employee_update_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid employee update payload.",
                "details": err.messages
            }
        }), 400

    try:
        updated = EmployeeService.update_employee(employee_id, validated)
        return jsonify({
            "success": True,
            "message": "Employee updated successfully.",
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

@employee_bp.route("/<string:employee_id>/status", methods=["PATCH"])
@hr_required
def update_employee_status(employee_id):
    """Activates or deactivates an employee (HR or Admin)."""
    data = request.get_json(silent=True) or {}
    try:
        validated = employee_status_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid status payload.",
                "details": err.messages
            }
        }), 400

    try:
        updated = EmployeeService.update_status(
            employee_id_raw=employee_id,
            status=validated["status"],
            is_active=validated.get("is_active")
        )
        return jsonify({
            "success": True,
            "message": f"Employee status updated to {validated['status']}.",
            "data": updated
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "STATUS_UPDATE_FAILED",
                "message": str(err)
            }
        }), 400

