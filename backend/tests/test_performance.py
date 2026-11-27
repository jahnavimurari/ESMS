import pytest
import uuid
from datetime import datetime, timezone, timedelta, date
from app.extension_registry import db
from app.models.department import Department
from app.models.employee import Employee
from app.models.performance import PerformanceCycle, PerformanceReview, RATING_DEFINITIONS
from app.models.user import User
from app.models.audit import AuditLog

@pytest.fixture
def setup_performance_fixtures(app, sample_users):
    """Sets up department and two active employees (Emp1, Emp2) and an inactive employee."""
    with app.app_context():
        dept = Department(name="Engineering", code="ENG", description="Core Platform Engineering")
        db.session.add(dept)
        db.session.commit()

        emp_user_1 = User.query.filter_by(email="emp@test.com").first()
        emp1 = Employee(
            user_id=emp_user_1.id,
            employee_code="EMP-PRF-01",
            first_name="Alice",
            last_name="Walker",
            department_id=dept.id,
            designation="Senior Engineer",
            status="ACTIVE"
        )

        emp_user_2 = User(email="emp2@test.com", role="EMPLOYEE", is_active=True)
        emp_user_2.set_password("Emp2Pass123!")
        db.session.add(emp_user_2)
        db.session.flush()

        emp2 = Employee(
            user_id=emp_user_2.id,
            employee_code="EMP-PRF-02",
            first_name="Bob",
            last_name="Builder",
            department_id=dept.id,
            designation="Quality Analyst",
            status="ACTIVE"
        )

        # Inactive employee
        emp_user_inactive = User.query.filter_by(email="inactive@test.com").first()
        emp_inactive = Employee(
            user_id=emp_user_inactive.id,
            employee_code="EMP-PRF-INACT",
            first_name="Charlie",
            last_name="Terminated",
            department_id=dept.id,
            designation="Ex-Employee",
            status="TERMINATED"
        )

        db.session.add_all([emp1, emp2, emp_inactive])
        db.session.commit()

        return {
            "department_id": dept.id,
            "emp1_id": str(emp1.id),
            "emp2_id": str(emp2.id),
            "emp_inactive_id": str(emp_inactive.id),
        }

@pytest.fixture
def auth_tokens_perf(client, setup_performance_fixtures):
    """Obtains JWT tokens for Admin, HR, Employee 1, and Employee 2."""
    res_admin = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "AdminPass123!"})
    res_hr = client.post("/api/auth/login", json={"email": "hr@test.com", "password": "HRPass123!"})
    res_emp1 = client.post("/api/auth/login", json={"email": "emp@test.com", "password": "EmpPass123!"})
    res_emp2 = client.post("/api/auth/login", json={"email": "emp2@test.com", "password": "Emp2Pass123!"})

    return {
        "admin": res_admin.json["data"]["access_token"],
        "hr": res_hr.json["data"]["access_token"],
        "emp1": res_emp1.json["data"]["access_token"],
        "emp2": res_emp2.json["data"]["access_token"],
    }


