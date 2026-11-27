import uuid
import re
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import String, Boolean, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(255), nullable=False)
    role = db.Column(String(20), nullable=False, default="EMPLOYEE")
    is_active = db.Column(Boolean, default=True, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = db.Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'HR', 'EMPLOYEE')", name="chk_user_role"),
        Index("idx_users_role", "role"),
    )

    # Relationships
    employee = db.relationship("Employee", back_populates="user", uselist=False, cascade="all, delete-orphan")
    revoked_tokens = db.relationship("RevokedToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = db.relationship("AuditLog", back_populates="user")
    created_tasks = db.relationship("Task", back_populates="creator")
    submitted_reviews = db.relationship("PerformanceReview", back_populates="reviewer")

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """Enforces enterprise password complexity standards."""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_]", password):
            raise ValueError("Password must contain at least one special character.")

    def set_password(self, password: str) -> None:
        """Hashes and sets the user's password using modern scrypt/pbkdf2."""
        self.validate_password_strength(password)
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies a plain text password against the stored password hash."""
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Returns a safe dictionary representation without sensitive credentials."""
        emp_data = None
        if self.employee:
            emp_data = {
                "id": str(self.employee.id),
                "employee_code": self.employee.employee_code,
                "first_name": self.employee.first_name,
                "last_name": self.employee.last_name,
                "full_name": self.employee.full_name,
                "department_id": self.employee.department_id,
                "designation": self.employee.designation,
                "status": self.employee.status,
                "profile_image_url": self.employee.profile_image_url,
            }
        return {
            "id": str(self.id),
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "employee": emp_data,
        }

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

