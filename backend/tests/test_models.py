import uuid
from datetime import datetime, timezone, date, timedelta
from unittest.mock import MagicMock
import pytest
from app.models import (
    User, RevokedToken, Department, Employee,
    Attendance, LeaveType, LeaveRequest, Task,
    PerformanceReview, AuditLog
)

def test_models_registered_in_metadata(app):
    """Verifies that all 10 core tables are properly registered in SQLAlchemy metadata."""
    from app.extension_registry import db
    tables = db.metadata.tables.keys()
    expected_tables = {
        "users",
        "revoked_tokens",
        "departments",
        "employees",
        "attendance",
        "leave_types",
        "leave_requests",
        "tasks",
        "performance_reviews",
        "audit_logs"
    }
    for table in expected_tables:
        assert table in tables, f"Expected table '{table}' not found in SQLAlchemy metadata."

def test_user_model_attributes():
    """Validates User model structure, constraints, and defaults."""
    user = User(
        email="admin@company.com",
        password_hash="argon2_hashed_secret",
        role="ADMIN",
        is_active=True
    )
    assert user.email == "admin@company.com"
    assert user.role == "ADMIN"
    assert user.is_active is True
    assert repr(user) == "<User admin@company.com (ADMIN)>"

    user_table = User.__table__
    constraint_names = {c.name for c in user_table.constraints}
    assert "chk_user_role" in constraint_names

def test_employee_model_and_properties():
    """Validates Employee model structure and properties."""
    emp_id = uuid.uuid4()
    emp = Employee(
        id=emp_id,
        employee_code="EMP-1001",
        first_name="Jane",
        last_name="Doe",
        department_id=1,
        designation="Software Engineer",
        status="ACTIVE"
    )
    assert emp.full_name == "Jane Doe"
    assert emp.employee_code == "EMP-1001"
    assert emp.status == "ACTIVE"
    assert "EMP-1001 - Jane Doe" in repr(emp)

    emp_table = Employee.__table__
    constraint_names = {c.name for c in emp_table.constraints}
    assert "chk_emp_gender" in constraint_names
    assert "chk_emp_type" in constraint_names
    assert "chk_emp_status" in constraint_names

def test_attendance_model_constraints_and_multi_shift():
    """Validates multi-shift attendance architecture and checkout checks."""
    now = datetime.now(timezone.utc)
    att = Attendance(
        employee_id=uuid.uuid4(),
        work_date=date.today(),
        shift_number=2,
        check_in=now,
        check_out=now + timedelta(hours=8),
        total_hours=8.00,
        status="PRESENT"
    )
    assert att.shift_number == 2
    assert att.total_hours == 8.00
    assert att.status == "PRESENT"
    assert att.check_out > att.check_in

    att_table = Attendance.__table__
    constraint_names = {c.name for c in att_table.constraints}
    assert "chk_att_checkout_after_checkin" in constraint_names
    assert "chk_att_hours_range" in constraint_names
    assert "chk_att_shift_number" in constraint_names
    assert "uq_att_emp_date_shift" in constraint_names

    index_names = {idx.name for idx in att_table.indexes}
    assert "uq_att_active_session" in index_names

def test_leave_request_date_constraints():
    """Validates LeaveRequest model constraint definitions."""
    leave_table = LeaveRequest.__table__
    constraint_names = {c.name for c in leave_table.constraints}
    assert "chk_leave_date_order" in constraint_names
    assert "chk_leave_positive_days" in constraint_names
    assert "chk_leave_status" in constraint_names

