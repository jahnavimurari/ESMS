from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class TaskCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=3, max=200), error_messages={"required": "Task title is required."})
    description = fields.String(allow_none=True)
    assigned_to = fields.String(required=True, error_messages={"required": "Assignee employee ID is required."})
    department_id = fields.Integer(allow_none=True)
    priority = fields.String(load_default="MEDIUM", validate=validate.OneOf(["LOW", "MEDIUM", "HIGH", "URGENT"]))
    category = fields.String(allow_none=True, validate=validate.Length(max=50))
    start_date = fields.Date(allow_none=True)
    due_date = fields.Date(allow_none=True)

    @validates_schema
    def validate_dates(self, data, **kwargs):
        start = data.get("start_date")
        due = data.get("due_date")
        if start and due and due < start:
            raise ValidationError({"due_date": ["Due date cannot be earlier than start date."]})

class TaskUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(min=3, max=200))
    description = fields.String(allow_none=True)
    assigned_to = fields.String(allow_none=True)
    department_id = fields.Integer(allow_none=True)
    priority = fields.String(validate=validate.OneOf(["LOW", "MEDIUM", "HIGH", "URGENT"]))
    category = fields.String(allow_none=True, validate=validate.Length(max=50))
    start_date = fields.Date(allow_none=True)
    due_date = fields.Date(allow_none=True)

    @validates_schema
    def validate_dates(self, data, **kwargs):
        start = data.get("start_date")
        due = data.get("due_date")
        if start and due and due < start:
            raise ValidationError({"due_date": ["Due date cannot be earlier than start date."]})

class TaskStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(["TODO", "IN_PROGRESS", "REVIEW", "COMPLETED", "BLOCKED", "CANCELLED"]), error_messages={"required": "Status is required."})
    comment = fields.String(allow_none=True, validate=validate.Length(max=1000))

class TaskAssignSchema(Schema):
    assigned_to = fields.String(required=True, error_messages={"required": "Assignee employee ID is required."})
    comment = fields.String(allow_none=True, validate=validate.Length(max=1000))

class TaskCancelSchema(Schema):
    reason = fields.String(allow_none=True, validate=validate.Length(max=1000))

task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
task_status_schema = TaskStatusSchema()
task_assign_schema = TaskAssignSchema()
task_cancel_schema = TaskCancelSchema()

