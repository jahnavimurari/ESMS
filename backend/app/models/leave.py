import threading
import zlib
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Integer, Date, DateTime, Numeric, String, Text, Boolean, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

_employee_locks = {}
_registry_lock = threading.Lock()

class LeaveType(db.Model):
    __tablename__ = "leave_types"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    code = db.Column(String(20), unique=True, nullable=False, index=True)
    name = db.Column(String(100), nullable=False)
    description = db.Column(Text, nullable=True)
    days_per_year = db.Column(Integer, nullable=False, default=12)
    is_paid = db.Column(Boolean, default=True, nullable=False)
    is_active = db.Column(Boolean, default=True, nullable=False)

    leave_requests = db.relationship("LeaveRequest", back_populates="leave_type")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "days_per_year": self.days_per_year,
            "is_paid": self.is_paid,
            "is_active": self.is_active,
        }

    def __repr__(self):
        return f"<LeaveType {self.code} - {self.name}>"

class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"

    id = db.Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    employee_id = db.Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    leave_type_id = db.Column(Integer, ForeignKey("leave_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    start_date = db.Column(Date, nullable=False)
    end_date = db.Column(Date, nullable=False)
    total_days = db.Column(Numeric(4, 1), nullable=False)
    reason = db.Column(Text, nullable=False)
    status = db.Column(String(20), nullable=False, default="PENDING")
    reviewed_by = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_comments = db.Column(Text, nullable=True)
    reviewed_at = db.Column(DateTime(timezone=True), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')", name="chk_leave_status"),
        CheckConstraint("end_date >= start_date", name="chk_leave_date_order"),
        CheckConstraint("total_days > 0", name="chk_leave_positive_days"),
        Index("idx_leave_emp_status", "employee_id", "status"),
        Index("idx_leave_dates", "start_date", "end_date"),
    )

    employee = db.relationship("Employee", back_populates="leave_requests")
    leave_type = db.relationship("LeaveType", back_populates="leave_requests")
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])

    def to_dict(self):
        """Returns comprehensive dictionary representation of leave request."""
        return {
            "id": self.id,
            "employee_id": str(self.employee_id),
            "employee_name": self.employee.full_name if self.employee else None,
            "employee_code": self.employee.employee_code if self.employee else None,
            "department_name": self.employee.department.name if (self.employee and self.employee.department) else None,
            "leave_type_id": self.leave_type_id,
            "leave_type_name": self.leave_type.name if self.leave_type else None,
            "leave_type_code": self.leave_type.code if self.leave_type else None,
            "is_paid": self.leave_type.is_paid if self.leave_type else True,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "total_days": float(self.total_days) if self.total_days is not None else 0.0,
            "reason": self.reason,
            "status": self.status,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewer_email": self.reviewer.email if self.reviewer else None,
            "reviewer_comments": self.reviewer_comments,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def get_employee_thread_lock(employee_id):
        """
        Provides in-process thread synchronization per employee.
        Ensures thread-safe isolation on local/in-memory SQLite environments
        complementing PostgreSQL database-level advisory locking.
        """
        with _registry_lock:
            key = str(employee_id)
            if key not in _employee_locks:
                _employee_locks[key] = threading.Lock()
            return _employee_locks[key]

    @staticmethod
    def acquire_employee_lock(session, employee_id):
        """
        Acquires a transaction-scoped PostgreSQL advisory lock specifically for the employee.
        Serializes concurrent leave submissions for the same employee at the database engine level,
        preventing phantom overlaps even before records exist.
        The lock automatically releases when the transaction commits or rolls back.
        """
        bind = session.get_bind()
        if bind and bind.dialect.name == "postgresql":
            # Hash the UUID to a 32-bit signed integer for pg_advisory_xact_lock
            lock_id = zlib.crc32(str(employee_id).encode("utf-8")) & 0x7fffffff
            session.execute(text("SELECT pg_advisory_xact_lock(:lock_id);"), {"lock_id": lock_id})

    @classmethod
    def check_overlap(cls, session, employee_id, start_date, end_date, exclude_id=None):
        """
        Queries for active (PENDING or APPROVED) requests for this employee
        that overlap with [start_date, end_date].
        Overlap formula: existing.start_date <= end_date AND existing.end_date >= start_date
        """
        query = session.query(cls).filter(
            cls.employee_id == employee_id,
            cls.status.in_(["PENDING", "APPROVED"]),
            cls.start_date <= end_date,
            cls.end_date >= start_date
        )
        if exclude_id is not None:
            query = query.filter(cls.id != exclude_id)
        return query.first()

    @classmethod
    def validate_and_submit(cls, session, employee_id, leave_type_id, start_date, end_date, total_days, reason):
        """
        Transactional helper providing full concurrency protection and clear validation errors.
        1. Acquires transaction-scoped advisory lock on employee_id.
        2. Validates date boundaries.
        3. Checks for overlapping PENDING/APPROVED requests.
        4. Instantiates and stages the new LeaveRequest.
        """
        if end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")
        if total_days <= 0:
            raise ValueError("Total leave days must be greater than zero.")

        cls.acquire_employee_lock(session, employee_id)

        overlapping = cls.check_overlap(session, employee_id, start_date, end_date)
        if overlapping:
            raise ValueError(
                f"An overlapping {overlapping.status.lower()} leave request already exists "
                f"from {overlapping.start_date} to {overlapping.end_date}."
            )

        new_request = cls(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            status="PENDING"
        )
        session.add(new_request)
        return new_request

    def __repr__(self):
        return f"<LeaveRequest emp={self.employee_id} [{self.start_date} to {self.end_date}] status={self.status}>"

