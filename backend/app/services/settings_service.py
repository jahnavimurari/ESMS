import json
from datetime import datetime, timezone, date
from decimal import Decimal
from app.extension_registry import db
from app.models.settings import (
    OrganizationSetting,
    Designation,
    Holiday,
    WorkShift,
    EmployeeCategory,
    UserPreference
)
from app.models.department import Department
from app.models.leave import LeaveType
from app.models.audit import AuditLog

class SettingsService:
    """Service handling organization profile, configuration, shifts, holidays, and user preferences."""

    # --------------------------------------------------------------------------
    # 1. Organization Settings
    # --------------------------------------------------------------------------
    @staticmethod
    def get_organization_settings():
        settings = OrganizationSetting.get_settings()
        return settings.to_dict()

    @staticmethod
    def update_organization_settings(data, user_id=None):
        settings = OrganizationSetting.get_settings()
        old_state = settings.to_dict()

        if "name" in data and data["name"]:
            settings.name = str(data["name"]).strip()
        if "logo_url" in data:
            settings.logo_url = data["logo_url"]
        if "address" in data:
            settings.address = data["address"]
        if "contact_email" in data:
            settings.contact_email = data["contact_email"]
        if "contact_phone" in data:
            settings.contact_phone = data["contact_phone"]
        if "website" in data:
            settings.website = data["website"]
        if "timezone" in data and data["timezone"]:
            settings.timezone = str(data["timezone"]).strip()
        if "date_format" in data and data["date_format"]:
            settings.date_format = str(data["date_format"]).strip()
        if "time_format" in data and data["time_format"]:
            settings.time_format = str(data["time_format"]).strip()
        if "working_days" in data:
            if isinstance(data["working_days"], list):
                settings.working_days = ",".join(data["working_days"])
            else:
                settings.working_days = str(data["working_days"])
        if "daily_working_hours" in data:
            hours = float(data["daily_working_hours"])
            if hours <= 0 or hours > 24:
                raise ValueError("Daily working hours must be between 0 and 24.")
            settings.daily_working_hours = Decimal(str(round(hours, 2)))
        if "fiscal_year_start_month" in data:
            month = int(data["fiscal_year_start_month"])
            if month < 1 or month > 12:
                raise ValueError("Fiscal year start month must be between 1 and 12.")
            settings.fiscal_year_start_month = month

        settings.updated_at = datetime.now(timezone.utc)

        # Audit log entry
        if user_id:
            audit = AuditLog(
                user_id=user_id,
                action="UPDATE_ORGANIZATION_SETTINGS",
                target_entity="ORGANIZATION",
                target_id=str(settings.id),
                previous_state=old_state,
                new_state=settings.to_dict(),
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(audit)

        db.session.commit()
        return settings.to_dict()

    # --------------------------------------------------------------------------
    # 2. Designation Management
    # --------------------------------------------------------------------------
    @staticmethod
    def list_designations(department_id=None, include_inactive=False):
        query = Designation.query
        if department_id:
            query = query.filter_by(department_id=department_id)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        designations = query.order_by(Designation.name.asc()).all()
        return [d.to_dict() for d in designations]

    @staticmethod
    def create_designation(data):
        name = str(data.get("name", "")).strip()
        code = str(data.get("code", "")).strip().upper()
        if not name or not code:
            raise ValueError("Designation name and code are required.")

        if Designation.query.filter((Designation.name == name) | (Designation.code == code)).first():
            raise ValueError(f"Designation with name '{name}' or code '{code}' already exists.")

        department_id = data.get("department_id")
        if department_id:
            dept = db.session.get(Department, department_id)
            if not dept:
                raise ValueError(f"Department ID {department_id} does not exist.")

        designation = Designation(
            name=name,
            code=code,
            department_id=department_id,
            description=data.get("description"),
            is_active=data.get("is_active", True)
        )
        db.session.add(designation)
        db.session.commit()
        return designation.to_dict()

    @staticmethod
    def update_designation(designation_id, data):
        designation = db.session.get(Designation, designation_id)
        if not designation:
            raise ValueError("Designation not found.")

        if "name" in data and data["name"]:
            name = str(data["name"]).strip()
            existing = Designation.query.filter(Designation.name == name, Designation.id != designation_id).first()
            if existing:
                raise ValueError(f"Designation name '{name}' is already taken.")
            designation.name = name

        if "code" in data and data["code"]:
            code = str(data["code"]).strip().upper()
            existing = Designation.query.filter(Designation.code == code, Designation.id != designation_id).first()
            if existing:
                raise ValueError(f"Designation code '{code}' is already taken.")
            designation.code = code

        if "department_id" in data:
            dept_id = data["department_id"]
            if dept_id is not None:
                if not Department.query.get(dept_id):
                    raise ValueError(f"Department ID {dept_id} does not exist.")
            designation.department_id = dept_id

        if "description" in data:
            designation.description = data["description"]
        if "is_active" in data:
            designation.is_active = bool(data["is_active"])

        db.session.commit()
        return designation.to_dict()

    @staticmethod
    def delete_designation(designation_id):
        designation = db.session.get(Designation, designation_id)
        if not designation:
            raise ValueError("Designation not found.")
        db.session.delete(designation)
        db.session.commit()
        return True

    # --------------------------------------------------------------------------
    # 3. Holiday Calendar
    # --------------------------------------------------------------------------
    @staticmethod
    def list_holidays(year=None):
        query = Holiday.query
        if year:
            query = query.filter_by(year=int(year))
        holidays = query.order_by(Holiday.holiday_date.asc()).all()
        return [h.to_dict() for h in holidays]

    @staticmethod
    def create_holiday(data):
        name = str(data.get("name", "")).strip()
        holiday_date_raw = data.get("holiday_date")
        if not name or not holiday_date_raw:
            raise ValueError("Holiday name and holiday_date are required.")

        if isinstance(holiday_date_raw, str):
            h_date = datetime.strptime(holiday_date_raw, "%Y-%m-%d").date()
        else:
            h_date = holiday_date_raw

        existing = Holiday.query.filter_by(holiday_date=h_date).first()
        if existing:
            raise ValueError(f"A holiday on {h_date} already exists ('{existing.name}').")

        holiday = Holiday(
            name=name,
            holiday_date=h_date,
            year=h_date.year,
            is_optional=data.get("is_optional", False),
            description=data.get("description")
        )
        db.session.add(holiday)
        db.session.commit()
        return holiday.to_dict()

    @staticmethod
    def update_holiday(holiday_id, data):
        holiday = db.session.get(Holiday, holiday_id)
        if not holiday:
            raise ValueError("Holiday not found.")

        if "name" in data and data["name"]:
            holiday.name = str(data["name"]).strip()
        if "holiday_date" in data and data["holiday_date"]:
            raw_date = data["holiday_date"]
            h_date = datetime.strptime(raw_date, "%Y-%m-%d").date() if isinstance(raw_date, str) else raw_date
            existing = Holiday.query.filter(Holiday.holiday_date == h_date, Holiday.id != holiday_id).first()
            if existing:
                raise ValueError(f"A holiday on {h_date} already exists.")
            holiday.holiday_date = h_date
            holiday.year = h_date.year
        if "is_optional" in data:
            holiday.is_optional = bool(data["is_optional"])
        if "description" in data:
            holiday.description = data["description"]

        db.session.commit()
        return holiday.to_dict()

    @staticmethod
    def delete_holiday(holiday_id):
        holiday = db.session.get(Holiday, holiday_id)
        if not holiday:
            raise ValueError("Holiday not found.")
        db.session.delete(holiday)
        db.session.commit()
        return True

    # --------------------------------------------------------------------------
    # 4. Work Shifts & Attendance Rules
    # --------------------------------------------------------------------------
    @staticmethod
    def list_shifts(include_inactive=False):
        query = WorkShift.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        shifts = query.order_by(WorkShift.name.asc()).all()
        # Seed default shift if none exist
        if not shifts and not include_inactive:
            default_shift = WorkShift(
                name="Regular Day Shift",
                code="REGULAR",
                start_time="09:00",
                end_time="18:00",
                grace_period_minutes=15,
                half_day_hours=Decimal("4.00"),
                full_day_hours=Decimal("8.00"),
                is_default=True,
                is_active=True
            )
            db.session.add(default_shift)
            db.session.commit()
            shifts = [default_shift]
        return [s.to_dict() for s in shifts]

    @staticmethod
    def create_shift(data):
        name = str(data.get("name", "")).strip()
        code = str(data.get("code", "")).strip().upper()
        start_time = str(data.get("start_time", "09:00")).strip()
        end_time = str(data.get("end_time", "18:00")).strip()

        if not name or not code:
            raise ValueError("Shift name and code are required.")

        if WorkShift.query.filter((WorkShift.name == name) | (WorkShift.code == code)).first():
            raise ValueError(f"Work shift with name '{name}' or code '{code}' already exists.")

        is_default = bool(data.get("is_default", False))
        if is_default:
            WorkShift.query.update({WorkShift.is_default: False})

        shift = WorkShift(
            name=name,
            code=code,
            start_time=start_time,
            end_time=end_time,
            grace_period_minutes=int(data.get("grace_period_minutes", 15)),
            half_day_hours=Decimal(str(data.get("half_day_hours", 4.0))),
            full_day_hours=Decimal(str(data.get("full_day_hours", 8.0))),
            is_default=is_default,
            is_active=data.get("is_active", True)
        )
        db.session.add(shift)
        db.session.commit()
        return shift.to_dict()

    @staticmethod
    def update_shift(shift_id, data):
        shift = db.session.get(WorkShift, shift_id)
        if not shift:
            raise ValueError("Work shift not found.")

        if "name" in data and data["name"]:
            name = str(data["name"]).strip()
            existing = WorkShift.query.filter(WorkShift.name == name, WorkShift.id != shift_id).first()
            if existing:
                raise ValueError(f"Shift name '{name}' already exists.")
            shift.name = name

        if "code" in data and data["code"]:
            code = str(data["code"]).strip().upper()
            existing = WorkShift.query.filter(WorkShift.code == code, WorkShift.id != shift_id).first()
            if existing:
                raise ValueError(f"Shift code '{code}' already exists.")
            shift.code = code

        if "start_time" in data:
            shift.start_time = str(data["start_time"]).strip()
        if "end_time" in data:
            shift.end_time = str(data["end_time"]).strip()
        if "grace_period_minutes" in data:
            shift.grace_period_minutes = int(data["grace_period_minutes"])
        if "half_day_hours" in data:
            shift.half_day_hours = Decimal(str(data["half_day_hours"]))
        if "full_day_hours" in data:
            shift.full_day_hours = Decimal(str(data["full_day_hours"]))
        if "is_default" in data:
            if bool(data["is_default"]):
                WorkShift.query.filter(WorkShift.id != shift_id).update({WorkShift.is_default: False})
            shift.is_default = bool(data["is_default"])
        if "is_active" in data:
            shift.is_active = bool(data["is_active"])

        db.session.commit()
        return shift.to_dict()

    @staticmethod
    def delete_shift(shift_id):
        shift = db.session.get(WorkShift, shift_id)
        if not shift:
            raise ValueError("Work shift not found.")
        db.session.delete(shift)
        db.session.commit()
        return True

    # --------------------------------------------------------------------------
    # 5. Employee Categories
    # --------------------------------------------------------------------------
    @staticmethod
    def list_categories(include_inactive=False):
        query = EmployeeCategory.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        categories = query.order_by(EmployeeCategory.name.asc()).all()
        # Seed standard categories if empty
        if not categories and not include_inactive:
            defaults = [
                ("FULL_TIME", "Full-Time Regular", "Standard full-time employment"),
                ("PART_TIME", "Part-Time", "Part-time scheduled hours"),
                ("CONTRACT", "Contractor", "External contract resource"),
                ("INTERN", "Intern", "Internship or trainee")
            ]
            for code, name, desc in defaults:
                cat = EmployeeCategory(code=code, name=name, description=desc, is_active=True)
                db.session.add(cat)
            db.session.commit()
            categories = EmployeeCategory.query.filter_by(is_active=True).all()
        return [c.to_dict() for c in categories]

    @staticmethod
    def create_category(data):
        code = str(data.get("code", "")).strip().upper()
        name = str(data.get("name", "")).strip()
        if not code or not name:
            raise ValueError("Category code and name are required.")

        if EmployeeCategory.query.filter_by(code=code).first():
            raise ValueError(f"Category code '{code}' already exists.")

        cat = EmployeeCategory(
            code=code,
            name=name,
            description=data.get("description"),
            is_active=data.get("is_active", True)
        )
        db.session.add(cat)
        db.session.commit()
        return cat.to_dict()

    @staticmethod
    def update_category(category_id, data):
        cat = db.session.get(EmployeeCategory, category_id)
        if not cat:
            raise ValueError("Employee category not found.")

        if "name" in data and data["name"]:
            cat.name = str(data["name"]).strip()
        if "code" in data and data["code"]:
            code = str(data["code"]).strip().upper()
            existing = EmployeeCategory.query.filter(EmployeeCategory.code == code, EmployeeCategory.id != category_id).first()
            if existing:
                raise ValueError(f"Category code '{code}' already exists.")
            cat.code = code
        if "description" in data:
            cat.description = data["description"]
        if "is_active" in data:
            cat.is_active = bool(data["is_active"])

        db.session.commit()
        return cat.to_dict()

    # --------------------------------------------------------------------------
    # 6. Leave Types & Policy Configuration
    # --------------------------------------------------------------------------
    @staticmethod
    def list_leave_policies(include_inactive=False):
        query = LeaveType.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        types = query.order_by(LeaveType.name.asc()).all()
        return [t.to_dict() for t in types]

    @staticmethod
    def update_leave_policy(leave_type_id, data):
        leave_type = db.session.get(LeaveType, leave_type_id)
        if not leave_type:
            raise ValueError("Leave type policy not found.")

        if "name" in data and data["name"]:
            leave_type.name = str(data["name"]).strip()
        if "description" in data:
            leave_type.description = data["description"]
        if "days_per_year" in data:
            days = int(data["days_per_year"])
            if days < 0:
                raise ValueError("Days per year cannot be negative.")
            leave_type.days_per_year = days
        if "is_paid" in data:
            leave_type.is_paid = bool(data["is_paid"])
        if "is_active" in data:
            leave_type.is_active = bool(data["is_active"])

        db.session.commit()
        return leave_type.to_dict()

    # --------------------------------------------------------------------------
    # 7. User Preferences
    # --------------------------------------------------------------------------
    @staticmethod
    def get_user_preferences(user_id):
        pref = UserPreference.get_or_create(user_id)
        return pref.to_dict()

    @staticmethod
    def update_user_preferences(user_id, data):
        pref = UserPreference.get_or_create(user_id)
        if "email_notifications" in data:
            pref.email_notifications = bool(data["email_notifications"])
        if "in_app_notifications" in data:
            pref.in_app_notifications = bool(data["in_app_notifications"])
        if "theme" in data and data["theme"]:
            pref.theme = str(data["theme"]).strip().upper()
        if "date_format" in data and data["date_format"]:
            pref.date_format = str(data["date_format"]).strip()
        if "time_format" in data and data["time_format"]:
            pref.time_format = str(data["time_format"]).strip()
        if "dashboard_layout" in data:
            pref.dashboard_layout = str(data["dashboard_layout"])

        pref.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return pref.to_dict()
