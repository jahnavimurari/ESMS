from datetime import datetime, timezone
from sqlalchemy import BigInteger, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import JSON
from app.extension_registry import db

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(String(100), nullable=False)
    target_entity = db.Column(String(50), nullable=False)
    target_id = db.Column(String(100), nullable=True)
    # Use JSONB on PostgreSQL, fallback to standard JSON on SQLite/others
    previous_state = db.Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    new_state = db.Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    ip_address = db.Column(String(45), nullable=True)
    user_agent = db.Column(String(255), nullable=True)
    timestamp = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("idx_audit_entity", "target_entity", "target_id"),
        Index("idx_audit_timestamp_desc", timestamp.desc()),
    )

    user = db.relationship("User", back_populates="audit_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action,
            "target_entity": self.target_entity,
            "target_id": self.target_id,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f"<AuditLog id={self.id} action={self.action} target={self.target_entity}:{self.target_id}>"

