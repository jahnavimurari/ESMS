from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Integer, SmallInteger, String, Text, Date, DateTime, 
    ForeignKey, CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from app.extension_registry import db

RATING_DEFINITIONS = {
    1: {"score": 1, "label": "Needs Improvement", "description": "Performance consistently falls below expected standards."},
    2: {"score": 2, "label": "Below Expectations", "description": "Performance meets some requirements but needs improvement in key areas."},
    3: {"score": 3, "label": "Meets Expectations", "description": "Consistently meets job requirements and performance goals."},
    4: {"score": 4, "label": "Exceeds Expectations", "description": "Frequently exceeds performance targets and demonstrates strong initiative."},
    5: {"score": 5, "label": "Outstanding", "description": "Consistently delivers exceptional outcomes and serves as an organization-wide model."}
}

class PerformanceCycle(db.Model):
    __tablename__ = "performance_cycles"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    title = db.Column(String(100), nullable=False)
    description = db.Column(Text, nullable=True)
    start_date = db.Column(Date, nullable=False)
    end_date = db.Column(Date, nullable=False)
    due_date = db.Column(Date, nullable=False)
    status = db.Column(String(20), nullable=False, default="ACTIVE")
    created_by = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="chk_cycle_date_order"),
        CheckConstraint("due_date >= start_date", name="chk_cycle_due_after_start"),
        CheckConstraint("status IN ('ACTIVE', 'CLOSED')", name="chk_cycle_status"),
    )

    reviews = db.relationship("PerformanceReview", back_populates="cycle", cascade="all, delete-orphan", lazy="dynamic")
    creator = db.relationship("User")

    def to_dict(self):
        """Returns dictionary representation of performance cycle with completion metrics."""
        total_reviews = self.reviews.count()
        completed_reviews = self.reviews.filter_by(status="COMPLETED").count()
        in_progress_reviews = self.reviews.filter(PerformanceReview.status.in_(["DRAFT", "SELF_ASSESSMENT", "MANAGER_REVIEW"])).count()

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metrics": {
                "total_reviews": total_reviews,
                "completed": completed_reviews,
                "in_progress": in_progress_reviews,
                "completion_rate": round((completed_reviews / total_reviews * 100), 1) if total_reviews > 0 else 0.0
            }
        }

    def __repr__(self):
        return f"<PerformanceCycle id={self.id} title={self.title} status={self.status}>"


class PerformanceReview(db.Model):
    __tablename__ = "performance_reviews"

    id = db.Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    cycle_id = db.Column(Integer, ForeignKey("performance_cycles.id", ondelete="SET NULL"), nullable=True, index=True)
    employee_id = db.Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    reviewer_id = db.Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    review_period = db.Column(String(50), nullable=False, index=True)
    status = db.Column(String(25), nullable=False, default="DRAFT")

    # Employee Self-Assessment Fields
    self_rating = db.Column(SmallInteger, nullable=True)
    accomplishments = db.Column(Text, nullable=True)
    challenges = db.Column(Text, nullable=True)
    skills_learned = db.Column(Text, nullable=True)
    goals_achievement = db.Column(Text, nullable=True)
    submitted_at = db.Column(DateTime(timezone=True), nullable=True)

    # Manager / Reviewer Evaluation Fields
    rating = db.Column(SmallInteger, nullable=True)
    manager_feedback = db.Column(Text, nullable=True)
    strengths = db.Column(Text, nullable=True)
    areas_for_improvement = db.Column(Text, nullable=True)
    development_plan = db.Column(Text, nullable=True)
    completed_at = db.Column(DateTime(timezone=True), nullable=True)

    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="chk_perf_rating_range"),
        CheckConstraint("self_rating IS NULL OR (self_rating >= 1 AND self_rating <= 5)", name="chk_perf_self_rating_range"),
        CheckConstraint("status IN ('DRAFT', 'SELF_ASSESSMENT', 'MANAGER_REVIEW', 'COMPLETED', 'CANCELLED')", name="chk_perf_status"),
        Index("idx_perf_emp_period", "employee_id", "review_period"),
        Index("idx_perf_emp_cycle", "employee_id", "cycle_id"),
        UniqueConstraint("employee_id", "cycle_id", name="uq_perf_emp_cycle"),
    )

    employee = db.relationship("Employee", back_populates="performance_reviews")
    reviewer = db.relationship("User", back_populates="submitted_reviews")
    cycle = db.relationship("PerformanceCycle", back_populates="reviews")

    def to_dict(self):
        """Returns comprehensive dictionary representation of a performance review."""
        rating_def = RATING_DEFINITIONS.get(self.rating) if self.rating else None
        self_rating_def = RATING_DEFINITIONS.get(self.self_rating) if self.self_rating else None

        return {
            "id": self.id,
            "cycle_id": self.cycle_id,
            "cycle_title": self.cycle.title if self.cycle else None,
            "cycle_status": self.cycle.status if self.cycle else None,
            "due_date": self.cycle.due_date.isoformat() if (self.cycle and self.cycle.due_date) else None,
            "employee_id": str(self.employee_id),
            "employee_name": self.employee.full_name if self.employee else None,
            "employee_code": self.employee.employee_code if self.employee else None,
            "department_id": self.employee.department_id if self.employee else None,
            "department_name": self.employee.department.name if (self.employee and self.employee.department) else None,
            "reviewer_id": str(self.reviewer_id) if self.reviewer_id else None,
            "reviewer_email": self.reviewer.email if self.reviewer else None,
            "review_period": self.review_period,
            "status": self.status,
            "self_assessment": {
                "self_rating": self.self_rating,
                "self_rating_label": self_rating_def["label"] if self_rating_def else None,
                "accomplishments": self.accomplishments,
                "challenges": self.challenges,
                "skills_learned": self.skills_learned,
                "goals_achievement": self.goals_achievement,
                "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            },
            "manager_evaluation": {
                "rating": self.rating,
                "rating_label": rating_def["label"] if rating_def else None,
                "rating_description": rating_def["description"] if rating_def else None,
                "manager_feedback": self.manager_feedback,
                "strengths": self.strengths,
                "areas_for_improvement": self.areas_for_improvement,
                "development_plan": self.development_plan,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<PerformanceReview emp={self.employee_id} period={self.review_period} status={self.status} rating={self.rating}>"
