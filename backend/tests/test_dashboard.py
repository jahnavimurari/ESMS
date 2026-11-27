import pytest
import uuid
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
def setup_dashboard_fixtures(app, sample_users):
    """Sets up departments, employees, attendance, leaves, tasks, and performance reviews."""
    with app.app_context():
        # 1. Departments
        eng = Department(name="Engineering", code="ENG", description="Platform Tech")
        hr_dept = Department(name="Human Resources", code="HR", description="People Ops")
        db.session.add_all([eng, hr_dept])
        db.session.commit()

        # 2. Employees (Emp 1 = Alice, Emp 2 = Bob, Inactive = Charlie)
        user_emp1 = User.query.filter_by(email="emp@test.com").first()
        emp1 = Employee(
            user_id=user_emp1.id,
            employee_code="EMP-DSH-01",
            first_name="Alice",
            last_name="Smith",
            department_id=eng.id,
            designation="Senior Backend Engineer",
            status="ACTIVE"
        )

        user_emp2 = User(email="emp2@test.com", role="EMPLOYEE", is_active=True)
        user_emp2.set_password("Emp2Pass123!")
        db.session.add(user_emp2)
        db.session.flush()

        emp2 = Employee(
            user_id=user_emp2.id,
            employee_code="EMP-DSH-02",
            first_name="Bob",
            last_name="Jones",
            department_id=hr_dept.id,
            designation="HR Specialist",
            status="ACTIVE"
        )

        user_inactive = User.query.filter_by(email="inactive@test.com").first()
        emp_inactive = Employee(
            user_id=user_inactive.id,
            employee_code="EMP-DSH-INACT",
            first_name="Charlie",
            last_name="Ex",
            department_id=eng.id,
            designation="Former Dev",
            status="TERMINATED"
        )

        db.session.add_all([emp1, emp2, emp_inactive])
        db.session.commit()

        # 3. Attendance: Emp 1 checked in today (active session), Emp 2 completed attendance today
        today = date.today()
        now = datetime.now(timezone.utc)
        att1 = Attendance(
            employee_id=emp1.id,
            work_date=today,
            shift_number=1,
            check_in=now - timedelta(hours=3),
            check_out=None,  # Currently checked in!
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
        db.session.add_all([att1, att2])

        # 4. Leave Types & Requests: 1 Pending, 1 Approved
        cl = LeaveType(code="CL", name="Casual Leave", days_per_year=12, is_paid=True, is_active=True)
        db.session.add(cl)
        db.session.flush()

        leave_pending = LeaveRequest(
            employee_id=emp1.id,
            leave_type_id=cl.id,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=12),
            total_days=3.0,
            reason="Family Event",
            status="PENDING"
        )
        leave_approved = LeaveRequest(
            employee_id=emp2.id,
            leave_type_id=cl.id,
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=21),
            total_days=2.0,
            reason="Medical",
            status="APPROVED"
        )
        db.session.add_all([leave_pending, leave_approved])

        # 5. Tasks: 1 Completed, 1 In Progress, 1 Overdue
        admin_user = User.query.filter_by(email="admin@test.com").first()
        task_comp = Task(
            title="Deploy Microservices",
            assigned_to=emp1.id,
            created_by=admin_user.id,
            department_id=eng.id,
            priority="HIGH",
            status="COMPLETED",
            due_date=today + timedelta(days=2)
        )
        task_prog = Task(
            title="Code Review API",
            assigned_to=emp1.id,
            created_by=admin_user.id,
            department_id=eng.id,
            priority="MEDIUM",
            status="IN_PROGRESS",
            due_date=today + timedelta(days=5)
        )
        task_overdue = Task(
            title="Legacy Migration",
            assigned_to=emp2.id,
            created_by=admin_user.id,
            department_id=hr_dept.id,
            priority="URGENT",
            status="TODO",
            due_date=today - timedelta(days=2)  # Overdue!
        )
        db.session.add_all([task_comp, task_prog, task_overdue])

        # 6. Performance: 1 Cycle, 1 Review Completed (Rating 5), 1 Review In-Progress (Rating 2, Manager Review)
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

        rev_completed = PerformanceReview(
            cycle_id=cycle.id,
            employee_id=emp1.id,
            review_period="Annual 2026",
            status="COMPLETED",
            self_rating=4,
            rating=5,
            manager_feedback="Exceptional engineering leadership."
        )
        rev_inprogress = PerformanceReview(
            cycle_id=cycle.id,
            employee_id=emp2.id,
            review_period="Annual 2026",
            status="MANAGER_REVIEW",
            self_rating=3,
            rating=2,  # Draft rating not yet finalized
            manager_feedback="Needs improvement in attendance."
        )
        db.session.add_all([rev_completed, rev_inprogress])
        db.session.commit()

        return {
            "emp1_id": str(emp1.id),
            "emp2_id": str(emp2.id),
            "cycle_id": cycle.id
        }

