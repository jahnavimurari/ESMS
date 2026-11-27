import pytest
from datetime import datetime, timezone, timedelta, date
from app.extension_registry import db
from app.models.department import Department
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.user import User

@pytest.fixture
def setup_attendance_fixtures(app, sample_users):
    """Sets up department and employee profiles linked to sample users."""
    with app.app_context():
        dept = Department(name="Engineering", code="ENG", description="Eng team")
        db.session.add(dept)
        db.session.commit()

        # Query user in current session to avoid DetachedInstanceError
        emp_user = User.query.filter_by(email="emp@test.com").first()
        employee = Employee(
            user_id=emp_user.id,
            employee_code="EMP-TEST-01",
            first_name="Test",
            last_name="Employee",
            department_id=dept.id,
            designation="Engineer",
            status="ACTIVE"
        )
        db.session.add(employee)
        db.session.commit()

        return {
            "department_id": dept.id,
            "employee_id": str(employee.id),
            "user_id": str(emp_user.id)
        }

@pytest.fixture
def auth_tokens(client, sample_users):
    """Logs in sample users and returns their respective Bearer access tokens."""
    res_admin = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "AdminPass123!"})
    admin_token = res_admin.get_json()["data"]["access_token"]

    res_hr = client.post("/api/auth/login", json={"email": "hr@test.com", "password": "HRPass123!"})
    hr_token = res_hr.get_json()["data"]["access_token"]

    res_emp = client.post("/api/auth/login", json={"email": "emp@test.com", "password": "EmpPass123!"})
    emp_token = res_emp.get_json()["data"]["access_token"]

    return {
        "admin": admin_token,
        "hr": hr_token,
        "employee": emp_token
    }

def test_check_in_success(client, auth_tokens, setup_attendance_fixtures):
    """Verifies that an authenticated employee can check in and start Shift 1."""
    res = client.post("/api/attendance/check-in",
                      headers={"Authorization": f"Bearer {auth_tokens['employee']}"},
                      json={"notes": "Starting shift on time"})
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["shift_number"] == 1
    assert data["check_in"] is not None
    assert data["check_out"] is None
    assert data["status"] in ["PRESENT", "LATE"]

