import uuid
from datetime import datetime, timezone, date
from sqlalchemy import or_, and_, func
from app.extension_registry import db
from app.models.performance import PerformanceCycle, PerformanceReview, RATING_DEFINITIONS
from app.models.employee import Employee
from app.models.department import Department
from app.models.user import User
from app.models.audit import AuditLog

class PerformanceService:
    """Service layer managing performance cycles, review lifecycles, RBAC, and audit trails."""

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
    # Performance Cycle Management
    # --------------------------------------------------------------------------
    @staticmethod
    def create_cycle(creator_user_id, data: dict, ip_address: str = None):
        """Creates a new performance cycle (HR / Admin)."""
        start = data["start_date"]
        end = data["end_date"]
        due = data["due_date"]

        if end < start:
            raise ValueError("End date cannot be earlier than start date.")
        if due < start:
            raise ValueError("Due date cannot be earlier than start date.")

        cycle = PerformanceCycle(
            title=data["title"].strip(),
            description=data.get("description", "").strip() if data.get("description") else None,
            start_date=start,
            end_date=end,
            due_date=due,
            status=data.get("status", "ACTIVE"),
            created_by=creator_user_id,
        )
        db.session.add(cycle)
        db.session.flush()

        audit = AuditLog(
            user_id=creator_user_id,
            action="CREATE_PERFORMANCE_CYCLE",
            target_entity="performance_cycles",
            target_id=str(cycle.id),
            new_state={
                "title": cycle.title,
                "start_date": cycle.start_date.isoformat(),
                "end_date": cycle.end_date.isoformat(),
                "due_date": cycle.due_date.isoformat(),
                "status": cycle.status,
            },
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return cycle.to_dict()

    @staticmethod
    def update_cycle(cycle_id: int, data: dict, user_id, ip_address: str = None):
        """Updates an existing performance cycle (HR / Admin)."""
        cycle = db.session.get(PerformanceCycle, cycle_id)
        if not cycle:
            raise ValueError("Performance cycle not found.")

        start = data.get("start_date", cycle.start_date)
        end = data.get("end_date", cycle.end_date)
        due = data.get("due_date", cycle.due_date)

        if end < start:
            raise ValueError("End date cannot be earlier than start date.")
        if due < start:
            raise ValueError("Due date cannot be earlier than start date.")

        prev_state = {
            "title": cycle.title,
            "description": cycle.description,
            "start_date": cycle.start_date.isoformat(),
            "end_date": cycle.end_date.isoformat(),
            "due_date": cycle.due_date.isoformat(),
            "status": cycle.status
        }

        changes = {}
        if "title" in data and data["title"] != cycle.title:
            changes["title"] = data["title"].strip()
            cycle.title = data["title"].strip()
        if "description" in data and data["description"] != cycle.description:
            changes["description"] = data["description"]
            cycle.description = data["description"]
        if "start_date" in data and data["start_date"] != cycle.start_date:
            changes["start_date"] = data["start_date"].isoformat()
            cycle.start_date = data["start_date"]
        if "end_date" in data and data["end_date"] != cycle.end_date:
            changes["end_date"] = data["end_date"].isoformat()
            cycle.end_date = data["end_date"]
        if "due_date" in data and data["due_date"] != cycle.due_date:
            changes["due_date"] = data["due_date"].isoformat()
            cycle.due_date = data["due_date"]
        if "status" in data and data["status"] != cycle.status:
            changes["status"] = data["status"]
            cycle.status = data["status"]

        if changes:
            audit = AuditLog(
                user_id=user_id,
                action="UPDATE_PERFORMANCE_CYCLE",
                target_entity="performance_cycles",
                target_id=str(cycle.id),
                previous_state=prev_state,
                new_state=changes,
                ip_address=ip_address
            )
            db.session.add(audit)
            db.session.commit()

        return cycle.to_dict()

    @staticmethod
    def update_cycle_status(cycle_id: int, status: str, user_id, ip_address: str = None):
        """Updates the status of a cycle (ACTIVE or CLOSED)."""
        cycle = db.session.get(PerformanceCycle, cycle_id)
        if not cycle:
            raise ValueError("Performance cycle not found.")

        if status not in ("ACTIVE", "CLOSED"):
            raise ValueError("Status must be ACTIVE or CLOSED.")

        if cycle.status == status:
            return cycle.to_dict()

        old_status = cycle.status
        cycle.status = status

        audit = AuditLog(
            user_id=user_id,
            action="CYCLE_STATUS_CHANGE",
            target_entity="performance_cycles",
            target_id=str(cycle.id),
            previous_state={"status": old_status},
            new_state={"status": status},
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return cycle.to_dict()

    @staticmethod
    def list_cycles(status: str = None, page: int = 1, per_page: int = 20):
        """Lists performance cycles with pagination and filtering."""
        query = PerformanceCycle.query
        if status:
            query = query.filter_by(status=status.upper())

        query = query.order_by(PerformanceCycle.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [cycle.to_dict() for cycle in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }

    @staticmethod
    def get_cycle_by_id(cycle_id: int):
        """Retrieves single cycle with detailed status metrics."""
        cycle = db.session.get(PerformanceCycle, cycle_id)
        if not cycle:
            raise ValueError("Performance cycle not found.")
        return cycle.to_dict()

    # --------------------------------------------------------------------------
    # Performance Review Initiation & Management
    # --------------------------------------------------------------------------
    @staticmethod
    def create_review(creator_user_id, data: dict, ip_address: str = None):
        """Initiates a performance review for an active employee in an active cycle."""
        cycle_id = data.get("cycle_id")
        cycle = db.session.get(PerformanceCycle, cycle_id)
        if not cycle:
            raise ValueError("Performance cycle not found.")
        if cycle.status != "ACTIVE":
            raise ValueError("Cannot initiate review in a CLOSED cycle.")

        try:
            emp_uuid = uuid.UUID(str(data["employee_id"]))
        except (ValueError, TypeError):
            raise ValueError("Invalid employee identifier.")

        employee = db.session.get(Employee, emp_uuid)
        if not employee:
            raise ValueError("Employee not found.")
        if employee.status != "ACTIVE":
            raise ValueError(f"Performance reviews can only be created for ACTIVE employees. Employee is {employee.status}.")

        # Check uniqueness constraint: one review per employee per cycle
        existing = PerformanceReview.query.filter_by(employee_id=emp_uuid, cycle_id=cycle_id).first()
        if existing:
            raise ValueError("A performance review already exists for this employee in this cycle.")

        reviewer_id = None
        if data.get("reviewer_id"):
            try:
                r_uuid = uuid.UUID(str(data["reviewer_id"]))
                reviewer_user = db.session.get(User, r_uuid)
                if not reviewer_user:
                    raise ValueError("Assigned reviewer user not found.")
                reviewer_id = r_uuid
            except (ValueError, TypeError):
                raise ValueError("Invalid reviewer identifier.")

        review_period = data.get("review_period") or cycle.title

        review = PerformanceReview(
            cycle_id=cycle.id,
            employee_id=employee.id,
            reviewer_id=reviewer_id,
            review_period=review_period.strip(),
            status="DRAFT"
        )
        db.session.add(review)
        db.session.flush()

        audit = AuditLog(
            user_id=creator_user_id,
            action="CREATE_PERFORMANCE_REVIEW",
            target_entity="performance_reviews",
            target_id=str(review.id),
            new_state={
                "cycle_id": cycle.id,
                "cycle_title": cycle.title,
                "employee_id": str(employee.id),
                "employee_name": employee.full_name,
                "reviewer_id": str(reviewer_id) if reviewer_id else None,
                "review_period": review.review_period,
                "status": review.status,
            },
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return review.to_dict()

    @staticmethod
    def list_reviews(user, role: str, filters: dict, page: int = 1, per_page: int = 20):
        """Lists reviews with strict RBAC: Employees see only own; HR/Admin see all with filters."""
        query = PerformanceReview.query

        if role == "EMPLOYEE":
            employee = Employee.query.filter_by(user_id=user.id).first()
            if not employee:
                return {
                    "items": [], "total": 0, "page": page, "pages": 0, "per_page": per_page,
                    "has_next": False, "has_prev": False
                }
            query = query.filter(PerformanceReview.employee_id == employee.id)
        else:
            # HR / Admin filters
            if filters.get("employee_id"):
                try:
                    e_uuid = uuid.UUID(str(filters["employee_id"]))
                    query = query.filter(PerformanceReview.employee_id == e_uuid)
                except (ValueError, TypeError):
                    pass

            if filters.get("reviewer_id"):
                try:
                    r_uuid = uuid.UUID(str(filters["reviewer_id"]))
                    query = query.filter(PerformanceReview.reviewer_id == r_uuid)
                except (ValueError, TypeError):
                    pass

            if filters.get("department_id"):
                query = query.join(Employee, PerformanceReview.employee_id == Employee.id)\
                             .filter(Employee.department_id == filters["department_id"])

        if filters.get("cycle_id"):
            query = query.filter(PerformanceReview.cycle_id == filters["cycle_id"])

        if filters.get("status"):
            query = query.filter(PerformanceReview.status == filters["status"].upper())

        if filters.get("search"):
            term = f"%{filters['search'].strip()}%"
            query = query.join(Employee, PerformanceReview.employee_id == Employee.id)\
                         .filter(or_(
                             Employee.first_name.ilike(term),
                             Employee.last_name.ilike(term),
                             Employee.employee_code.ilike(term),
                             PerformanceReview.review_period.ilike(term)
                         ))

        query = query.order_by(PerformanceReview.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [r.to_dict() for r in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }

    @staticmethod
    def get_review_by_id(review_id: int, user, role: str):
        """Retrieves a single performance review with strict RBAC authorization."""
        review = db.session.get(PerformanceReview, review_id)
        if not review:
            raise ValueError("Performance review not found.")

        if role == "EMPLOYEE":
            employee = Employee.query.filter_by(user_id=user.id).first()
            if not employee or review.employee_id != employee.id:
                raise PermissionError("Access denied: You can only view your own performance reviews.")

        return review.to_dict()

    # --------------------------------------------------------------------------
    # Employee Self-Assessment
    # --------------------------------------------------------------------------
    @staticmethod
    def update_self_assessment(review_id: int, user, role: str, data: dict, ip_address: str = None):
        """Drafts or updates self-assessment fields while review is in DRAFT or SELF_ASSESSMENT."""
        review = db.session.get(PerformanceReview, review_id)
        if not review:
            raise ValueError("Performance review not found.")

        if role == "EMPLOYEE":
            employee = Employee.query.filter_by(user_id=user.id).first()
            if not employee or review.employee_id != employee.id:
                raise PermissionError("Access denied: You can only edit your own self-assessment.")

        if review.status in ("COMPLETED", "CANCELLED"):
            raise ValueError(f"Self-assessment cannot be modified when review is {review.status}.")
        if review.status == "MANAGER_REVIEW":
            raise ValueError("Self-assessment has already been submitted and is currently under manager review.")

        if "self_rating" in data:
            rating = data["self_rating"]
            if rating is not None and (rating < 1 or rating > 5):
                raise ValueError("Self-rating must be an integer between 1 and 5.")
            review.self_rating = rating

        if "accomplishments" in data:
            review.accomplishments = data["accomplishments"]
        if "challenges" in data:
            review.challenges = data["challenges"]
        if "skills_learned" in data:
            review.skills_learned = data["skills_learned"]
        if "goals_achievement" in data:
            review.goals_achievement = data["goals_achievement"]

        if review.status == "DRAFT":
            review.status = "SELF_ASSESSMENT"

        db.session.commit()
        return review.to_dict()

    @staticmethod
    def submit_self_assessment(review_id: int, user, role: str, ip_address: str = None):
        """Submits the completed self-assessment, advancing status to MANAGER_REVIEW."""
        review = db.session.get(PerformanceReview, review_id)
        if not review:
            raise ValueError("Performance review not found.")

        if role == "EMPLOYEE":
            employee = Employee.query.filter_by(user_id=user.id).first()
            if not employee or review.employee_id != employee.id:
                raise PermissionError("Access denied: You can only submit your own self-assessment.")

        if review.status in ("COMPLETED", "CANCELLED"):
            raise ValueError(f"Cannot submit self-assessment for review that is already {review.status}.")
        if review.status == "MANAGER_REVIEW":
            raise ValueError("Self-assessment has already been submitted.")

        review.status = "MANAGER_REVIEW"
        review.submitted_at = datetime.now(timezone.utc)

        audit = AuditLog(
            user_id=user.id,
            action="SUBMIT_SELF_ASSESSMENT",
            target_entity="performance_reviews",
            target_id=str(review.id),
            new_state={
                "self_rating": review.self_rating,
                "status": review.status,
                "submitted_at": review.submitted_at.isoformat(),
            },
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return review.to_dict()

    # --------------------------------------------------------------------------
    # Manager Evaluation & Completion
    # --------------------------------------------------------------------------
    @staticmethod
    def submit_manager_review(review_id: int, reviewer_user, role: str, data: dict, ip_address: str = None):
        """Submits manager evaluation fields (rating 1-5, feedback, strengths, improvement, development plan)."""
        review = db.session.get(PerformanceReview, review_id)
        if not review:
            raise ValueError("Performance review not found.")

        if role not in ("ADMIN", "HR") and review.reviewer_id != reviewer_user.id:
            raise PermissionError("Access denied: Only the designated reviewer, HR, or Admin can submit manager evaluation.")

        if review.status in ("COMPLETED", "CANCELLED"):
            raise ValueError(f"Cannot modify manager evaluation for review that is already {review.status}.")

        rating = data.get("rating")
        if rating is None or rating < 1 or rating > 5:
            raise ValueError("Manager rating is required and must be an integer between 1 and 5.")

        feedback = data.get("manager_feedback")
        if not feedback or len(feedback.strip()) < 5:
            raise ValueError("Manager feedback is required (at least 5 characters).")

        review.rating = rating
        review.manager_feedback = feedback.strip()
        review.strengths = data.get("strengths", "").strip() if data.get("strengths") else None
        review.areas_for_improvement = data.get("areas_for_improvement", "").strip() if data.get("areas_for_improvement") else None
        review.development_plan = data.get("development_plan", "").strip() if data.get("development_plan") else None
        review.reviewer_id = reviewer_user.id

        audit = AuditLog(
            user_id=reviewer_user.id,
            action="SUBMIT_MANAGER_EVALUATION",
            target_entity="performance_reviews",
            target_id=str(review.id),
            new_state={
                "rating": review.rating,
                "rating_label": RATING_DEFINITIONS[rating]["label"],
                "reviewer_id": str(reviewer_user.id),
            },
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return review.to_dict()

    @staticmethod
    def complete_review(review_id: int, user, role: str, ip_address: str = None):
        """Finalizes the review into COMPLETED status."""
        review = db.session.get(PerformanceReview, review_id)
        if not review:
            raise ValueError("Performance review not found.")

        if role not in ("ADMIN", "HR") and review.reviewer_id != user.id:
            raise PermissionError("Access denied: Only the designated reviewer, HR, or Admin can complete a review.")

        if review.status == "COMPLETED":
            return review.to_dict()

        if review.status == "CANCELLED":
            raise ValueError("Cannot complete a cancelled review.")

        if not review.rating or not review.manager_feedback:
            raise ValueError("Cannot complete review without a manager rating (1-5) and manager feedback.")

        review.status = "COMPLETED"
        review.completed_at = datetime.now(timezone.utc)

        audit = AuditLog(
            user_id=user.id,
            action="COMPLETE_PERFORMANCE_REVIEW",
            target_entity="performance_reviews",
            target_id=str(review.id),
            new_state={
                "final_rating": review.rating,
                "rating_label": RATING_DEFINITIONS[review.rating]["label"],
                "completed_at": review.completed_at.isoformat(),
                "completed_by": str(user.id),
            },
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return review.to_dict()

    # --------------------------------------------------------------------------
    # Reopen Completed Review (HR / Admin only, with strict AuditLog)
    # --------------------------------------------------------------------------
    @staticmethod
    def reopen_review(review_id: int, user, role: str, reason: str, ip_address: str = None):
        """Reopens a COMPLETED review for re-evaluation. Requires HR / Admin role, reason, and writes AuditLog."""
        if role not in ("ADMIN", "HR"):
            raise PermissionError("Access denied: Only HR or Admin can reopen a completed review.")

        review = db.session.get(PerformanceReview, review_id)
        if not review:
            raise ValueError("Performance review not found.")

        if review.status != "COMPLETED":
            raise ValueError(f"Only COMPLETED reviews can be reopened. Current status is {review.status}.")

        if not reason or len(reason.strip()) < 5:
            raise ValueError("A valid justification reason (at least 5 characters) is required to reopen a review.")

        old_status = review.status
        review.status = "MANAGER_REVIEW"

        audit = AuditLog(
            user_id=user.id,
            action="REOPEN_PERFORMANCE_REVIEW",
            target_entity="performance_reviews",
            target_id=str(review.id),
            previous_state={"status": old_status},
            new_state={
                "status": "MANAGER_REVIEW",
                "reason": reason.strip(),
                "reopened_by": str(user.id),
                "reopened_at": datetime.now(timezone.utc).isoformat(),
            },
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()

        return review.to_dict()

    # --------------------------------------------------------------------------
    # Performance Summary & History
    # --------------------------------------------------------------------------
    @staticmethod
    def get_summary():
        """Returns organizational performance distribution and completion statistics."""
        total_reviews = PerformanceReview.query.count()
        completed = PerformanceReview.query.filter_by(status="COMPLETED").count()
        in_progress = PerformanceReview.query.filter(PerformanceReview.status.in_(["DRAFT", "SELF_ASSESSMENT", "MANAGER_REVIEW"])).count()
        cancelled = PerformanceReview.query.filter_by(status="CANCELLED").count()

        # Ratings distribution for completed reviews (1 to 5)
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        ratings_query = db.session.query(
            PerformanceReview.rating, func.count(PerformanceReview.id)
        ).filter(
            PerformanceReview.status == "COMPLETED",
            PerformanceReview.rating.isnot(None)
        ).group_by(PerformanceReview.rating).all()

        for score, count in ratings_query:
            if score in rating_counts:
                rating_counts[score] = count

        avg_rating_res = db.session.query(func.avg(PerformanceReview.rating)).filter(
            PerformanceReview.status == "COMPLETED",
            PerformanceReview.rating.isnot(None)
        ).scalar()
        avg_rating = round(float(avg_rating_res), 2) if avg_rating_res is not None else 0.0

        cycles_count = PerformanceCycle.query.count()
        active_cycles_count = PerformanceCycle.query.filter_by(status="ACTIVE").count()

        return {
            "total_reviews": total_reviews,
            "status_breakdown": {
                "completed": completed,
                "in_progress": in_progress,
                "cancelled": cancelled,
                "draft": PerformanceReview.query.filter_by(status="DRAFT").count(),
                "self_assessment": PerformanceReview.query.filter_by(status="SELF_ASSESSMENT").count(),
                "manager_review": PerformanceReview.query.filter_by(status="MANAGER_REVIEW").count(),
            },
            "average_rating": avg_rating,
            "ratings_distribution": [
                {
                    "score": score,
                    "label": RATING_DEFINITIONS[score]["label"],
                    "description": RATING_DEFINITIONS[score]["description"],
                    "count": rating_counts[score]
                }
                for score in range(1, 6)
            ],
            "total_cycles": cycles_count,
            "active_cycles": active_cycles_count,
        }

    @staticmethod
    def get_review_history(review_id: int):
        """Retrieves audit trail events for this review."""
        review = db.session.get(PerformanceReview, review_id)
        if not review:
            raise ValueError("Performance review not found.")

        logs = AuditLog.query.filter_by(
            target_entity="performance_reviews",
            target_id=str(review_id)
        ).order_by(AuditLog.timestamp.desc()).all()

        return [log.to_dict() for log in logs]

    @staticmethod
    def get_rating_scale():
        """Returns reference dictionary of 5-point rating scale definitions."""
        return list(RATING_DEFINITIONS.values())
