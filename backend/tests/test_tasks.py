import pytest
import uuid
from datetime import datetime, timezone, timedelta, date
from app.extension_registry import db
from app.models.department import Department
from app.models.employee import Employee
from app.models.task import Task
from app.models.user import User
from app.models.audit import AuditLog

@pytest.fixture
def setup_task_fixtures(app, sample_users):
    """Sets up department, active employees (Emp1, Emp2) and an inactive employee."""
    with app.app_context():
        dept = Department(name="Engineering", code="ENG", description="Core Platform Engineering")
        db.session.add(dept)
        db.session.commit()

        emp_user_1 = User.query.filter_by(email="emp@test.com").first()
        emp1 = Employee(
            user_id=emp_user_1.id,
            employee_code="EMP-TSK-01",
            first_name="Diana",
            last_name="Prince",
            department_id=dept.id,
            designation="Lead Architect",
            status="ACTIVE"
        )

        emp_user_2 = User(email="emp2@test.com", role="EMPLOYEE", is_active=True)
        emp_user_2.set_password("Emp2Pass123!")
        db.session.add(emp_user_2)
        db.session.flush()

        emp2 = Employee(
            user_id=emp_user_2.id,
            employee_code="EMP-TSK-02",
            first_name="Barry",
            last_name="Allen",
            department_id=dept.id,
            designation="Systems Engineer",
            status="ACTIVE"
        )

        # Inactive employee
        emp_user_inactive = User.query.filter_by(email="inactive@test.com").first()
        emp_inactive = Employee(
            user_id=emp_user_inactive.id,
            employee_code="EMP-TSK-INACT",
            first_name="Victor",
            last_name="Stone",
            department_id=dept.id,
            designation="Former Engineer",
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
def auth_tokens_task(client, setup_task_fixtures):
    """Obtains JWT tokens for Admin, HR, Employee 1, and Employee 2."""
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

# ------------------------------------------------------------------------------
# 1. Task Creation & Date Validation
# ------------------------------------------------------------------------------
def test_task_creation_success(client, auth_tokens_task, setup_task_fixtures):
    """Admin and HR can create tasks with priority, dates, category, and assignee."""
    emp1_id = setup_task_fixtures["emp1_id"]
    today = date.today()
    due = today + timedelta(days=7)

    res = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={
            "title": "Migrate Neon DB Pooler",
            "description": "Configure pgBouncer pooled connection strings for production.",
            "category": "Infrastructure",
            "priority": "HIGH",
            "assigned_to": emp1_id,
            "start_date": today.isoformat(),
            "due_date": due.isoformat(),
        }
    )
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["title"] == "Migrate Neon DB Pooler"
    assert data["status"] == "TODO"
    assert data["priority"] == "HIGH"
    assert data["category"] == "Infrastructure"
    assert data["assigned_to"] == emp1_id
    assert data["assignee_name"] == "Diana Prince"
    assert data["is_overdue"] is False

def test_task_creation_invalid_dates_rejected(client, auth_tokens_task, setup_task_fixtures):
    """Validates that due_date cannot be earlier than start_date."""
    emp1_id = setup_task_fixtures["emp1_id"]
    res = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['hr']}"},
        json={
            "title": "Invalid Date Task",
            "assigned_to": emp1_id,
            "start_date": "2026-12-10",
            "due_date": "2026-12-01",
        }
    )
    assert res.status_code == 400
    assert "due_date" in res.get_json()["error"]["details"]

def test_task_creation_inactive_or_invalid_employee(client, auth_tokens_task, setup_task_fixtures):
    """Validates that tasks cannot be assigned to non-existent or inactive employees."""
    fake_id = str(uuid.uuid4())
    res_fake = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={
            "title": "Non-existent Employee Task",
            "assigned_to": fake_id
        }
    )
    assert res_fake.status_code == 400
    assert "not found" in res_fake.get_json()["error"]["message"].lower()

    # Inactive employee
    inact_id = setup_task_fixtures["emp_inactive_id"]
    res_inact = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={
            "title": "Inactive Employee Task",
            "assigned_to": inact_id
        }
    )
    assert res_inact.status_code == 400
    assert "active" in res_inact.get_json()["error"]["message"].lower()

# ------------------------------------------------------------------------------
# 2. RBAC & Data Isolation
# ------------------------------------------------------------------------------
def test_employee_cannot_create_task(client, auth_tokens_task, setup_task_fixtures):
    """Regular employees cannot create tasks."""
    res = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['emp1']}"},
        json={
            "title": "Unauthorized Task",
            "assigned_to": setup_task_fixtures["emp1_id"]
        }
    )
    assert res.status_code == 403

