import uuid
from datetime import datetime, timezone, date
from sqlalchemy import String, Text, Date, DateTime, Integer, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), unique=True, nullable=False)
    employee_code = db.Column(String(30), unique=True, nullable=False, index=True)
    first_name = db.Column(String(100), nullable=False)
    last_name = db.Column(String(100), nullable=False)
    phone = db.Column(String(30), nullable=True)
    gender = db.Column(String(20), nullable=True)
    date_of_birth = db.Column(Date, nullable=True)
    address = db.Column(Text, nullable=True)
    department_id = db.Column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    designation = db.Column(String(100), nullable=False)
    joining_date = db.Column(Date, nullable=False, default=date.today)
    employment_type = db.Column(String(30), nullable=False, default="FULL_TIME")
    status = db.Column(String(30), nullable=False, default="ACTIVE")
    reporting_manager_id = db.Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    profile_image_url = db.Column(String(500), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("gender IN ('MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY')", name="chk_emp_gender"),
        CheckConstraint("employment_type IN ('FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERN')", name="chk_emp_type"),
        CheckConstraint("status IN ('ACTIVE', 'ON_LEAVE', 'TERMINATED', 'SUSPENDED')", name="chk_emp_status"),
        Index("idx_emp_names", "first_name", "last_name"),
    )

    # Relationships
    user = db.relationship("User", back_populates="employee")
    department = db.relationship("Department", back_populates="employees")
    reporting_manager = db.relationship("Employee", remote_side=[id], backref=db.backref("subordinates", lazy="dynamic"))
    attendances = db.relationship("Attendance", back_populates="employee", cascade="all, delete-orphan", lazy="dynamic")
    leave_requests = db.relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan", lazy="dynamic")
    tasks = db.relationship("Task", back_populates="assignee", cascade="all, delete-orphan", lazy="dynamic")
    performance_reviews = db.relationship("PerformanceReview", back_populates="employee", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self, include_manager=True, include_user=True):
        """Returns comprehensive dictionary representation of employee."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "employee_code": self.employee_code,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.user.email if self.user else None,
            "phone": self.phone,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "address": self.address,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "department_code": self.department.code if self.department else None,
            "designation": self.designation,
            "joining_date": self.joining_date.isoformat() if self.joining_date else None,
            "employment_type": self.employment_type,
            "status": self.status,
            "reporting_manager_id": str(self.reporting_manager_id) if self.reporting_manager_id else None,
            "reporting_manager_name": self.reporting_manager.full_name if (include_manager and self.reporting_manager) else None,
            "profile_image_url": self.profile_image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "role": self.user.role if (include_user and self.user) else None,
            "is_active": self.user.is_active if (include_user and self.user) else True,
        }

    def __repr__(self):
        return f"<Employee {self.employee_code} - {self.full_name}>"

