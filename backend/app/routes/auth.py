from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, current_user
from marshmallow import ValidationError
from app.schemas.auth_schema import login_schema, change_password_schema
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/health", methods=["GET"])
def auth_health():
    """Diagnostic health endpoint for authentication service."""
    return jsonify({
        "success": True,
        "subsystem": "Authentication & RBAC",
        "status": "ready"
    }), 200

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticates a user via email and password.
    Returns access token, refresh token, and user profile metadata.
    """
    data = request.get_json(silent=True) or {}
    try:
        validated_data = login_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid login payload.",
                "details": err.messages
            }
        }), 400

    try:
        result = AuthService.login(validated_data["email"], validated_data["password"])
        return jsonify({
            "success": True,
            "message": "Authentication successful.",
            "data": result
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": str(err)
            }
        }), 401
    except PermissionError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "ACCOUNT_DISABLED",
                "message": str(err)
            }
        }), 403

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Refreshes an expired access token using a valid refresh token.
    Must be called with Bearer <refresh_token>.
    """
    try:
        result = AuthService.refresh(current_user)
        return jsonify({
            "success": True,
            "message": "Access token refreshed successfully.",
            "data": result
        }), 200
    except PermissionError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "ACCOUNT_DISABLED",
                "message": str(err)
            }
        }), 403

@auth_bp.route("/logout", methods=["POST"])
@jwt_required(verify_type=False)
def logout():
    """
    Revokes the caller's JWT token and adds it to the revoked_tokens store.
    Accepts either access or refresh tokens.
    """
    jwt_payload = get_jwt()
    try:
        AuthService.logout(jwt_payload)
        return jsonify({
            "success": True,
            "message": "Session terminated and token revoked successfully."
        }), 200
    except Exception as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "LOGOUT_FAILED",
                "message": f"Failed to revoke token: {str(err)}"
            }
        }), 500

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user_profile():
    """
    Returns the profile and role details of the currently authenticated user.
    """
    claims = get_jwt()
    if claims.get("type", "access") != "access":
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_TOKEN_TYPE",
                "message": "Access token required."
            }
        }), 401

    if not current_user:
        return jsonify({
            "success": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found."
            }
        }), 404

    if not current_user.is_active:
        return jsonify({
            "success": False,
            "error": {
                "code": "ACCOUNT_DEACTIVATED",
                "message": "Account is deactivated."
            }
        }), 403

    return jsonify({
        "success": True,
        "data": current_user.to_dict()
    }), 200

@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """
    Allows authenticated users to change their password securely.
    """
    claims = get_jwt()
    if claims.get("type", "access") != "access":
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_TOKEN_TYPE",
                "message": "Access token required."
            }
        }), 401

    data = request.get_json(silent=True) or {}
    try:
        validated_data = change_password_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid password change payload.",
                "details": err.messages
            }
        }), 400

    try:
        AuthService.change_password(
            current_user,
            validated_data["current_password"],
            validated_data["new_password"]
        )
        return jsonify({
            "success": True,
            "message": "Password changed successfully."
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "PASSWORD_CHANGE_FAILED",
                "message": str(err)
            }
        }), 400

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    Initiates a password reset request.
    Always returns a generic message to prevent user enumeration.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    if not email:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Email address is required."
            }
        }), 400

    result = AuthService.request_password_reset(email)
    return jsonify({
        "success": True,
        "message": result["message"],
        # debug_token is provided for test suites; in pure production it is omitted
        "debug_token": result.get("debug_token")
    }), 200

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    Completes password reset using a valid, unexpired reset token.
    """
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    new_password = data.get("new_password", "").strip()

    if not token or not new_password:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Both token and new_password are required."
            }
        }), 400

    try:
        result = AuthService.reset_password(token, new_password)
        return jsonify({
            "success": True,
            "message": result["message"]
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {
                "code": "PASSWORD_RESET_FAILED",
                "message": str(err)
            }
        }), 400