def test_cross_employee_access_rejection(client, auth_tokens_task, setup_task_fixtures):
    """Employee 2 cannot view or update details of a task assigned to Employee 1."""
    # Create task for Emp1
    res_create = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={
            "title": "Emp1 Secret Project",
            "assigned_to": setup_task_fixtures["emp1_id"]
        }
    )
    assert res_create.status_code == 201
    task_id = res_create.get_json()["data"]["id"]

    # Emp1 can access
    res_emp1 = client.get(f"/api/tasks/{task_id}", headers={"Authorization": f"Bearer {auth_tokens_task['emp1']}"})
    assert res_emp1.status_code == 200

    # Emp2 cannot access
    res_emp2 = client.get(f"/api/tasks/{task_id}", headers={"Authorization": f"Bearer {auth_tokens_task['emp2']}"})
    assert res_emp2.status_code == 403

def test_employee_my_tasks_scoping(client, auth_tokens_task, setup_task_fixtures):
    """GET /api/tasks/my returns strictly the authenticated employee's tasks."""
    # Create 1 task for Emp1 and 1 task for Emp2
    client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Diana's Mission", "assigned_to": setup_task_fixtures["emp1_id"]}
    )
    client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Barry's Mission", "assigned_to": setup_task_fixtures["emp2_id"]}
    )

    # Emp1 fetches my tasks
    res_my1 = client.get("/api/tasks/my", headers={"Authorization": f"Bearer {auth_tokens_task['emp1']}"})
    assert res_my1.status_code == 200
    items1 = res_my1.get_json()["data"]
    assert all(t["assigned_to"] == setup_task_fixtures["emp1_id"] for t in items1)

    # Emp2 fetches my tasks
    res_my2 = client.get("/api/tasks/my", headers={"Authorization": f"Bearer {auth_tokens_task['emp2']}"})
    assert res_my2.status_code == 200
    items2 = res_my2.get_json()["data"]
    assert all(t["assigned_to"] == setup_task_fixtures["emp2_id"] for t in items2)

# ------------------------------------------------------------------------------
# 3. Task Status Lifecycle Transitions
# ------------------------------------------------------------------------------
def test_valid_task_status_lifecycle(client, auth_tokens_task, setup_task_fixtures):
    """
    Tests complete lifecycle:
    TODO -> IN_PROGRESS (Emp) -> REVIEW (Emp) -> COMPLETED (Admin)
    """
    res_create = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Lifecycle Task", "assigned_to": setup_task_fixtures["emp1_id"]}
    )
    task_id = res_create.get_json()["data"]["id"]

    # 1. Emp moves to IN_PROGRESS
    res_prog = client.patch(
        f"/api/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {auth_tokens_task['emp1']}"},
        json={"status": "IN_PROGRESS", "comment": "Started architectural review."}
    )
    assert res_prog.status_code == 200
    assert res_prog.get_json()["data"]["status"] == "IN_PROGRESS"

    # 2. Emp moves to REVIEW
    res_rev = client.patch(
        f"/api/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {auth_tokens_task['emp1']}"},
        json={"status": "REVIEW", "comment": "Ready for manager sign-off."}
    )
    assert res_rev.status_code == 200
    assert res_rev.get_json()["data"]["status"] == "REVIEW"

    # 3. Admin approves to COMPLETED
    res_comp = client.patch(
        f"/api/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"status": "COMPLETED", "comment": "Approved and validated."}
    )
    assert res_comp.status_code == 200
    assert res_comp.get_json()["data"]["status"] == "COMPLETED"
    assert res_comp.get_json()["data"]["completed_at"] is not None

def test_employee_cannot_mark_task_completed_directly(client, auth_tokens_task, setup_task_fixtures):
    """Employees are blocked from self-approving tasks to COMPLETED."""
    res_create = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Self Completion Blocked", "assigned_to": setup_task_fixtures["emp1_id"]}
    )
    task_id = res_create.get_json()["data"]["id"]

    # Attempt to jump to COMPLETED
    res_comp = client.patch(
        f"/api/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {auth_tokens_task['emp1']}"},
        json={"status": "COMPLETED"}
    )
    assert res_comp.status_code == 403
    assert "cannot mark tasks directly as completed" in res_comp.get_json()["error"]["message"].lower()

def test_invalid_status_transition_rejected(client, auth_tokens_task, setup_task_fixtures):
    """Invalid transitions (e.g. TODO directly to REVIEW) are rejected."""
    res_create = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Invalid Transition Task", "assigned_to": setup_task_fixtures["emp1_id"]}
    )
    task_id = res_create.get_json()["data"]["id"]

    res_invalid = client.patch(
        f"/api/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {auth_tokens_task['emp1']}"},
        json={"status": "REVIEW"}
    )
    assert res_invalid.status_code == 400
    assert "invalid status transition" in res_invalid.get_json()["error"]["message"].lower()

# ------------------------------------------------------------------------------
# 4. Task Editing, Reassignment & Cancellation
# ------------------------------------------------------------------------------
def test_task_editing_by_admin(client, auth_tokens_task, setup_task_fixtures):
    """Admin and HR can edit task title, description, priority, and dates."""
    res_create = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Initial Title", "priority": "LOW", "assigned_to": setup_task_fixtures["emp1_id"]}
    )
    task_id = res_create.get_json()["data"]["id"]

    res_edit = client.put(
        f"/api/tasks/{task_id}",
        headers={"Authorization": f"Bearer {auth_tokens_task['hr']}"},
        json={
            "title": "Updated Title via HR",
            "priority": "URGENT",
            "description": "Updated detailed description.",
            "category": "Security"
        }
    )
    assert res_edit.status_code == 200
    data = res_edit.get_json()["data"]
    assert data["title"] == "Updated Title via HR"
    assert data["priority"] == "URGENT"
    assert data["category"] == "Security"