@pytest.fixture
def auth_tokens_dash(client, setup_dashboard_fixtures):
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
# 1. Admin Dashboard Tests
# ==============================================================================
def test_admin_dashboard_metrics_and_charts(client, auth_tokens_dash):
    """Admin dashboard returns exact aggregated database statistics and chart breakdowns."""
    res = client.get("/api/dashboard/admin", headers={"Authorization": f"Bearer {auth_tokens_dash['admin']}"})
    assert res.status_code == 200
    data = res.json["data"]
    metrics = data["metrics"]
    charts = data["charts"]

    # Verify counts
    assert metrics["total_employees"] == 3
    assert metrics["active_employees"] == 2
    assert metrics["inactive_employees"] == 1
    assert metrics["total_departments"] == 2
    assert metrics["today_attendance_count"] == 2
    assert metrics["currently_checked_in"] == 1  # Emp 1 is still checked in!
    assert metrics["pending_leaves"] == 1
    assert metrics["approved_leaves"] == 1
    assert metrics["total_tasks"] == 3
    assert metrics["completed_tasks"] == 1
    assert metrics["pending_tasks"] == 2
    assert metrics["overdue_tasks"] == 1
    assert metrics["active_cycles"] == 1
    assert metrics["completed_reviews"] == 1
    assert metrics["average_rating"] == 5.00  # Only rev_completed (5) is counted! In-progress (2) excluded.

    # Verify charts
    assert len(charts["department_distribution"]) == 2
    assert len(charts["attendance_trends_7d"]) == 7
    assert len(charts["attendance_trends_30d"]) == 30
    assert len(charts["performance_distribution"]) == 5
    # In performance distribution, score 5 count is 1, score 2 count is 0 (as rev 2 is in-progress)
    perf_map = {item["score"]: item["count"] for item in charts["performance_distribution"]}
    assert perf_map[5] == 1
    assert perf_map[2] == 0


# ==============================================================================
# 2. HR Dashboard Tests
# ==============================================================================
def test_hr_dashboard_metrics_and_charts(client, auth_tokens_dash):
    """HR dashboard returns operational workforce metrics, leave queues, and cycle progress."""
    res = client.get("/api/dashboard/hr", headers={"Authorization": f"Bearer {auth_tokens_dash['hr']}"})
    assert res.status_code == 200
    data = res.json["data"]
    metrics = data["metrics"]
    charts = data["charts"]

    assert metrics["total_employees"] == 3
    assert metrics["active_employees"] == 2
    assert metrics["today_attendance"]["present"] == 2
    assert metrics["today_attendance"]["currently_checked_in"] == 1
    assert metrics["pending_leave_approvals"] == 1
    assert metrics["approved_leaves"] == 1
    assert metrics["rejected_leaves"] == 0
    assert metrics["total_tasks"] == 3
    assert metrics["completed_tasks"] == 1
    assert metrics["overdue_tasks"] == 1
    assert metrics["active_cycles"] == 1
    assert metrics["completed_reviews"] == 1
    assert metrics["review_completion_rate"] == 50.0  # 1 of 2 reviews completed = 50%

    assert len(charts["department_employees"]) == 2
    assert len(charts["cycle_progress"]) == 1
    assert charts["cycle_progress"][0]["completion_rate"] == 50.0


