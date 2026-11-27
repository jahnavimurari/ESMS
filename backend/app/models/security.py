import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = db.Column(String(64), nullable=False, index=True)
    expires_at = db.Column(DateTime(timezone=True), nullable=False, index=True)
    is_used = db.Column(Boolean, default=False, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User")

    @classmethod
    def hash_token(cls, token: str) -> str:
        """Returns the SHA-256 hex digest of the raw token."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def create_token(cls, user_id, expires_in_minutes=60):
        """Generates a secure cryptographically random reset token and persists its SHA-256 hash."""
        raw_token = secrets.token_urlsafe(32)
        hashed = cls.hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

        token_record = cls(
            user_id=user_id,
            token_hash=hashed,
            expires_at=expires_at,
            is_used=False
        )
        db.session.add(token_record)
        db.session.commit()
        return raw_token

    @classmethod
    def verify_token(cls, raw_token: str):
        """Verifies if the token is valid, unexpired, and unused. Returns the token record if valid."""
        if not raw_token:
            return None

        hashed = cls.hash_token(raw_token)
        now = datetime.now(timezone.utc)
        record = cls.query.filter(
            cls.token_hash == hashed,
            cls.is_used.is_(False),
            cls.expires_at > now
        ).first()
        return record

    def mark_as_used(self):
        """Marks the reset token as consumed."""
        self.is_used = True
        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_used": self.is_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<PasswordResetToken user={self.user_id} used={self.is_used}>"

