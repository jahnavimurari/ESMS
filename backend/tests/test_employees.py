import pytest
from app.extension_registry import db
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User

@pytest.fixture
def sample_department(app):
    with app.app_context():
        dept = Department(name="Engineering", code="ENG", description="Core engineering teams")
        db.session.add(dept)
        db.session.commit()
        return dept.id

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

def test_department_creation_and_listing(client, auth_tokens):
    """Verifies department creation by HR and listing."""
    # Unauthorized employee cannot create department
    res_unauth = client.post("/api/employees/departments",
                             headers={"Authorization": f"Bearer {auth_tokens['employee']}"},
                             json={"name": "Sales", "code": "SALES"})
    assert res_unauth.status_code == 403

    # HR creates department
    res_hr = client.post("/api/employees/departments",
                         headers={"Authorization": f"Bearer {auth_tokens['hr']}"},
                         json={"name": "Human Resources", "code": "HR", "description": "HR ops"})
    assert res_hr.status_code == 201
    data = res_hr.get_json()["data"]
    assert data["name"] == "Human Resources"
    assert data["code"] == "HR"
    dept_id = data["id"]

    # Duplicate department rejection
    res_dup = client.post("/api/employees/departments",
                          headers={"Authorization": f"Bearer {auth_tokens['hr']}"},
                          json={"name": "Human Resources", "code": "HR_NEW"})
    assert res_dup.status_code == 409

    # Update department by Admin
    res_update = client.put(f"/api/employees/departments/{dept_id}",
                            headers={"Authorization": f"Bearer {auth_tokens['admin']}"},
                            json={"description": "Updated HR ops"})
    assert res_update.status_code == 200
    assert res_update.get_json()["data"]["description"] == "Updated HR ops"

    # List departments (accessible by employee too)
    res_list = client.get("/api/employees/departments",
                          headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_list.status_code == 200
    items = res_list.get_json()["data"]
    assert len(items) >= 1

def test_employee_creation_success(client, auth_tokens, sample_department):
    """Verifies successful employee creation by HR."""
    payload = {
        "employee_code": "EMP-001",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@company.com",
        "password": "Password123!",
        "role": "EMPLOYEE",
        "phone": "+1234567890",
        "department_id": sample_department,
        "designation": "Software Engineer",
        "joining_date": "2026-01-15",
        "employment_type": "FULL_TIME"
    }

    res = client.post("/api/employees",
                      headers={"Authorization": f"Bearer {auth_tokens['hr']}"},
                      json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["employee_code"] == "EMP-001"
    assert data["data"]["first_name"] == "Jane"
    assert data["data"]["email"] == "jane.doe@company.com"

def test_employee_creation_missing_required_fields(client, auth_tokens):
    """Verifies validation error on missing required fields."""
    res = client.post("/api/employees",
                      headers={"Authorization": f"Bearer {auth_tokens['hr']}"},
                      json={"first_name": "Jane"})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"

def test_employee_creation_duplicate_email(client, auth_tokens, sample_department):
    """Verifies rejection of duplicate email."""
    # admin@test.com already exists in sample_users
    payload = {
        "employee_code": "EMP-999",
        "first_name": "Duplicate",
        "last_name": "User",
        "email": "admin@test.com",
        "department_id": sample_department,
        "designation": "Architect"
    }
    res = client.post("/api/employees",
                      headers={"Authorization": f"Bearer {auth_tokens['hr']}"},
                      json=payload)
    assert res.status_code == 409
    assert "already exists" in res.get_json()["error"]["message"]

def test_employee_creation_invalid_department(client, auth_tokens):
    """Verifies rejection when department does not exist."""
    payload = {
        "employee_code": "EMP-998",
        "first_name": "No",
        "last_name": "Dept",
        "email": "nodept@company.com",
        "department_id": 99999,
        "designation": "Manager"
    }
    res = client.post("/api/employees",
                      headers={"Authorization": f"Bearer {auth_tokens['admin']}"},
                      json=payload)
    assert res.status_code == 409
    assert "Department ID 99999 does not exist" in res.get_json()["error"]["message"]

def test_employee_list_and_details_rbac(client, auth_tokens, sample_department):
    """Verifies listing, filtering, and role-based clearance for employee details."""
    # Create an employee first
    create_res = client.post("/api/employees",
                             headers={"Authorization": f"Bearer {auth_tokens['admin']}"},
                             json={
                                 "employee_code": "EMP-101",
                                 "first_name": "Alice",
                                 "last_name": "Smith",
                                 "email": "alice@company.com",
                                 "department_id": sample_department,
                                 "designation": "QA Lead"
                             })
    emp_id = create_res.get_json()["data"]["id"]

    # HR lists employees
    res_list = client.get("/api/employees?search=Alice",
                          headers={"Authorization": f"Bearer {auth_tokens['hr']}"})
    assert res_list.status_code == 200
    items = res_list.get_json()["data"]["items"]
    assert len(items) >= 1
    assert items[0]["first_name"] == "Alice"

    # HR views employee details
    res_details = client.get(f"/api/employees/{emp_id}",
                             headers={"Authorization": f"Bearer {auth_tokens['hr']}"})
    assert res_details.status_code == 200
    assert res_details.get_json()["data"]["employee_code"] == "EMP-101"

    # Unauthorized employee cannot view Alice's details
    res_emp_view = client.get(f"/api/employees/{emp_id}",
                              headers={"Authorization": f"Bearer {auth_tokens['employee']}"})
    assert res_emp_view.status_code == 403

def test_employee_update_and_status_deactivation(client, auth_tokens, sample_department):
    """Verifies updating employee details and activating/deactivating status."""
    create_res = client.post("/api/employees",
                             headers={"Authorization": f"Bearer {auth_tokens['hr']}"},
                             json={
                                 "employee_code": "EMP-202",
                                 "first_name": "Bob",
                                 "last_name": "Jones",
                                 "email": "bob@company.com",
                                 "department_id": sample_department,
                                 "designation": "Developer"
                             })
    emp_id = create_res.get_json()["data"]["id"]

    # Update designation
    res_update = client.put(f"/api/employees/{emp_id}",
                            headers={"Authorization": f"Bearer {auth_tokens['hr']}"},
                            json={"designation": "Senior Developer"})
    assert res_update.status_code == 200
    assert res_update.get_json()["data"]["designation"] == "Senior Developer"

    # Deactivate / Suspend employee
    res_status = client.patch(f"/api/employees/{emp_id}/status",
                              headers={"Authorization": f"Bearer {auth_tokens['admin']}"},
                              json={"status": "SUSPENDED", "is_active": False})
    assert res_status.status_code == 200
    assert res_status.get_json()["data"]["status"] == "SUSPENDED"

def test_unauthenticated_requests_rejected(client):
    """Verifies that all employee endpoints reject unauthenticated requests."""
    assert client.get("/api/employees").status_code == 401
    assert client.post("/api/employees", json={}).status_code == 401
    assert client.get("/api/employees/departments").status_code == 401

