import uuid
from datetime import datetime, timezone, date, timedelta
from calendar import monthrange
from sqlalchemy import func, or_, and_, extract
from app.extension_registry import db
from app.models.employee import Employee
from app.models.department import Department
from app.models.user import User
from app.models.attendance import Attendance
from app.models.leave import LeaveRequest, LeaveType
from app.models.task import Task
from app.models.performance import PerformanceCycle, PerformanceReview, RATING_DEFINITIONS
from app.services.leave_service import LeaveService

class DashboardService:
    """Service providing SQL-aggregated operational metrics and analytics for Admin, HR, and Employee dashboards."""

    @staticmethod
    def _resolve_employee(user_id):
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            raise ValueError("Invalid user identifier.")

        employee = Employee.query.filter_by(user_id=u_uuid).first()
        if not employee:
            raise ValueError("No employee profile found for this user account.")
        return employee

    # --------------------------------------------------------------------------
    # 1. Admin Dashboard Metrics & Analytics
    # --------------------------------------------------------------------------
    @staticmethod
    def get_admin_dashboard(date_from=None, date_to=None):
        """Returns organization-wide KPIs and aggregated chart analytics for Admins."""
        today = date.today()

        # Employee counts
        total_employees = Employee.query.count()
        active_employees = Employee.query.filter_by(status="ACTIVE").count()
        inactive_employees = Employee.query.filter(Employee.status != "ACTIVE").count()
        total_departments = Department.query.count()

        # Attendance metrics for today
        today_attendance_count = Attendance.query.filter_by(work_date=today).count()
        currently_checked_in = Attendance.query.filter(
            Attendance.work_date == today,
            Attendance.check_out.is_(None)
        ).count()

        # Leave metrics
        pending_leaves = LeaveRequest.query.filter_by(status="PENDING").count()
        approved_leaves = LeaveRequest.query.filter_by(status="APPROVED").count()

        # Task metrics
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter_by(status="COMPLETED").count()
        pending_tasks = Task.query.filter(Task.status.in_(["TODO", "IN_PROGRESS", "REVIEW", "BLOCKED"])).count()
        overdue_tasks = Task.query.filter(
            Task.due_date < today,
            ~Task.status.in_(["COMPLETED", "CANCELLED"])
        ).count()

        # Performance metrics
        active_cycles = PerformanceCycle.query.filter_by(status="ACTIVE").count()
        completed_reviews = PerformanceReview.query.filter_by(status="COMPLETED").count()
        avg_rating_res = db.session.query(func.avg(PerformanceReview.rating)).filter(
            PerformanceReview.status == "COMPLETED",
            PerformanceReview.rating.isnot(None)
        ).scalar()
        average_rating = round(float(avg_rating_res), 2) if avg_rating_res is not None else 0.0

        # Charts: Department distribution
        dept_dist = (
            db.session.query(Department.name, func.count(Employee.id))
            .outerjoin(Employee, and_(Employee.department_id == Department.id, Employee.status == "ACTIVE"))
            .group_by(Department.id, Department.name)
            .order_by(Department.name.asc())
            .all()
        )
        department_distribution = [{"name": name, "count": count} for name, count in dept_dist]

        # Charts: Attendance trends (7-day and 30-day)
        attendance_trends_7d = DashboardService.get_attendance_trends(days=7)
        attendance_trends_30d = DashboardService.get_attendance_trends(days=30)

        # Charts: Leave distribution
        leave_dist = (
            db.session.query(LeaveRequest.status, func.count(LeaveRequest.id))
            .group_by(LeaveRequest.status)
            .all()
        )
        leave_distribution = [{"status": status, "count": count} for status, count in leave_dist]

        # Charts: Task distribution
        task_dist = (
            db.session.query(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )
        task_distribution = [{"status": status, "count": count} for status, count in task_dist]

        # Charts: Performance ratings distribution (1 to 5)
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        ratings_query = (
            db.session.query(PerformanceReview.rating, func.count(PerformanceReview.id))
            .filter(PerformanceReview.status == "COMPLETED", PerformanceReview.rating.isnot(None))
            .group_by(PerformanceReview.rating)
            .all()
        )
        for score, count in ratings_query:
            if score in rating_counts:
                rating_counts[score] = count

        performance_distribution = [
            {
                "score": score,
                "label": RATING_DEFINITIONS[score]["label"],
                "count": rating_counts[score]
            }
            for score in range(1, 6)
        ]

        return {
            "metrics": {
                "total_employees": total_employees,
                "active_employees": active_employees,
                "inactive_employees": inactive_employees,
                "total_departments": total_departments,
                "today_attendance_count": today_attendance_count,
                "currently_checked_in": currently_checked_in,
                "pending_leaves": pending_leaves,
                "approved_leaves": approved_leaves,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
                "overdue_tasks": overdue_tasks,
                "active_cycles": active_cycles,
                "completed_reviews": completed_reviews,
                "average_rating": average_rating
            },
            "charts": {
                "department_distribution": department_distribution,
                "attendance_trends_7d": attendance_trends_7d,
                "attendance_trends_30d": attendance_trends_30d,
                "leave_distribution": leave_distribution,
                "task_distribution": task_distribution,
                "performance_distribution": performance_distribution
            }
        }

    # --------------------------------------------------------------------------
    # 2. HR Dashboard Metrics & Analytics
    # --------------------------------------------------------------------------
    @staticmethod
    def get_hr_dashboard(department_id=None):
        """Returns HR-focused workforce metrics, approval queues, and progress trends."""
        today = date.today()

        emp_query = Employee.query
        if department_id:
            emp_query = emp_query.filter_by(department_id=department_id)

        total_employees = emp_query.count()
        active_employees = emp_query.filter_by(status="ACTIVE").count()

        # Department-wise counts
        dept_dist_query = (
            db.session.query(Department.name, func.count(Employee.id))
            .outerjoin(Employee, and_(Employee.department_id == Department.id, Employee.status == "ACTIVE"))
        )
        if department_id:
            dept_dist_query = dept_dist_query.filter(Department.id == department_id)
        dept_dist = dept_dist_query.group_by(Department.id, Department.name).order_by(Department.name.asc()).all()
        department_employees = [{"name": name, "count": count} for name, count in dept_dist]

        # Attendance today
        att_query = Attendance.query.filter_by(work_date=today)
        if department_id:
            att_query = att_query.join(Employee).filter(Employee.department_id == department_id)
        today_present = att_query.count()
        today_checked_in = att_query.filter(Attendance.check_out.is_(None)).count()

        # Leaves
        leave_q = LeaveRequest.query
        if department_id:
            leave_q = leave_q.join(Employee).filter(Employee.department_id == department_id)
        pending_leaves = leave_q.filter(LeaveRequest.status == "PENDING").count()
        approved_leaves = leave_q.filter(LeaveRequest.status == "APPROVED").count()
        rejected_leaves = leave_q.filter(LeaveRequest.status == "REJECTED").count()

        # Tasks
        task_q = Task.query
        if department_id:
            task_q = task_q.filter(Task.department_id == department_id)
        total_tasks = task_q.count()
        completed_tasks = task_q.filter(Task.status == "COMPLETED").count()
        pending_tasks = task_q.filter(Task.status.in_(["TODO", "IN_PROGRESS", "REVIEW", "BLOCKED"])).count()
        overdue_tasks = task_q.filter(
            Task.due_date < today,
            ~Task.status.in_(["COMPLETED", "CANCELLED"])
        ).count()

        # Performance Cycles
        active_cycles = PerformanceCycle.query.filter_by(status="ACTIVE").count()
        total_reviews = PerformanceReview.query.count()
        completed_reviews = PerformanceReview.query.filter_by(status="COMPLETED").count()
        completion_rate = round((completed_reviews / total_reviews * 100), 1) if total_reviews > 0 else 0.0

        # Cycle progress summary for active cycles
        active_cycles_objs = PerformanceCycle.query.filter_by(status="ACTIVE").all()
        cycle_progress = []
        for cycle in active_cycles_objs:
            tot = cycle.reviews.count()
            comp = cycle.reviews.filter_by(status="COMPLETED").count()
            rate = round((comp / tot * 100), 1) if tot > 0 else 0.0
            cycle_progress.append({
                "cycle_id": cycle.id,
                "title": cycle.title,
                "total": tot,
                "completed": comp,
                "completion_rate": rate,
                "due_date": cycle.due_date.isoformat() if cycle.due_date else None
            })

        # Charts: Attendance trends
        attendance_trends = DashboardService.get_attendance_trends(days=14)

        # Charts: Leave trends / status
        leave_dist = (
            db.session.query(LeaveRequest.status, func.count(LeaveRequest.id))
            .group_by(LeaveRequest.status)
            .all()
        )
        leave_trends = [{"status": s, "count": c} for s, c in leave_dist]

        # Charts: Task completion breakdown
        task_dist = (
            db.session.query(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )
        task_completion = [{"status": s, "count": c} for s, c in task_dist]

        return {
            "metrics": {
                "total_employees": total_employees,
                "active_employees": active_employees,
                "today_attendance": {
                    "present": today_present,
                    "currently_checked_in": today_checked_in
                },
                "pending_leave_approvals": pending_leaves,
                "approved_leaves": approved_leaves,
                "rejected_leaves": rejected_leaves,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
                "overdue_tasks": overdue_tasks,
                "active_cycles": active_cycles,
                "completed_reviews": completed_reviews,
                "review_completion_rate": completion_rate
            },
            "charts": {
                "department_employees": department_employees,
                "attendance_trends": attendance_trends,
                "leave_trends": leave_trends,
                "task_completion": task_completion,
                "cycle_progress": cycle_progress
            }
        }

    # --------------------------------------------------------------------------
    # 3. Employee Dashboard Metrics & Analytics (Strictly Scoped to Current User)
    # --------------------------------------------------------------------------
    @staticmethod
    def get_employee_dashboard(user_id):
        """Returns personalized metrics and charts for the authenticated employee ONLY."""
        employee = DashboardService._resolve_employee(user_id)
        today = date.today()

        # 1. Profile Summary
        profile = {
            "id": str(employee.id),
            "full_name": employee.full_name,
            "employee_code": employee.employee_code,
            "department": employee.department.name if employee.department else "Unassigned",
            "designation": employee.designation or "Employee",
            "status": employee.status,
            "email": employee.user.email if employee.user else None
        }

        # 2. Today's Attendance Status
        today_att = Attendance.query.filter_by(
            employee_id=employee.id,
            work_date=today
        ).order_by(Attendance.shift_number.desc()).first()

        if today_att:
            if today_att.check_out is None:
                today_status = "CHECKED_IN"
            else:
                today_status = "CHECKED_OUT"
            today_check_in = today_att.check_in.isoformat() if today_att.check_in else None
            current_shift = today_att.shift_number
        else:
            today_status = "NOT_CHECKED_IN"
            today_check_in = None
            current_shift = None

        # Monthly Attendance Stats
        first_of_month = date(today.year, today.month, 1)
        month_attendance_days = (
            db.session.query(func.count(func.distinct(Attendance.work_date)))
            .filter(
                Attendance.employee_id == employee.id,
                Attendance.work_date >= first_of_month,
                Attendance.work_date <= today
            )
            .scalar() or 0
        )

        month_hours_sum = (
            db.session.query(func.coalesce(func.sum(Attendance.total_hours), 0.0))
            .filter(
                Attendance.employee_id == employee.id,
                Attendance.work_date >= first_of_month,
                Attendance.work_date <= today
            )
            .scalar() or 0.0
        )
        month_working_hours = round(float(month_hours_sum), 2)

        # 3. Leave Requests & Balances
        pending_leaves = LeaveRequest.query.filter_by(
            employee_id=employee.id,
            status="PENDING"
        ).count()
        leave_balances = LeaveService.get_employee_balance(employee.id, year=today.year)

        # 4. Assigned Tasks
        assigned_tasks = Task.query.filter_by(assigned_to=employee.id).count()
        completed_tasks = Task.query.filter_by(assigned_to=employee.id, status="COMPLETED").count()
        pending_tasks = Task.query.filter(
            Task.assigned_to == employee.id,
            Task.status.in_(["TODO", "IN_PROGRESS", "REVIEW", "BLOCKED"])
        ).count()
        overdue_tasks = Task.query.filter(
            Task.assigned_to == employee.id,
            Task.due_date < today,
            ~Task.status.in_(["COMPLETED", "CANCELLED"])
        ).count()

        # 5. Latest Performance Review
        latest_review = (
            PerformanceReview.query.filter_by(employee_id=employee.id)
            .order_by(PerformanceReview.created_at.desc())
            .first()
        )

        performance_data = {
            "has_review": latest_review is not None,
            "latest_cycle_title": latest_review.cycle.title if (latest_review and latest_review.cycle) else None,
            "latest_review_period": latest_review.review_period if latest_review else None,
            "latest_review_status": latest_review.status if latest_review else None,
            # Rating strictly shown ONLY IF review is COMPLETED
            "latest_rating": latest_review.rating if (latest_review and latest_review.status == "COMPLETED") else None,
            "latest_rating_label": (
                RATING_DEFINITIONS[latest_review.rating]["label"]
                if (latest_review and latest_review.status == "COMPLETED" and latest_review.rating in RATING_DEFINITIONS)
                else None
            ),
            "review_id": latest_review.id if latest_review else None
        }

        # 6. Charts: 7-day personal attendance
        attendance_7d = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_att = Attendance.query.filter_by(employee_id=employee.id, work_date=day).all()
            total_day_hours = sum(float(a.total_hours or 0.0) for a in day_att)
            status_label = "Present" if day_att else "Absent"
            attendance_7d.append({
                "date": day.isoformat(),
                "day_name": day.strftime("%a"),
                "hours": round(total_day_hours, 2),
                "status": status_label
            })

        # 7. Charts: Personal task distribution
        emp_task_dist = (
            db.session.query(Task.status, func.count(Task.id))
            .filter(Task.assigned_to == employee.id)
            .group_by(Task.status)
            .all()
        )
        task_distribution = [{"status": s, "count": c} for s, c in emp_task_dist]

        # 8. Charts: Recent leave history (up to 5 items)
        recent_leaves = (
            LeaveRequest.query.filter_by(employee_id=employee.id)
            .order_by(LeaveRequest.created_at.desc())
            .limit(5)
            .all()
        )
        leave_history = [
            {
                "id": lr.id,
                "leave_type": lr.leave_type.name if lr.leave_type else "Leave",
                "start_date": lr.start_date.isoformat(),
                "end_date": lr.end_date.isoformat(),
                "total_days": float(lr.total_days),
                "status": lr.status
            }
            for lr in recent_leaves
        ]

        return {
            "profile": profile,
            "attendance": {
                "today_status": today_status,
                "today_check_in_time": today_check_in,
                "current_shift": current_shift,
                "month_attendance_days": month_attendance_days,
                "month_working_hours": month_working_hours
            },
            "leaves": {
                "pending_requests": pending_leaves,
                "balances": leave_balances
            },
            "tasks": {
                "assigned_tasks": assigned_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
                "overdue_tasks": overdue_tasks
            },
            "performance": performance_data,
            "charts": {
                "attendance_7d": attendance_7d,
                "task_distribution": task_distribution,
                "leave_history": leave_history
            }
        }

    # --------------------------------------------------------------------------
    # 4. Reusable Analytics Aggregations
    # --------------------------------------------------------------------------
    @staticmethod
    def get_attendance_trends(days=7, employee_id=None):
        """Computes daily attendance count and hours worked over the last N days."""
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        query = (
            db.session.query(
                Attendance.work_date,
                func.count(func.distinct(Attendance.employee_id)).label("attendee_count"),
                func.coalesce(func.sum(Attendance.total_hours), 0.0).label("total_hours")
            )
            .filter(Attendance.work_date >= start_date, Attendance.work_date <= today)
        )

        if employee_id:
            try:
                e_uuid = uuid.UUID(str(employee_id)) if not isinstance(employee_id, uuid.UUID) else employee_id
                query = query.filter(Attendance.employee_id == e_uuid)
            except (ValueError, TypeError):
                pass

        results = query.group_by(Attendance.work_date).order_by(Attendance.work_date.asc()).all()
        results_map = {r[0]: (r[1], float(r[2])) for r in results}

        trends = []
        for i in range(days):
            current_day = start_date + timedelta(days=i)
            cnt, hrs = results_map.get(current_day, (0, 0.0))
            trends.append({
                "date": current_day.isoformat(),
                "day_name": current_day.strftime("%a"),
                "count": cnt,
                "hours": round(hrs, 2)
            })

        return trends

    @staticmethod
    def get_department_distribution():
        """Returns headcount distribution across all departments."""
        dept_dist = (
            db.session.query(Department.name, func.count(Employee.id))
            .outerjoin(Employee, and_(Employee.department_id == Department.id, Employee.status == "ACTIVE"))
            .group_by(Department.id, Department.name)
            .order_by(Department.name.asc())
            .all()
        )
        return [{"name": name, "count": count} for name, count in dept_dist]

    @staticmethod
    def get_task_analytics(employee_id=None):
        """Returns task priority and status breakdown, optionally scoped by employee."""
        query = db.session.query(Task.status, func.count(Task.id))
        if employee_id:
            try:
                e_uuid = uuid.UUID(str(employee_id)) if not isinstance(employee_id, uuid.UUID) else employee_id
                query = query.filter(Task.assigned_to == e_uuid)
            except (ValueError, TypeError):
                pass

        status_counts = query.group_by(Task.status).all()

        prio_query = db.session.query(Task.priority, func.count(Task.id))
        if employee_id:
            prio_query = prio_query.filter(Task.assigned_to == e_uuid)
        prio_counts = prio_query.group_by(Task.priority).all()

        return {
            "by_status": [{"status": s, "count": c} for s, c in status_counts],
            "by_priority": [{"priority": p, "count": c} for p, c in prio_counts]
        }

    @staticmethod
    def get_leave_analytics(employee_id=None):
        """Returns leave request status and type distribution."""
        status_q = db.session.query(LeaveRequest.status, func.count(LeaveRequest.id))
        type_q = (
            db.session.query(LeaveType.name, func.count(LeaveRequest.id))
            .join(LeaveRequest, LeaveRequest.leave_type_id == LeaveType.id)
        )

        if employee_id:
            try:
                e_uuid = uuid.UUID(str(employee_id)) if not isinstance(employee_id, uuid.UUID) else employee_id
                status_q = status_q.filter(LeaveRequest.employee_id == e_uuid)
                type_q = type_q.filter(LeaveRequest.employee_id == e_uuid)
            except (ValueError, TypeError):
                pass

        status_counts = status_q.group_by(LeaveRequest.status).all()
        type_counts = type_q.group_by(LeaveType.id, LeaveType.name).all()

        return {
            "by_status": [{"status": s, "count": c} for s, c in status_counts],
            "by_type": [{"type": name, "count": c} for name, c in type_counts]
        }

    @staticmethod
    def get_performance_analytics(cycle_id=None, employee_id=None):
        """Returns rating distribution and cycle statistics."""
        query = db.session.query(PerformanceReview.rating, func.count(PerformanceReview.id))\
                          .filter(PerformanceReview.status == "COMPLETED", PerformanceReview.rating.isnot(None))

        if cycle_id:
            query = query.filter(PerformanceReview.cycle_id == cycle_id)
        if employee_id:
            try:
                e_uuid = uuid.UUID(str(employee_id)) if not isinstance(employee_id, uuid.UUID) else employee_id
                query = query.filter(PerformanceReview.employee_id == e_uuid)
            except (ValueError, TypeError):
                pass

        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for score, count in query.group_by(PerformanceReview.rating).all():
            if score in rating_counts:
                rating_counts[score] = count

        return [
            {
                "score": score,
                "label": RATING_DEFINITIONS[score]["label"],
                "count": rating_counts[score]
            }
            for score in range(1, 6)
        ]

