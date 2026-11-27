import uuid
from datetime import datetime, timezone, date, time
from sqlalchemy import func, and_, or_
from app.extension_registry import db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User

# Configurable attendance thresholds (defaults)
# Shift starting threshold: e.g. 09:30 AM is standard start, late if checked in after 09:30 AM for Shift 1
DEFAULT_LATE_THRESHOLD_HOUR = 9
DEFAULT_LATE_THRESHOLD_MINUTE = 30
# Duration thresholds in hours
HALF_DAY_MIN_HOURS = 4.0
FULL_DAY_MIN_HOURS = 8.0

class AttendanceService:
    """Encapsulates check-in, checkout, multi-shift calculations and corrections."""

    @staticmethod
    def get_employee_for_user(user_id):
        """Resolves employee profile for a given user or raises ValueError."""
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            raise ValueError("Invalid user identifier.")

        employee = Employee.query.filter_by(user_id=u_uuid).first()
        if not employee:
            raise ValueError("No employee record associated with this user account.")
        if employee.status != "ACTIVE":
            raise PermissionError(f"Employee account is currently {employee.status}. Attendance is not permitted.")
        return employee

    @staticmethod
    def get_active_session(employee_id):
        """Finds any active attendance session (check_out is NULL) for the employee."""
        return Attendance.query.filter_by(employee_id=employee_id, check_out=None).first()

    @staticmethod
    def check_in(user_id, notes=None):
        """
        Starts an attendance session for the authenticated user's employee profile.
        Determines the work date, assigns next shift number, and creates the record.
        """
        employee = AttendanceService.get_employee_for_user(user_id)
        now_utc = datetime.now(timezone.utc)
        today = now_utc.date()

        # Enforce single active session rule
        active = AttendanceService.get_active_session(employee.id)
        if active:
            raise ValueError(f"You already have an active shift session (Shift {active.shift_number} started at {active.check_in.strftime('%H:%M:%S UTC')}). You must check out before starting a new shift.")

        # Determine next shift number for today
        latest_shift = (
            db.session.query(func.max(Attendance.shift_number))
            .filter_by(employee_id=employee.id, work_date=today)
            .scalar()
        )
        next_shift_number = (latest_shift or 0) + 1

        # Determine initial status
        # For Shift 1, evaluate late arrival based on configured threshold
        status = "PRESENT"
        if next_shift_number == 1:
            late_time = time(DEFAULT_LATE_THRESHOLD_HOUR, DEFAULT_LATE_THRESHOLD_MINUTE)
            if now_utc.time() > late_time:
                status = "LATE"

        session = Attendance(
            employee_id=employee.id,
            work_date=today,
            shift_number=next_shift_number,
            check_in=now_utc,
            check_out=None,
            total_hours=0.00,
            status=status,
            notes=notes
        )
        try:
            db.session.add(session)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # If concurrent check-in hit the partial unique index or unique shift constraint
            if "uq_att_active_session" in str(e).lower() or "unique constraint" in str(e).lower():
                raise ValueError("An active shift session is already running for this employee.")
            raise

        return session.to_dict()

    @staticmethod
    def check_out(user_id, notes=None):
        """
        Ends the active attendance session for the authenticated user's employee profile.
        Calculates worked hours and updates status.
        """
        employee = AttendanceService.get_employee_for_user(user_id)
        active = AttendanceService.get_active_session(employee.id)

        if not active:
            raise ValueError("No active attendance session found to check out from.")

        now_utc = datetime.now(timezone.utc)
        check_in_time = active.check_in
        if check_in_time and check_in_time.tzinfo is None:
            check_in_time = check_in_time.replace(tzinfo=timezone.utc)

        # Enforce check_out > check_in
        if now_utc <= check_in_time:
            raise ValueError("Checkout timestamp must be strictly later than check-in timestamp.")

        # Calculate duration in hours
        duration_seconds = (now_utc - check_in_time).total_seconds()
        worked_hours = round(duration_seconds / 3600.0, 2)

        active.check_out = now_utc
        active.total_hours = worked_hours
        if notes:
            active.notes = f"{active.notes} | {notes}" if active.notes else notes

        # Calculate daily cumulative hours
        prior_shifts = (
            Attendance.query
            .filter(Attendance.employee_id == employee.id, Attendance.work_date == active.work_date, Attendance.id != active.id)
            .all()
        )
        prior_completed_hours = sum(float(s.total_hours) for s in prior_shifts)
        total_day_hours = prior_completed_hours + worked_hours

        # Determine shift status:
        # If total cumulative day hours reach full day (>= 8.0) or standard work day, mark PRESENT.
        # If prior shifts were marked HALF_DAY because cumulative hours were initially < 4.0,
        # but now total_day_hours >= 4.0 (or >= 8.0), update earlier shifts so employee is not penalized.
        if total_day_hours >= HALF_DAY_MIN_HOURS:
            if active.status != "LATE":
                active.status = "PRESENT"
            for prev in prior_shifts:
                if prev.status == "HALF_DAY":
                    prev.status = "PRESENT"
        else:
            if active.status != "LATE":
                active.status = "HALF_DAY"

        db.session.commit()
        return active.to_dict()

    @staticmethod
    def get_my_attendance(user_id, start_date=None, end_date=None, limit=50, offset=0):
        """Retrieves attendance history and today's status for the calling employee."""
        employee = AttendanceService.get_employee_for_user(user_id)
        query = Attendance.query.filter_by(employee_id=employee.id)

        if start_date:
            query = query.filter(Attendance.work_date >= start_date)
        if end_date:
            query = query.filter(Attendance.work_date <= end_date)

        total_count = query.count()
        records = query.order_by(Attendance.work_date.desc(), Attendance.shift_number.desc()).offset(offset).limit(limit).all()

        today = datetime.now(timezone.utc).date()
        today_records = Attendance.query.filter_by(employee_id=employee.id, work_date=today).order_by(Attendance.shift_number.asc()).all()
        active_session = AttendanceService.get_active_session(employee.id)

        today_hours = sum(float(r.total_hours) for r in today_records)

        return {
            "total": total_count,
            "items": [r.to_dict() for r in records],
            "today": {
                "work_date": today.isoformat(),
                "has_active_session": active_session is not None,
                "active_session": active_session.to_dict() if active_session else None,
                "shifts_count": len(today_records),
                "today_hours": round(today_hours, 2),
                "shifts": [r.to_dict() for r in today_records]
            }
        }

    @staticmethod
    def get_attendance_by_id(attendance_id):
        """Retrieves a single attendance record by primary key."""
        record = db.session.get(Attendance, attendance_id)
        if not record:
            raise ValueError(f"Attendance record {attendance_id} not found.")
        return record

    @staticmethod
    def list_attendance(search=None, department_id=None, status=None, work_date=None, start_date=None, end_date=None, limit=50, offset=0):
        """HR/Admin query to filter and list organizational attendance."""
        query = Attendance.query.join(Employee, Attendance.employee_id == Employee.id).outerjoin(User, Employee.user_id == User.id)

        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        if status and status.strip():
            query = query.filter(Attendance.status == status.strip().upper())

        def parse_date(d):
            if isinstance(d, str):
                try:
                    return datetime.strptime(d.strip(), "%Y-%m-%d").date()
                except ValueError:
                    return None
            elif isinstance(d, datetime):
                return d.date()
            return d

        parsed_work_date = parse_date(work_date)
        if parsed_work_date:
            query = query.filter(Attendance.work_date == parsed_work_date)
        else:
            parsed_start = parse_date(start_date)
            parsed_end = parse_date(end_date)
            if parsed_start:
                query = query.filter(Attendance.work_date >= parsed_start)
            if parsed_end:
                query = query.filter(Attendance.work_date <= parsed_end)

        total_count = query.count()
        records = query.order_by(Attendance.work_date.desc(), Attendance.check_in.desc()).offset(offset).limit(limit).all()

        return {
            "total": total_count,
            "items": [r.to_dict() for r in records],
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def get_summary(work_date=None, department_id=None):
        """Calculates daily organizational attendance stats."""
        if isinstance(work_date, str):
            try:
                target_date = datetime.strptime(work_date.strip(), "%Y-%m-%d").date()
            except ValueError:
                target_date = datetime.now(timezone.utc).date()
        elif isinstance(work_date, datetime):
            target_date = work_date.date()
        elif isinstance(work_date, date):
            target_date = work_date
        else:
            target_date = datetime.now(timezone.utc).date()

        # Base active employees query
        emp_query = Employee.query.filter_by(status="ACTIVE")
        if department_id:
            emp_query = emp_query.filter_by(department_id=department_id)
        total_employees = emp_query.count()

        # Attendance records for target date
        att_query = Attendance.query.join(Employee, Attendance.employee_id == Employee.id).filter(Attendance.work_date == target_date)
        if department_id:
            att_query = att_query.filter(Employee.department_id == department_id)
        records = att_query.all()

        # Distinct employees who checked in today
        checked_in_emp_ids = set(r.employee_id for r in records)
        present_count = len(checked_in_emp_ids)
        late_count = len(set(r.employee_id for r in records if r.status == "LATE"))
        half_day_count = len(set(r.employee_id for r in records if r.status == "HALF_DAY"))
        active_shifts = sum(1 for r in records if r.check_out is None)
        total_hours = sum(float(r.total_hours) for r in records)
        absent_count = max(0, total_employees - present_count)

        return {
            "work_date": target_date.isoformat(),
            "total_employees": total_employees,
            "present_count": present_count,
            "absent_count": absent_count,
            "late_count": late_count,
            "half_day_count": half_day_count,
            "active_shifts_now": active_shifts,
            "total_hours_logged": round(total_hours, 2),
            "attendance_rate": round((present_count / total_employees * 100), 1) if total_employees > 0 else 0.0
        }

    @staticmethod
    def correct_attendance(attendance_id, data, admin_user_id):
        """Performs authorized correction on an attendance record with audit trail."""
        record = AttendanceService.get_attendance_by_id(attendance_id)

        if "check_in" in data and data["check_in"]:
            record.check_in = data["check_in"]

        check_in_time = record.check_in
        if check_in_time and check_in_time.tzinfo is None:
            check_in_time = check_in_time.replace(tzinfo=timezone.utc)

        if "check_out" in data:
            check_out_time = data["check_out"]
            if check_out_time:
                if check_out_time.tzinfo is None:
                    check_out_time = check_out_time.replace(tzinfo=timezone.utc)
                if check_out_time <= check_in_time:
                    raise ValueError("Checkout timestamp must be strictly later than check-in.")
            record.check_out = data["check_out"]

        if "status" in data and data["status"]:
            record.status = data["status"]

        if "total_hours" in data and data["total_hours"] is not None:
            record.total_hours = round(float(data["total_hours"]), 2)
        elif record.check_out:
            # Recalculate duration
            rec_out = record.check_out
            if rec_out and rec_out.tzinfo is None:
                rec_out = rec_out.replace(tzinfo=timezone.utc)
            sec = (rec_out - check_in_time).total_seconds()
            record.total_hours = round(sec / 3600.0, 2)

        if "notes" in data and data["notes"]:
            record.notes = f"{record.notes or ''} [Corrected: {data['notes']}]".strip()

        record.is_corrected = True
        record.corrected_by = admin_user_id

        db.session.commit()
        return record.to_dict()
