import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(String(200), nullable=False)
    message = db.Column(Text, nullable=False)
    category = db.Column(String(50), nullable=False, default="SYSTEM")
    priority = db.Column(String(20), nullable=False, default="NORMAL")
    is_read = db.Column(Boolean, nullable=False, default=False, index=True)
    read_at = db.Column(DateTime(timezone=True), nullable=True)
    action_url = db.Column(String(255), nullable=True)
    meta_data = db.Column(Text, nullable=True)  # JSON or text metadata
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        CheckConstraint(
            "category IN ('ATTENDANCE', 'LEAVE', 'TASK', 'PERFORMANCE', 'SYSTEM', 'ANNOUNCEMENT')",
            name="chk_notif_category"
        ),
        CheckConstraint(
            "priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')",
            name="chk_notif_priority"
        ),
        Index("idx_notif_user_unread", "user_id", "is_read"),
        Index("idx_notif_user_created", "user_id", "created_at"),
    )

    # Relationships
    user = db.relationship("User", backref=db.backref("notifications", cascade="all, delete-orphan", lazy="dynamic"))

    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "priority": self.priority,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "action_url": self.action_url,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Notification id={self.id} user={self.user_id} category={self.category} read={self.is_read}>"

