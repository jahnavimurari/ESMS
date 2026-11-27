import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.extension_registry import db
from app.models.notification import Notification
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService

@pytest.fixture
def setup_notification_fixtures(app, sample_users):
    """Sets up test users and employees for notification testing."""
    with app.app_context():
        eng = Department(name="Engineering", code="ENG", description="Platform Tech")
        db.session.add(eng)
        db.session.commit()

        user_emp1 = User.query.filter_by(email="emp@test.com").first()
        emp1 = Employee(
            user_id=user_emp1.id,
            employee_code="EMP-NOTIF-01",
            first_name="Alice",
            last_name="Smith",
            department_id=eng.id,
            designation="Engineer",
            status="ACTIVE"
        )

        user_emp2 = User(email="emp2@test.com", role="EMPLOYEE", is_active=True)
        user_emp2.set_password("Emp2Pass123!")
        db.session.add(user_emp2)
        db.session.flush()

        emp2 = Employee(
            user_id=user_emp2.id,
            employee_code="EMP-NOTIF-02",
            first_name="Bob",
            last_name="Jones",
            department_id=eng.id,
            designation="Engineer",
            status="ACTIVE"
        )
        db.session.add_all([emp1, emp2])
        db.session.commit()

        return {
            "emp1_user_id": str(user_emp1.id),
            "emp2_user_id": str(user_emp2.id)
        }

@pytest.fixture
def auth_tokens_notif(client, setup_notification_fixtures):
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
# Phase 7: Notifications & Reminders Tests
# ==============================================================================

def test_notification_creation_and_listing(app, client, auth_tokens_notif, setup_notification_fixtures):
    """Verifies in-app notification creation and listing for the recipient."""
    emp1_uid = setup_notification_fixtures["emp1_user_id"]
    with app.app_context():
        NotificationService.create_notification(
            user_id=emp1_uid,
            title="Check-in Reminder",
            message="Please remember to clock in for your morning shift.",
            category="ATTENDANCE",
            priority="HIGH",
            action_url="/attendance"
        )

    res = client.get("/api/notifications", headers={"Authorization": f"Bearer {auth_tokens_notif['emp1']}"})
    assert res.status_code == 200
    data = res.json["data"]
    assert data["total"] >= 1
    assert data["unread_count"] >= 1
    titles = [n["title"] for n in data["notifications"]]
    assert "Check-in Reminder" in titles

def test_unread_count_badge_endpoint(app, client, auth_tokens_notif, setup_notification_fixtures):
    """Verifies that unread-count returns a valid numeric badge count."""
    emp1_uid = setup_notification_fixtures["emp1_user_id"]
    with app.app_context():
        NotificationService.create_notification(
            user_id=emp1_uid,
            title="Badge Test Alert",
            message="Testing unread count badge counter."
        )

    res = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {auth_tokens_notif['emp1']}"})
    assert res.status_code == 200
    assert "unread_count" in res.json["data"]
    assert res.json["data"]["unread_count"] >= 1

def test_employee_data_isolation(app, client, auth_tokens_notif, setup_notification_fixtures):
    """Verifies that Employee 2 cannot see Employee 1's notifications."""
    emp1_uid = setup_notification_fixtures["emp1_user_id"]
    with app.app_context():
        NotificationService.create_notification(
            user_id=emp1_uid,
            title="Confidential Leave Approval",
            message="Your leave request #101 was approved.",
            category="LEAVE"
        )

    # Employee 2 queries their notifications
    res2 = client.get("/api/notifications", headers={"Authorization": f"Bearer {auth_tokens_notif['emp2']}"})
    assert res2.status_code == 200
    emp2_titles = [n["title"] for n in res2.json["data"]["notifications"]]
    assert "Confidential Leave Approval" not in emp2_titles