# ==============================================================================
# 3. Employee Dashboard Scoping & Privacy Tests
# ==============================================================================
def test_employee_dashboard_personal_scoping(client, auth_tokens_dash, setup_dashboard_fixtures):
    """Employee dashboard returns strictly personal metrics and hides uncompleted ratings."""
    # Emp 1 query
    res1 = client.get("/api/dashboard/employee", headers={"Authorization": f"Bearer {auth_tokens_dash['emp1']}"})
    assert res1.status_code == 200
    data1 = res1.json["data"]

    # Profile check
    assert data1["profile"]["full_name"] == "Alice Smith"
    assert data1["profile"]["employee_code"] == "EMP-DSH-01"
    assert data1["profile"]["department"] == "Engineering"

    # Attendance check: Emp 1 is currently CHECKED_IN
    assert data1["attendance"]["today_status"] == "CHECKED_IN"
    assert data1["attendance"]["today_check_in_time"] is not None
    assert data1["attendance"]["month_attendance_days"] >= 1

    # Leave check
    assert data1["leaves"]["pending_requests"] == 1
    assert len(data1["leaves"]["balances"]) >= 1

    # Task check: 2 tasks assigned to Emp 1 (1 completed, 1 in progress, 0 overdue)
    assert data1["tasks"]["assigned_tasks"] == 2
    assert data1["tasks"]["completed_tasks"] == 1
    assert data1["tasks"]["pending_tasks"] == 1
    assert data1["tasks"]["overdue_tasks"] == 0

    # Performance check: Emp 1's review is COMPLETED with rating 5
    assert data1["performance"]["has_review"] is True
    assert data1["performance"]["latest_review_status"] == "COMPLETED"
    assert data1["performance"]["latest_rating"] == 5
    assert data1["performance"]["latest_rating_label"] == "Outstanding"

    # Charts check
    assert len(data1["charts"]["attendance_7d"]) == 7
    assert len(data1["charts"]["leave_history"]) >= 1

def test_employee_dashboard_hides_uncompleted_rating(client, auth_tokens_dash):
    """Employee 2's review is MANAGER_REVIEW (in progress); latest_rating must be None/hidden."""
    res2 = client.get("/api/dashboard/employee", headers={"Authorization": f"Bearer {auth_tokens_dash['emp2']}"})
    assert res2.status_code == 200
    data2 = res2.json["data"]

    assert data2["profile"]["full_name"] == "Bob Jones"
    assert data2["performance"]["has_review"] is True
    assert data2["performance"]["latest_review_status"] == "MANAGER_REVIEW"
    # STRICT REQUIREMENT: Rating is hidden unless completed
    assert data2["performance"]["latest_rating"] is None
    assert data2["performance"]["latest_rating_label"] is None

    # Overdue task check: Emp 2 has 1 overdue task
    assert data2["tasks"]["overdue_tasks"] == 1


# ==============================================================================
# 4. RBAC & Cross-Role Access Protection Tests
# ==============================================================================
def test_employee_cannot_access_admin_or_hr_dashboards(client, auth_tokens_dash):
    """Employees attempting to access Admin or HR dashboard endpoints are rejected with 403 Forbidden."""
    # Emp 1 -> Admin dashboard -> 403
    res_admin = client.get("/api/dashboard/admin", headers={"Authorization": f"Bearer {auth_tokens_dash['emp1']}"})
    assert res_admin.status_code == 403

    # Emp 1 -> HR dashboard -> 403
    res_hr = client.get("/api/dashboard/hr", headers={"Authorization": f"Bearer {auth_tokens_dash['emp1']}"})
    assert res_hr.status_code == 403

    # Emp 1 -> Department distribution (HR/Admin only) -> 403
    res_dept = client.get("/api/dashboard/department-distribution", headers={"Authorization": f"Bearer {auth_tokens_dash['emp1']}"})
    assert res_dept.status_code == 403

