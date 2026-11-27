from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class PerformanceCycleCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=3, max=100), error_messages={"required": "Cycle title is required."})
    description = fields.String(allow_none=True)
    start_date = fields.Date(required=True, error_messages={"required": "Start date is required."})
    end_date = fields.Date(required=True, error_messages={"required": "End date is required."})
    due_date = fields.Date(required=True, error_messages={"required": "Due date is required."})
    status = fields.String(load_default="ACTIVE", validate=validate.OneOf(["ACTIVE", "CLOSED"]))

    @validates_schema
    def validate_dates(self, data, **kwargs):
        start = data.get("start_date")
        end = data.get("end_date")
        due = data.get("due_date")
        if start and end and end < start:
            raise ValidationError({"end_date": ["End date cannot be earlier than start date."]})
        if start and due and due < start:
            raise ValidationError({"due_date": ["Due date cannot be earlier than start date."]})


class PerformanceCycleUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(min=3, max=100))
    description = fields.String(allow_none=True)
    start_date = fields.Date()
    end_date = fields.Date()
    due_date = fields.Date()
    status = fields.String(validate=validate.OneOf(["ACTIVE", "CLOSED"]))

    @validates_schema
    def validate_dates(self, data, **kwargs):
        start = data.get("start_date")
        end = data.get("end_date")
        due = data.get("due_date")
        if start and end and end < start:
            raise ValidationError({"end_date": ["End date cannot be earlier than start date."]})
        if start and due and due < start:
            raise ValidationError({"due_date": ["Due date cannot be earlier than start date."]})


class PerformanceCycleStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(["ACTIVE", "CLOSED"]), error_messages={"required": "Status is required."})


class PerformanceReviewCreateSchema(Schema):
    cycle_id = fields.Integer(required=True, error_messages={"required": "Performance cycle ID is required."})
    employee_id = fields.String(required=True, error_messages={"required": "Employee ID is required."})
    reviewer_id = fields.String(allow_none=True)
    review_period = fields.String(allow_none=True, validate=validate.Length(max=50))


class SelfAssessmentUpdateSchema(Schema):
    self_rating = fields.Integer(allow_none=True, validate=validate.Range(min=1, max=5, error="Self-rating must be an integer between 1 and 5."))
    accomplishments = fields.String(allow_none=True)
    challenges = fields.String(allow_none=True)
    skills_learned = fields.String(allow_none=True)
    goals_achievement = fields.String(allow_none=True)


class ManagerReviewSchema(Schema):
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5, error="Rating must be an integer between 1 and 5."), error_messages={"required": "Manager rating is required."})
    manager_feedback = fields.String(required=True, validate=validate.Length(min=5, max=5000), error_messages={"required": "Manager feedback is required."})
    strengths = fields.String(allow_none=True)
    areas_for_improvement = fields.String(allow_none=True)
    development_plan = fields.String(allow_none=True)


class ReviewReopenSchema(Schema):
    reason = fields.String(required=True, validate=validate.Length(min=5, max=1000), error_messages={"required": "Justification reason is required to reopen a review."})


performance_cycle_create_schema = PerformanceCycleCreateSchema()
performance_cycle_update_schema = PerformanceCycleUpdateSchema()
performance_cycle_status_schema = PerformanceCycleStatusSchema()
performance_review_create_schema = PerformanceReviewCreateSchema()
self_assessment_update_schema = SelfAssessmentUpdateSchema()
manager_review_schema = ManagerReviewSchema()
review_reopen_schema = ReviewReopenSchema()