def test_task_reassignment(client, auth_tokens_task, setup_task_fixtures):
    """Admin can reassign task from Emp1 to Emp2."""
    res_create = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Reassignment Task", "assigned_to": setup_task_fixtures["emp1_id"]}
    )
    task_id = res_create.get_json()["data"]["id"]

    res_reassign = client.patch(
        f"/api/tasks/{task_id}/assign",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"assigned_to": setup_task_fixtures["emp2_id"], "comment": "Reassigned for urgent sprint."}
    )
    assert res_reassign.status_code == 200
    data = res_reassign.get_json()["data"]
    assert data["assigned_to"] == setup_task_fixtures["emp2_id"]
    assert data["assignee_name"] == "Barry Allen"

def test_task_cancellation_and_locking(client, auth_tokens_task, setup_task_fixtures):
    """Admin cancels task; cancelled tasks cannot be modified or re-transitioned."""
    res_create = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Cancellation Test Task", "assigned_to": setup_task_fixtures["emp1_id"]}
    )
    task_id = res_create.get_json()["data"]["id"]

    # Cancel
    res_cancel = client.patch(
        f"/api/tasks/{task_id}/cancel",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"reason": "Project deselect."}
    )
    assert res_cancel.status_code == 200
    assert res_cancel.get_json()["data"]["status"] == "CANCELLED"

    # Cannot transition cancelled task
    res_trans = client.patch(
        f"/api/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"status": "IN_PROGRESS"}
    )
    assert res_trans.status_code == 400

    # Cannot edit cancelled task
    res_edit = client.put(
        f"/api/tasks/{task_id}",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Change after cancel"}
    )
    assert res_edit.status_code == 400

# ------------------------------------------------------------------------------
# 5. Overdue Tracking, Summary KPIs & Audit History
# ------------------------------------------------------------------------------
def test_overdue_tasks_and_summary_kpis(client, auth_tokens_task, setup_task_fixtures):
    """Verifies overdue calculation and KPI aggregation."""
    yesterday = date.today() - timedelta(days=2)
    tomorrow = date.today() + timedelta(days=2)

    # 1. Overdue task
    client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={
            "title": "Past Due Task",
            "assigned_to": setup_task_fixtures["emp1_id"],
            "due_date": yesterday.isoformat(),
            "priority": "URGENT"
        }
    )

    # 2. Future task
    client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={
            "title": "Future Task",
            "assigned_to": setup_task_fixtures["emp1_id"],
            "due_date": tomorrow.isoformat(),
            "priority": "LOW"
        }
    )

    # Query summary
    res_sum = client.get("/api/tasks/summary", headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"})
    assert res_sum.status_code == 200
    kpis = res_sum.get_json()["data"]
    assert kpis["total_tasks"] >= 2
    assert kpis["overdue"] >= 1
    assert kpis["high_priority"] >= 1

    # Filter overdue
    res_overdue = client.get("/api/tasks?overdue=true", headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"})
    assert res_overdue.status_code == 200
    overdue_items = res_overdue.get_json()["data"]
    assert any(t["title"] == "Past Due Task" for t in overdue_items)
    assert all(t["is_overdue"] is True for t in overdue_items)

def test_task_audit_history(client, auth_tokens_task, setup_task_fixtures):
    """Verifies that creation, status updates, and comments generate an audit timeline."""
    res_create = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {auth_tokens_task['admin']}"},
        json={"title": "Audited Task", "assigned_to": setup_task_fixtures["emp1_id"]}
    )
    task_id = res_create.get_json()["data"]["id"]

    # Status update with comment
    client.patch(
        f"/api/tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {auth_tokens_task['emp1']}"},
        json={"status": "IN_PROGRESS", "comment": "Started work on ticket."}
    )

    # Fetch history
    res_hist = client.get(f"/api/tasks/{task_id}/history", headers={"Authorization": f"Bearer {auth_tokens_task['emp1']}"})
    assert res_hist.status_code == 200
    history = res_hist.get_json()["data"]
    assert len(history) >= 2
    actions = [h["action"] for h in history]
    assert "CREATE_TASK" in actions
    assert "UPDATE_STATUS" in actions
    status_entry = next(h for h in history if h["action"] == "UPDATE_STATUS")
    assert status_entry["new_state"]["comment"] == "Started work on ticket."

def test_unauthenticated_requests_rejected(client):
    """Requests without a valid Bearer token return 401 Unauthorized."""
    assert client.get("/api/tasks").status_code == 401
    assert client.get("/api/tasks/my").status_code == 401
    assert client.post("/api/tasks", json={}).status_code == 401
    assert client.patch("/api/tasks/1/status", json={}).status_code == 401
    assert client.get("/api/tasks/1/history").status_code == 401

