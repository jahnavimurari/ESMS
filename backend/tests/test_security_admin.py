import pytest
from app.extension_registry import db
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.audit import AuditLog
from app.services.auth_service import AuthService, _login_attempts

@pytest.fixture
def auth_tokens_admin(client, sample_users):
    """Generates authentication headers for Admin, HR, and Employee."""
    res_admin = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "AdminPass123!"})
    res_hr = client.post("/api/auth/login", json={"email": "hr@test.com", "password": "HRPass123!"})
    res_emp = client.post("/api/auth/login", json={"email": "emp@test.com", "password": "EmpPass123!"})

    return {
        "admin": res_admin.json["data"]["access_token"],
        "hr": res_hr.json["data"]["access_token"],
        "emp": res_emp.json["data"]["access_token"]
    }

def test_admin_can_list_users_paginated(client, auth_tokens_admin):
    """Admin can list registered users with pagination."""
    headers = {"Authorization": f"Bearer {auth_tokens_admin['admin']}"}
    res = client.get("/api/admin/users?page=1&per_page=10", headers=headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "users" in data
    assert data["total"] >= 3
    assert any(u["email"] == "admin@test.com" for u in data["users"])

def test_admin_can_search_and_filter_users(client, auth_tokens_admin):
    """Admin can search users by email and filter by role or status."""
    headers = {"Authorization": f"Bearer {auth_tokens_admin['admin']}"}

    # Filter by role HR
    res_role = client.get("/api/admin/users?role=HR", headers=headers)
    assert res_role.status_code == 200
    users_hr = res_role.get_json()["data"]["users"]
    assert all(u["role"] == "HR" for u in users_hr)

    # Filter by search
    res_search = client.get("/api/admin/users?search=emp@test.com", headers=headers)
    assert res_search.status_code == 200
    users_search = res_search.get_json()["data"]["users"]
    assert len(users_search) >= 1
    assert users_search[0]["email"] == "emp@test.com"

def test_admin_can_update_user_role(app, client, auth_tokens_admin):
    """Admin can promote an employee to HR role."""
    headers = {"Authorization": f"Bearer {auth_tokens_admin['admin']}"}
    with app.app_context():
        emp_user = User.query.filter_by(email="emp@test.com").first()
        emp_id = str(emp_user.id)

    res = client.patch(f"/api/admin/users/{emp_id}/role", json={"role": "HR"}, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["role"] == "HR"

    # Reset back to EMPLOYEE
    client.patch(f"/api/admin/users/{emp_id}/role", json={"role": "EMPLOYEE"}, headers=headers)

def test_prevent_demoting_last_active_admin(app, client, auth_tokens_admin):
    """Security rule: System rejects removing or demoting the last active administrator."""
    headers = {"Authorization": f"Bearer {auth_tokens_admin['admin']}"}
    with app.app_context():
        admin_user = User.query.filter_by(email="admin@test.com").first()
        admin_id = str(admin_user.id)

    # Attempt to demote the sole admin to EMPLOYEE
    res = client.patch(f"/api/admin/users/{admin_id}/role", json={"role": "EMPLOYEE"}, headers=headers)
    assert res.status_code == 400
    assert "last active administrator" in res.get_json()["error"]["message"]

def test_admin_can_activate_and_deactivate_user(app, client, auth_tokens_admin):
    """Admin can deactivate and subsequently reactivate a user account."""
    headers = {"Authorization": f"Bearer {auth_tokens_admin['admin']}"}
    with app.app_context():
        emp_user = User.query.filter_by(email="emp@test.com").first()
        emp_id = str(emp_user.id)

    # Deactivate
    res_deact = client.patch(f"/api/admin/users/{emp_id}/status", json={"is_active": False}, headers=headers)
    assert res_deact.status_code == 200
    assert res_deact.get_json()["data"]["is_active"] is False

    # Login fails for deactivated account
    login_res = client.post("/api/auth/login", json={"email": "emp@test.com", "password": "EmpPass123!"})
    assert login_res.status_code == 403

    # Reactivate
    res_act = client.patch(f"/api/admin/users/{emp_id}/status", json={"is_active": True}, headers=headers)
    assert res_act.status_code == 200
    assert res_act.get_json()["data"]["is_active"] is True

def test_prevent_deactivating_last_active_admin(app, client, auth_tokens_admin):
    """Security rule: System rejects deactivating the last active administrator."""
    headers = {"Authorization": f"Bearer {auth_tokens_admin['admin']}"}
    with app.app_context():
        admin_user = User.query.filter_by(email="admin@test.com").first()
        admin_id = str(admin_user.id)

    res = client.patch(f"/api/admin/users/{admin_id}/status", json={"is_active": False}, headers=headers)
    assert res.status_code == 400
    assert "last active administrator" in res.get_json()["error"]["message"]

def test_unauthorized_user_cannot_access_admin_endpoints(client, auth_tokens_admin):
    """RBAC: HR and ordinary employees receive 403 Forbidden on administrative endpoints."""
    emp_headers = {"Authorization": f"Bearer {auth_tokens_admin['emp']}"}
    hr_headers = {"Authorization": f"Bearer {auth_tokens_admin['hr']}"}

    assert client.get("/api/admin/users", headers=emp_headers).status_code == 403
    assert client.get("/api/admin/users", headers=hr_headers).status_code == 403
    assert client.get("/api/admin/audit-logs", headers=emp_headers).status_code == 403
    assert client.get("/api/admin/audit-logs", headers=hr_headers).status_code == 403
    assert client.get("/api/admin/system-stats", headers=emp_headers).status_code == 403
    assert client.get("/api/admin/system-stats", headers=hr_headers).status_code == 403

def test_password_strength_validation(app):
    """Enforces enterprise password complexity standards."""
    with app.app_context():
        u = User(email="pwdtest@test.com", role="EMPLOYEE")
        # Too short (< 8)
        with pytest.raises(ValueError, match="at least 8 characters"):
            u.set_password("Short1!")
        # No uppercase
        with pytest.raises(ValueError, match="uppercase"):
            u.set_password("nouppercase123!")
        # No lowercase
        with pytest.raises(ValueError, match="lowercase"):
            u.set_password("NOLOWERCASE123!")
        # No digit
        with pytest.raises(ValueError, match="number"):
            u.set_password("NoDigitsHere!")
        # No special symbol
        with pytest.raises(ValueError, match="special character"):
            u.set_password("NoSpecialChar123")
        # Strong password succeeds
        u.set_password("StrongPassword123!")
        assert u.check_password("StrongPassword123!") is True

def test_password_reset_workflow(client, sample_users):
    """Tests secure password reset workflow without user enumeration."""
    # 1. Non-existent email returns identical generic message
    res_fake = client.post("/api/auth/forgot-password", json={"email": "nonexistent@test.com"})
    assert res_fake.status_code == 200
    assert "password reset instructions" in res_fake.get_json()["message"]

    # 2. Existing user requests reset
    res_real = client.post("/api/auth/forgot-password", json={"email": "emp@test.com"})
    assert res_real.status_code == 200
    raw_token = res_real.get_json()["debug_token"]
    assert raw_token is not None

    # 3. Invalid token rejected
    bad_reset = client.post("/api/auth/reset-password", json={"token": "invalid_fake_token", "new_password": "NewStrongPass99!"})
    assert bad_reset.status_code == 400

    # 4. Valid token resets password
    good_reset = client.post("/api/auth/reset-password", json={"token": raw_token, "new_password": "NewStrongPass99!"})
    assert good_reset.status_code == 200

    # 5. Token cannot be reused (consumed)
    reuse_reset = client.post("/api/auth/reset-password", json={"token": raw_token, "new_password": "AnotherStrongPass99!"})
    assert reuse_reset.status_code == 400

    # 6. User can authenticate with new password
    login_new = client.post("/api/auth/login", json={"email": "emp@test.com", "password": "NewStrongPass99!"})
    assert login_new.status_code == 200

def test_login_rate_limiting_brute_force_protection(client):
    """Enforces lockout after repeated failed login attempts."""
    _login_attempts.clear()
    target_email = "brute_target@test.com"

    # 5 consecutive failed logins
    for i in range(5):
        client.post("/api/auth/login", json={"email": target_email, "password": "WrongPassword!"})

    # 6th attempt should be locked out
    locked_res = client.post("/api/auth/login", json={"email": target_email, "password": "WrongPassword!"})
    assert locked_res.status_code == 403
    assert "temporarily locked" in locked_res.get_json()["error"]["message"]
    _login_attempts.clear()

def test_token_revocation_on_logout(client, auth_tokens_admin):
    """Logout revokes access token preventing further API usage."""
    emp_token = auth_tokens_admin["emp"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # Verify token works before logout
    check_res = client.get("/api/auth/me", headers=emp_headers)
    assert check_res.status_code == 200

    # Logout
    logout_res = client.post("/api/auth/logout", headers=emp_headers)
    assert logout_res.status_code == 200

    # Subsequent request with revoked token returns 401
    post_res = client.get("/api/auth/me", headers=emp_headers)
    assert post_res.status_code == 401
    assert "revoked" in post_res.get_json()["error"]["message"].lower()

def test_admin_audit_logs_viewer_and_filters(client, auth_tokens_admin):
    """Admin can query and filter append-only audit trail."""
    headers = {"Authorization": f"Bearer {auth_tokens_admin['admin']}"}
    res = client.get("/api/admin/audit-logs?page=1&per_page=20", headers=headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "audit_logs" in data
    assert "total" in data

def test_admin_system_stats_dashboard(client, auth_tokens_admin):
    """Admin receives real application health and user telemetry."""
    headers = {"Authorization": f"Bearer {auth_tokens_admin['admin']}"}
    res = client.get("/api/admin/system-stats", headers=headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "metrics" in data
    assert "role_distribution" in data
    assert "system_health" in data
    assert data["metrics"]["total_users"] >= 3
    assert data["system_health"]["database_connection"] == "connected"

