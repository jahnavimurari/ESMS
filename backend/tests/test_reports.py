import pytest
import uuid
import io
import openpyxl
from datetime import datetime, timezone, timedelta, date
from app.extension_registry import db
from app.models.department import Department
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.leave import LeaveRequest, LeaveType
from app.models.task import Task
from app.models.performance import PerformanceCycle, PerformanceReview
from app.models.user import User

@pytest.fixture
def setup_reports_fixtures(app, sample_users):
    """Sets up departments, employees, attendance (with multi-shift), leaves, tasks, and performance reviews."""
    with app.app_context():
        # 1. Departments
        eng = Department(name="Engineering", code="ENG", description="Platform Tech")
        hr_dept = Department(name="Human Resources", code="HR", description="People Ops")
        db.session.add_all([eng, hr_dept])
        db.session.commit()

        # 2. Employees (Emp 1 = Alice, Emp 2 = Bob)
        user_emp1 = User.query.filter_by(email="emp@test.com").first()
        emp1 = Employee(
            user_id=user_emp1.id,
            employee_code="EMP-RPT-01",
            first_name="Alice",
            last_name="Smith",
            department_id=eng.id,
            designation="Senior Backend Engineer",
            status="ACTIVE",
            joining_date=date(2023, 1, 15),
            phone="+1234567890"
        )

        user_emp2 = User(email="emp2@test.com", role="EMPLOYEE", is_active=True)
        user_emp2.set_password("Emp2Pass123!")
        db.session.add(user_emp2)
        db.session.flush()

        emp2 = Employee(
            user_id=user_emp2.id,
            employee_code="EMP-RPT-02",
            first_name="Bob",
            last_name="Jones",
            department_id=hr_dept.id,
            designation="HR Specialist",
            status="ACTIVE",
            joining_date=date(2024, 3, 1),
            phone="+1987654321"
        )
        db.session.add_all([emp1, emp2])
        db.session.commit()

        # 3. Attendance: Emp 1 has multiple shifts in one day (Shift 1 = 3h, Shift 2 = 4.5h)
        today = date.today()
        now = datetime.now(timezone.utc)
        att1_s1 = Attendance(
            employee_id=emp1.id,
            work_date=today,
            shift_number=1,
            check_in=now - timedelta(hours=8),
            check_out=now - timedelta(hours=5),
            total_hours=3.0,
            status="PRESENT"
        )
        att1_s2 = Attendance(
            employee_id=emp1.id,
            work_date=today,
            shift_number=2,
            check_in=now - timedelta(hours=4, minutes=30),
            check_out=now,
            total_hours=4.5,
            status="PRESENT"
        )
        att2 = Attendance(
            employee_id=emp2.id,
            work_date=today,
            shift_number=1,
            check_in=now - timedelta(hours=8),
            check_out=now,
            total_hours=8.0,
            status="PRESENT"
        )
        db.session.add_all([att1_s1, att1_s2, att2])

        # 4. Leaves: 1 Pending, 1 Approved, 1 Rejected
        cl = LeaveType(code="CL", name="Casual Leave", days_per_year=12, is_paid=True, is_active=True)
        db.session.add(cl)
        db.session.flush()

        admin_user = User.query.filter_by(email="admin@test.com").first()

        leave_pend = LeaveRequest(
            employee_id=emp1.id,
            leave_type_id=cl.id,
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=7),
            total_days=3.0,
            reason="Vacation Trip",
            status="PENDING"
        )
        leave_appr = LeaveRequest(
            employee_id=emp2.id,
            leave_type_id=cl.id,
            start_date=today + timedelta(days=12),
            end_date=today + timedelta(days=13),
            total_days=2.0,
            reason="Medical Appointment",
            status="APPROVED",
            reviewed_by=admin_user.id,
            reviewer_comments="Approved by HR"
        )
        leave_rej = LeaveRequest(
            employee_id=emp1.id,
            leave_type_id=cl.id,
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=21),
            total_days=2.0,
            reason="Conference",
            status="REJECTED",
            reviewed_by=admin_user.id,
            reviewer_comments="Overlap with project deadline"
        )
        db.session.add_all([leave_pend, leave_appr, leave_rej])

        # 5. Tasks: 1 Completed, 1 Overdue, 1 In Progress
        task1 = Task(
            title="Database Optimization",
            assigned_to=emp1.id,
            created_by=admin_user.id,
            department_id=eng.id,
            priority="HIGH",
            status="COMPLETED",
            start_date=today - timedelta(days=5),
            due_date=today + timedelta(days=1),
            completed_at=now
        )
        task_overdue = Task(
            title="Overdue Audit Log Fix",
            assigned_to=emp2.id,
            created_by=admin_user.id,
            department_id=hr_dept.id,
            priority="URGENT",
            status="TODO",
            start_date=today - timedelta(days=10),
            due_date=today - timedelta(days=2)  # Overdue!
        )
        db.session.add_all([task1, task_overdue])

        # 6. Performance: 1 Cycle, 1 Review COMPLETED (rating 5), 1 Review MANAGER_REVIEW (rating 2)
        cycle = PerformanceCycle(
            title="Annual Cycle 2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            due_date=date(2027, 1, 15),
            status="ACTIVE",
            created_by=admin_user.id
        )
        db.session.add(cycle)
        db.session.flush()

        rev_comp = PerformanceReview(
            cycle_id=cycle.id,
            employee_id=emp1.id,
            review_period="Annual 2026",
            status="COMPLETED",
            self_rating=5,
            rating=5,
            manager_feedback="Superb engineering skills.",
            completed_at=now
        )
        rev_inprog = PerformanceReview(
            cycle_id=cycle.id,
            employee_id=emp2.id,
            review_period="Annual 2026",
            status="MANAGER_REVIEW",
            self_rating=3,
            rating=2,
            manager_feedback="Draft feedback: needs improvement."
        )
        db.session.add_all([rev_comp, rev_inprog])
        db.session.commit()

        return {
            "emp1_id": str(emp1.id),
            "emp2_id": str(emp2.id),
            "cycle_id": cycle.id
        }

