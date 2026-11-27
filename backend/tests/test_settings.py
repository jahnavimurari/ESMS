import pytest
from datetime import date, datetime, timezone
from app.extension_registry import db
from app.models.department import Department
from app.models.leave import LeaveType, LeaveRequest
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.user import User
from app.models.settings import (
    OrganizationSetting,
    Designation,
    Holiday,
    WorkShift,
    EmployeeCategory,
    UserPreference
)
from app.services.settings_service import SettingsService

@pytest.fixture
def setup_settings_fixtures(app, sample_users):
    """Sets up prerequisite departments and leave types for testing settings."""
    with app.app_context():
        dept = Department(name="Information Technology", code="IT", description="IT & Infrastructure")
        lt = LeaveType(name="Annual Leave", code="AL", days_per_year=15, is_paid=True, is_active=True)
        db.session.add_all([dept, lt])
        db.session.commit()
        return {
            "dept_id": dept.id,
            "lt_id": lt.id
        }

@pytest.fixture
def auth_tokens_settings(client, setup_settings_fixtures):
    """Generates JWT tokens for Admin, HR, and Employee."""
    res_admin = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "AdminPass123!"})
    res_hr = client.post("/api/auth/login", json={"email": "hr@test.com", "password": "HRPass123!"})
    res_emp = client.post("/api/auth/login", json={"email": "emp@test.com", "password": "EmpPass123!"})

    return {
        "admin": res_admin.json["data"]["access_token"],
        "hr": res_hr.json["data"]["access_token"],
        "emp": res_emp.json["data"]["access_token"]
    }

def test_get_organization_settings(client, auth_tokens_settings):
    """Test getting organization profile and global settings."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['admin']}"}
    res = client.get("/api/settings/organization", headers=headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "name" in data
    assert "timezone" in data
    assert "working_days" in data

def test_update_organization_settings_as_admin(client, auth_tokens_settings):
    """Test admin updating organization profile settings."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['admin']}"}
    payload = {
        "name": "Acme Global Solutions",
        "timezone": "America/New_York",
        "date_format": "MM/DD/YYYY",
        "daily_working_hours": 7.5,
        "working_days": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    }
    res = client.put("/api/settings/organization", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["name"] == "Acme Global Solutions"
    assert data["timezone"] == "America/New_York"
    assert data["daily_working_hours"] == 7.5

def test_employee_cannot_update_organization_settings(client, auth_tokens_settings):
    """RBAC: Ordinary employee cannot update organization settings."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['emp']}"}
    payload = {"name": "Hacked Organization"}
    res = client.put("/api/settings/organization", json=payload, headers=headers)
    assert res.status_code == 403

def test_designation_crud(client, auth_tokens_settings, setup_settings_fixtures):
    """Test designation lifecycle and department assignment."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['admin']}"}
    dept_id = setup_settings_fixtures["dept_id"]

    # 1. Create designation
    create_payload = {
        "name": "Senior Cloud Architect",
        "code": "SR_CLOUD_ARCH",
        "department_id": dept_id,
        "description": "Leads cloud platform engineering"
    }
    res = client.post("/api/settings/designations", json=create_payload, headers=headers)
    assert res.status_code == 201
    desig = res.get_json()["data"]
    desig_id = desig["id"]
    assert desig["name"] == "Senior Cloud Architect"
    assert desig["code"] == "SR_CLOUD_ARCH"
    assert desig["department_id"] == dept_id

    # 2. List designations
    list_res = client.get("/api/settings/designations", headers=headers)
    assert list_res.status_code == 200
    all_desigs = list_res.get_json()["data"]
    assert any(d["id"] == desig_id for d in all_desigs)

    # 3. Update designation
    update_payload = {"name": "Lead Cloud Architect"}
    up_res = client.put(f"/api/settings/designations/{desig_id}", json=update_payload, headers=headers)
    assert up_res.status_code == 200
    assert up_res.get_json()["data"]["name"] == "Lead Cloud Architect"

    # 4. Delete designation
    del_res = client.delete(f"/api/settings/designations/{desig_id}", headers=headers)
    assert del_res.status_code == 200