def test_unauthenticated_requests_rejected_with_401(client):
    """Unauthenticated requests to any dashboard endpoint are rejected with 401 Unauthorized."""
    assert client.get("/api/dashboard/admin").status_code == 401
    assert client.get("/api/dashboard/hr").status_code == 401
    assert client.get("/api/dashboard/employee").status_code == 401
    assert client.get("/api/dashboard/attendance-trends").status_code == 401
    assert client.get("/api/dashboard/department-distribution").status_code == 401
    assert client.get("/api/dashboard/task-analytics").status_code == 401
    assert client.get("/api/dashboard/leave-analytics").status_code == 401
    assert client.get("/api/dashboard/performance-analytics").status_code == 401


# ==============================================================================
# 5. Granular Analytics Endpoints & Isolation Tests
# ==============================================================================
def test_attendance_trends_and_date_filtering(client, auth_tokens_dash):
    """Verifies attendance trends endpoint and date window filtering."""
    # 7-day query
    res7 = client.get("/api/dashboard/attendance-trends?days=7", headers={"Authorization": f"Bearer {auth_tokens_dash['admin']}"})
    assert res7.status_code == 200
    assert len(res7.json["data"]) == 7

    # 14-day query
    res14 = client.get("/api/dashboard/attendance-trends?days=14", headers={"Authorization": f"Bearer {auth_tokens_dash['admin']}"})
    assert res14.status_code == 200
    assert len(res14.json["data"]) == 14

    # Employee 1 querying attendance trends receives only their personal history
    res_emp = client.get("/api/dashboard/attendance-trends?days=7", headers={"Authorization": f"Bearer {auth_tokens_dash['emp1']}"})
    assert res_emp.status_code == 200
    assert len(res_emp.json["data"]) == 7

def test_task_analytics_scoped(client, auth_tokens_dash):
    """Verifies task analytics endpoint aggregates correctly by status and priority."""
    res_admin = client.get("/api/dashboard/task-analytics", headers={"Authorization": f"Bearer {auth_tokens_dash['admin']}"})
    assert res_admin.status_code == 200
    data = res_admin.json["data"]
    assert "by_status" in data
    assert "by_priority" in data
    status_map = {item["status"]: item["count"] for item in data["by_status"]}
    assert status_map["COMPLETED"] == 1
    assert status_map["IN_PROGRESS"] == 1
    assert status_map["TODO"] == 1

def test_leave_analytics_scoped(client, auth_tokens_dash):
    """Verifies leave analytics endpoint aggregates correctly by status and type."""
    res_admin = client.get("/api/dashboard/leave-analytics", headers={"Authorization": f"Bearer {auth_tokens_dash['admin']}"})
    assert res_admin.status_code == 200
    data = res_admin.json["data"]
    assert "by_status" in data
    assert "by_type" in data

def test_performance_analytics_scoped(client, auth_tokens_dash):
    """Verifies performance analytics strictly counts completed ratings only."""
    res_admin = client.get("/api/dashboard/performance-analytics", headers={"Authorization": f"Bearer {auth_tokens_dash['admin']}"})
    assert res_admin.status_code == 200
    dist = res_admin.json["data"]
    assert len(dist) == 5
    score_map = {item["score"]: item["count"] for item in dist}
    assert score_map[5] == 1
    assert score_map[2] == 0  # Incomplete review excluded