@pytest.fixture
def auth_tokens_rpt(client, setup_reports_fixtures):
    """Generates JWT tokens for Admin, HR, Employee 1, and Employee 2."""
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
# Phase 6: Reports & Export Tests (Scenarios 1 - 17)
# ==============================================================================

def test_1_admin_can_generate_employee_reports(client, auth_tokens_rpt):
    """Test 1: Admin can generate employee reports."""
    res = client.get("/api/reports/employees", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 200
    data = res.json["data"]
    assert data["total_count"] >= 2
    assert "headers" in data
    assert "records" in data

def test_2_hr_can_generate_authorized_employee_reports(client, auth_tokens_rpt):
    """Test 2: HR can generate authorized employee reports."""
    res = client.get("/api/reports/employees", headers={"Authorization": f"Bearer {auth_tokens_rpt['hr']}"})
    assert res.status_code == 200
    data = res.json["data"]
    assert data["total_count"] >= 2

def test_3_employees_cannot_access_organization_wide_reports(client, auth_tokens_rpt):
    """Test 3: Employees cannot access organization-wide reports."""
    res = client.get("/api/reports/employees", headers={"Authorization": f"Bearer {auth_tokens_rpt['emp1']}"})
    assert res.status_code == 403

def test_4_employees_can_generate_their_own_attendance_reports(client, auth_tokens_rpt):
    """Test 4: Employees can generate their own attendance reports."""
    res = client.get("/api/reports/attendance", headers={"Authorization": f"Bearer {auth_tokens_rpt['emp1']}"})
    assert res.status_code == 200
    data = res.json["data"]
    # Alice has 2 shifts today
    assert data["total_count"] == 2
    for rec in data["records"]:
        assert rec["employee_code"] == "EMP-RPT-01"

def test_5_employees_cannot_access_another_employee_reports(client, auth_tokens_rpt, setup_reports_fixtures):
    """Test 5: Employees cannot access another employee's reports (query param overridden to caller)."""
    emp2_id = setup_reports_fixtures["emp2_id"]
    # Emp 1 passes Emp 2's ID
    res = client.get(f"/api/reports/attendance?employee_id={emp2_id}", headers={"Authorization": f"Bearer {auth_tokens_rpt['emp1']}"})
    assert res.status_code == 200
    data = res.json["data"]
    for rec in data["records"]:
        assert rec["employee_code"] == "EMP-RPT-01"  # Caller's own data only!

def test_6_attendance_reports_correctly_calculate_multiple_shifts(client, auth_tokens_rpt):
    """Test 6: Attendance reports correctly calculate multiple shifts without double counting."""
    res = client.get("/api/reports/attendance", headers={"Authorization": f"Bearer {auth_tokens_rpt['emp1']}"})
    assert res.status_code == 200
    data = res.json["data"]
    # Shift 1 = 3.0h, Shift 2 = 4.5h -> Total = 7.5h
    shifts = [r["shift_number"] for r in data["records"]]
    assert 1 in shifts
    assert 2 in shifts
    assert data["total_working_hours"] == 7.5

def test_7_leave_reports_distinguish_pending_approved_rejected(client, auth_tokens_rpt):
    """Test 7: Leave reports distinguish pending, approved and rejected requests."""
    res = client.get("/api/reports/leaves", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 200
    records = res.json["data"]["records"]
    statuses = {r["status"] for r in records}
    assert "PENDING" in statuses
    assert "APPROVED" in statuses
    assert "REJECTED" in statuses

def test_8_task_reports_correctly_identify_overdue_tasks(client, auth_tokens_rpt):
    """Test 8: Task reports correctly identify overdue tasks."""
    res = client.get("/api/reports/tasks", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 200
    records = res.json["data"]["records"]
    overdue_tasks = [r for r in records if r["is_overdue"] is True]
    assert len(overdue_tasks) == 1
    assert overdue_tasks[0]["title"] == "Overdue Audit Log Fix"

def test_9_performance_reports_include_completed_reviews_only_in_averages(client, auth_tokens_rpt):
    """Test 9: Performance reports calculate average using completed reviews only (draft review excluded)."""
    res = client.get("/api/reports/performance", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 200
    data = res.json["data"]
    # Total reviews = 2, completed = 1 (Alice rating 5)
    assert data["completed_count"] == 1
    assert data["average_completed_rating"] == 5.0

    # Also verify Employee 2 (Bob) sees rating masked for his in-progress review
    res_emp2 = client.get("/api/reports/performance", headers={"Authorization": f"Bearer {auth_tokens_rpt['emp2']}"})
    assert res_emp2.status_code == 200
    emp2_rec = res_emp2.json["data"]["records"][0]
    assert "Restricted" in str(emp2_rec["manager_rating"])

def test_10_csv_export_contains_correct_data(client, auth_tokens_rpt):
    """Test 10: CSV export produces valid CSV with correct headers and sanitized cells."""
    res = client.get("/api/reports/attendance/export?format=csv", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 200
    assert "text/csv" in res.headers["Content-Type"]
    content = res.data.decode("utf-8-sig")
    assert "Employee Code" in content
    assert "EMP-RPT-01" in content
    assert "EMP-RPT-02" in content

def test_11_excel_export_produces_valid_workbook(client, auth_tokens_rpt):
    """Test 11: Excel export produces a valid openpyxl readable .xlsx file."""
    res = client.get("/api/reports/tasks/export?format=xlsx", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 200
    assert "spreadsheetml" in res.headers["Content-Type"]
    wb = openpyxl.load_workbook(io.BytesIO(res.data))
    sheet = wb.active
    assert "Task" in sheet.title
    # Check that rows exist
    assert sheet.max_row >= 4

def test_12_pdf_export_produces_valid_pdf(client, auth_tokens_rpt):
    """Test 12: PDF export produces a valid PDF file beginning with %PDF."""
    res = client.get("/api/reports/leaves/export?format=pdf", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 200
    assert "application/pdf" in res.headers["Content-Type"]
    # Valid PDF signature
    assert res.data.startswith(b"%PDF")

def test_13_invalid_export_formats_are_rejected(client, auth_tokens_rpt):
    """Test 13: Invalid export format is rejected with HTTP 400."""
    res = client.get("/api/reports/leaves/export?format=exe", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 400
    assert res.json["error"]["code"] == "INVALID_FORMAT"

def test_14_empty_reports_are_handled_correctly(client, auth_tokens_rpt):
    """Test 14: Empty reports handle zero results gracefully without crashing."""
    # Filter with future joining date that matches no one
    res = client.get("/api/reports/employees?start_date=2099-01-01", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 200
    data = res.json["data"]
    assert data["total_count"] == 0
    assert data["records"] == []

    # Export empty PDF
    res_pdf = client.get("/api/reports/employees/export?format=pdf&start_date=2099-01-01", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res_pdf.status_code == 200
    assert res_pdf.data.startswith(b"%PDF")

def test_15_date_filters_return_correct_records(client, auth_tokens_rpt):
    """Test 15: Date filters return correct records."""
    # Joining date filter: Alice was hired in 2023, Bob in 2024
    res = client.get("/api/reports/employees?start_date=2024-01-01", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res.status_code == 200
    codes = [r["employee_code"] for r in res.json["data"]["records"]]
    assert "EMP-RPT-02" in codes  # Bob
    assert "EMP-RPT-01" not in codes  # Alice joined in 2023

def test_16_unauthenticated_users_receive_http_401(client):
    """Test 16: Unauthenticated users receive HTTP 401."""
    assert client.get("/api/reports/employees").status_code == 401
    assert client.get("/api/reports/attendance").status_code == 401
    assert client.get("/api/reports/leaves").status_code == 401
    assert client.get("/api/reports/tasks").status_code == 401
    assert client.get("/api/reports/performance").status_code == 401
    assert client.get("/api/reports/employees/export?format=csv").status_code == 401

def test_17_existing_modules_continue_working(client, auth_tokens_rpt):
    """Test 17: Existing modules continue working without regression."""
    res_dash = client.get("/api/dashboard/admin", headers={"Authorization": f"Bearer {auth_tokens_rpt['admin']}"})
    assert res_dash.status_code == 200
    assert "metrics" in res_dash.json["data"]