def test_employee_cannot_create_or_modify_designations(client, auth_tokens_settings):
    """RBAC: Ordinary employee cannot create or edit designations."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['emp']}"}
    payload = {"name": "Unauthorized Designation", "code": "UNAUTH"}
    res = client.post("/api/settings/designations", json=payload, headers=headers)
    assert res.status_code == 403

def test_holiday_calendar_crud(client, auth_tokens_settings):
    """Test holiday calendar addition, listing, updating and deletion."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['hr']}"}

    # 1. Create holiday
    holiday_payload = {
        "name": "New Year's Day",
        "holiday_date": "2027-01-01",
        "is_optional": False,
        "description": "Public holiday celebrating the New Year"
    }
    res = client.post("/api/settings/holidays", json=holiday_payload, headers=headers)
    assert res.status_code == 201
    h_data = res.get_json()["data"]
    h_id = h_data["id"]
    assert h_data["name"] == "New Year's Day"
    assert h_data["holiday_date"] == "2027-01-01"

    # 2. List holidays with year filter
    list_res = client.get("/api/settings/holidays?year=2027", headers=headers)
    assert list_res.status_code == 200
    holidays = list_res.get_json()["data"]
    assert any(h["id"] == h_id for h in holidays)

    # 3. Update holiday
    up_res = client.put(f"/api/settings/holidays/{h_id}", json={"name": "New Year Day (Observed)"}, headers=headers)
    assert up_res.status_code == 200
    assert up_res.get_json()["data"]["name"] == "New Year Day (Observed)"

    # 4. Delete holiday
    del_res = client.delete(f"/api/settings/holidays/{h_id}", headers=headers)
    assert del_res.status_code == 200

def test_employee_cannot_manage_holidays(client, auth_tokens_settings):
    """RBAC: Ordinary employee cannot create holidays."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['emp']}"}
    payload = {"name": "Employee Day", "holiday_date": "2027-05-01"}
    res = client.post("/api/settings/holidays", json=payload, headers=headers)
    assert res.status_code == 403

def test_work_shifts_and_attendance_rules(client, auth_tokens_settings):
    """Test shift creation, timing rules, and listing."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['admin']}"}
    payload = {
        "name": "Night Shift",
        "code": "NIGHT_01",
        "start_time": "22:00",
        "end_time": "06:00",
        "grace_period_minutes": 10,
        "half_day_hours": 4.0,
        "full_day_hours": 8.0,
        "is_default": False
    }
    res = client.post("/api/settings/shifts", json=payload, headers=headers)
    assert res.status_code == 201
    shift = res.get_json()["data"]
    assert shift["code"] == "NIGHT_01"
    assert shift["start_time"] == "22:00"

    # List shifts
    list_res = client.get("/api/settings/shifts", headers=headers)
    assert list_res.status_code == 200
    shifts = list_res.get_json()["data"]
    assert any(s["code"] == "NIGHT_01" for s in shifts)

