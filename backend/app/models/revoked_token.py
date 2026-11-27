from datetime import datetime, timezone
from sqlalchemy import BigInteger, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

class RevokedToken(db.Model):
    __tablename__ = "revoked_tokens"

    id = db.Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    jti = db.Column(String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(String(10), nullable=False, default="access")
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    expires_at = db.Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", back_populates="revoked_tokens")

    @classmethod
    def is_token_revoked(cls, jti: str) -> bool:
        """Checks if a given JWT unique identifier (jti) is in the revocation list."""
        if not jti:
            return False
        return cls.query.filter_by(jti=jti).first() is not None

    @classmethod
    def revoke(cls, jti: str, token_type: str, user_id=None, expires_at=None):
        """Records a token as revoked in the database."""
        if not expires_at:
            expires_at = datetime.now(timezone.utc)
        record = cls(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(record)
        db.session.commit()
        return record

    def __repr__(self):
        return f"<RevokedToken {self.jti} ({self.token_type})>"