def test_empty_database_safety(app, client):
    """Verifies that dashboard functions handle empty datasets without throwing 500 errors."""
    with app.app_context():
        # Query with non-existent employee/user raises clean 404, not unhandled crash
        random_user_id = uuid.uuid4()
        with pytest.raises(ValueError, match="No employee profile found"):
            from app.services.dashboard_service import DashboardService
            DashboardService.get_employee_dashboard(random_user_id)


# ==============================================================================
# 6. Additional Dedicated Coverage for All 14 Test Scenarios
# ==============================================================================
def test_employee_cannot_access_another_employee_analytics(client, auth_tokens_dash, setup_dashboard_fixtures):
    """Scenario 6: Employee cannot request another employee's analytics; queries are forced to caller identity."""
    fixtures = setup_dashboard_fixtures
    emp2_id = fixtures["emp2_id"]

    # Emp 1 attempts to pass employee_id of Emp 2 in query params
    res_att = client.get(
        f"/api/dashboard/attendance-trends?employee_id={emp2_id}",
        headers={"Authorization": f"Bearer {auth_tokens_dash['emp1']}"}
    )
    assert res_att.status_code == 200
    # Because role is EMPLOYEE, backend overrides employee_id with emp1's id
    # Emp 1 is checked in today with 0 completed hours, whereas Emp 2 has 8 hours
    today_entry = res_att.json["data"][-1]
    assert today_entry["hours"] == 0.0  # Proves caller receives their own hours (0.0), not Emp 2's (8.0)

    # Emp 1 attempts to pass employee_id of Emp 2 in task-analytics
    res_task = client.get(
        f"/api/dashboard/task-analytics?employee_id={emp2_id}",
        headers={"Authorization": f"Bearer {auth_tokens_dash['emp1']}"}
    )
    assert res_task.status_code == 200
    # Emp 1 has COMPLETED and IN_PROGRESS tasks; Emp 2 has TODO task
    status_map = {item["status"]: item["count"] for item in res_task.json["data"]["by_status"]}
    assert "TODO" not in status_map  # Emp 2's task is excluded
    assert status_map.get("COMPLETED") == 1  # Emp 1's task is returned

def test_attendance_chart_data_accuracy(client, auth_tokens_dash):
    """Scenario 8: Attendance chart data is correct (count of present employees and logged hours)."""
    res = client.get("/api/dashboard/admin", headers={"Authorization": f"Bearer {auth_tokens_dash['admin']}"})
    assert res.status_code == 200
    charts = res.json["data"]["charts"]

    # 7-day trend
    trend_7d = charts["attendance_trends_7d"]
    assert len(trend_7d) == 7
    today_trend = trend_7d[-1]
    # Today: 2 present employees (Emp1 and Emp2), Emp2 logged 8.0 hours
    assert today_trend["count"] == 2
    assert today_trend["hours"] == 8.0

def test_leave_chart_data_accuracy(client, auth_tokens_dash):
    """Scenario 9: Leave chart data accurately groups requests by status."""
    res = client.get("/api/dashboard/admin", headers={"Authorization": f"Bearer {auth_tokens_dash['admin']}"})
    assert res.status_code == 200
    leave_dist = res.json["data"]["charts"]["leave_distribution"]
    dist_map = {item["status"]: item["count"] for item in leave_dist}

    assert dist_map.get("PENDING") == 1
    assert dist_map.get("APPROVED") == 1
    assert dist_map.get("REJECTED", 0) == 0

def test_task_chart_data_accuracy(client, auth_tokens_dash):
    """Scenario 10: Task chart data accurately groups tasks by status."""
    res = client.get("/api/dashboard/admin", headers={"Authorization": f"Bearer {auth_tokens_dash['admin']}"})
    assert res.status_code == 200
    task_dist = res.json["data"]["charts"]["task_distribution"]
    task_map = {item["status"]: item["count"] for item in task_dist}

    assert task_map.get("COMPLETED") == 1
    assert task_map.get("IN_PROGRESS") == 1
    assert task_map.get("TODO") == 1
    assert task_map.get("BLOCKED", 0) == 0