def test_mark_as_read_and_read_all(client, auth_tokens_notif):
    """Verifies marking single notification as read and mark-all-as-read."""
    # List notifications to get an ID
    res = client.get("/api/notifications?unread_only=true", headers={"Authorization": f"Bearer {auth_tokens_notif['emp1']}"})
    assert res.status_code == 200
    items = res.json["data"]["notifications"]
    if items:
        notif_id = items[0]["id"]
        res_read = client.patch(f"/api/notifications/{notif_id}/read", headers={"Authorization": f"Bearer {auth_tokens_notif['emp1']}"})
        assert res_read.status_code == 200
        assert res_read.json["data"]["is_read"] is True

    # Mark all read
    res_all = client.patch("/api/notifications/read-all", headers={"Authorization": f"Bearer {auth_tokens_notif['emp1']}"})
    assert res_all.status_code == 200

    # Unread count should now be 0
    res_badge = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {auth_tokens_notif['emp1']}"})
    assert res_badge.json["data"]["unread_count"] == 0

def test_delete_notification(app, client, auth_tokens_notif, setup_notification_fixtures):
    """Verifies deleting an in-app notification owned by the caller."""
    emp1_uid = setup_notification_fixtures["emp1_user_id"]
    with app.app_context():
        n = NotificationService.create_notification(
            user_id=emp1_uid,
            title="Task Review Completed",
            message="Your submitted task code was reviewed.",
            category="TASK"
        )
        notif_id = n.id

    res_del = client.delete(f"/api/notifications/{notif_id}", headers={"Authorization": f"Bearer {auth_tokens_notif['emp1']}"})
    assert res_del.status_code == 200

    # Employee 2 attempting to delete Employee 1's notification gets 404
    res_bad_del = client.delete(f"/api/notifications/{notif_id}", headers={"Authorization": f"Bearer {auth_tokens_notif['emp2']}"})
    assert res_bad_del.status_code == 404

def test_duplicate_notification_prevention(app, setup_notification_fixtures):
    """Verifies exact same notification within 10 minutes returns existing record."""
    emp1_uid = setup_notification_fixtures["emp1_user_id"]
    with app.app_context():
        n1 = NotificationService.create_notification(
            user_id=emp1_uid,
            title="Performance Review Open",
            message="Annual cycle 2026 self-assessment is open.",
            category="PERFORMANCE"
        )
        n2 = NotificationService.create_notification(
            user_id=emp1_uid,
            title="Performance Review Open",
            message="Annual cycle 2026 self-assessment is open.",
            category="PERFORMANCE"
        )
        assert n1.id == n2.id

def test_admin_hr_announcement_broadcast(client, auth_tokens_notif):
    """Verifies Admin can broadcast an announcement to all active users."""
    payload = {
        "title": "Townhall Scheduled",
        "message": "All-hands company townhall this Friday at 4 PM.",
        "priority": "HIGH"
    }
    res_admin = client.post("/api/notifications/announcements", json=payload, headers={"Authorization": f"Bearer {auth_tokens_notif['admin']}"})
    assert res_admin.status_code == 201
    assert res_admin.json["data"]["recipients_count"] >= 2

    # Regular employee trying to broadcast receives 403 Forbidden
    res_emp = client.post("/api/notifications/announcements", json=payload, headers={"Authorization": f"Bearer {auth_tokens_notif['emp1']}"})
    assert res_emp.status_code == 403

def test_email_failure_does_not_break_notification_creation(app, setup_notification_fixtures):
    """Verifies unconfigured/failed SMTP does not abort notification creation."""
    emp1_uid = setup_notification_fixtures["emp1_user_id"]
    with app.app_context():
        notif = NotificationService.create_notification(
            user_id=emp1_uid,
            title="Offline Notification",
            message="SMTP is offline but database notification must succeed.",
            send_email=True
        )
        assert notif is not None
        assert notif.id is not None

def test_unauthenticated_notifications_rejected(client):
    """Verifies that unauthenticated notification requests return 401."""
    assert client.get("/api/notifications").status_code == 401
    assert client.get("/api/notifications/unread-count").status_code == 401
    assert client.patch("/api/notifications/1/read").status_code == 401
    assert client.patch("/api/notifications/read-all").status_code == 401
    assert client.delete("/api/notifications/1").status_code == 401
    assert client.post("/api/notifications/announcements", json={}).status_code == 401