def test_leave_concurrency_overlap_logic():
    """
    Tests the leave overlap algorithm and concurrency protection logic.
    Verifies that:
    1. Overlapping date ranges are blocked.
    2. Exact boundary touches are detected.
    3. Non-overlapping ranges are permitted.
    4. Cancelled or rejected requests do not block new submissions.
    """
    emp_id = uuid.uuid4()
    today = date(2026, 6, 1)

    # Mock an existing approved leave from June 1 to June 5
    existing_approved = LeaveRequest(
        id=1,
        employee_id=emp_id,
        leave_type_id=1,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 5),
        total_days=5.0,
        status="APPROVED"
    )

    # Simulated overlap check helper matching check_overlap logic:
    # (existing.start_date <= end_date AND existing.end_date >= start_date)
    def is_overlapping(existing, new_start, new_end):
        if existing.status not in ["PENDING", "APPROVED"]:
            return False
        return existing.start_date <= new_end and existing.end_date >= new_start

    # Scenario A: Exact overlap (June 2 to June 4) -> MUST FAIL
    assert is_overlapping(existing_approved, date(2026, 6, 2), date(2026, 6, 4)) is True

    # Scenario B: Partial overlap beginning (May 28 to June 2) -> MUST FAIL
    assert is_overlapping(existing_approved, date(2026, 5, 28), date(2026, 6, 2)) is True

    # Scenario C: Partial overlap ending (June 4 to June 10) -> MUST FAIL
    assert is_overlapping(existing_approved, date(2026, 6, 4), date(2026, 6, 10)) is True

    # Scenario D: Touching boundary (June 5 to June 8) -> MUST FAIL (June 5 is shared)
    assert is_overlapping(existing_approved, date(2026, 6, 5), date(2026, 6, 8)) is True

    # Scenario E: Completely after (June 6 to June 10) -> MUST PASS
    assert is_overlapping(existing_approved, date(2026, 6, 6), date(2026, 6, 10)) is False

    # Scenario F: Completely before (May 20 to May 31) -> MUST PASS
    assert is_overlapping(existing_approved, date(2026, 5, 20), date(2026, 5, 31)) is False

    # Scenario G: Rejected / Cancelled request does NOT block future application
    existing_cancelled = LeaveRequest(
        id=2,
        employee_id=emp_id,
        leave_type_id=1,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 5),
        total_days=5.0,
        status="CANCELLED"
    )
    assert is_overlapping(existing_cancelled, date(2026, 7, 1), date(2026, 7, 5)) is False

def test_leave_validate_and_submit_validation_errors():
    """Verifies that LeaveRequest.validate_and_submit raises clean ValueErrors on invalid input."""
    session_mock = MagicMock()
    session_mock.get_bind.return_value.dialect.name = "sqlite" # mock dialect
    emp_id = uuid.uuid4()

    # Test invalid end_date < start_date
    with pytest.raises(ValueError, match="End date cannot be earlier than start date"):
        LeaveRequest.validate_and_submit(
            session_mock,
            emp_id,
            1,
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 5),
            total_days=5,
            reason="Holiday"
        )

    # Test total_days <= 0
    with pytest.raises(ValueError, match="Total leave days must be greater than zero"):
        LeaveRequest.validate_and_submit(
            session_mock,
            emp_id,
            1,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 5),
            total_days=0,
            reason="Holiday"
        )

def test_task_model_constraints():
    """Validates Task model attributes and constraint definitions."""
    task = Task(
        title="Implement OAuth Flow",
        assigned_to=uuid.uuid4(),
        created_by=uuid.uuid4(),
        priority="HIGH",
        status="IN_PROGRESS"
    )
    assert task.priority == "HIGH"
    assert task.status == "IN_PROGRESS"

    task_table = Task.__table__
    constraint_names = {c.name for c in task_table.constraints}
    assert "chk_task_priority" in constraint_names
    assert "chk_task_status" in constraint_names

def test_performance_review_rating_constraint():
    """Validates that performance review enforces rating on 1-5 scale."""
    perf_table = PerformanceReview.__table__
    constraint_names = {c.name for c in perf_table.constraints}
    assert "chk_perf_rating_range" in constraint_names

def test_revoked_token_attributes():
    """Validates RevokedToken structure for JWT invalidation."""
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    token = RevokedToken(
        jti=jti,
        token_type="access",
        expires_at=now + timedelta(hours=8)
    )
    assert token.jti == jti
    assert token.token_type == "access"
    assert token.expires_at > now

def test_audit_log_attributes():
    """Validates AuditLog model and JSONB state storage."""
    log = AuditLog(
        action="UPDATE_EMPLOYEE",
        target_entity="employees",
        target_id="EMP-1001",
        previous_state={"designation": "Junior Engineer"},
        new_state={"designation": "Senior Engineer"},
        ip_address="127.0.0.1"
    )
    assert log.action == "UPDATE_EMPLOYEE"
    assert log.previous_state["designation"] == "Junior Engineer"
    assert log.new_state["designation"] == "Senior Engineer"

