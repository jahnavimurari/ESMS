from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, current_user

def role_required(*allowed_roles):
    """
    Decorator that checks JWT presence, user active status,
    and enforces role authorization at the controller boundary.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # 1. Enforce JWT presence & valid signature
            verify_jwt_in_request()
            claims = get_jwt()

            # Ensure access token is used (refresh token cannot access protected endpoints!)
            token_type = claims.get("type", "access")
            if token_type != "access":
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "INVALID_TOKEN_TYPE",
                        "message": "Access token required. Refresh token cannot be used to access API endpoints."
                    }
                }), 401

            # 2. Check if user is loaded and active
            if not current_user:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "User account associated with this token was not found."
                    }
                }), 401

            if not current_user.is_active:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "ACCOUNT_DEACTIVATED",
                        "message": "This user account is deactivated. Contact an administrator."
                    }
                }), 403

            # 3. Check role authorization
            user_role = current_user.role
            if user_role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Access denied. Required roles: {list(allowed_roles)}. Your role: '{user_role}'."
                    }
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Convenience decorators
def admin_required(fn):
    """Enforces ADMIN role."""
    return role_required("ADMIN")(fn)

def hr_required(fn):
    """Enforces HR or ADMIN role."""
    return role_required("ADMIN", "HR")(fn)

def employee_required(fn):
    """Enforces valid active user across all roles (ADMIN, HR, EMPLOYEE)."""
    return role_required("ADMIN", "HR", "EMPLOYEE")(fn)

