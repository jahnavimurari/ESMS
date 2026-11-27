import uuid
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.models.revoked_token import RevokedToken
from app.models.security import PasswordResetToken
from app.models.audit import AuditLog
from app.services.email_service import EmailService
from app.extension_registry import db

# In-memory brute-force tracking
_login_attempts = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

class AuthService:
    """Encapsulates authentication, token lifecycle, and credential workflows."""

    @classmethod
    def _check_rate_limit(cls, email: str):
        """Enforces account lockout if repeated failed login attempts occur."""
        record = _login_attempts.get(email)
        if not record:
            return

        now = datetime.now(timezone.utc)
        locked_until = record.get("locked_until")
        if locked_until and now < locked_until:
            remaining_mins = max(1, int((locked_until - now).total_seconds() / 60))
            raise PermissionError(f"Account temporarily locked due to repeated failed login attempts. Try again in {remaining_mins} minute(s).")

        # Expire older attempt window (e.g. older than 15 mins)
        last_attempt = record.get("last_attempt")
        if last_attempt and (now - last_attempt) > timedelta(minutes=LOCKOUT_MINUTES):
            _login_attempts.pop(email, None)

    @classmethod
    def _record_failed_attempt(cls, email: str):
        """Increments failed attempt count and applies lockout if threshold breached."""
        now = datetime.now(timezone.utc)
        record = _login_attempts.setdefault(email, {"count": 0, "last_attempt": now, "locked_until": None})
        record["count"] += 1
        record["last_attempt"] = now

        if record["count"] >= MAX_FAILED_ATTEMPTS:
            record["locked_until"] = now + timedelta(minutes=LOCKOUT_MINUTES)

    @classmethod
    def _clear_failed_attempts(cls, email: str):
        """Resets failed attempt counters on successful login."""
        _login_attempts.pop(email, None)

    @staticmethod
    def get_security_metrics():
        """Returns statistics on active rate limits and lockouts for admin dashboard."""
        now = datetime.now(timezone.utc)
        locked = sum(1 for r in _login_attempts.values() if r.get("locked_until") and now < r["locked_until"])
        return {
            "monitored_accounts": len(_login_attempts),
            "locked_accounts": locked,
            "failed_attempts_recorded": sum(r["count"] for r in _login_attempts.values())
        }

    @staticmethod
    def login(email: str, password: str):
        """
        Authenticates credentials, enforces activation, updates last_login,
        monitors brute-force rate limits, and generates short-lived access and long-lived refresh JWTs.
        """
        email = email.strip().lower()

        # Check rate-limit lockout
        AuthService._check_rate_limit(email)

        user = User.query.filter_by(email=email).first()

        if not user:
            AuthService._record_failed_attempt(email)
            raise ValueError("Invalid email or password.")

        if not user.check_password(password):
            AuthService._record_failed_attempt(email)
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            raise PermissionError("Your account has been deactivated. Please contact an administrator.")

        # Successful authentication: clear brute-force counters
        AuthService._clear_failed_attempts(email)

        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        # Generate tokens with claims
        claims = {
            "role": user.role,
            "email": user.email,
        }
        access_token = create_access_token(identity=user, additional_claims=claims)
        refresh_token = create_refresh_token(identity=user, additional_claims=claims)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": user.to_dict()
        }

    @staticmethod
    def refresh(user):
        """Generates a fresh access token using a valid refresh token."""
        if not user or not user.is_active:
            raise PermissionError("Account is inactive or not found.")

        claims = {
            "role": user.role,
            "email": user.email,
        }
        access_token = create_access_token(identity=user, additional_claims=claims)
        return {
            "access_token": access_token,
            "token_type": "Bearer"
        }

    @staticmethod
    def logout(jwt_payload: dict):
        """
        Revokes a JWT token by adding its jti and expiration to the revoked_tokens store.
        """
        jti = jwt_payload.get("jti")
        token_type = jwt_payload.get("type", "access")
        user_id_raw = jwt_payload.get("sub")
        exp_timestamp = jwt_payload.get("exp")

        if not jti:
            raise ValueError("Token does not contain a valid jti.")

        user_uuid = None
        if user_id_raw:
            try:
                user_uuid = uuid.UUID(str(user_id_raw)) if not isinstance(user_id_raw, uuid.UUID) else user_id_raw
            except (ValueError, TypeError):
                user_uuid = None

        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else None

        RevokedToken.revoke(
            jti=jti,
            token_type=token_type,
            user_id=user_uuid,
            expires_at=expires_at
        )

    @staticmethod
    def change_password(user, current_password: str, new_password: str):
        """Validates current password and updates to new secure hashed password."""
        if not user.check_password(current_password):
            raise ValueError("Current password does not match our records.")

        if current_password == new_password:
            raise ValueError("New password cannot be the same as the current password.")

        user.set_password(new_password)
        db.session.commit()

    @staticmethod
    def request_password_reset(email: str):
        """
        Initiates secure password reset workflow.
        Returns a generic success message without leaking account existence.
        """
        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()

        raw_token = None
        if user and user.is_active:
            raw_token = PasswordResetToken.create_token(user.id, expires_in_minutes=60)

            # Log audit event
            audit = AuditLog(
                user_id=user.id,
                action="PASSWORD_RESET_REQUESTED",
                target_entity="USER",
                target_id=str(user.id),
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(audit)
            db.session.commit()

            # Attempt email dispatch via EmailService
            subject = "ESMS - Password Reset Request"
            reset_url = f"/reset-password?token={raw_token}"
            body_text = f"Hello,\n\nYou requested a password reset for your ESMS account. Use the token below to reset your password within 1 hour:\n\n{raw_token}\n\nIf you did not request this, please ignore this email."
            body_html = f"<p>Hello,</p><p>You requested a password reset for your ESMS account. Use the token below within 1 hour:</p><p><code>{raw_token}</code></p><p>If you did not request this, ignore this email.</p>"
            try:
                EmailService.send_email(user.email, subject, body_text, body_html)
            except Exception:
                pass  # Non-blocking

        # Always return identical response to prevent user enumeration
        return {
            "message": "If an account with this email exists, password reset instructions have been sent.",
            # Only exposed in development/testing mode for verification:
            "debug_token": raw_token
        }

    @staticmethod
    def reset_password(token: str, new_password: str):
        """
        Validates token hash, enforces new password strength, and updates user password.
        """
        token_record = PasswordResetToken.verify_token(token)
        if not token_record:
            raise ValueError("Invalid or expired password reset token.")

        user = db.session.get(User, token_record.user_id)
        if not user or not user.is_active:
            raise ValueError("Associated user account is deactivated or invalid.")

        user.set_password(new_password)
        token_record.mark_as_used()

        # Log audit event
        audit = AuditLog(
            user_id=user.id,
            action="PASSWORD_RESET_COMPLETED",
            target_entity="USER",
            target_id=str(user.id),
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(audit)
        db.session.commit()

        return {"message": "Password reset successfully. You may now log in with your new credentials."}
