import uuid
from flask import jsonify
from app.extension_registry import db
from app.models.revoked_token import RevokedToken
from app.models.user import User

def register_jwt_callbacks(jwt):
    """Configures Flask-JWT-Extended blocklist and error response hooks."""

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        try:
            return RevokedToken.is_token_revoked(jti)
        except Exception:
            return False

    @jwt.user_identity_loader
    def user_identity_lookup(user_or_id):
        if hasattr(user_or_id, "id"):
            return str(user_or_id.id)
        return str(user_or_id)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        try:
            # Try as uuid.UUID object first
            try:
                user_id_obj = uuid.UUID(str(identity))
                user = db.session.get(User, user_id_obj)
                if user:
                    return user
            except (ValueError, TypeError):
                pass
            return User.query.filter_by(id=identity).first()
        except Exception:
            return None

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        token_type = jwt_payload.get("type", "token")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": f"The {token_type} has expired. Please authenticate again.",
                "token_type": token_type
            }
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_TOKEN",
                "message": f"Invalid token: {reason}"
            }
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({
            "success": False,
            "error": {
                "code": "AUTHORIZATION_REQUIRED",
                "message": f"Authorization header is required: {reason}"
            }
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_REVOKED",
                "message": "This token has been revoked (logged out). Please log in again."
            }
        }), 401
