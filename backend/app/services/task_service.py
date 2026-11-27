import uuid
from datetime import datetime, timezone, date
from sqlalchemy import or_, and_, func
from app.extension_registry import db
from app.models.task import Task
from app.models.employee import Employee
from app.models.department import Department
from app.models.user import User
from app.models.audit import AuditLog

class TaskService:
    """Service layer managing task lifecycle, RBAC enforcement, filtering, and audit trails."""

    @staticmethod
    def _resolve_employee(user_id):
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            raise ValueError("Invalid user identifier.")

        employee = Employee.query.filter_by(user_id=u_uuid).first()
        if not employee:
            raise ValueError("No employee profile found for this user.")
        return employee

    # --------------------------------------------------------------------------
    # Task Creation
    # --------------------------------------------------------------------------
    @staticmethod
    def create_task(creator_user_id, data: dict, ip_address: str = None):
        """Creates a new task assigned to an ACTIVE employee (HR or Admin)."""
        try:
            assignee_uuid = uuid.UUID(str(data["assigned_to"]))
        except (ValueError, TypeError):
            raise ValueError("Invalid assignee employee ID.")

        employee = db.session.get(Employee, assignee_uuid)
        if not employee:
            raise ValueError("Assignee employee not found.")
        if employee.status != "ACTIVE":
            raise ValueError(f"Tasks can only be assigned to ACTIVE employees. Employee is currently {employee.status}.")

        start_date = data.get("start_date")
        due_date = data.get("due_date")
        if start_date and due_date and due_date < start_date:
            raise ValueError("Due date cannot be earlier than start date.")

        dept_id = data.get("department_id") or employee.department_id

        task = Task(
            title=data["title"].strip(),
            description=data.get("description", "").strip() if data.get("description") else None,
            category=data.get("category", "").strip() if data.get("category") else None,
            assigned_to=employee.id,
            department_id=dept_id,
            created_by=creator_user_id,
            priority=data.get("priority", "MEDIUM").upper(),
            status="TODO",
            start_date=start_date,
            due_date=due_date,
        )
        db.session.add(task)
        db.session.flush()

        # Audit log creation
        audit = AuditLog(
            user_id=creator_user_id,
            action="CREATE_TASK",
            target_entity="tasks",
            target_id=str(task.id),
            new_state=task.to_dict(),
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return task.to_dict()

    # --------------------------------------------------------------------------
    # Task Retrieval & RBAC
    # --------------------------------------------------------------------------
    @staticmethod
    def get_task_by_id(task_id: int, current_user):
        """Fetches task details with strict cross-employee access authorization."""
        task = db.session.get(Task, task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")

        if current_user.role == "EMPLOYEE":
            employee = TaskService._resolve_employee(current_user.id)
            if task.assigned_to != employee.id:
                raise PermissionError("You do not have permission to access tasks assigned to other employees.")

        return task.to_dict()

    @staticmethod
    def list_tasks(current_user, filters: dict):
        """Lists tasks with filtering, search, pagination, and role-based scoping."""
        query = Task.query

        if current_user.role == "EMPLOYEE":
            employee = TaskService._resolve_employee(current_user.id)
            query = query.filter(Task.assigned_to == employee.id)
        else:
            if filters.get("assigned_to"):
                try:
                    emp_uuid = uuid.UUID(str(filters["assigned_to"]))
                    query = query.filter(Task.assigned_to == emp_uuid)
                except (ValueError, TypeError):
                    raise ValueError("Invalid assigned_to UUID.")

            if filters.get("department_id"):
                try:
                    dept_id = int(filters["department_id"])
                    query = query.filter(or_(Task.department_id == dept_id, Task.assignee.has(department_id=dept_id)))
                except ValueError:
                    raise ValueError("Invalid department_id.")

        if filters.get("status"):
            query = query.filter(Task.status == filters["status"].upper())

        if filters.get("priority"):
            query = query.filter(Task.priority == filters["priority"].upper())

        if filters.get("category"):
            query = query.filter(Task.category.ilike(f"%{filters['category'].strip()}%"))

        if filters.get("overdue") is True or str(filters.get("overdue")).lower() == "true":
            today = datetime.now(timezone.utc).date()
            query = query.filter(Task.due_date < today, Task.status.notin_(["COMPLETED", "CANCELLED"]))

        if filters.get("search"):
            term = f"%{filters['search'].strip()}%"
            query = query.filter(or_(Task.title.ilike(term), Task.description.ilike(term), Task.category.ilike(term)))

        # Default ordering: Overdue and high priority first, then due_date, then created_at desc
        query = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())

        page = int(filters.get("page", 1))
        per_page = min(int(filters.get("per_page", 20)), 100)
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [t.to_dict() for t in paginated.items],
            "pagination": {
                "total": paginated.total,
                "page": paginated.page,
                "per_page": paginated.per_page,
                "pages": paginated.pages
            }
        }

    @staticmethod
    def list_my_tasks(current_user, filters: dict):
        """Convenience method returning assigned tasks for current employee."""
        employee = TaskService._resolve_employee(current_user.id)
        filters["assigned_to"] = str(employee.id)
        return TaskService.list_tasks(current_user, filters)

    # --------------------------------------------------------------------------
    # Task Updating & Configuration
    # --------------------------------------------------------------------------
    @staticmethod
    def update_task(task_id: int, current_user, data: dict, ip_address: str = None):
        """Updates task parameters (HR or Admin only)."""
        if current_user.role == "EMPLOYEE":
            raise PermissionError("Employees are not authorized to edit task configurations.")

        task = db.session.get(Task, task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")

        if task.status == "CANCELLED":
            raise ValueError("Cancelled tasks cannot be modified.")

        prev_state = task.to_dict()

        if "assigned_to" in data and data["assigned_to"]:
            try:
                emp_uuid = uuid.UUID(str(data["assigned_to"]))
            except (ValueError, TypeError):
                raise ValueError("Invalid assigned_to UUID.")
            employee = db.session.get(Employee, emp_uuid)
            if not employee:
                raise ValueError("Assignee employee not found.")
            if employee.status != "ACTIVE":
                raise ValueError(f"Tasks can only be assigned to ACTIVE employees. Target is {employee.status}.")
            task.assigned_to = employee.id
            if "department_id" not in data:
                task.department_id = employee.department_id

        if "title" in data and data["title"]:
            task.title = data["title"].strip()
        if "description" in data:
            task.description = data["description"].strip() if data["description"] else None
        if "category" in data:
            task.category = data["category"].strip() if data["category"] else None
        if "priority" in data and data["priority"]:
            task.priority = data["priority"].upper()
        if "department_id" in data:
            task.department_id = data["department_id"]

        start_date = data.get("start_date") if "start_date" in data else task.start_date
        due_date = data.get("due_date") if "due_date" in data else task.due_date
        if start_date and due_date and due_date < start_date:
            raise ValueError("Due date cannot be earlier than start date.")

        if "start_date" in data:
            task.start_date = data["start_date"]
        if "due_date" in data:
            task.due_date = data["due_date"]

        task.updated_at = datetime.now(timezone.utc)

        audit = AuditLog(
            user_id=current_user.id,
            action="UPDATE_TASK",
            target_entity="tasks",
            target_id=str(task.id),
            previous_state=prev_state,
            new_state=task.to_dict(),
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return task.to_dict()

    # --------------------------------------------------------------------------
    # Status Lifecycle Transitions
    # --------------------------------------------------------------------------
    @staticmethod
    def update_task_status(task_id: int, current_user, new_status: str, comment: str = None, ip_address: str = None):
        """
        Manages task lifecycle with role-specific transition rules.
        Lifecycle: TODO -> IN_PROGRESS -> REVIEW -> COMPLETED
        Employees cannot directly mark tasks COMPLETED without HR/Admin review.
        """
        task = db.session.get(Task, task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")

        target_status = new_status.upper().strip()
        current_status = task.status

        if target_status == current_status:
            return task.to_dict()

        if current_status == "CANCELLED":
            raise ValueError("Cancelled tasks cannot be moved to another status.")

        # Role-based transition guard
        if current_user.role == "EMPLOYEE":
            employee = TaskService._resolve_employee(current_user.id)
            if task.assigned_to != employee.id:
                raise PermissionError("You can only update the status of tasks assigned to you.")

            if target_status == "COMPLETED":
                raise PermissionError("Employees cannot mark tasks directly as COMPLETED. Please submit for REVIEW.")

            if target_status == "CANCELLED":
                raise PermissionError("Employees cannot cancel tasks. Please contact HR or Admin.")

            valid_transitions = {
                "TODO": ["IN_PROGRESS", "BLOCKED"],
                "IN_PROGRESS": ["REVIEW", "BLOCKED"],
                "REVIEW": ["IN_PROGRESS"],  # Allow moving back to in_progress if employee resumes work
                "BLOCKED": ["IN_PROGRESS", "TODO"],
                "COMPLETED": []  # Employee cannot reopen completed tasks
            }

            if target_status not in valid_transitions.get(current_status, []):
                raise ValueError(
                    f"Invalid status transition from '{current_status}' to '{target_status}'. "
                    f"Allowed next statuses for employee: {valid_transitions.get(current_status, [])}."
                )

        else:
            # HR or Admin transitions
            valid_admin_transitions = {
                "TODO": ["IN_PROGRESS", "BLOCKED", "CANCELLED"],
                "IN_PROGRESS": ["REVIEW", "COMPLETED", "BLOCKED", "CANCELLED"],
                "REVIEW": ["COMPLETED", "IN_PROGRESS", "BLOCKED", "CANCELLED"],
                "BLOCKED": ["IN_PROGRESS", "TODO", "CANCELLED"],
                "COMPLETED": ["IN_PROGRESS", "CANCELLED"],  # Admin can reopen or cancel
            }

            if target_status not in valid_admin_transitions.get(current_status, []):
                raise ValueError(
                    f"Invalid status transition from '{current_status}' to '{target_status}'."
                )

        prev_state = task.to_dict()
        task.status = target_status
        task.updated_at = datetime.now(timezone.utc)

        if target_status == "COMPLETED":
            task.completed_at = datetime.now(timezone.utc)
        else:
            task.completed_at = None

        audit = AuditLog(
            user_id=current_user.id,
            action="UPDATE_STATUS",
            target_entity="tasks",
            target_id=str(task.id),
            previous_state={"status": current_status},
            new_state={"status": target_status, "comment": comment.strip() if comment else None},
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return task.to_dict()

    # --------------------------------------------------------------------------
    # Task Assignment
    # --------------------------------------------------------------------------
    @staticmethod
    def assign_task(task_id: int, current_user, new_assignee_id: str, comment: str = None, ip_address: str = None):
        """Reassigns a task to another active employee (HR or Admin only)."""
        if current_user.role == "EMPLOYEE":
            raise PermissionError("Employees are not authorized to reassign tasks.")

        task = db.session.get(Task, task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")

        if task.status == "CANCELLED":
            raise ValueError("Cancelled tasks cannot be reassigned.")

        try:
            emp_uuid = uuid.UUID(str(new_assignee_id))
        except (ValueError, TypeError):
            raise ValueError("Invalid assignee employee ID.")

        new_emp = db.session.get(Employee, emp_uuid)
        if not new_emp:
            raise ValueError("Assignee employee not found.")
        if new_emp.status != "ACTIVE":
            raise ValueError(f"Tasks can only be assigned to ACTIVE employees. Target is {new_emp.status}.")

        prev_assignee_id = str(task.assigned_to)
        prev_assignee_name = task.assignee.full_name if task.assignee else None

        task.assigned_to = new_emp.id
        task.department_id = new_emp.department_id
        task.updated_at = datetime.now(timezone.utc)

        audit = AuditLog(
            user_id=current_user.id,
            action="REASSIGN_TASK",
            target_entity="tasks",
            target_id=str(task.id),
            previous_state={"assigned_to": prev_assignee_id, "assignee_name": prev_assignee_name},
            new_state={
                "assigned_to": str(new_emp.id),
                "assignee_name": new_emp.full_name,
                "comment": comment.strip() if comment else None
            },
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return task.to_dict()

    # --------------------------------------------------------------------------
    # Task Cancellation
    # --------------------------------------------------------------------------
    @staticmethod
    def cancel_task(task_id: int, current_user, reason: str = None, ip_address: str = None):
        """Cancels a task (HR or Admin only)."""
        if current_user.role == "EMPLOYEE":
            raise PermissionError("Employees are not authorized to cancel tasks.")

        task = db.session.get(Task, task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")

        if task.status == "CANCELLED":
            raise ValueError("Task is already cancelled.")

        prev_status = task.status
        task.status = "CANCELLED"
        task.updated_at = datetime.now(timezone.utc)

        audit = AuditLog(
            user_id=current_user.id,
            action="CANCEL_TASK",
            target_entity="tasks",
            target_id=str(task.id),
            previous_state={"status": prev_status},
            new_state={"status": "CANCELLED", "reason": reason.strip() if reason else None},
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return task.to_dict()

    # --------------------------------------------------------------------------
    # Summary KPIs
    # --------------------------------------------------------------------------
    @staticmethod
    def get_task_summary(current_user, department_id: int = None):
        """Calculates role-aware KPI summary cards."""
        query = Task.query
        today = datetime.now(timezone.utc).date()

        if current_user.role == "EMPLOYEE":
            employee = TaskService._resolve_employee(current_user.id)
            query = query.filter(Task.assigned_to == employee.id)
        elif department_id:
            query = query.filter(or_(Task.department_id == department_id, Task.assignee.has(department_id=department_id)))

        total_tasks = query.count()
        todo = query.filter(Task.status == "TODO").count()
        in_progress = query.filter(Task.status == "IN_PROGRESS").count()
        review = query.filter(Task.status == "REVIEW").count()
        completed = query.filter(Task.status == "COMPLETED").count()
        blocked = query.filter(Task.status == "BLOCKED").count()
        cancelled = query.filter(Task.status == "CANCELLED").count()
        overdue = query.filter(Task.due_date < today, Task.status.notin_(["COMPLETED", "CANCELLED"])).count()
        high_priority = query.filter(Task.priority.in_(["HIGH", "URGENT"]), Task.status.notin_(["COMPLETED", "CANCELLED"])).count()

        return {
            "total_tasks": total_tasks,
            "todo": todo,
            "in_progress": in_progress,
            "review": review,
            "completed": completed,
            "blocked": blocked,
            "cancelled": cancelled,
            "overdue": overdue,
            "high_priority": high_priority
        }

    # --------------------------------------------------------------------------
    # Activity History
    # --------------------------------------------------------------------------
    @staticmethod
    def get_task_history(task_id: int, current_user):
        """Fetches the complete audit timeline for a task."""
        # Enforces access check
        TaskService.get_task_by_id(task_id, current_user)

        logs = (
            AuditLog.query.filter_by(target_entity="tasks", target_id=str(task_id))
            .order_by(AuditLog.timestamp.desc())
            .all()
        )

        history = []
        for log in logs:
            history.append({
                "id": log.id,
                "action": log.action,
                "user_id": str(log.user_id) if log.user_id else None,
                "user_email": log.user.email if log.user else None,
                "previous_state": log.previous_state,
                "new_state": log.new_state,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "ip_address": log.ip_address
            })

        return history

