import pytest
import concurrent.futures
from datetime import datetime, timezone, timedelta, date
from app.extension_registry import db
from app.models.department import Department
from app.models.employee import Employee
from app.models.leave import LeaveRequest, LeaveType
from app.models.user import User

@pytest.fixture
def setup_leave_fixtures(app, sample_users):
    """Sets up leave types, department, and two employees."""
    with app.app_context():
        # Ensure standard leave types
        cl = LeaveType(code="CL", name="Casual Leave", days_per_year=12, is_paid=True, is_active=True)
        sl = LeaveType(code="SL", name="Sick Leave", days_per_year=10, is_paid=True, is_active=True)
        ul = LeaveType(code="UL", name="Unpaid Leave", days_per_year=0, is_paid=False, is_active=True)
        dept = Department(name="Operations", code="OPS", description="Operations team")
        db.session.add_all([cl, sl, ul, dept])
        db.session.commit()

        # Employee 1
        emp_user_1 = User.query.filter_by(email="emp@test.com").first()
        emp1 = Employee(
            user_id=emp_user_1.id,
            employee_code="EMP-LV-01",
            first_name="Carol",
            last_name="Danvers",
            department_id=dept.id,
            designation="Specialist",
            status="ACTIVE"
        )

        # Employee 2
        emp_user_2 = User(email="emp2@test.com", role="EMPLOYEE", is_active=True)
        emp_user_2.set_password("Emp2Pass123!")
        db.session.add(emp_user_2)
        db.session.flush()

        emp2 = Employee(
            user_id=emp_user_2.id,
            employee_code="EMP-LV-02",
            first_name="David",
            last_name="Banner",
            department_id=dept.id,
            designation="Scientist",
            status="ACTIVE"
        )
        db.session.add_all([emp1, emp2])
        db.session.commit()

        return {
            "dept_id": dept.id,
            "cl_id": cl.id,
            "sl_id": sl.id,
            "ul_id": ul.id,
            "emp1_id": str(emp1.id),
            "emp2_id": str(emp2.id)
        }

@pytest.fixture
def auth_tokens_leave(client, setup_leave_fixtures):
    """Generates access tokens for Admin, HR, Employee 1, and Employee 2."""
    res_admin = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "AdminPass123!"})
    admin_token = res_admin.get_json()["data"]["access_token"]

    res_hr = client.post("/api/auth/login", json={"email": "hr@test.com", "password": "HRPass123!"})
    hr_token = res_hr.get_json()["data"]["access_token"]

    res_emp1 = client.post("/api/auth/login", json={"email": "emp@test.com", "password": "EmpPass123!"})
    emp1_token = res_emp1.get_json()["data"]["access_token"]

    res_emp2 = client.post("/api/auth/login", json={"email": "emp2@test.com", "password": "Emp2Pass123!"})
    emp2_token = res_emp2.get_json()["data"]["access_token"]

    return {
        "admin": admin_token,
        "hr": hr_token,
        "emp1": emp1_token,
        "emp2": emp2_token
    }

