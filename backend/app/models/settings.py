from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import Integer, String, Text, Boolean, DateTime, Date, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

class OrganizationSetting(db.Model):
    __tablename__ = "organization_settings"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(150), default="ESMS Enterprise", nullable=False)
    logo_url = db.Column(String(500), nullable=True)
    address = db.Column(Text, nullable=True)
    contact_email = db.Column(String(255), nullable=True)
    contact_phone = db.Column(String(50), nullable=True)
    website = db.Column(String(255), nullable=True)
    timezone = db.Column(String(50), default="UTC", nullable=False)
    date_format = db.Column(String(30), default="YYYY-MM-DD", nullable=False)
    time_format = db.Column(String(20), default="24H", nullable=False)
    working_days = db.Column(String(100), default="MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY", nullable=False)
    daily_working_hours = db.Column(Numeric(4, 2), default=8.00, nullable=False)
    fiscal_year_start_month = db.Column(Integer, default=1, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    @classmethod
    def get_settings(cls):
        """Returns the singleton organization settings instance, creating default if absent."""
        settings = cls.query.first()
        if not settings:
            settings = cls(
                name="ESMS Enterprise",
                timezone="UTC",
                date_format="YYYY-MM-DD",
                time_format="24H",
                working_days="MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY",
                daily_working_hours=8.00,
                fiscal_year_start_month=1
            )
            db.session.add(settings)
            db.session.commit()
        return settings

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "logo_url": self.logo_url,
            "address": self.address,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "website": self.website,
            "timezone": self.timezone,
            "date_format": self.date_format,
            "time_format": self.time_format,
            "working_days": [d.strip() for d in self.working_days.split(",") if d.strip()] if self.working_days else [],
            "daily_working_hours": float(self.daily_working_hours) if self.daily_working_hours is not None else 8.0,
            "fiscal_year_start_month": self.fiscal_year_start_month,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<OrganizationSetting {self.name}>"


class Designation(db.Model):
    __tablename__ = "designations"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(100), unique=True, nullable=False, index=True)
    code = db.Column(String(30), unique=True, nullable=False, index=True)
    department_id = db.Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    description = db.Column(Text, nullable=True)
    is_active = db.Column(Boolean, default=True, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    department = db.relationship("Department")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Designation {self.code} - {self.name}>"


class Holiday(db.Model):
    __tablename__ = "holidays"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(150), nullable=False)
    holiday_date = db.Column(Date, nullable=False, unique=True, index=True)
    year = db.Column(Integer, nullable=False, index=True)
    is_optional = db.Column(Boolean, default=False, nullable=False)
    description = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "holiday_date": self.holiday_date.isoformat() if self.holiday_date else None,
            "year": self.year,
            "is_optional": self.is_optional,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Holiday {self.holiday_date} - {self.name}>"


class WorkShift(db.Model):
    __tablename__ = "work_shifts"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(100), unique=True, nullable=False)
    code = db.Column(String(30), unique=True, nullable=False)
    start_time = db.Column(String(10), default="09:00", nullable=False)
    end_time = db.Column(String(10), default="18:00", nullable=False)
    grace_period_minutes = db.Column(Integer, default=15, nullable=False)
    half_day_hours = db.Column(Numeric(4, 2), default=4.00, nullable=False)
    full_day_hours = db.Column(Numeric(4, 2), default=8.00, nullable=False)
    is_default = db.Column(Boolean, default=False, nullable=False)
    is_active = db.Column(Boolean, default=True, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "grace_period_minutes": self.grace_period_minutes,
            "half_day_hours": float(self.half_day_hours) if self.half_day_hours is not None else 4.0,
            "full_day_hours": float(self.full_day_hours) if self.full_day_hours is not None else 8.0,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<WorkShift {self.code} - {self.name}>"


class EmployeeCategory(db.Model):
    __tablename__ = "employee_categories"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    code = db.Column(String(30), unique=True, nullable=False)
    name = db.Column(String(100), nullable=False)
    description = db.Column(Text, nullable=True)
    is_active = db.Column(Boolean, default=True, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<EmployeeCategory {self.code} - {self.name}>"


class UserPreference(db.Model):
    __tablename__ = "user_preferences"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    email_notifications = db.Column(Boolean, default=True, nullable=False)
    in_app_notifications = db.Column(Boolean, default=True, nullable=False)
    theme = db.Column(String(20), default="LIGHT", nullable=False)
    date_format = db.Column(String(30), default="YYYY-MM-DD", nullable=False)
    time_format = db.Column(String(20), default="24H", nullable=False)
    dashboard_layout = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User")

    @classmethod
    def get_or_create(cls, user_id):
        """Returns the user preferences for user_id, initializing defaults if missing."""
        pref = cls.query.filter_by(user_id=user_id).first()
        if not pref:
            pref = cls(
                user_id=user_id,
                email_notifications=True,
                in_app_notifications=True,
                theme="LIGHT",
                date_format="YYYY-MM-DD",
                time_format="24H"
            )
            db.session.add(pref)
            db.session.commit()
        return pref

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "email_notifications": self.email_notifications,
            "in_app_notifications": self.in_app_notifications,
            "theme": self.theme,
            "date_format": self.date_format,
            "time_format": self.time_format,
            "dashboard_layout": self.dashboard_layout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<UserPreference user={self.user_id}>"

