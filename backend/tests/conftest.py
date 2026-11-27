import os
import pytest
from app import create_app
from app.extension_registry import db
from app.models.user import User

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_users(app):
    """Creates sample Admin, HR, and Employee users for testing."""
    with app.app_context():
        admin = User(email="admin@test.com", role="ADMIN", is_active=True)
        admin.set_password("AdminPass123!")

        hr = User(email="hr@test.com", role="HR", is_active=True)
        hr.set_password("HRPass123!")

        employee = User(email="emp@test.com", role="EMPLOYEE", is_active=True)
        employee.set_password("EmpPass123!")

        inactive = User(email="inactive@test.com", role="EMPLOYEE", is_active=False)
        inactive.set_password("InactivePass123!")

        db.session.add_all([admin, hr, employee, inactive])
        db.session.commit()

        return {
            "admin": admin,
            "hr": hr,
            "employee": employee,
            "inactive": inactive
        }
