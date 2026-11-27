from datetime import datetime, timezone
from sqlalchemy import BigInteger, Date, DateTime, Numeric, String, Text, Boolean, Integer, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    employee_id = db.Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    work_date = db.Column(Date, nullable=False, index=True)
    shift_number = db.Column(Integer, nullable=False, default=1)
    check_in = db.Column(DateTime(timezone=True), nullable=False)
    check_out = db.Column(DateTime(timezone=True), nullable=True)
    total_hours = db.Column(Numeric(4, 2), nullable=False, default=0.00)
    status = db.Column(String(20), nullable=False, default="PRESENT")
    notes = db.Column(Text, nullable=True)
    is_corrected = db.Column(Boolean, default=False, nullable=False)
    corrected_by = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('PRESENT', 'LATE', 'HALF_DAY', 'ABSENT')", name="chk_att_status"),
        CheckConstraint("check_out IS NULL OR check_out > check_in", name="chk_att_checkout_after_checkin"),
        CheckConstraint("total_hours >= 0 AND total_hours <= 24", name="chk_att_hours_range"),
        CheckConstraint("shift_number >= 1", name="chk_att_shift_number"),
        UniqueConstraint("employee_id", "work_date", "shift_number", name="uq_att_emp_date_shift"),
        # Partial unique index: Only one active attendance session (check_out is NULL) per employee
        Index(
            "uq_att_active_session",
            "employee_id",
            unique=True,
            postgresql_where=(check_out.is_(None)),
            sqlite_where=(check_out.is_(None))
        ),
    )

    employee = db.relationship("Employee", back_populates="attendances")
    corrector = db.relationship("User", foreign_keys=[corrected_by])

    def to_dict(self):
        """Returns dictionary representation of attendance session."""
        return {
            "id": self.id,
            "employee_id": str(self.employee_id),
            "employee_name": self.employee.full_name if self.employee else None,
            "employee_code": self.employee.employee_code if self.employee else None,
            "department_name": self.employee.department.name if (self.employee and self.employee.department) else None,
            "work_date": self.work_date.isoformat() if self.work_date else None,
            "shift_number": self.shift_number,
            "check_in": self.check_in.isoformat() if self.check_in else None,
            "check_out": self.check_out.isoformat() if self.check_out else None,
            "total_hours": float(self.total_hours) if self.total_hours is not None else 0.0,
            "status": self.status,
            "notes": self.notes,
            "is_corrected": self.is_corrected,
            "corrected_by": str(self.corrected_by) if self.corrected_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Attendance emp={self.employee_id} date={self.work_date} shift={self.shift_number} status={self.status}>"

