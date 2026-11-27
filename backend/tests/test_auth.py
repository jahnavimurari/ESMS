import pytest
from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token
from app.middleware.auth_guard import admin_required, hr_required, employee_required
from app.extension_registry import db
from app.models.user import User

# Test Blueprint for verifying Role-Based Access Control guards
test_rbac_bp = Blueprint("test_rbac", __name__, url_prefix="/api/test-rbac")

@test_rbac_bp.route("/admin-only", methods=["GET"])
@admin_required
def admin_only_view():
    return jsonify({"success": True, "message": "Admin clearance granted."}), 200

@test_rbac_bp.route("/hr-only", methods=["GET"])
@hr_required
def hr_only_view():
    return jsonify({"success": True, "message": "HR clearance granted."}), 200

@test_rbac_bp.route("/employee-all", methods=["GET"])
@employee_required
def employee_all_view():
    return jsonify({"success": True, "message": "Employee clearance granted."}), 200


def test_auth_health_endpoint(client):
    """Verifies that GET /api/auth/health returns 200 and subsystem status."""
    res = client.get("/api/auth/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["status"] == "ready"


def test_login_success(client, sample_users):
    """Verifies successful login with valid credentials."""
    res = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminPass123!"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["email"] == "admin@test.com"
    assert data["data"]["user"]["role"] == "ADMIN"


def test_login_incorrect_password(client, sample_users):
    """Verifies login rejection with incorrect password."""
    res = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email(client, sample_users):
    """Verifies login rejection for non-existent email."""
    res = client.post("/api/auth/login", json={
        "email": "nobody@test.com",
        "password": "AnyPassword123!"
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_inactive_account(client, sample_users):
    """Verifies login rejection for deactivated user accounts."""
    res = client.post("/api/auth/login", json={
        "email": "inactive@test.com",
        "password": "InactivePass123!"
    })
    assert res.status_code == 403
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "ACCOUNT_DISABLED"


def test_login_validation_errors(client):
    """Verifies payload validation on missing or malformed email/password."""
    res = client.post("/api/auth/login", json={"email": "not-an-email"})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_get_current_user_me(client, sample_users):
    """Verifies GET /api/auth/me returns current user data."""
    # First login to get access token
    login_res = client.post("/api/auth/login", json={
        "email": "emp@test.com",
        "password": "EmpPass123!"
    })
    token = login_res.get_json()["data"]["access_token"]

    # Request without token
    res_no_token = client.get("/api/auth/me")
    assert res_no_token.status_code == 401

    # Request with valid token
    res_token = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_token.status_code == 200
    data = res_token.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "emp@test.com"
    assert data["data"]["role"] == "EMPLOYEE"


def test_refresh_token_strategy(client, sample_users):
    """Verifies refreshing an access token using a valid refresh token."""
    login_res = client.post("/api/auth/login", json={
        "email": "hr@test.com",
        "password": "HRPass123!"
    })
    login_data = login_res.get_json()["data"]
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # Calling refresh with access token must be rejected
    res_bad = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {access_token}"})
    assert res_bad.status_code in [401, 422]

    # Calling refresh with valid refresh token must return new access token
    res_good = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert res_good.status_code == 200
    new_data = res_good.get_json()["data"]
    assert "access_token" in new_data
    assert new_data["access_token"] != ""


def test_logout_and_token_revocation(client, sample_users):
    """Verifies that logging out revokes the token and prevents further usage."""
    login_res = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminPass123!"
    })
    token = login_res.get_json()["data"]["access_token"]

    # Token works before logout
    me_before = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_before.status_code == 200

    # Logout
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # Token must now be rejected as revoked
    me_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after.status_code == 401
    assert me_after.get_json()["error"]["code"] == "TOKEN_REVOKED"


def test_change_password(client, sample_users):
    """Verifies password change workflow and subsequent authentication with new password."""
    login_res = client.post("/api/auth/login", json={
        "email": "emp@test.com",
        "password": "EmpPass123!"
    })
    token = login_res.get_json()["data"]["access_token"]

    # Attempt with wrong current password
    bad_change = client.post("/api/auth/change-password", headers={"Authorization": f"Bearer {token}"}, json={
        "current_password": "WrongCurrentPassword!",
        "new_password": "NewSecretPass456!"
    })
    assert bad_change.status_code == 400

    # Successful change
    good_change = client.post("/api/auth/change-password", headers={"Authorization": f"Bearer {token}"}, json={
        "current_password": "EmpPass123!",
        "new_password": "NewSecretPass456!"
    })
    assert good_change.status_code == 200

    # Old password no longer works
    old_login = client.post("/api/auth/login", json={
        "email": "emp@test.com",
        "password": "EmpPass123!"
    })
    assert old_login.status_code == 401

    # New password works
    new_login = client.post("/api/auth/login", json={
        "email": "emp@test.com",
        "password": "NewSecretPass456!"
    })
    assert new_login.status_code == 200


def test_role_based_access_control(app, client, sample_users):
    """
    Verifies that @role_required, @admin_required, @hr_required, and @employee_required
    strictly enforce permissions at the controller boundary.
    """
    # Register the test RBAC blueprint
    app.register_blueprint(test_rbac_bp)

    admin_token = client.post("/api/auth/login", json={
        "email": "admin@test.com", "password": "AdminPass123!"
    }).get_json()["data"]["access_token"]

    hr_token = client.post("/api/auth/login", json={
        "email": "hr@test.com", "password": "HRPass123!"
    }).get_json()["data"]["access_token"]

    emp_token = client.post("/api/auth/login", json={
        "email": "emp@test.com", "password": "EmpPass123!"
    }).get_json()["data"]["access_token"]

    # 1. Admin accessing admin-only endpoint -> 200 OK
    res_admin_admin = client.get("/api/test-rbac/admin-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin_admin.status_code == 200

    # 2. HR accessing admin-only endpoint -> 403 Forbidden
    res_hr_admin = client.get("/api/test-rbac/admin-only", headers={"Authorization": f"Bearer {hr_token}"})
    assert res_hr_admin.status_code == 403
    assert res_hr_admin.get_json()["error"]["code"] == "FORBIDDEN"

    # 3. Employee accessing admin-only endpoint -> 403 Forbidden
    res_emp_admin = client.get("/api/test-rbac/admin-only", headers={"Authorization": f"Bearer {emp_token}"})
    assert res_emp_admin.status_code == 403

    # 4. HR accessing hr-only endpoint -> 200 OK
    res_hr_hr = client.get("/api/test-rbac/hr-only", headers={"Authorization": f"Bearer {hr_token}"})
    assert res_hr_hr.status_code == 200

    # 5. Admin accessing hr-only endpoint -> 200 OK (Admin has full access)
    res_admin_hr = client.get("/api/test-rbac/hr-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin_hr.status_code == 200

    # 6. Employee accessing hr-only endpoint -> 403 Forbidden
    res_emp_hr = client.get("/api/test-rbac/hr-only", headers={"Authorization": f"Bearer {emp_token}"})
    assert res_emp_hr.status_code == 403

    # 7. Employee accessing employee endpoint -> 200 OK
    res_emp_emp = client.get("/api/test-rbac/employee-all", headers={"Authorization": f"Bearer {emp_token}"})
    assert res_emp_emp.status_code == 200


def test_cli_admin_creation(app):
    """Verifies that the CLI create-admin command creates an admin and prevents duplicates."""
    runner = app.test_cli_runner()

    # Create new administrator
    res = runner.invoke(args=["create-admin", "--email", "superadmin@esms.com", "--password", "SecureMaster99!"])
    assert res.exit_code == 0
    assert "created successfully" in res.output

    # Try duplicate email
    res_dup = runner.invoke(args=["create-admin", "--email", "superadmin@esms.com", "--password", "AnotherPass!"])
    assert res_dup.exit_code == 0
    assert "already exists" in res_dup.output