def test_employee_categories_management(client, auth_tokens_settings):
    """Test employee categories listing and creation."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['admin']}"}
    payload = {
        "code": "CONSULTANT",
        "name": "External Consultant",
        "description": "Specialized third-party advisory staff"
    }
    res = client.post("/api/settings/categories", json=payload, headers=headers)
    assert res.status_code == 201
    cat = res.get_json()["data"]
    assert cat["code"] == "CONSULTANT"

    list_res = client.get("/api/settings/categories", headers=headers)
    assert list_res.status_code == 200
    cats = list_res.get_json()["data"]
    assert any(c["code"] == "CONSULTANT" for c in cats)

def test_leave_policy_configuration(client, auth_tokens_settings, setup_settings_fixtures):
    """Test leave policy configuration adjustments."""
    headers = {"Authorization": f"Bearer {auth_tokens_settings['admin']}"}
    lt_id = setup_settings_fixtures["lt_id"]

    # List policies
    list_res = client.get("/api/settings/leave-policies", headers=headers)
    assert list_res.status_code == 200
    policies = list_res.get_json()["data"]
    assert any(p["id"] == lt_id for p in policies)

    # Update policy entitlements
    up_res = client.put(f"/api/settings/leave-policies/{lt_id}", json={"days_per_year": 18, "description": "Updated 18 days"}, headers=headers)
    assert up_res.status_code == 200
    assert up_res.get_json()["data"]["days_per_year"] == 18

def test_user_preferences_isolation_and_update(client, auth_tokens_settings):
    """Test user preferences retrieve and update per user."""
    emp_headers = {"Authorization": f"Bearer {auth_tokens_settings['emp']}"}
    admin_headers = {"Authorization": f"Bearer {auth_tokens_settings['admin']}"}

    # Employee fetches their own preferences
    emp_res = client.get("/api/settings/preferences", headers=emp_headers)
    assert emp_res.status_code == 200
    pref = emp_res.get_json()["data"]
    assert pref["theme"] == "LIGHT"

    # Employee updates preferences
    update_payload = {
        "theme": "DARK",
        "date_format": "DD/MM/YYYY",
        "email_notifications": False
    }
    emp_up_res = client.put("/api/settings/preferences", json=update_payload, headers=emp_headers)
    assert emp_up_res.status_code == 200
    updated_pref = emp_up_res.get_json()["data"]
    assert updated_pref["theme"] == "DARK"
    assert updated_pref["date_format"] == "DD/MM/YYYY"
    assert updated_pref["email_notifications"] is False

    # Admin fetches their own preferences (should not be affected by employee's change)
    admin_res = client.get("/api/settings/preferences", headers=admin_headers)
    assert admin_res.status_code == 200
    admin_pref = admin_res.get_json()["data"]
    assert admin_pref["user_id"] != updated_pref["user_id"]

def test_leave_policy_update_preserves_historical_records(app, sample_users):
    """Verifies updating LeaveType entitlements does not modify historical leave requests."""
    with app.app_context():
        dept = Department(name="Ops", code="OPS")
        db.session.add(dept)
        db.session.commit()

        u = User.query.filter_by(email="emp@test.com").first()
        emp = Employee(
            user_id=u.id, employee_code="EMP-HIST-01",
            first_name="Jane", last_name="Doe",
            department_id=dept.id, designation="Analyst",
            status="ACTIVE"
        )
        db.session.add(emp)
        db.session.commit()

        lt = LeaveType(name="Casual Leave", code="CL", days_per_year=12, is_paid=True)
        db.session.add(lt)
        db.session.commit()

        req = LeaveRequest(
            employee_id=emp.id,
            leave_type_id=lt.id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 3),
            total_days=3.0,
            reason="Family event",
            status="APPROVED"
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

        # Update leave policy to 20 days
        SettingsService.update_leave_policy(lt.id, {"days_per_year": 20})

        # Re-fetch leave request
        re_req = db.session.get(LeaveRequest, req_id)
        assert re_req.total_days == 3.0
        assert re_req.status == "APPROVED"
        assert re_req.start_date == date(2026, 3, 1)

def test_shift_modification_preserves_historical_attendance(app, sample_users):
    """Verifies modifying a WorkShift does not alter historical attendance records."""
    with app.app_context():
        dept = Department(name="Support", code="SUP")
        db.session.add(dept)
        db.session.commit()

        u = User.query.filter_by(email="emp@test.com").first()
        emp = Employee(
            user_id=u.id, employee_code="EMP-HIST-02",
            first_name="John", last_name="Doe",
            department_id=dept.id, designation="Support Rep",
            status="ACTIVE"
        )
        db.session.add(emp)
        db.session.commit()

        shift = WorkShift(name="Day Shift", code="DAY", start_time="09:00", end_time="17:00")
        db.session.add(shift)
        db.session.commit()

        # Historical attendance record
        att = Attendance(
            employee_id=emp.id,
            work_date=date(2026, 2, 10),
            shift_number=1,
            check_in=datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc),
            check_out=datetime(2026, 2, 10, 17, 0, tzinfo=timezone.utc),
            total_hours=8.00,
            status="PRESENT"
        )
        db.session.add(att)
        db.session.commit()
        att_id = att.id

        # Update shift configuration
        SettingsService.update_shift(shift.id, {"start_time": "10:00", "end_time": "19:00"})

        # Verify historical attendance record is unchanged
        re_att = db.session.get(Attendance, att_id)
        assert float(re_att.total_hours) == 8.00
        assert re_att.status == "PRESENT"
        assert re_att.check_in.year == 2026 and re_att.check_in.month == 2 and re_att.check_in.day == 10
        assert re_att.check_in.hour == 9 and re_att.check_in.minute == 0
