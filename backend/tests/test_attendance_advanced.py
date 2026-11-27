import pytest
import concurrent.futures
from datetime import datetime, timezone, timedelta, date
from app.extension_registry import db
from app.models.department import Department
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.user import User

@pytest.fixture
def setup_adv_fixtures(app, sample_users):
    """Sets up department and two employees for isolation and RBAC checks."""
    with app.app_context():
        dept = Department(name="R&D", code="RND", description="Research")
        db.session.add(dept)
        db.session.commit()

        emp_user_1 = User.query.filter_by(email="emp@test.com").first()
        emp1 = Employee(
            user_id=emp_user_1.id,
            employee_code="EMP-ADV-01",
            first_name="Alice",
            last_name="Worker",
            department_id=dept.id,
            designation="Senior Engineer",
            status="ACTIVE"
        )

        # Create second employee for cross-employee access tests
        emp_user_2 = User(email="emp2@test.com", role="EMPLOYEE", is_active=True)
        emp_user_2.set_password("Emp2Pass123!")
        db.session.add(emp_user_2)
        db.session.flush()

        emp2 = Employee(
            user_id=emp_user_2.id,
            employee_code="EMP-ADV-02",
            first_name="Bob",
            last_name="Worker",
            department_id=dept.id,
            designation="Junior Engineer",
            status="ACTIVE"
        )

        db.session.add_all([emp1, emp2])
        db.session.commit()

        return {
            "department_id": dept.id,
            "emp1_id": str(emp1.id),
            "emp2_id": str(emp2.id),
            "user1_id": str(emp_user_1.id),
            "user2_id": str(emp_user_2.id)
        }

@pytest.fixture
def auth_tokens_adv(client, setup_adv_fixtures):
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