def test_leave_application_success_and_balance(client, auth_tokens_leave, setup_leave_fixtures):
    """Verifies applying for leave and that pending leave does NOT deduct approved balance."""
    cl_id = setup_leave_fixtures["cl_id"]
    today = date.today()
    start = today + timedelta(days=5)
    end = today + timedelta(days=7)  # 3 days

    res = client.post("/api/leaves",
                      headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"},
                      json={
                          "leave_type_id": cl_id,
                          "start_date": start.isoformat(),
                          "end_date": end.isoformat(),
                          "reason": "Family vacation"
                      })
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["status"] == "PENDING"
    assert data["total_days"] == 3.0

    # Check balance: pending_days=3, approved_days=0, remaining_balance=12
    res_bal = client.get("/api/leaves/balance", headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"})
    assert res_bal.status_code == 200
    balances = res_bal.get_json()["data"]
    cl_bal = next(b for b in balances if b["leave_type_id"] == cl_id)
    assert cl_bal["pending_days"] == 3.0
    assert cl_bal["approved_days"] == 0.0
    assert cl_bal["remaining_balance"] == 12.0

def test_invalid_date_range_rejected(client, auth_tokens_leave, setup_leave_fixtures):
    """Verifies that start date after end date is rejected."""
    cl_id = setup_leave_fixtures["cl_id"]
    today = date.today()
    start = today + timedelta(days=5)
    end = today + timedelta(days=2)  # Invalid

    res = client.post("/api/leaves",
                      headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"},
                      json={
                          "leave_type_id": cl_id,
                          "start_date": start.isoformat(),
                          "end_date": end.isoformat(),
                          "reason": "Invalid dates"
                      })
    assert res.status_code == 400
    assert "End date cannot be earlier than start date" in res.get_json()["error"]["message"]

def test_overlapping_leave_rejection_for_same_employee(client, auth_tokens_leave, setup_leave_fixtures):
    """Verifies that an employee cannot submit overlapping leave requests."""
    cl_id = setup_leave_fixtures["cl_id"]
    today = date.today()
    start = today + timedelta(days=10)
    end = today + timedelta(days=15)

    # First request
    res1 = client.post("/api/leaves",
                       headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"},
                       json={"leave_type_id": cl_id, "start_date": start.isoformat(), "end_date": end.isoformat(), "reason": "First"})
    assert res1.status_code == 201

    # Overlapping request (e.g. days 12-14)
    res_overlap = client.post("/api/leaves",
                              headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"},
                              json={"leave_type_id": cl_id, "start_date": (today + timedelta(days=12)).isoformat(), "end_date": (today + timedelta(days=14)).isoformat(), "reason": "Overlap"})
    assert res_overlap.status_code == 400
    assert "overlapping" in res_overlap.get_json()["error"]["message"].lower()

def test_different_employees_can_apply_for_same_dates(client, auth_tokens_leave, setup_leave_fixtures):
    """Verifies that different employees can apply for the same dates without conflict."""
    cl_id = setup_leave_fixtures["cl_id"]
    today = date.today()
    start = today + timedelta(days=20)
    end = today + timedelta(days=22)

    res_emp1 = client.post("/api/leaves",
                           headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"},
                           json={"leave_type_id": cl_id, "start_date": start.isoformat(), "end_date": end.isoformat(), "reason": "Carol leave"})
    assert res_emp1.status_code == 201

    res_emp2 = client.post("/api/leaves",
                           headers={"Authorization": f"Bearer {auth_tokens_leave['emp2']}"},
                           json={"leave_type_id": cl_id, "start_date": start.isoformat(), "end_date": end.isoformat(), "reason": "David leave"})
    assert res_emp2.status_code == 201

def test_approval_workflow_and_balance_deduction(client, auth_tokens_leave, setup_leave_fixtures):
    """Verifies HR/Admin approval deducts approved balance and prevents duplicate approval."""
    cl_id = setup_leave_fixtures["cl_id"]
    today = date.today()
    start = today + timedelta(days=30)
    end = today + timedelta(days=33)  # 4 days

    # Apply
    res_apply = client.post("/api/leaves",
                            headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"},
                            json={"leave_type_id": cl_id, "start_date": start.isoformat(), "end_date": end.isoformat(), "reason": "Project break"})
    leave_id = res_apply.get_json()["data"]["id"]

    # Employee cannot approve own request
    res_unauth = client.patch(f"/api/leaves/{leave_id}/approve",
                              headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"})
    assert res_unauth.status_code == 403

    # HR approves request
    res_approve = client.patch(f"/api/leaves/{leave_id}/approve",
                               headers={"Authorization": f"Bearer {auth_tokens_leave['hr']}"},
                               json={"comments": "Approved. Enjoy your break."})
    assert res_approve.status_code == 200
    assert res_approve.get_json()["data"]["status"] == "APPROVED"

    # Duplicate approval rejected
    res_dup = client.patch(f"/api/leaves/{leave_id}/approve",
                           headers={"Authorization": f"Bearer {auth_tokens_leave['hr']}"})
    assert res_dup.status_code == 400
    assert "already approved" in res_dup.get_json()["error"]["message"].lower()

    # Verify balance: approved_days=4, remaining_balance=12-4=8
    res_bal = client.get("/api/leaves/balance", headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"})
    cl_bal = next(b for b in res_bal.get_json()["data"] if b["leave_type_id"] == cl_id)
    assert cl_bal["approved_days"] == 4.0
    assert cl_bal["remaining_balance"] == 8.0

def test_rejection_workflow_does_not_deduct_balance(client, auth_tokens_leave, setup_leave_fixtures):
    """Verifies rejection workflow leaves remaining balance intact."""
    sl_id = setup_leave_fixtures["sl_id"]
    today = date.today()
    start = today + timedelta(days=40)
    end = today + timedelta(days=41)  # 2 days

    res_apply = client.post("/api/leaves",
                            headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"},
                            json={"leave_type_id": sl_id, "start_date": start.isoformat(), "end_date": end.isoformat(), "reason": "Medical appointment"})
    leave_id = res_apply.get_json()["data"]["id"]

    # HR rejects request
    res_reject = client.patch(f"/api/leaves/{leave_id}/reject",
                              headers={"Authorization": f"Bearer {auth_tokens_leave['hr']}"},
                              json={"comments": "Please provide medical certificate first."})
    assert res_reject.status_code == 200
    assert res_reject.get_json()["data"]["status"] == "REJECTED"

    # Verify balance unchanged: approved_days=0, remaining_balance=10
    res_bal = client.get("/api/leaves/balance", headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"})
    sl_bal = next(b for b in res_bal.get_json()["data"] if b["leave_type_id"] == sl_id)
    assert sl_bal["approved_days"] == 0.0
    assert sl_bal["remaining_balance"] == 10.0

def test_cancellation_workflow(client, auth_tokens_leave, setup_leave_fixtures):
    """Verifies employee can cancel their own pending or approved request."""
    cl_id = setup_leave_fixtures["cl_id"]
    today = date.today()
    start = today + timedelta(days=50)
    end = today + timedelta(days=51)

    res_apply = client.post("/api/leaves",
                            headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"},
                            json={"leave_type_id": cl_id, "start_date": start.isoformat(), "end_date": end.isoformat(), "reason": "Will cancel"})
    leave_id = res_apply.get_json()["data"]["id"]

    # Cancel
    res_cancel = client.patch(f"/api/leaves/{leave_id}/cancel",
                              headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"})
    assert res_cancel.status_code == 200
    assert res_cancel.get_json()["data"]["status"] == "CANCELLED"

def test_cross_employee_access_authorization(client, auth_tokens_leave, setup_leave_fixtures):
    """Verifies that Employee 2 cannot view Employee 1's leave details."""
    cl_id = setup_leave_fixtures["cl_id"]
    today = date.today()
    start = today + timedelta(days=60)
    end = today + timedelta(days=61)

    res_apply = client.post("/api/leaves",
                            headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"},
                            json={"leave_type_id": cl_id, "start_date": start.isoformat(), "end_date": end.isoformat(), "reason": "Confidential"})
    leave_id = res_apply.get_json()["data"]["id"]

    # Emp2 forbidden
    res_forbidden = client.get(f"/api/leaves/{leave_id}",
                               headers={"Authorization": f"Bearer {auth_tokens_leave['emp2']}"})
    assert res_forbidden.status_code == 403

    # Emp1 allowed
    res_emp1 = client.get(f"/api/leaves/{leave_id}",
                          headers={"Authorization": f"Bearer {auth_tokens_leave['emp1']}"})
    assert res_emp1.status_code == 200

    # HR allowed
    res_hr = client.get(f"/api/leaves/{leave_id}",
                        headers={"Authorization": f"Bearer {auth_tokens_leave['hr']}"})
    assert res_hr.status_code == 200

def test_unauthenticated_requests_rejected(client):
    """Verifies unauthenticated calls to leave endpoints return 401."""
    assert client.post("/api/leaves", json={}).status_code == 401
    assert client.get("/api/leaves/my").status_code == 401
    assert client.get("/api/leaves").status_code == 401
    assert client.get("/api/leaves/balance").status_code == 401
    assert client.get("/api/leaves/types").status_code == 401

