import uuid
from datetime import date, datetime, timezone
from sqlalchemy import or_
from app.extension_registry import db
from app.models.employee import Employee
from app.models.department import Department
from app.models.user import User

class EmployeeService:
    """Service layer for department and employee business logic and queries."""

    # --------------------------------------------------------------------------
    # Department Operations
    # --------------------------------------------------------------------------
    @staticmethod
    def list_departments(include_inactive=False):
        query = Department.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        departments = query.order_by(Department.name.asc()).all()
        return [dept.to_dict(include_employee_count=True) for dept in departments]

    @staticmethod
    def get_department_by_id(department_id: int):
        dept = db.session.get(Department, department_id)
        if not dept:
            raise ValueError(f"Department with ID {department_id} not found.")
        return dept

    @staticmethod
    def create_department(data: dict):
        name = data["name"].strip()
        code = data["code"].strip().upper()

        if Department.query.filter(Department.name.ilike(name)).first():
            raise ValueError(f"Department with name '{name}' already exists.")
        if Department.query.filter(Department.code.ilike(code)).first():
            raise ValueError(f"Department with code '{code}' already exists.")

        department = Department(
            name=name,
            code=code,
            description=data.get("description"),
            is_active=data.get("is_active", True)
        )
        db.session.add(department)
        db.session.commit()
        return department.to_dict(include_employee_count=True)

    @staticmethod
    def update_department(department_id: int, data: dict):
        dept = EmployeeService.get_department_by_id(department_id)

        if "name" in data and data["name"]:
            name = data["name"].strip()
            existing = Department.query.filter(Department.name.ilike(name), Department.id != department_id).first()
            if existing:
                raise ValueError(f"Department with name '{name}' already exists.")
            dept.name = name

        if "code" in data and data["code"]:
            code = data["code"].strip().upper()
            existing = Department.query.filter(Department.code.ilike(code), Department.id != department_id).first()
            if existing:
                raise ValueError(f"Department with code '{code}' already exists.")
            dept.code = code

        if "description" in data:
            dept.description = data["description"]

        if "is_active" in data:
            dept.is_active = data["is_active"]

        db.session.commit()
        return dept.to_dict(include_employee_count=True)

    # --------------------------------------------------------------------------
    # Employee Operations
    # --------------------------------------------------------------------------
    @staticmethod
    def list_employees(search=None, department_id=None, status=None, role=None, limit=100, offset=0):
        query = Employee.query.join(User).join(Department)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    User.email.ilike(search_term),
                    Employee.designation.ilike(search_term)
                )
            )

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        if status:
            query = query.filter(Employee.status == status)

        if role:
            query = query.filter(User.role == role)

        total_count = query.count()
        employees = query.order_by(Employee.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total_count,
            "items": [emp.to_dict() for emp in employees],
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def get_employee_by_id(employee_id_raw):
        try:
            emp_uuid = uuid.UUID(str(employee_id_raw)) if not isinstance(employee_id_raw, uuid.UUID) else employee_id_raw
        except (ValueError, TypeError):
            raise ValueError(f"Invalid employee UUID: {employee_id_raw}")

        employee = db.session.get(Employee, emp_uuid)
        if not employee:
            raise ValueError(f"Employee with ID {employee_id_raw} not found.")
        return employee

    @staticmethod
    def get_employee_by_user_id(user_id_raw):
        try:
            user_uuid = uuid.UUID(str(user_id_raw)) if not isinstance(user_id_raw, uuid.UUID) else user_id_raw
        except (ValueError, TypeError):
            raise ValueError(f"Invalid user UUID: {user_id_raw}")

        employee = Employee.query.filter_by(user_id=user_uuid).first()
        if not employee:
            raise ValueError(f"No employee profile found for user ID {user_id_raw}.")
        return employee

    @staticmethod
    def create_employee(data: dict):
        email = data["email"].strip().lower()
        employee_code = data["employee_code"].strip().upper()

        # Check duplicate email
        if User.query.filter_by(email=email).first():
            raise ValueError(f"A user with email '{email}' already exists.")

        # Check duplicate employee_code
        if Employee.query.filter_by(employee_code=employee_code).first():
            raise ValueError(f"An employee with code '{employee_code}' already exists.")

        # Check department existence
        department_id = data["department_id"]
        department = db.session.get(Department, department_id)
        if not department:
            raise ValueError(f"Department ID {department_id} does not exist.")

        # Check manager if supplied
        manager_id = data.get("reporting_manager_id")
        manager_uuid = None
        if manager_id:
            try:
                manager_uuid = uuid.UUID(str(manager_id))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid reporting manager UUID: {manager_id}")
            manager = db.session.get(Employee, manager_uuid)
            if not manager:
                raise ValueError(f"Reporting manager with ID '{manager_id}' does not exist.")

        # Create user account
        user = User(
            email=email,
            role=data.get("role", "EMPLOYEE"),
            is_active=True
        )
        password = data.get("password", "Welcome123!")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create employee record
        employee = Employee(
            user_id=user.id,
            employee_code=employee_code,
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
            phone=data.get("phone"),
            gender=data.get("gender"),
            date_of_birth=data.get("date_of_birth"),
            address=data.get("address"),
            department_id=department.id,
            designation=data["designation"].strip(),
            joining_date=data.get("joining_date") or date.today(),
            employment_type=data.get("employment_type", "FULL_TIME"),
            status=data.get("status", "ACTIVE"),
            reporting_manager_id=manager_uuid,
            profile_image_url=data.get("profile_image_url")
        )
        db.session.add(employee)
        db.session.commit()

        return employee.to_dict()

    @staticmethod
    def update_employee(employee_id_raw, data: dict):
        employee = EmployeeService.get_employee_by_id(employee_id_raw)

        if "department_id" in data and data["department_id"] is not None:
            department_id = data["department_id"]
            department = db.session.get(Department, department_id)
            if not department:
                raise ValueError(f"Department ID {department_id} does not exist.")
            employee.department_id = department_id

        if "reporting_manager_id" in data:
            manager_id = data["reporting_manager_id"]
            if manager_id:
                try:
                    manager_uuid = uuid.UUID(str(manager_id))
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid reporting manager UUID: {manager_id}")
                if manager_uuid == employee.id:
                    raise ValueError("An employee cannot be their own reporting manager.")
                manager = db.session.get(Employee, manager_uuid)
                if not manager:
                    raise ValueError(f"Reporting manager with ID '{manager_id}' does not exist.")
                employee.reporting_manager_id = manager_uuid
            else:
                employee.reporting_manager_id = None

        if "first_name" in data and data["first_name"]:
            employee.first_name = data["first_name"].strip()

        if "last_name" in data and data["last_name"]:
            employee.last_name = data["last_name"].strip()

        if "phone" in data:
            employee.phone = data["phone"]

        if "gender" in data:
            employee.gender = data["gender"]

        if "date_of_birth" in data:
            employee.date_of_birth = data["date_of_birth"]

        if "address" in data:
            employee.address = data["address"]

        if "designation" in data and data["designation"]:
            employee.designation = data["designation"].strip()

        if "joining_date" in data and data["joining_date"]:
            employee.joining_date = data["joining_date"]

        if "employment_type" in data and data["employment_type"]:
            employee.employment_type = data["employment_type"]

        if "status" in data and data["status"]:
            employee.status = data["status"]

        if "profile_image_url" in data:
            employee.profile_image_url = data["profile_image_url"]

        if "role" in data and data["role"] and employee.user:
            employee.user.role = data["role"]

        employee.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return employee.to_dict()

    @staticmethod
    def update_status(employee_id_raw, status: str, is_active: bool = None):
        employee = EmployeeService.get_employee_by_id(employee_id_raw)
        employee.status = status

        if is_active is not None and employee.user:
            employee.user.is_active = is_active
        elif status == "TERMINATED" and employee.user:
            employee.user.is_active = False
        elif status == "ACTIVE" and employee.user:
            employee.user.is_active = True

        employee.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return employee.to_dict()