def test_repeated_check_in_rejection(client, auth_tokens, setup_attendance_fixtures):
    """Verifies that an employee cannot start a second shift while one is already active."""
    # First check-in
    res1 = client.post("/api/attendance/check-in",
                       headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res1.status_code == 201

    # Second check-in must be rejected
    res2 = client.post("/api/attendance/check-in",
                       headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res2.status_code == 400
    assert "already have an active shift" in res2.get_json()["error"]["message"]

def test_check_out_success(app, client, auth_tokens, setup_attendance_fixtures):
    """Verifies that an employee with an active shift can check out successfully."""
    # Check in
    res_in = client.post("/api/attendance/check-in",
                         headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_in.status_code == 201
    s_id = res_in.get_json()["data"]["id"]

    # Provide controlled timestamp (check-in occurred 4 hours ago)
    with app.app_context():
        s = db.session.get(Attendance, s_id)
        s.check_in = datetime.now(timezone.utc) - timedelta(hours=4)
        db.session.commit()

    # Check out
    res = client.post("/api/attendance/check-out",
                      headers={"Authorization": f"Bearer {auth_tokens['employee']}"},
                      json={"notes": "Lunch break"})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["check_out"] is not None
    assert data["total_hours"] >= 4.0

def test_check_out_without_active_session_rejected(client, auth_tokens, setup_attendance_fixtures):
    """Verifies that checking out without an active session is rejected."""
    res = client.post("/api/attendance/check-out",
                      headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res.status_code == 400
    assert "No active attendance session found" in res.get_json()["error"]["message"]

def test_multiple_shifts_in_one_day(app, client, auth_tokens, setup_attendance_fixtures):
    """Verifies multi-shift support using controlled timestamps for shifts."""
    # Shift 1: Check-in
    res_in1 = client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_in1.status_code == 201
    s1_id = res_in1.get_json()["data"]["id"]

    # Emulate Shift 1 check-in 5 hours ago
    with app.app_context():
        s1 = db.session.get(Attendance, s1_id)
        s1.check_in = datetime.now(timezone.utc) - timedelta(hours=5)
        db.session.commit()

    # Shift 1: Check-out
    res_out1 = client.post("/api/attendance/check-out", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_out1.status_code == 200

    # Shift 2: Check-in
    res_in2 = client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_in2.status_code == 201
    assert res_in2.get_json()["data"]["shift_number"] == 2
    s2_id = res_in2.get_json()["data"]["id"]

    # Emulate Shift 2 check-in 1 hour ago
    with app.app_context():
        s2 = db.session.get(Attendance, s2_id)
        s2.check_in = datetime.now(timezone.utc) - timedelta(hours=1)
        db.session.commit()

    # Shift 2: Check-out
    res_out2 = client.post("/api/attendance/check-out", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_out2.status_code == 200

def test_employee_my_attendance_and_rbac(client, auth_tokens, setup_attendance_fixtures):
    """Verifies employee can fetch their own history but cannot view another employee's record directly."""
    # Create an attendance record
    checkin_res = client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    att_id = checkin_res.get_json()["data"]["id"]

    # Employee views their own history
    res_my = client.get("/api/attendance/my", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_my.status_code == 200
    assert res_my.get_json()["data"]["today"]["has_active_session"] is True

    # Employee views their own record by ID
    res_detail = client.get(f"/api/attendance/{att_id}", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_detail.status_code == 200

    # Unauthorized employee cannot list all attendance
    res_unauth_list = client.get("/api/attendance", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_unauth_list.status_code == 403

def test_hr_and_admin_attendance_listing_and_summary(client, auth_tokens, setup_attendance_fixtures):
    """Verifies HR and Admin can list attendance and view summaries."""
    # Check in
    client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})

    # HR lists attendance
    res_list = client.get("/api/attendance", headers={"Authorization": f"Bearer {auth_tokens['hr']}"})
    assert res_list.status_code == 200
    assert res_list.get_json()["data"]["total"] >= 1

    # Admin checks summary
    res_summary = client.get("/api/attendance/summary", headers={"Authorization": f"Bearer {auth_tokens['admin']}"})
    assert res_summary.status_code == 200
    summary = res_summary.get_json()["data"]
    assert "present_count" in summary
    assert "active_shifts_now" in summary
    assert summary["active_shifts_now"] >= 1

def test_attendance_correction_by_admin(client, auth_tokens, setup_attendance_fixtures):
    """Verifies authorized attendance correction by HR/Admin with audit tracking."""
    checkin = client.post("/api/attendance/check-in", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    att_id = checkin.get_json()["data"]["id"]
    client.post("/api/attendance/check-out", headers={"Authorization": f"Bearer {auth_tokens['employee']}"})

    # Employee cannot correct attendance
    res_emp_corr = client.put(f"/api/attendance/{att_id}",
                              headers={"Authorization": f"Bearer {auth_tokens['employee']}"},
                              json={"total_hours": 8.5})
    assert res_emp_corr.status_code == 403

    # Admin corrects attendance
    res_admin_corr = client.put(f"/api/attendance/{att_id}",
                                headers={"Authorization": f"Bearer {auth_tokens['admin']}"},
                                json={"status": "PRESENT", "total_hours": 8.0, "notes": "Approved overtime"})
    assert res_admin_corr.status_code == 200
    data = res_admin_corr.get_json()["data"]
    assert data["is_corrected"] is True
    assert data["total_hours"] == 8.0
    assert data["corrected_by"] is not None

def test_unauthenticated_attendance_requests_rejected(client):
    """Verifies all attendance endpoints reject unauthenticated calls."""
    assert client.post("/api/attendance/check-in").status_code == 401
    assert client.post("/api/attendance/check-out").status_code == 401
    assert client.get("/api/attendance/my").status_code == 401
    assert client.get("/api/attendance").status_code == 401
    assert client.get("/api/attendance/summary").status_code == 401
