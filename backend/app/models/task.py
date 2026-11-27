from datetime import datetime, timezone
from sqlalchemy import BigInteger, Integer, String, Text, Date, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    title = db.Column(String(200), nullable=False)
    description = db.Column(Text, nullable=True)
    category = db.Column(String(50), nullable=True)
    assigned_to = db.Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    department_id = db.Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    priority = db.Column(String(20), nullable=False, default="MEDIUM")
    status = db.Column(String(20), nullable=False, default="TODO")
    start_date = db.Column(Date, nullable=True)
    due_date = db.Column(Date, nullable=True, index=True)
    completed_at = db.Column(DateTime(timezone=True), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')", name="chk_task_priority"),
        CheckConstraint("status IN ('TODO', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'BLOCKED', 'CANCELLED')", name="chk_task_status"),
        CheckConstraint("due_date IS NULL OR start_date IS NULL OR due_date >= start_date", name="chk_task_date_order"),
        Index("idx_tasks_assignee_status", "assigned_to", "status"),
        Index("idx_tasks_due_date", "due_date"),
    )

    assignee = db.relationship("Employee", back_populates="tasks")
    creator = db.relationship("User", back_populates="created_tasks")
    department = db.relationship("Department")

    def to_dict(self):
        """Returns comprehensive dictionary representation of a task."""
        now_date = datetime.now(timezone.utc).date()
        is_overdue = False
        if self.due_date and self.status not in ["COMPLETED", "CANCELLED"]:
            if self.due_date < now_date:
                is_overdue = True

        dept_id = self.department_id or (self.assignee.department_id if self.assignee else None)
        dept_name = None
        if self.department:
            dept_name = self.department.name
        elif self.assignee and self.assignee.department:
            dept_name = self.assignee.department.name

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "assignee_name": self.assignee.full_name if self.assignee else None,
            "assignee_code": self.assignee.employee_code if self.assignee else None,
            "assignee_email": self.assignee.user.email if (self.assignee and self.assignee.user) else None,
            "department_id": dept_id,
            "department_name": dept_name,
            "created_by": str(self.created_by) if self.created_by else None,
            "creator_email": self.creator.email if self.creator else None,
            "priority": self.priority,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "is_overdue": is_overdue,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Task id={self.id} title={self.title[:30]} status={self.status}>"
