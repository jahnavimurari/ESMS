import uuid
from datetime import datetime, timezone
from sqlalchemy import or_, func, text
from app.extension_registry import db
from app.models.user import User
from app.models.employee import Employee
from app.models.audit import AuditLog
from app.models.revoked_token import RevokedToken
from app.services.auth_service import AuthService

class AdminService:
    """Encapsulates system administration, user management, audit review, and health telemetry."""

    # --------------------------------------------------------------------------
    # 1. User Administration
    # --------------------------------------------------------------------------
    @staticmethod
    def list_users(search=None, role=None, is_active=None, page=1, per_page=20):
        query = User.query.outerjoin(Employee, User.id == Employee.user_id)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term)
                )
            )

        if role:
            query = query.filter(User.role == role.strip().upper())

        if is_active is not None:
            query = query.filter(User.is_active.is_(is_active))

        total = query.count()
        users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if per_page else 1,
            "users": [u.to_dict() for u in users]
        }

    @staticmethod
    def get_user_details(user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        return user.to_dict()

    @staticmethod
    def update_user_role(user_id, new_role, actor_id):
        new_role = new_role.strip().upper()
        if new_role not in ["ADMIN", "HR", "EMPLOYEE"]:
            raise ValueError(f"Invalid role '{new_role}'. Must be ADMIN, HR, or EMPLOYEE.")

        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        old_role = user.role
        if old_role == new_role:
            return user.to_dict()

        # Prevent removing or demoting the last active administrator
        if old_role == "ADMIN" and new_role != "ADMIN":
            active_admin_count = User.query.filter_by(role="ADMIN", is_active=True).count()
            if active_admin_count <= 1:
                raise ValueError("Operation rejected: Cannot remove or demote the last active administrator account.")

        user.role = new_role

        # Audit log entry
        audit = AuditLog(
            user_id=actor_id,
            action="UPDATE_USER_ROLE",
            target_entity="USER",
            target_id=str(user.id),
            previous_state={"role": old_role},
            new_state={"role": new_role},
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(audit)
        db.session.commit()
        return user.to_dict()

    @staticmethod
    def update_user_status(user_id, is_active: bool, actor_id):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        if user.is_active == is_active:
            return user.to_dict()

        # Prevent deactivating the last active administrator
        if user.role == "ADMIN" and not is_active:
            active_admin_count = User.query.filter_by(role="ADMIN", is_active=True).count()
            if active_admin_count <= 1:
                raise ValueError("Operation rejected: Cannot deactivate the last active administrator account.")

        old_status = user.is_active
        user.is_active = is_active

        # If deactivating user, log token revocation notice
        if not is_active:
            RevokedToken.revoke(
                jti=f"deactivated-{user.id}-{datetime.now(timezone.utc).timestamp()}",
                token_type="all",
                user_id=user.id,
                expires_at=datetime.now(timezone.utc)
            )

        # Audit log entry
        audit = AuditLog(
            user_id=actor_id,
            action="UPDATE_USER_STATUS",
            target_entity="USER",
            target_id=str(user.id),
            previous_state={"is_active": old_status},
            new_state={"is_active": is_active},
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(audit)
        db.session.commit()
        return user.to_dict()

    # --------------------------------------------------------------------------
    # 2. Audit Log Viewer
    # --------------------------------------------------------------------------
    @staticmethod
    def list_audit_logs(user_id=None, action=None, target_entity=None, start_date=None, end_date=None, page=1, per_page=25):
        query = AuditLog.query

        if user_id:
            try:
                u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
                query = query.filter(AuditLog.user_id == u_uuid)
            except (ValueError, TypeError):
                pass

        if action:
            query = query.filter(AuditLog.action == action.strip().upper())

        if target_entity:
            query = query.filter(AuditLog.target_entity == target_entity.strip().upper())

        if start_date:
            try:
                s_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                query = query.filter(AuditLog.timestamp >= s_dt)
            except ValueError:
                pass

        if end_date:
            try:
                e_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                query = query.filter(AuditLog.timestamp <= e_dt)
            except ValueError:
                pass

        total = query.count()
        logs = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if per_page else 1,
            "audit_logs": [log.to_dict() for log in logs]
        }

    # --------------------------------------------------------------------------
    # 3. System Administration Dashboard
    # --------------------------------------------------------------------------
    @staticmethod
    def get_system_stats():
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = User.query.filter_by(is_active=False).count()
        total_employees = Employee.query.count()

        # Role distribution
        role_counts = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
        role_distribution = {role: count for role, count in role_counts}

        # Recent 10 audit events
        recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

        # Database health check
        db_status = "connected"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"error: {str(e)}"

        # Security rate-limit metrics
        sec_metrics = AuthService.get_security_metrics()

        metrics_data = {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "total_employees": total_employees,
            "roles_distribution": role_distribution,
        }
        health_data = {
            "api_service": "operational",
            "database_connection": db_status,
            "auth_subsystem": "enforced",
            "rate_limiter": "active"
        }

        return {
            "metrics": metrics_data,
            "user_metrics": metrics_data,
            "role_distribution": role_distribution,
            "roles_distribution": role_distribution,
            "recent_activity": [log.to_dict() for log in recent_logs],
            "security_telemetry": sec_metrics,
            "system_health": health_data,
            "database_health": health_data
        }

