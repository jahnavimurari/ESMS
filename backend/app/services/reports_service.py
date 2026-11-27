import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import func, or_, and_
from app.extension_registry import db
from app.models.employee import Employee
from app.models.department import Department
from app.models.user import User
from app.models.attendance import Attendance
from app.models.leave import LeaveRequest, LeaveType
from app.models.task import Task
from app.models.performance import PerformanceCycle, PerformanceReview, RATING_DEFINITIONS
from app.services.export_service import ExportFormatter

class ReportsService:
    """Service providing filtering, tabular data extraction, and multi-format exports for ESMS reports."""

    # --------------------------------------------------------------------------
    # 1. Employee Reports
    # --------------------------------------------------------------------------
    @staticmethod
    def get_employee_report_data(filters=None, current_user=None):
        """
        Extracts employee report data with RBAC security:
        - ADMIN / HR: full organization list, contact info visible.
        - EMPLOYEE: strictly forbidden (raises PermissionError).
        """
        if current_user and current_user.role == "EMPLOYEE":
            raise PermissionError("Employees are not authorized to view organization-wide employee reports.")

        filters = filters or {}
        query = db.session.query(Employee).join(Department, Employee.department_id == Department.id)

        # Filters
        dept_id = filters.get("department_id")
        if dept_id:
            query = query.filter(Employee.department_id == dept_id)

        status = filters.get("status")
        if status:
            query = query.filter(Employee.status == status)

        start_date = filters.get("start_date")
        if start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(Employee.joining_date >= sd)
            except ValueError:
                pass

        end_date = filters.get("end_date")
        if end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(Employee.joining_date <= ed)
            except ValueError:
                pass

        employees = query.order_by(Employee.employee_code.asc()).all()

        headers = [
            "Employee Code", "Full Name", "Department", "Designation",
            "Employment Type", "Joining Date", "Status", "Email", "Phone"
        ]

        rows = []
        records = []
        for emp in employees:
            email = emp.user.email if emp.user else "N/A"
            phone = emp.phone or "N/A"
            dept_name = emp.department.name if emp.department else "Unassigned"
            joining_str = emp.joining_date.isoformat() if emp.joining_date else ""

            row = [
                emp.employee_code,
                emp.full_name,
                dept_name,
                emp.designation,
                emp.employment_type,
                joining_str,
                emp.status,
                email,
                phone
            ]
            rows.append(row)
            records.append({
                "employee_code": emp.employee_code,
                "full_name": emp.full_name,
                "department": dept_name,
                "designation": emp.designation,
                "employment_type": emp.employment_type,
                "joining_date": joining_str,
                "status": emp.status,
                "email": email,
                "phone": phone
            })

        return {
            "title": "Employee Directory Report",
            "headers": headers,
            "rows": rows,
            "records": records,
            "total_count": len(records)
        }

    # --------------------------------------------------------------------------
    # 2. Attendance Reports
    # --------------------------------------------------------------------------
    @staticmethod
    def get_attendance_report_data(filters=None, current_user=None):
        """
        Extracts attendance report data with RBAC security:
        - ADMIN / HR: organization-wide with optional filters.
        - EMPLOYEE: strictly filtered to their own attendance sessions.
        """
        filters = filters or {}
        query = db.session.query(Attendance).join(Employee, Attendance.employee_id == Employee.id)

        # RBAC Enforcement
        if current_user and current_user.role == "EMPLOYEE":
            emp = Employee.query.filter_by(user_id=current_user.id).first()
            if not emp:
                raise ValueError("No employee profile found for user.")
            query = query.filter(Attendance.employee_id == emp.id)
        else:
            # HR/Admin optional filters
            emp_id = filters.get("employee_id")
            if emp_id:
                try:
                    e_uuid = uuid.UUID(str(emp_id))
                    query = query.filter(Attendance.employee_id == e_uuid)
                except (ValueError, TypeError):
                    pass

            dept_id = filters.get("department_id")
            if dept_id:
                query = query.filter(Employee.department_id == dept_id)

        # Common filters
        status = filters.get("status")
        if status:
            query = query.filter(Attendance.status == status)

        start_date = filters.get("start_date")
        if start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(Attendance.work_date >= sd)
            except ValueError:
                pass

        end_date = filters.get("end_date")
        if end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(Attendance.work_date <= ed)
            except ValueError:
                pass

        records_obj = query.order_by(Attendance.work_date.desc(), Attendance.shift_number.asc()).all()

        headers = [
            "Employee Code", "Employee Name", "Department", "Work Date",
            "Shift", "Check In", "Check Out", "Working Hours", "Status", "Notes"
        ]

        rows = []
        records = []
        total_hours_sum = Decimal("0.00")

        for att in records_obj:
            emp = att.employee
            dept_name = emp.department.name if (emp and emp.department) else "Unassigned"
            emp_name = emp.full_name if emp else "Unknown"
            emp_code = emp.employee_code if emp else "Unknown"
            date_str = att.work_date.isoformat() if att.work_date else ""
            in_str = att.check_in.strftime("%H:%M:%S") if att.check_in else ""
            out_str = att.check_out.strftime("%H:%M:%S") if att.check_out else "Active (Not Checked Out)"
            hrs = float(att.total_hours or 0.0)
            total_hours_sum += Decimal(str(hrs))

            row = [
                emp_code,
                emp_name,
                dept_name,
                date_str,
                att.shift_number,
                in_str,
                out_str,
                hrs,
                att.status,
                att.notes or ""
            ]
            rows.append(row)
            records.append({
                "employee_code": emp_code,
                "employee_name": emp_name,
                "department": dept_name,
                "work_date": date_str,
                "shift_number": att.shift_number,
                "check_in": in_str,
                "check_out": out_str,
                "working_hours": hrs,
                "status": att.status,
                "notes": att.notes or ""
            })

        return {
            "title": "Attendance & Shift Summary Report",
            "headers": headers,
            "rows": rows,
            "records": records,
            "total_count": len(records),
            "total_working_hours": float(total_hours_sum)
        }

    # --------------------------------------------------------------------------
    # 3. Leave Reports
    # --------------------------------------------------------------------------
    @staticmethod
    def get_leave_report_data(filters=None, current_user=None):
        """
        Extracts leave report data with RBAC security:
        - ADMIN / HR: full or filtered leave requests, reasons visible.
        - EMPLOYEE: strictly filtered to their own leave requests.
        """
        filters = filters or {}
        query = (
            db.session.query(LeaveRequest)
            .join(Employee, LeaveRequest.employee_id == Employee.id)
            .join(LeaveType, LeaveRequest.leave_type_id == LeaveType.id)
            .outerjoin(User, LeaveRequest.reviewed_by == User.id)
        )

        if current_user and current_user.role == "EMPLOYEE":
            emp = Employee.query.filter_by(user_id=current_user.id).first()
            if not emp:
                raise ValueError("No employee profile found for user.")
            query = query.filter(LeaveRequest.employee_id == emp.id)
        else:
            emp_id = filters.get("employee_id")
            if emp_id:
                try:
                    e_uuid = uuid.UUID(str(emp_id))
                    query = query.filter(LeaveRequest.employee_id == e_uuid)
                except (ValueError, TypeError):
                    pass

            dept_id = filters.get("department_id")
            if dept_id:
                query = query.filter(Employee.department_id == dept_id)

        leave_type_id = filters.get("leave_type_id")
        if leave_type_id:
            query = query.filter(LeaveRequest.leave_type_id == leave_type_id)

        status = filters.get("status")
        if status:
            query = query.filter(LeaveRequest.status == status)

        start_date = filters.get("start_date")
        if start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(LeaveRequest.start_date >= sd)
            except ValueError:
                pass

        end_date = filters.get("end_date")
        if end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(LeaveRequest.end_date <= ed)
            except ValueError:
                pass

        leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()

        headers = [
            "Employee Code", "Employee Name", "Department", "Leave Type",
            "Start Date", "End Date", "Total Days", "Status",
            "Reason", "Reviewer", "Reviewed At", "Reviewer Comments"
        ]

        rows = []
        records = []
        for lr in leave_requests:
            emp = lr.employee
            emp_code = emp.employee_code if emp else "Unknown"
            emp_name = emp.full_name if emp else "Unknown"
            dept_name = emp.department.name if (emp and emp.department) else "Unassigned"
            lt_name = lr.leave_type.name if lr.leave_type else "Leave"
            reviewer_email = lr.reviewer.email if lr.reviewer else "Pending"
            reviewed_at_str = lr.reviewed_at.strftime("%Y-%m-%d %H:%M") if hasattr(lr, "reviewed_at") and lr.reviewed_at else "N/A"

            row = [
                emp_code,
                emp_name,
                dept_name,
                lt_name,
                lr.start_date.isoformat(),
                lr.end_date.isoformat(),
                float(lr.total_days),
                lr.status,
                lr.reason,
                reviewer_email,
                reviewed_at_str,
                lr.reviewer_comments or ""
            ]
            rows.append(row)
            records.append({
                "employee_code": emp_code,
                "employee_name": emp_name,
                "department": dept_name,
                "leave_type": lt_name,
                "start_date": lr.start_date.isoformat(),
                "end_date": lr.end_date.isoformat(),
                "total_days": float(lr.total_days),
                "status": lr.status,
                "reason": lr.reason,
                "reviewer": reviewer_email,
                "reviewed_at": reviewed_at_str,
                "reviewer_comments": lr.reviewer_comments or ""
            })

        return {
            "title": "Leave Management & Approvals Report",
            "headers": headers,
            "rows": rows,
            "records": records,
            "total_count": len(records)
        }

    # --------------------------------------------------------------------------
    # 4. Task Reports
    # --------------------------------------------------------------------------
    @staticmethod
    def get_task_report_data(filters=None, current_user=None):
        """
        Extracts task report data with RBAC security:
        - ADMIN / HR: full or filtered tasks across the organization.
        - EMPLOYEE: strictly filtered to tasks assigned to them.
        """
        filters = filters or {}
        query = db.session.query(Task).join(Employee, Task.assigned_to == Employee.id)

        if current_user and current_user.role == "EMPLOYEE":
            emp = Employee.query.filter_by(user_id=current_user.id).first()
            if not emp:
                raise ValueError("No employee profile found for user.")
            query = query.filter(Task.assigned_to == emp.id)
        else:
            emp_id = filters.get("employee_id")
            if emp_id:
                try:
                    e_uuid = uuid.UUID(str(emp_id))
                    query = query.filter(Task.assigned_to == e_uuid)
                except (ValueError, TypeError):
                    pass

            dept_id = filters.get("department_id")
            if dept_id:
                query = query.filter(or_(Task.department_id == dept_id, Employee.department_id == dept_id))

        priority = filters.get("priority")
        if priority:
            query = query.filter(Task.priority == priority)

        status = filters.get("status")
        if status:
            if status == "OVERDUE":
                today = date.today()
                query = query.filter(Task.due_date < today, ~Task.status.in_(["COMPLETED", "CANCELLED"]))
            else:
                query = query.filter(Task.status == status)

        start_date = filters.get("start_date")
        if start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(Task.due_date >= sd)
            except ValueError:
                pass

        end_date = filters.get("end_date")
        if end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(Task.due_date <= ed)
            except ValueError:
                pass

        tasks = query.order_by(Task.due_date.asc().nullslast()).all()
        today = date.today()

        headers = [
            "Task Title", "Assigned Employee", "Department", "Category",
            "Priority", "Status", "Start Date", "Due Date",
            "Completed At", "Is Overdue"
        ]

        rows = []
        records = []
        for t in tasks:
            emp = t.assignee
            emp_name = emp.full_name if emp else "Unassigned"
            dept_name = t.department.name if t.department else (emp.department.name if (emp and emp.department) else "Unassigned")
            is_overdue = bool(t.due_date and t.due_date < today and t.status not in ["COMPLETED", "CANCELLED"])
            comp_str = t.completed_at.strftime("%Y-%m-%d %H:%M") if t.completed_at else "N/A"
            start_str = t.start_date.isoformat() if t.start_date else "N/A"
            due_str = t.due_date.isoformat() if t.due_date else "N/A"

            row = [
                t.title,
                emp_name,
                dept_name,
                t.category or "General",
                t.priority,
                t.status,
                start_str,
                due_str,
                comp_str,
                "YES" if is_overdue else "NO"
            ]
            rows.append(row)
            records.append({
                "title": t.title,
                "assigned_employee": emp_name,
                "department": dept_name,
                "category": t.category or "General",
                "priority": t.priority,
                "status": t.status,
                "start_date": start_str,
                "due_date": due_str,
                "completed_at": comp_str,
                "is_overdue": is_overdue
            })

        return {
            "title": "Task Assignment & Progress Report",
            "headers": headers,
            "rows": rows,
            "records": records,
            "total_count": len(records)
        }

    # --------------------------------------------------------------------------
    # 5. Performance Reports
    # --------------------------------------------------------------------------
    @staticmethod
    def get_performance_report_data(filters=None, current_user=None):
        """
        Extracts performance reviews with RBAC security:
        - ADMIN / HR: full or cycle-filtered reviews.
        - EMPLOYEE: strictly their own reviews. Manager feedback and rating hidden if uncompleted.
        """
        filters = filters or {}
        query = (
            db.session.query(PerformanceReview)
            .join(Employee, PerformanceReview.employee_id == Employee.id)
            .join(PerformanceCycle, PerformanceReview.cycle_id == PerformanceCycle.id)
            .outerjoin(User, PerformanceReview.reviewer_id == User.id)
        )

        is_employee = current_user and current_user.role == "EMPLOYEE"
        if is_employee:
            emp = Employee.query.filter_by(user_id=current_user.id).first()
            if not emp:
                raise ValueError("No employee profile found for user.")
            query = query.filter(PerformanceReview.employee_id == emp.id)
        else:
            emp_id = filters.get("employee_id")
            if emp_id:
                try:
                    e_uuid = uuid.UUID(str(emp_id))
                    query = query.filter(PerformanceReview.employee_id == e_uuid)
                except (ValueError, TypeError):
                    pass

            dept_id = filters.get("department_id")
            if dept_id:
                query = query.filter(Employee.department_id == dept_id)

        cycle_id = filters.get("cycle_id")
        if cycle_id:
            query = query.filter(PerformanceReview.cycle_id == cycle_id)

        status = filters.get("status")
        if status:
            query = query.filter(PerformanceReview.status == status)

        reviews = query.order_by(PerformanceReview.created_at.desc()).all()

        headers = [
            "Employee Code", "Employee Name", "Department", "Cycle Title",
            "Review Period", "Status", "Self Rating", "Manager Rating",
            "Rating Label", "Reviewer", "Completed Date", "Manager Feedback"
        ]

        rows = []
        records = []
        completed_ratings = []

        for rev in reviews:
            emp = rev.employee
            emp_code = emp.employee_code if emp else "Unknown"
            emp_name = emp.full_name if emp else "Unknown"
            dept_name = emp.department.name if (emp and emp.department) else "Unassigned"
            cycle_title = rev.cycle.title if rev.cycle else "General"
            reviewer_email = rev.reviewer.email if rev.reviewer else "Unassigned"
            comp_str = rev.completed_at.strftime("%Y-%m-%d %H:%M") if rev.completed_at else "In Progress"

            # Rating masking rules:
            # If review is NOT completed, rating and manager feedback are hidden/restricted
            if rev.status == "COMPLETED":
                mgr_rating = rev.rating
                rating_label = RATING_DEFINITIONS[rev.rating]["label"] if rev.rating in RATING_DEFINITIONS else "Rated"
                mgr_feedback = rev.manager_feedback or "Completed without comments"
                if rev.rating is not None:
                    completed_ratings.append(rev.rating)
            else:
                if is_employee:
                    mgr_rating = "Restricted (In Progress)"
                    rating_label = "Pending Completion"
                    mgr_feedback = "Restricted until evaluation completed"
                else:
                    mgr_rating = rev.rating if rev.rating is not None else "Pending"
                    rating_label = "Draft"
                    mgr_feedback = rev.manager_feedback or "Draft feedback"

            row = [
                emp_code,
                emp_name,
                dept_name,
                cycle_title,
                rev.review_period,
                rev.status,
                rev.self_rating if rev.self_rating is not None else "Pending",
                mgr_rating,
                rating_label,
                reviewer_email,
                comp_str,
                mgr_feedback
            ]
            rows.append(row)
            records.append({
                "employee_code": emp_code,
                "employee_name": emp_name,
                "department": dept_name,
                "cycle_title": cycle_title,
                "review_period": rev.review_period,
                "status": rev.status,
                "self_rating": rev.self_rating,
                "manager_rating": mgr_rating,
                "rating_label": rating_label,
                "reviewer": reviewer_email,
                "completed_at": comp_str,
                "manager_feedback": mgr_feedback
            })

        avg_rating = round(sum(completed_ratings) / len(completed_ratings), 2) if completed_ratings else 0.0

        return {
            "title": "Performance Reviews & Appraisal Report",
            "headers": headers,
            "rows": rows,
            "records": records,
            "total_count": len(records),
            "completed_count": len(completed_ratings),
            "average_completed_rating": avg_rating
        }

    # --------------------------------------------------------------------------
    # 6. Format Exporter Dispatcher
    # --------------------------------------------------------------------------
    @staticmethod
    def export_data(report_data, export_format="csv", filter_summary=None):
        """
        Dispatches report data to the requested file format exporter.
        Returns: (file_bytes, content_type, filename_extension)
        """
        export_format = str(export_format).lower().strip()
        title = report_data.get("title", "Report")
        headers = report_data.get("headers", [])
        rows = report_data.get("rows", [])

        if export_format == "csv":
            content = ExportFormatter.to_csv(headers, rows)
            return content, "text/csv; charset=utf-8", "csv"
        elif export_format in ["xlsx", "excel"]:
            content = ExportFormatter.to_excel(title, headers, rows, filter_summary)
            return content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
        elif export_format == "pdf":
            content = ExportFormatter.to_pdf(title, headers, rows, filter_summary)
            return content, "application/pdf", "pdf"
        else:
            raise ValueError(f"Unsupported export format '{export_format}'. Supported formats: csv, xlsx, pdf.")