# ==============================================================================
# 1. Performance Cycle Tests
# ==============================================================================
def test_create_cycle_success(client, auth_tokens_perf):
    """HR creates a valid performance cycle."""
    payload = {
        "title": "Annual Review 2026",
        "description": "2026 Annual Employee Performance Evaluation Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15",
        "status": "ACTIVE"
    }
    res = client.post("/api/performance/cycles", json=payload, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res.status_code == 201
    data = res.json["data"]
    assert data["title"] == "Annual Review 2026"
    assert data["status"] == "ACTIVE"
    assert data["metrics"]["total_reviews"] == 0

def test_create_cycle_date_validation(client, auth_tokens_perf):
    """Cycle creation fails if end_date or due_date is before start_date."""
    # End date before start date
    res = client.post("/api/performance/cycles", json={
        "title": "Invalid Cycle",
        "start_date": "2026-06-01",
        "end_date": "2026-05-01",
        "due_date": "2026-06-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res.status_code == 400

    # Due date before start date
    res2 = client.post("/api/performance/cycles", json={
        "title": "Invalid Cycle 2",
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
        "due_date": "2026-05-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res2.status_code == 400

def test_employee_cannot_create_or_update_cycle(client, auth_tokens_perf):
    """Employees are blocked by RBAC from creating or modifying cycles."""
    res = client.post("/api/performance/cycles", json={
        "title": "Hacked Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res.status_code == 403

def test_update_cycle_and_toggle_status(client, auth_tokens_perf):
    """HR updates cycle details and toggles status between ACTIVE and CLOSED."""
    res_create = client.post("/api/performance/cycles", json={
        "title": "Q1 2026 Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
        "due_date": "2026-04-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['admin']}"})
    cycle_id = res_create.json["data"]["id"]

    # Update description
    res_update = client.put(f"/api/performance/cycles/{cycle_id}", json={
        "description": "Updated Q1 Evaluation"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res_update.status_code == 200
    assert res_update.json["data"]["description"] == "Updated Q1 Evaluation"

    # Toggle to CLOSED
    res_status = client.patch(f"/api/performance/cycles/{cycle_id}/status", json={
        "status": "CLOSED"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res_status.status_code == 200
    assert res_status.json["data"]["status"] == "CLOSED"


# ==============================================================================
# 2. Performance Review Creation & Uniqueness Tests
# ==============================================================================
def test_create_review_success(client, auth_tokens_perf, setup_performance_fixtures):
    """HR creates review for active employee in active cycle."""
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "H1 2026",
        "start_date": "2026-01-01",
        "end_date": "2026-06-30",
        "due_date": "2026-07-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    res_review = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
        "review_period": "H1 2026"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res_review.status_code == 201
    data = res_review.json["data"]
    assert data["cycle_id"] == cycle_id
    assert data["employee_id"] == setup_performance_fixtures["emp1_id"]
    assert data["status"] == "DRAFT"

def test_duplicate_review_in_same_cycle_rejected(client, auth_tokens_perf, setup_performance_fixtures):
    """Enforces uq_perf_emp_cycle: one employee cannot have two reviews in the same cycle."""
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "H2 2026",
        "start_date": "2026-07-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    # First review creation
    res1 = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res1.status_code == 201

    # Second review for same employee in same cycle MUST FAIL
    res2 = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res2.status_code == 400
    assert "already exists" in res2.json["error"]["message"].lower()

def test_create_review_for_inactive_employee_rejected(client, auth_tokens_perf, setup_performance_fixtures):
    """Cannot initiate performance review for terminated or inactive employee."""
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Cycle Active",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    res = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp_inactive_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res.status_code == 400
    assert "active" in res.json["error"]["message"].lower()

def test_cannot_create_review_in_closed_cycle(client, auth_tokens_perf, setup_performance_fixtures):
    """Cannot initiate review in a CLOSED cycle."""
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Old Closed Cycle",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "due_date": "2026-01-15",
        "status": "CLOSED"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    res = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res.status_code == 400
    assert "closed" in res.json["error"]["message"].lower()


# ==============================================================================
# 3. RBAC & Cross-Employee Isolation Tests
# ==============================================================================
def test_employee_can_only_view_own_reviews(client, auth_tokens_perf, setup_performance_fixtures):
    """Employee 1 can view their own review; cannot access Employee 2's review."""
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Security Isolation Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['admin']}"})
    cycle_id = res_cycle.json["data"]["id"]

    # Review for Emp 1
    res_r1 = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    r1_id = res_r1.json["data"]["id"]

    # Review for Emp 2
    res_r2 = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp2_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    r2_id = res_r2.json["data"]["id"]

    # Emp 1 views own review -> 200 OK
    res_get_own = client.get(f"/api/performance/reviews/{r1_id}", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res_get_own.status_code == 200

    # Emp 1 attempts to view Emp 2's review -> 403 Forbidden
    res_get_other = client.get(f"/api/performance/reviews/{r2_id}", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res_get_other.status_code == 403

    # Listing reviews as Emp 1 only lists Emp 1's reviews
    res_list_emp1 = client.get("/api/performance/reviews", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res_list_emp1.status_code == 200
    items = res_list_emp1.json["data"]["items"]
    assert len(items) == 1
    assert items[0]["id"] == r1_id


# ==============================================================================
# 4. Self-Assessment Lifecycle & Validation Tests
# ==============================================================================
def test_self_assessment_flow_and_lockout(client, auth_tokens_perf, setup_performance_fixtures):
    """
    Tests:
    1. Employee saves draft self-assessment.
    2. Rating constraint: self_rating 1-5 enforced (6 rejected).
    3. Status transitions from DRAFT -> SELF_ASSESSMENT -> MANAGER_REVIEW upon submission.
    4. Once submitted, employee cannot modify self-assessment.
    """
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Self Assessment Test Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    res_review = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    review_id = res_review.json["data"]["id"]

    # Invalid self rating: 6 rejected
    res_invalid_rating = client.patch(f"/api/performance/reviews/{review_id}/self-assessment", json={
        "self_rating": 6,
        "accomplishments": "Delivered all milestones early."
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res_invalid_rating.status_code == 400

    # Valid draft update
    res_draft = client.patch(f"/api/performance/reviews/{review_id}/self-assessment", json={
        "self_rating": 4,
        "accomplishments": "Architected new event-driven microservices.",
        "challenges": "Tight integration deadlines with legacy systems.",
        "skills_learned": "PostgreSQL exclusion constraints and Docker orchestration.",
        "goals_achievement": "Exceeded all Q1 engineering objectives."
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res_draft.status_code == 200
    data = res_draft.json["data"]
    assert data["status"] == "SELF_ASSESSMENT"
    assert data["self_assessment"]["self_rating"] == 4
    assert data["self_assessment"]["self_rating_label"] == "Exceeds Expectations"

    # Submit self-assessment
    res_submit = client.patch(f"/api/performance/reviews/{review_id}/submit", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res_submit.status_code == 200
    assert res_submit.json["data"]["status"] == "MANAGER_REVIEW"
    assert res_submit.json["data"]["self_assessment"]["submitted_at"] is not None

    # Employee tries to edit self-assessment after submit -> 400 Bad Request
    res_locked = client.patch(f"/api/performance/reviews/{review_id}/self-assessment", json={
        "self_rating": 5
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res_locked.status_code == 400
    assert "already been submitted" in res_locked.json["error"]["message"].lower()


# ==============================================================================
# 5. Manager Evaluation & Completion Lifecycle Tests
# ==============================================================================
def test_manager_evaluation_and_completion_lifecycle(client, auth_tokens_perf, setup_performance_fixtures):
    """
    Tests:
    1. Employee submits self-assessment.
    2. Manager evaluation validation (rating must be 1-5, feedback >= 5 chars).
    3. Rating scale label mapping (5 -> Outstanding).
    4. Completion requirement (cannot complete without rating & feedback).
    5. Completed review is locked from modification.
    """
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Manager Review Flow Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    res_review = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    review_id = res_review.json["data"]["id"]

    # Submit self assessment
    client.patch(f"/api/performance/reviews/{review_id}/submit", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})

    # Cannot complete review before manager evaluation is provided
    res_premature_complete = client.patch(f"/api/performance/reviews/{review_id}/complete", headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res_premature_complete.status_code == 400
    assert "cannot complete review without a manager rating" in res_premature_complete.json["error"]["message"].lower()

    # Invalid manager rating (0 rejected)
    res_invalid_rating = client.patch(f"/api/performance/reviews/{review_id}/manager-review", json={
        "rating": 0,
        "manager_feedback": "Invalid rating test"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['admin']}"})
    assert res_invalid_rating.status_code == 400

    # Valid manager evaluation (Rating 5 - Outstanding)
    res_mgr_review = client.patch(f"/api/performance/reviews/{review_id}/manager-review", json={
        "rating": 5,
        "manager_feedback": "Exceptional leadership on backend architecture and zero-defect delivery.",
        "strengths": "System design, mentoring, cross-functional collaboration.",
        "areas_for_improvement": "Continue scaling delegation across junior engineers.",
        "development_plan": "Executive leadership sponsorship in Q3."
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['admin']}"})
    assert res_mgr_review.status_code == 200
    data = res_mgr_review.json["data"]
    assert data["manager_evaluation"]["rating"] == 5
    assert data["manager_evaluation"]["rating_label"] == "Outstanding"

    # Complete the review
    res_complete = client.patch(f"/api/performance/reviews/{review_id}/complete", headers={"Authorization": f"Bearer {auth_tokens_perf['admin']}"})
    assert res_complete.status_code == 200
    assert res_complete.json["data"]["status"] == "COMPLETED"
    assert res_complete.json["data"]["manager_evaluation"]["completed_at"] is not None

    # Completed review cannot have manager review modified
    res_mod_completed = client.patch(f"/api/performance/reviews/{review_id}/manager-review", json={
        "rating": 4,
        "manager_feedback": "Trying to modify completed review"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['admin']}"})
    assert res_mod_completed.status_code == 400


# ==============================================================================
# 6. Reopening Completed Reviews & Strict Audit Trail Tests
# ==============================================================================
def test_reopen_completed_review_with_audit_trail(client, auth_tokens_perf, setup_performance_fixtures):
    """
    Tests:
    1. Only HR/Admin can reopen a completed review (Employee rejected with 403).
    2. Reopening without reason is rejected (400).
    3. Reopened review transitions from COMPLETED -> MANAGER_REVIEW.
    4. AuditLog contains REOPEN_PERFORMANCE_REVIEW action with justification reason and user.
    """
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Reopen Audit Test Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    res_review = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    review_id = res_review.json["data"]["id"]

    # Submit self-assessment, manager review, and complete
    client.patch(f"/api/performance/reviews/{review_id}/submit", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    client.patch(f"/api/performance/reviews/{review_id}/manager-review", json={
        "rating": 3,
        "manager_feedback": "Solid performance meeting all requirements."
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    client.patch(f"/api/performance/reviews/{review_id}/complete", headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})

    # Employee attempts to reopen -> 403 Forbidden
    res_emp_reopen = client.patch(f"/api/performance/reviews/{review_id}/reopen", json={
        "reason": "I disagree with the rating"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res_emp_reopen.status_code == 403

    # HR attempts to reopen without reason -> 400 Validation Error
    res_no_reason = client.patch(f"/api/performance/reviews/{review_id}/reopen", json={}, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res_no_reason.status_code == 400

    # HR reopens with valid justification
    justification = "Executive committee approved additional project credits resulting in rating adjustment."
    res_reopen = client.patch(f"/api/performance/reviews/{review_id}/reopen", json={
        "reason": justification
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res_reopen.status_code == 200
    assert res_reopen.json["data"]["status"] == "MANAGER_REVIEW"

    # Check history / audit trail
    res_history = client.get(f"/api/performance/reviews/{review_id}/history", headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res_history.status_code == 200
    logs = res_history.json["data"]
    reopen_logs = [log for log in logs if log["action"] == "REOPEN_PERFORMANCE_REVIEW"]
    assert len(reopen_logs) >= 1
    assert reopen_logs[0]["new_state"]["reason"] == justification


# ==============================================================================
# 7. Summary & Ratings Scale Reference Tests
# ==============================================================================
def test_performance_summary_and_ratings_scale(client, auth_tokens_perf, setup_performance_fixtures):
    """Verifies organizational summary and rating scale reference endpoints."""
    # Scale reference
    res_scale = client.get("/api/performance/ratings-scale", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    assert res_scale.status_code == 200
    scale = res_scale.json["data"]
    assert len(scale) == 5
    assert scale[0]["label"] == "Needs Improvement"
    assert scale[4]["label"] == "Outstanding"

    # Summary
    res_summary = client.get("/api/performance/summary", headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    assert res_summary.status_code == 200
    summary = res_summary.json["data"]
    assert "total_reviews" in summary
    assert "status_breakdown" in summary
    assert "ratings_distribution" in summary
    assert len(summary["ratings_distribution"]) == 5

def test_unauthenticated_requests_return_401(client):
    """Unauthenticated access to any performance endpoint returns 401."""
    assert client.get("/api/performance/cycles").status_code == 401
    assert client.get("/api/performance/reviews").status_code == 401
    assert client.get("/api/performance/summary").status_code == 401


# ==============================================================================
# 8. Detailed Audit & Verification Tests for Final Clearance
# ==============================================================================
def test_unrelated_employee_cannot_evaluate_or_complete(client, auth_tokens_perf, setup_performance_fixtures):
    """An unrelated employee cannot submit manager feedback or complete another employee's review."""
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Authorization Strict Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    res_review = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    review_id = res_review.json["data"]["id"]

    # Submit self assessment
    client.patch(f"/api/performance/reviews/{review_id}/submit", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})

    # Employee 2 attempts to submit manager evaluation for Employee 1 -> 403 Forbidden
    res_eval = client.patch(f"/api/performance/reviews/{review_id}/manager-review", json={
        "rating": 4,
        "manager_feedback": "Unauthorized employee evaluation attempt."
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['emp2']}"})
    assert res_eval.status_code == 403

    # Employee 2 attempts to finalize Employee 1's review -> 403 Forbidden
    res_comp = client.patch(f"/api/performance/reviews/{review_id}/complete", headers={"Authorization": f"Bearer {auth_tokens_perf['emp2']}"})
    assert res_comp.status_code == 403

def test_employee_cannot_submit_self_assessment_for_another_employee(client, auth_tokens_perf, setup_performance_fixtures):
    """Employee 2 cannot update or submit self-assessment for Employee 1."""
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Cross Employee Assessment Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    res_review = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    review_id = res_review.json["data"]["id"]

    # Employee 2 attempts to edit Employee 1's draft self-assessment -> 403 Forbidden
    res_edit = client.patch(f"/api/performance/reviews/{review_id}/self-assessment", json={
        "self_rating": 2,
        "accomplishments": "Tampered accomplishments"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['emp2']}"})
    assert res_edit.status_code == 403

    # Employee 2 attempts to submit Employee 1's self-assessment -> 403 Forbidden
    res_sub = client.patch(f"/api/performance/reviews/{review_id}/submit", headers={"Authorization": f"Bearer {auth_tokens_perf['emp2']}"})
    assert res_sub.status_code == 403

def test_incomplete_reviews_excluded_from_completed_metrics(client, auth_tokens_perf, setup_performance_fixtures):
    """Verifies that in-progress/draft reviews do not taint completed review metrics or ratings distribution."""
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Metrics Isolation Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    # Review 1: Completed with rating 4
    res_r1 = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    r1_id = res_r1.json["data"]["id"]
    client.patch(f"/api/performance/reviews/{r1_id}/submit", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})
    client.patch(f"/api/performance/reviews/{r1_id}/manager-review", json={
        "rating": 4,
        "manager_feedback": "Exceeds expectations."
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    client.patch(f"/api/performance/reviews/{r1_id}/complete", headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})

    # Review 2: In MANAGER_REVIEW status with rating 2 (NOT finalized)
    res_r2 = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp2_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    r2_id = res_r2.json["data"]["id"]
    client.patch(f"/api/performance/reviews/{r2_id}/submit", headers={"Authorization": f"Bearer {auth_tokens_perf['emp2']}"})
    client.patch(f"/api/performance/reviews/{r2_id}/manager-review", json={
        "rating": 2,
        "manager_feedback": "Draft feedback not yet finalized."
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})

    # Verify summary: average rating should be exactly 4.00, NOT diluted by uncompleted review 2
    res_summary = client.get("/api/performance/summary", headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    summary = res_summary.json["data"]
    assert summary["average_rating"] == 4.00
    assert summary["status_breakdown"]["completed"] == 1
    assert summary["status_breakdown"]["in_progress"] == 1

    # In ratings distribution, score 4 count is 1, score 2 count is 0 (since review 2 is incomplete)
    dist_map = {item["score"]: item["count"] for item in summary["ratings_distribution"]}
    assert dist_map[4] == 1
    assert dist_map[2] == 0

def test_audit_logs_capture_all_lifecycle_events(app, client, auth_tokens_perf, setup_performance_fixtures):
    """Direct database audit log query confirming all 6 required lifecycle events are recorded with actor, id, and timestamp."""
    # 1. Cycle creation & modification
    res_cycle = client.post("/api/performance/cycles", json={
        "title": "Audit Verification Cycle",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "due_date": "2027-01-15"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    cycle_id = res_cycle.json["data"]["id"]

    client.put(f"/api/performance/cycles/{cycle_id}", json={
        "title": "Audit Verification Cycle Updated"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})

    client.patch(f"/api/performance/cycles/{cycle_id}/status", json={
        "status": "CLOSED"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})

    client.patch(f"/api/performance/cycles/{cycle_id}/status", json={
        "status": "ACTIVE"
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})

    # 2. Review initiation
    res_review = client.post("/api/performance/reviews", json={
        "cycle_id": cycle_id,
        "employee_id": setup_performance_fixtures["emp1_id"],
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})
    review_id = res_review.json["data"]["id"]

    # 3. Employee self-assessment submission
    client.patch(f"/api/performance/reviews/{review_id}/submit", headers={"Authorization": f"Bearer {auth_tokens_perf['emp1']}"})

    # 4. Manager evaluation
    client.patch(f"/api/performance/reviews/{review_id}/manager-review", json={
        "rating": 5,
        "manager_feedback": "Outstanding contributions to platform architecture."
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})

    # 5. Review completion
    client.patch(f"/api/performance/reviews/{review_id}/complete", headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})

    # 6. Review reopening
    client.patch(f"/api/performance/reviews/{review_id}/reopen", json={
        "reason": "Calibration meeting adjustment."
    }, headers={"Authorization": f"Bearer {auth_tokens_perf['hr']}"})

    with app.app_context():
        actions = [log.action for log in AuditLog.query.order_by(AuditLog.timestamp.asc()).all()]
        assert "CREATE_PERFORMANCE_CYCLE" in actions
        assert "UPDATE_PERFORMANCE_CYCLE" in actions
        assert "CYCLE_STATUS_CHANGE" in actions
        assert "CREATE_PERFORMANCE_REVIEW" in actions
        assert "SUBMIT_SELF_ASSESSMENT" in actions
        assert "SUBMIT_MANAGER_EVALUATION" in actions
        assert "COMPLETE_PERFORMANCE_REVIEW" in actions
        assert "REOPEN_PERFORMANCE_REVIEW" in actions

