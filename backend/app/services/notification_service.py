import uuid
from datetime import datetime, timezone, timedelta
from app.extension_registry import db
from app.models.notification import Notification
from app.models.user import User
from app.models.employee import Employee
from app.services.email_service import EmailService

class NotificationService:
    """Service providing creation, listing, marking, and dispatching of in-app & email notifications."""

    # --------------------------------------------------------------------------
    # 1. Notification Creation
    # --------------------------------------------------------------------------
    @staticmethod
    def create_notification(
        user_id,
        title,
        message,
        category="SYSTEM",
        priority="NORMAL",
        action_url=None,
        meta_data=None,
        send_email=True
    ):
        """
        Creates an in-app notification and optionally dispatches an email.
        Guarantees that email failure does not roll back or block database creation.
        """
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            raise ValueError("Invalid user_id for notification.")

        user = User.query.get(u_uuid)
        if not user:
            raise ValueError(f"User {user_id} not found.")

        # Prevent exact duplicate notification in the last 10 minutes
        ten_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
        existing = Notification.query.filter(
            Notification.user_id == u_uuid,
            Notification.title == title,
            Notification.message == message,
            Notification.created_at >= ten_mins_ago
        ).first()

        if existing:
            return existing

        notif = Notification(
            user_id=u_uuid,
            title=title,
            message=message,
            category=category,
            priority=priority,
            action_url=action_url,
            meta_data=meta_data,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()

        # Optional Email Dispatch (Safe & non-blocking)
        if send_email and user.email:
            try:
                html_body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; rounded: 8px;">
                    <h2 style="color: #1e3a8a;">ESMS Notification</h2>
                    <p style="font-size: 16px; font-weight: bold; color: #111827;">{title}</p>
                    <p style="font-size: 14px; color: #4b5563; line-height: 1.5;">{message}</p>
                    <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">Category: {category} | Priority: {priority}</p>
                </div>
                """
                EmailService.send_email(
                    to_email=user.email,
                    subject=f"[ESMS] {title}",
                    body_text=f"{title}\n\n{message}",
                    body_html=html_body
                )
            except Exception:
                pass

        return notif

    # --------------------------------------------------------------------------
    # 2. Bulk / System Announcements
    # --------------------------------------------------------------------------
    @staticmethod
    def broadcast_announcement(title, message, priority="NORMAL", target_role=None, current_user=None):
        """
        Creates an announcement for all active users (or filtered by role).
        Authorized for Admin and HR only.
        """
        if current_user and current_user.role not in ["ADMIN", "HR"]:
            raise PermissionError("Only Admin and HR can broadcast announcements.")

        query = User.query.filter_by(is_active=True)
        if target_role:
            query = query.filter_by(role=target_role)

        users = query.all()
        created_count = 0

        for u in users:
            NotificationService.create_notification(
                user_id=u.id,
                title=f"📢 {title}",
                message=message,
                category="ANNOUNCEMENT",
                priority=priority,
                action_url="/notifications",
                send_email=False  # Do not flood email for broadcast
            )
            created_count += 1

        return created_count

    # --------------------------------------------------------------------------
    # 3. Listing & Queries
    # --------------------------------------------------------------------------
    @staticmethod
    def get_user_notifications(user_id, unread_only=False, category=None, page=1, limit=20):
        """Retrieves paginated notifications for the specified user."""
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            raise ValueError("Invalid user_id.")

        query = Notification.query.filter_by(user_id=u_uuid)

        if unread_only:
            query = query.filter_by(is_read=False)
        if category:
            query = query.filter_by(category=category)

        total = query.count()
        unread_count = Notification.query.filter_by(user_id=u_uuid, is_read=False).count()

        items = (
            query.order_by(Notification.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return {
            "notifications": [n.to_dict() for n in items],
            "total": total,
            "unread_count": unread_count,
            "page": page,
            "limit": limit
        }

    @staticmethod
    def get_unread_count(user_id):
        """Returns the number of unread notifications for a user."""
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            return 0
        return Notification.query.filter_by(user_id=u_uuid, is_read=False).count()

    # --------------------------------------------------------------------------
    # 4. State Transitions (Read / Archive / Retention)
    # --------------------------------------------------------------------------
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Marks a specific notification as read for its owner."""
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            raise ValueError("Invalid user_id.")

        notif = Notification.query.filter_by(id=notification_id, user_id=u_uuid).first()
        if not notif:
            raise ValueError("Notification not found or access denied.")

        notif.mark_as_read()
        db.session.commit()
        return notif

    @staticmethod
    def mark_all_as_read(user_id):
        """Marks all unread notifications as read for a user."""
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            raise ValueError("Invalid user_id.")

        now = datetime.now(timezone.utc)
        count = Notification.query.filter_by(user_id=u_uuid, is_read=False).update(
            {"is_read": True, "read_at": now},
            synchronize_session=False
        )
        db.session.commit()
        return count

    @staticmethod
    def delete_notification(notification_id, user_id):
        """Deletes a single notification owned by user."""
        try:
            u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        except (ValueError, TypeError):
            raise ValueError("Invalid user_id.")

        notif = Notification.query.filter_by(id=notification_id, user_id=u_uuid).first()
        if not notif:
            raise ValueError("Notification not found or access denied.")

        db.session.delete(notif)
        db.session.commit()
        return True

    @staticmethod
    def clean_old_notifications(user_id=None, days_retention=30):
        """Retention policy: cleans read notifications older than N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_retention)
        query = Notification.query.filter(Notification.is_read == True, Notification.created_at < cutoff)
        if user_id:
            try:
                u_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
                query = query.filter_by(user_id=u_uuid)
            except (ValueError, TypeError):
                pass

        count = query.delete(synchronize_session=False)
        db.session.commit()
        return count

