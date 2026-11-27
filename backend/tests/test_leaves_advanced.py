import pytest
import concurrent.futures
from datetime import datetime, timezone, timedelta, date
from app.extension_registry import db
from app.models.department import Department
from app.models.employee import Employee
from app.models.leave import LeaveRequest, LeaveType
from app.models.user import User

@pytest.fixture
def setup_adv_leave_fixtures(app, sample_users):
    """Sets up department, leave types, and employees."""
    with app.app_context():
        cl = LeaveType(code="CL", name="Casual Leave", days_per_year=12, is_paid=True, is_active=True)
        sl = LeaveType(code="SL", name="Sick Leave", days_per_year=10, is_paid=True, is_active=True)
        ul = LeaveType(code="UL", name="Unpaid Leave", days_per_year=0, is_paid=False, is_active=True)
        dept = Department(name="Logistics", code="LOG", description="Logistics ops")
        db.session.add_all([cl, sl, ul, dept])
        db.session.commit()

        emp_user_1 = User.query.filter_by(email="emp@test.com").first()
        emp1 = Employee(
            user_id=emp_user_1.id,
            employee_code="EMP-ADV-LV1",
            first_name="Elena",
            last_name="Rostova",
            department_id=dept.id,
            designation="Logistics Manager",
            status="ACTIVE"
        )

        emp_user_2 = User(email="emp2@test.com", role="EMPLOYEE", is_active=True)
        emp_user_2.set_password("Emp2Pass123!")
        db.session.add(emp_user_2)
        db.session.flush()

        emp2 = Employee(
            user_id=emp_user_2.id,
            employee_code="EMP-ADV-LV2",
            first_name="Marcus",
            last_name="Vance",
            department_id=dept.id,
            designation="Dispatcher",
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
def auth_tokens_adv_leave(client, setup_adv_leave_fixtures):
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

def test_concurrent_same_employee_overlapping_leave(app, auth_tokens_adv_leave, setup_adv_leave_fixtures):
    """
    Submits two simultaneous overlapping leave requests for the same employee across threads.
    Verifies that only one request succeeds and the other is safely rejected.
    """
    cl_id = setup_adv_leave_fixtures["cl_id"]
    emp1_token = auth_tokens_adv_leave["emp1"]
    start = date(2027, 6, 1)
    end = date(2027, 6, 5)

    def submit_app():
        thread_client = app.test_client()
        return thread_client.post(
            "/api/leaves",
            headers={"Authorization": f"Bearer {emp1_token}"},
            json={
                "leave_type_id": cl_id,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "reason": "Concurrent summer vacation"
            }
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(submit_app) for _ in range(2)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    status_codes = [r.status_code for r in results]
    # Exactly one 201 Created and one 400 Bad Request
    assert status_codes.count(201) == 1
    assert status_codes.count(400) == 1

    # Database must contain exactly one request for this employee during this range
    import uuid
    emp_uuid = uuid.UUID(setup_adv_leave_fixtures["emp1_id"])
    with app.app_context():
        count = LeaveRequest.query.filter(
            LeaveRequest.employee_id == emp_uuid,
            LeaveRequest.start_date == start,
            LeaveRequest.end_date == end
        ).count()
        assert count == 1

def test_concurrent_approval_race_condition(app, client, auth_tokens_adv_leave, setup_adv_leave_fixtures):
    """
    Two administrators attempt to approve the same pending request simultaneously.
    Verifies that only one approval succeeds (200), the other is rejected (400),
    and balance is deducted exactly once.
    """
    cl_id = setup_adv_leave_fixtures["cl_id"]
    emp1_token = auth_tokens_adv_leave["emp1"]
    admin_token = auth_tokens_adv_leave["admin"]
    hr_token = auth_tokens_adv_leave["hr"]

    # Submit request for 3 days
    start = date(2027, 7, 10)
    end = date(2027, 7, 12)
    res_apply = client.post(
        "/api/leaves",
        headers={"Authorization": f"Bearer {emp1_token}"},
        json={
            "leave_type_id": cl_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "reason": "Conference attendance"
        }
    )
    assert res_apply.status_code == 201
    leave_id = res_apply.get_json()["data"]["id"]

    def perform_approval(token, comments):
        thread_client = app.test_client()
        return thread_client.patch(
            f"/api/leaves/{leave_id}/approve",
            headers={"Authorization": f"Bearer {token}"},
            json={"comments": comments}
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(perform_approval, admin_token, "Admin review")
        f2 = executor.submit(perform_approval, hr_token, "HR review")
        results = [f1.result(), f2.result()]

    status_codes = [r.status_code for r in results]
    assert status_codes.count(200) == 1
    assert status_codes.count(400) == 1

    # Check that balance was deducted only once (12 - 3 = 9 remaining)
    res_bal = client.get("/api/leaves/balance?year=2027", headers={"Authorization": f"Bearer {emp1_token}"})
    cl_bal = next(b for b in res_bal.get_json()["data"] if b["leave_type_id"] == cl_id)
    assert cl_bal["approved_days"] == 3.0
    assert cl_bal["remaining_balance"] == 9.0

def test_cancel_approved_request_restores_balance_exactly_once(client, auth_tokens_adv_leave, setup_adv_leave_fixtures):
    """Verifies that cancelling an approved request restores balance, and repeat cancel is rejected."""
    cl_id = setup_adv_leave_fixtures["cl_id"]
    emp1_token = auth_tokens_adv_leave["emp1"]
    hr_token = auth_tokens_adv_leave["hr"]

    start = date(2027, 8, 1)
    end = date(2027, 8, 5)  # 5 days
    res_apply = client.post(
        "/api/leaves",
        headers={"Authorization": f"Bearer {emp1_token}"},
        json={"leave_type_id": cl_id, "start_date": start.isoformat(), "end_date": end.isoformat(), "reason": "Travel"}
    )
    leave_id = res_apply.get_json()["data"]["id"]

    # HR approves
    client.patch(f"/api/leaves/{leave_id}/approve", headers={"Authorization": f"Bearer {hr_token}"})

    # Balance shows 5 approved days
    bal1 = client.get("/api/leaves/balance?year=2027", headers={"Authorization": f"Bearer {emp1_token}"}).get_json()["data"]
    assert next(b for b in bal1 if b["leave_type_id"] == cl_id)["approved_days"] == 5.0

    # Employee cancels
    res_cancel = client.patch(f"/api/leaves/{leave_id}/cancel", headers={"Authorization": f"Bearer {emp1_token}"})
    assert res_cancel.status_code == 200

    # Balance is fully restored: approved_days = 0, remaining_balance = 12
    bal2 = client.get("/api/leaves/balance?year=2027", headers={"Authorization": f"Bearer {emp1_token}"}).get_json()["data"]
    cl_bal2 = next(b for b in bal2 if b["leave_type_id"] == cl_id)
    assert cl_bal2["approved_days"] == 0.0
    assert cl_bal2["remaining_balance"] == 12.0

    # Second cancel must be rejected
    res_cancel_again = client.patch(f"/api/leaves/{leave_id}/cancel", headers={"Authorization": f"Bearer {emp1_token}"})
    assert res_cancel_again.status_code == 400

def test_interval_matrix_and_leap_year(client, auth_tokens_adv_leave, setup_adv_leave_fixtures):
    """
    Tests full interval boundary matrix:
    - Same-day leave
    - Adjacent non-overlapping leave
    - Partial overlap
    - Fully contained overlap
    - Leap year date (Feb 29, 2028)
    """
    cl_id = setup_adv_leave_fixtures["cl_id"]
    emp1_token = auth_tokens_adv_leave["emp1"]

    # 1. Same-day leave (May 1, 2027 to May 1, 2027 -> 1 day)
    res_same = client.post("/api/leaves", headers={"Authorization": f"Bearer {emp1_token}"},
                           json={"leave_type_id": cl_id, "start_date": "2027-05-01", "end_date": "2027-05-01", "reason": "Single day off"})
    assert res_same.status_code == 201
    assert res_same.get_json()["data"]["total_days"] == 1.0

    # 2. Adjacent non-overlapping leave (May 2, 2027 to May 3, 2027 -> allowed)
    res_adj = client.post("/api/leaves", headers={"Authorization": f"Bearer {emp1_token}"},
                          json={"leave_type_id": cl_id, "start_date": "2027-05-02", "end_date": "2027-05-03", "reason": "Adjacent day off"})
    assert res_adj.status_code == 201

    # 3. Partial overlap (May 3, 2027 to May 5, 2027 -> overlaps with May 3 -> rejected)
    res_part = client.post("/api/leaves", headers={"Authorization": f"Bearer {emp1_token}"},
                           json={"leave_type_id": cl_id, "start_date": "2027-05-03", "end_date": "2027-05-05", "reason": "Partial overlap"})
    assert res_part.status_code == 400

    # 4. Fully contained overlap (May 2, 2027 to May 2, 2027 -> contained inside May 2-3 -> rejected)
    res_cont = client.post("/api/leaves", headers={"Authorization": f"Bearer {emp1_token}"},
                           json={"leave_type_id": cl_id, "start_date": "2027-05-02", "end_date": "2027-05-02", "reason": "Contained overlap"})
    assert res_cont.status_code == 400

    # 5. Leap year date (Feb 28, 2028 to Feb 29, 2028 -> 2 days)
    res_leap = client.post("/api/leaves", headers={"Authorization": f"Bearer {emp1_token}"},
                           json={"leave_type_id": cl_id, "start_date": "2028-02-28", "end_date": "2028-02-29", "reason": "Leap year day"})
    assert res_leap.status_code == 201
    assert res_leap.get_json()["data"]["total_days"] == 2.0

def test_unpaid_leave_does_not_affect_paid_balance(client, auth_tokens_adv_leave, setup_adv_leave_fixtures):
    """Verifies that taking unpaid leave does not reduce Casual Leave or Sick Leave balances."""
    ul_id = setup_adv_leave_fixtures["ul_id"]
    cl_id = setup_adv_leave_fixtures["cl_id"]
    emp1_token = auth_tokens_adv_leave["emp1"]
    hr_token = auth_tokens_adv_leave["hr"]

    # Apply 10 days of unpaid leave
    res_apply = client.post(
        "/api/leaves",
        headers={"Authorization": f"Bearer {emp1_token}"},
        json={"leave_type_id": ul_id, "start_date": "2027-09-01", "end_date": "2027-09-10", "reason": "Unpaid sabbatical"}
    )
    assert res_apply.status_code == 201
    leave_id = res_apply.get_json()["data"]["id"]

    # HR approves unpaid leave
    client.patch(f"/api/leaves/{leave_id}/approve", headers={"Authorization": f"Bearer {hr_token}"})

    # Verify Casual Leave balance remains 12 days
    balances = client.get("/api/leaves/balance?year=2027", headers={"Authorization": f"Bearer {emp1_token}"}).get_json()["data"]
    cl_bal = next(b for b in balances if b["leave_type_id"] == cl_id)
    assert cl_bal["remaining_balance"] == 12.0
    ul_bal = next(b for b in balances if b["leave_type_id"] == ul_id)
    assert ul_bal["approved_days"] == 10.0
    assert ul_bal["is_paid"] is False