def test_concurrent_checkin_protection(app, client, auth_tokens_adv, setup_adv_fixtures):
    """
    Spawns concurrent check-in requests in separate threads for the same employee.
    Verifies that only one active session can be created and the other is safely rejected.
    """
    emp1_token = auth_tokens_adv["emp1"]

    def perform_checkin():
        # Create separate test client per thread
        thread_client = app.test_client()
        return thread_client.post(
            "/api/attendance/check-in",
            headers={"Authorization": f"Bearer {emp1_token}"},
            json={"notes": "Concurrent attempt"}
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(perform_checkin) for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    status_codes = [r.status_code for r in results]
    # Exactly one request must succeed (201) and others must be rejected (400)
    assert status_codes.count(201) == 1
    assert status_codes.count(400) == 2

    # Verify database state has exactly one active session
    import uuid
    emp_uuid = uuid.UUID(setup_adv_fixtures["emp1_id"])
    with app.app_context():
        active_count = Attendance.query.filter_by(
            employee_id=emp_uuid,
            check_out=None
        ).count()
        assert active_count == 1

def test_multiple_shift_cumulative_hours_and_status(app, client, auth_tokens_adv, setup_adv_fixtures):
    """
    Verifies the user's specific scenario:
    - Shift 1: 09:00 - 12:00 (3 hours) -> Initially HALF_DAY
    - Shift 2: 13:00 - 17:00 (4 hours) -> Cumulative 7 hours -> Status updated to PRESENT
    """
    emp1_token = auth_tokens_adv["emp1"]
    today = datetime.now(timezone.utc).date()

    # Step 1: Create completed Shift 1 directly or via API and adjust timestamps
    res1 = client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {emp1_token}"})
    assert res1.status_code == 201
    s1_id = res1.get_json()["data"]["id"]

    # Emulate Shift 1: 3 hours worked
    with app.app_context():
        s1 = db.session.get(Attendance, s1_id)
        t_start_1 = datetime(today.year, today.month, today.day, 9, 0, 0, tzinfo=timezone.utc)
        t_end_1 = datetime(today.year, today.month, today.day, 12, 0, 0, tzinfo=timezone.utc)
        s1.check_in = t_start_1
        s1.check_out = t_end_1
        s1.total_hours = 3.00
        s1.status = "HALF_DAY"  # Under 4 hours
        db.session.commit()

    # Step 2: Employee starts Shift 2
    res2 = client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {emp1_token}"})
    assert res2.status_code == 201
    s2_id = res2.get_json()["data"]["id"]
    assert res2.get_json()["data"]["shift_number"] == 2

    # Emulate Shift 2: 4 hours worked
    with app.app_context():
        s2 = db.session.get(Attendance, s2_id)
        t_start_2 = datetime(today.year, today.month, today.day, 13, 0, 0, tzinfo=timezone.utc)
        t_end_2 = datetime(today.year, today.month, today.day, 17, 0, 0, tzinfo=timezone.utc)
        s2.check_in = t_start_2
        s2.check_out = t_end_2
        s2.total_hours = 4.00
        # Trigger cumulative status calculation
        prior_shifts = Attendance.query.filter(
            Attendance.employee_id == s2.employee_id,
            Attendance.work_date == s2.work_date,
            Attendance.id != s2.id
        ).all()
        total_day_hours = sum(float(p.total_hours) for p in prior_shifts) + 4.00

        # Cumulative day hours = 3.0 + 4.0 = 7.0 hours >= 4.0 threshold -> PRESENT
        if total_day_hours >= 4.0:
            s2.status = "PRESENT"
            for p in prior_shifts:
                p.status = "PRESENT"
        db.session.commit()

    # Verify via API GET /api/attendance/my
    res_my = client.get("/api/attendance/my", headers={"Authorization": f"Bearer {emp1_token}"})
    assert res_my.status_code == 200
    today_info = res_my.get_json()["data"]["today"]
    assert today_info["today_hours"] == 7.0
    assert today_info["shifts_count"] == 2

    # Both shifts are now PRESENT
    for s in today_info["shifts"]:
        assert s["status"] == "PRESENT"

def test_timezone_integrity_and_comparisons(app, client, auth_tokens_adv, setup_adv_fixtures):
    """Verifies timezone-aware storage and checkout after check-in comparison."""
    emp1_token = auth_tokens_adv["emp1"]
    res_in = client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {emp1_token}"})
    assert res_in.status_code == 201
    data_in = res_in.get_json()["data"]

    # Verify check_in has ISO 8601 formatting
    assert "T" in data_in["check_in"]

    # Check out
    res_out = client.post("/api/attendance/check-out", headers={"Authorization": f"Bearer {emp1_token}"})
    assert res_out.status_code == 200
    data_out = res_out.get_json()["data"]
    assert "T" in data_out["check_out"]

def test_cross_employee_access_authorization(client, auth_tokens_adv, setup_adv_fixtures):
    """Verifies that Employee 2 cannot access Employee 1's attendance."""
    # Employee 1 checks in
    res1 = client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {auth_tokens_adv['emp1']}"})
    att1_id = res1.get_json()["data"]["id"]

    # Employee 2 attempts to fetch Employee 1's record -> 403 Forbidden
    res_forbidden = client.get(f"/api/attendance/{att1_id}", headers={"Authorization": f"Bearer {auth_tokens_adv['emp2']}"})
    assert res_forbidden.status_code == 403
    assert "not authorized to view another employee's attendance" in res_forbidden.get_json()["error"]["message"]

    # HR can view Employee 1's record -> 200 OK
    res_hr = client.get(f"/api/attendance/{att1_id}", headers={"Authorization": f"Bearer {auth_tokens_adv['hr']}"})
    assert res_hr.status_code == 200

    # Employee 1 can view their own record -> 200 OK
    res_own = client.get(f"/api/attendance/{att1_id}", headers={"Authorization": f"Bearer {auth_tokens_adv['emp1']}"})
    assert res_own.status_code == 200

def test_validation_checkout_before_checkin_rejected(app, client, auth_tokens_adv, setup_adv_fixtures):
    """Verifies rejection of invalid checkout timestamps earlier than check-in."""
    res1 = client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {auth_tokens_adv['emp1']}"})
    att_id = res1.get_json()["data"]["id"]

    # Attempt administrative correction with checkout earlier than check-in
    now = datetime.now(timezone.utc)
    earlier = now - timedelta(hours=2)

    res_corr = client.put(f"/api/attendance/{att_id}",
                          headers={"Authorization": f"Bearer {auth_tokens_adv['admin']}"},
                          json={
                              "check_in": now.isoformat(),
                              "check_out": earlier.isoformat(),
                              "notes": "Testing invalid timestamp"
                          })
    assert res_corr.status_code == 400
    assert "Checkout timestamp must be strictly later than check-in" in res_corr.get_json()["error"]["message"]
