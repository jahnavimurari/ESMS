from marshmallow import Schema, fields, validate

class LeaveTypeCreateSchema(Schema):
    code = fields.String(required=True, validate=validate.Length(min=2, max=20))
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
    days_per_year = fields.Integer(load_default=12, validate=validate.Range(min=0, max=365))
    is_paid = fields.Boolean(load_default=True)
    is_active = fields.Boolean(load_default=True)

class LeaveTypeUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=2, max=100))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
    days_per_year = fields.Integer(validate=validate.Range(min=0, max=365))
    is_paid = fields.Boolean()
    is_active = fields.Boolean()

class LeaveApplySchema(Schema):
    leave_type_id = fields.Integer(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    reason = fields.String(required=True, validate=validate.Length(min=3, max=1000))

class LeaveUpdateSchema(Schema):
    leave_type_id = fields.Integer()
    start_date = fields.Date()
    end_date = fields.Date()
    reason = fields.String(validate=validate.Length(min=3, max=1000))

class LeaveReviewSchema(Schema):
    comments = fields.String(allow_none=True, validate=validate.Length(max=500))

leave_type_create_schema = LeaveTypeCreateSchema()
leave_type_update_schema = LeaveTypeUpdateSchema()
leave_apply_schema = LeaveApplySchema()
leave_update_schema = LeaveUpdateSchema()
leave_review_schema = LeaveReviewSchema()

