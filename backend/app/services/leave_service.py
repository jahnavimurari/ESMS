import uuid
from datetime import datetime, timezone, date, timedelta
from sqlalchemy import or_, and_, func, extract
from app.extension_registry import db
from app.models.leave import LeaveRequest, LeaveType
from app.models.employee import Employee
from app.models.user import User

class LeaveService:
    """Service encapsulating leave policies, balance calculations, workflows, and overlap verification."""

    # --------------------------------------------------------------------------
    # Leave Type Management
    # --------------------------------------------------------------------------
    @staticmethod
    def ensure_default_leave_types():
        """Seeds default standard leave types if table is empty."""
        if LeaveType.query.count() == 0:
            defaults = [
                LeaveType(code="CL", name="Casual Leave", description="Short-term planned leave", days_per_year=12, is_paid=True, is_active=True),
                LeaveType(code="SL", name="Sick Leave", description="Medical and recovery leave", days_per_year=10, is_paid=True, is_active=True),
                LeaveType(code="EL", name="Earned Leave", description="Annual vacation entitlement", days_per_year=15, is_paid=True, is_active=True),
                LeaveType(code="UL", name="Unpaid Leave", description="Leave without pay / sabbatical", days_per_year=0, is_paid=False, is_active=True),
            ]
            db.session.add_all(defaults)
            db.session.commit()

    @staticmethod
    def list_leave_types(include_inactive=False):
        LeaveService.ensure_default_leave_types()
        query = LeaveType.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        types = query.order_by(LeaveType.id.asc()).all()
        return [t.to_dict() for t in types]

    @staticmethod
    def get_leave_type_by_id(type_id: int):
        lt = db.session.get(LeaveType, type_id)
        if not lt:
            raise ValueError(f"Leave type with ID {type_id} does not exist.")
        return lt

    @staticmethod
    def create_leave_type(data: dict):
        code = data["code"].strip().upper()
        name = data["name"].strip()
        if LeaveType.query.filter_by(code=code).first():
            raise ValueError(f"Leave type with code '{code}' already exists.")

        lt = LeaveType(
            code=code,
            name=name,
            description=data.get("description"),
            days_per_year=data.get("days_per_year", 12),
            is_paid=data.get("is_paid", True),
            is_active=data.get("is_active", True)
        )
        db.session.add(lt)
        db.session.commit()
        return lt.to_dict()

    @staticmethod
    def update_leave_type(type_id: int, data: dict):
        lt = LeaveService.get_leave_type_by_id(type_id)
        if "name" in data and data["name"]:
            lt.name = data["name"].strip()
        if "description" in data:
            lt.description = data["description"]
        if "days_per_year" in data and data["days_per_year"] is not None:
            lt.days_per_year = data["days_per_year"]
        if "is_paid" in data and data["is_paid"] is not None:
            lt.is_paid = data["is_paid"]
        if "is_active" in data and data["is_active"] is not None:
            lt.is_active = data["is_active"]
        db.session.commit()
        return lt.to_dict()

    # --------------------------------------------------------------------------
    # Helper: Resolve Employee from User ID
    # --------------------------------------------------------------------------
    @staticmethod
    def get_employee_for_user(user_id):
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            raise ValueError("Invalid user identifier.")

        employee = Employee.query.filter_by(user_id=u_uuid).first()
        if not employee:
            raise ValueError("No employee record associated with this user account.")
        if employee.status != "ACTIVE":
            raise PermissionError(f"Employee account is currently {employee.status}. Leave operations are not permitted.")
        return employee

    # --------------------------------------------------------------------------
    # Leave Application & Modification
    # --------------------------------------------------------------------------
    @staticmethod
    def calculate_requested_days(start_date: date, end_date: date):
        """Calculates total consecutive calendar days inclusive."""
        if end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")
        delta = (end_date - start_date).days + 1
        return float(delta)

    @staticmethod
    def apply_leave(user_id, leave_type_id: int, start_date: date, end_date: date, reason: str):
        """Validates boundaries, checks overlap, locks employee, and registers PENDING request."""
        employee = LeaveService.get_employee_for_user(user_id)
        leave_type = LeaveService.get_leave_type_by_id(leave_type_id)
        if not leave_type.is_active:
            raise ValueError(f"Leave type '{leave_type.name}' is currently inactive.")

        total_days = LeaveService.calculate_requested_days(start_date, end_date)

        emp_lock = LeaveRequest.get_employee_thread_lock(employee.id)
        with emp_lock:
            # Call LeaveRequest's transactional validator & lock
            new_request = LeaveRequest.validate_and_submit(
                session=db.session,
                employee_id=employee.id,
                leave_type_id=leave_type.id,
                start_date=start_date,
                end_date=end_date,
                total_days=total_days,
                reason=reason.strip()
            )
            db.session.commit()
            return new_request.to_dict()

    @staticmethod
    def update_pending_leave(leave_id: int, user_id, data: dict):
        """Allows an employee to edit their own request if it is still PENDING."""
        employee = LeaveService.get_employee_for_user(user_id)
        req = db.session.get(LeaveRequest, leave_id)
        if not req:
            raise ValueError(f"Leave request {leave_id} not found.")

        if req.employee_id != employee.id:
            raise PermissionError("You can only modify your own leave request.")

        if req.status != "PENDING":
            raise ValueError(f"Cannot edit request in {req.status} status. Only PENDING requests can be edited.")

        start_date = data.get("start_date") or req.start_date
        end_date = data.get("end_date") or req.end_date

        if end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")

        if "leave_type_id" in data and data["leave_type_id"]:
            LeaveService.get_leave_type_by_id(data["leave_type_id"])
            req.leave_type_id = data["leave_type_id"]

        emp_lock = LeaveRequest.get_employee_thread_lock(employee.id)
        with emp_lock:
            # Check overlap excluding self
            overlapping = LeaveRequest.check_overlap(
                session=db.session,
                employee_id=employee.id,
                start_date=start_date,
                end_date=end_date,
                exclude_id=req.id
            )
            if overlapping:
                raise ValueError(
                    f"An overlapping {overlapping.status.lower()} leave request already exists "
                    f"from {overlapping.start_date} to {overlapping.end_date}."
                )

            req.start_date = start_date
            req.end_date = end_date
            req.total_days = LeaveService.calculate_requested_days(start_date, end_date)
            if "reason" in data and data["reason"]:
                req.reason = data["reason"].strip()

            db.session.commit()
            return req.to_dict()

    # --------------------------------------------------------------------------
    # Approval, Rejection, Cancellation Workflows
    # --------------------------------------------------------------------------
    @staticmethod
    def approve_leave(leave_id: int, reviewer_user_id, comments: str = None):
        """Approves a PENDING request (HR or Admin). Prevents duplicate approval with row-level lock and thread synchronization."""
        req_lock = LeaveRequest.get_employee_thread_lock(f"leave_req_{leave_id}")
        with req_lock:
            db.session.expire_all()

            # Apply row-level lock on PostgreSQL
            bind = db.session.get_bind()
            query = LeaveRequest.query.filter_by(id=leave_id)
            if bind and bind.dialect.name == "postgresql":
                query = query.with_for_update()
            req = query.first()

            if not req:
                raise ValueError(f"Leave request {leave_id} not found.")

            if req.status == "APPROVED":
                raise ValueError("This leave request is already approved.")
            if req.status != "PENDING":
                raise ValueError(f"Cannot approve request with status '{req.status}'. Only PENDING requests can be approved.")

            # Re-check overlap before approving to ensure no concurrent conflicts
            overlapping = LeaveRequest.check_overlap(
                session=db.session,
                employee_id=req.employee_id,
                start_date=req.start_date,
                end_date=req.end_date,
                exclude_id=req.id
            )
            if overlapping and overlapping.status == "APPROVED":
                raise ValueError(
                    f"Conflict detected: an approved leave already exists from {overlapping.start_date} to {overlapping.end_date}."
                )

            req.status = "APPROVED"
            req.reviewed_by = reviewer_user_id
            req.reviewer_comments = comments
            req.reviewed_at = datetime.now(timezone.utc)

            db.session.commit()
            return req.to_dict()

    @staticmethod
    def reject_leave(leave_id: int, reviewer_user_id, comments: str = None):
        """Rejects a PENDING request (HR or Admin)."""
        req_lock = LeaveRequest.get_employee_thread_lock(f"leave_req_{leave_id}")
        with req_lock:
            db.session.expire_all()
            req = db.session.get(LeaveRequest, leave_id)
            if not req:
                raise ValueError(f"Leave request {leave_id} not found.")

            if req.status != "PENDING":
                raise ValueError(f"Cannot reject request with status '{req.status}'. Only PENDING requests can be rejected.")

            req.status = "REJECTED"
            req.reviewed_by = reviewer_user_id
            req.reviewer_comments = comments
            req.reviewed_at = datetime.now(timezone.utc)

            db.session.commit()
            return req.to_dict()

    @staticmethod
    def cancel_leave(leave_id: int, user_id, user_role: str):
        """
        Cancels a request.
        - Employee can cancel their own PENDING or APPROVED future request.
        - HR/Admin can cancel on behalf of employee.
        """
        req_lock = LeaveRequest.get_employee_thread_lock(f"leave_req_{leave_id}")
        with req_lock:
            db.session.expire_all()
            req = db.session.get(LeaveRequest, leave_id)
            if not req:
                raise ValueError(f"Leave request {leave_id} not found.")

            if user_role == "EMPLOYEE":
                employee = LeaveService.get_employee_for_user(user_id)
                if req.employee_id != employee.id:
                    raise PermissionError("You can only cancel your own leave requests.")

            if req.status in ["REJECTED", "CANCELLED"]:
                raise ValueError(f"Request is already {req.status}.")

            req.status = "CANCELLED"
            db.session.commit()
            return req.to_dict()

    # --------------------------------------------------------------------------
    # Balance Calculations
    # --------------------------------------------------------------------------
    @staticmethod
    def get_employee_balance(employee_id, year: int = None):
        """
        Calculates year-wise leave balances per leave type:
        - Annual entitlement
        - Approved days taken
        - Pending days requested
        - Available balance = Entitlement - Approved (for paid leave types)
        """
        target_year = year or datetime.now(timezone.utc).year
        LeaveService.ensure_default_leave_types()

        leave_types = LeaveType.query.filter_by(is_active=True).order_by(LeaveType.id.asc()).all()

        balances = []
        for lt in leave_types:
            # Query approved days in target year
            approved_sum = (
                db.session.query(func.coalesce(func.sum(LeaveRequest.total_days), 0.0))
                .filter(
                    LeaveRequest.employee_id == employee_id,
                    LeaveRequest.leave_type_id == lt.id,
                    LeaveRequest.status == "APPROVED",
                    extract("year", LeaveRequest.start_date) == target_year
                )
                .scalar()
            )
            approved_days = float(approved_sum)

            # Query pending days in target year
            pending_sum = (
                db.session.query(func.coalesce(func.sum(LeaveRequest.total_days), 0.0))
                .filter(
                    LeaveRequest.employee_id == employee_id,
                    LeaveRequest.leave_type_id == lt.id,
                    LeaveRequest.status == "PENDING",
                    extract("year", LeaveRequest.start_date) == target_year
                )
                .scalar()
            )
            pending_days = float(pending_sum)

            if lt.is_paid:
                remaining_balance = max(0.0, float(lt.days_per_year) - approved_days)
            else:
                remaining_balance = 0.0  # Unpaid leave has no fixed entitlement limit

            balances.append({
                "leave_type_id": lt.id,
                "leave_type_name": lt.name,
                "leave_type_code": lt.code,
                "is_paid": lt.is_paid,
                "annual_entitlement": lt.days_per_year,
                "approved_days": approved_days,
                "pending_days": pending_days,
                "remaining_balance": remaining_balance,
                "year": target_year
            })

        return balances

    # --------------------------------------------------------------------------
    # History, Listing & Summary
    # --------------------------------------------------------------------------
    @staticmethod
    def get_my_leave_history(user_id, status=None, year: int = None, limit=50, offset=0):
        employee = LeaveService.get_employee_for_user(user_id)
        query = LeaveRequest.query.filter_by(employee_id=employee.id)

        if status:
            query = query.filter_by(status=status)
        if year:
            query = query.filter(extract("year", LeaveRequest.start_date) == year)

        total_count = query.count()
        records = query.order_by(LeaveRequest.created_at.desc()).offset(offset).limit(limit).all()

        balances = LeaveService.get_employee_balance(employee.id, year=year)

        return {
            "total": total_count,
            "items": [r.to_dict() for r in records],
            "balances": balances,
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def list_leaves(search=None, department_id=None, leave_type_id=None, status=None, start_date=None, end_date=None, limit=50, offset=0):
        query = LeaveRequest.query.join(Employee).join(User)

        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(term),
                    Employee.last_name.ilike(term),
                    Employee.employee_code.ilike(term),
                    User.email.ilike(term)
                )
            )

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        if leave_type_id:
            query = query.filter(LeaveRequest.leave_type_id == leave_type_id)

        if status:
            query = query.filter(LeaveRequest.status == status)

        if start_date:
            query = query.filter(LeaveRequest.start_date >= start_date)
        if end_date:
            query = query.filter(LeaveRequest.end_date <= end_date)

        total_count = query.count()
        records = query.order_by(LeaveRequest.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total_count,
            "items": [r.to_dict() for r in records],
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def get_summary(year: int = None):
        target_year = year or datetime.now(timezone.utc).year
        today = datetime.now(timezone.utc).date()

        pending_count = LeaveRequest.query.filter_by(status="PENDING").count()
        approved_year = LeaveRequest.query.filter(
            LeaveRequest.status == "APPROVED",
            extract("year", LeaveRequest.start_date) == target_year
        ).count()
        rejected_year = LeaveRequest.query.filter(
            LeaveRequest.status == "REJECTED",
            extract("year", LeaveRequest.start_date) == target_year
        ).count()

        # Currently on leave today
        on_leave_today = LeaveRequest.query.filter(
            LeaveRequest.status == "APPROVED",
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today
        ).count()

        return {
            "year": target_year,
            "pending_approvals": pending_count,
            "approved_this_year": approved_year,
            "rejected_this_year": rejected_year,
            "employees_on_leave_today": on_leave_today
        }

