from marshmallow import Schema, fields, validate

class AttendanceCheckInSchema(Schema):
    notes = fields.String(allow_none=True, validate=validate.Length(max=500))

class AttendanceCheckOutSchema(Schema):
    notes = fields.String(allow_none=True, validate=validate.Length(max=500))

class AttendanceCorrectionSchema(Schema):
    check_in = fields.DateTime(allow_none=True)
    check_out = fields.DateTime(allow_none=True)
    status = fields.String(allow_none=True, validate=validate.OneOf(["PRESENT", "LATE", "HALF_DAY", "ABSENT"]))
    total_hours = fields.Float(allow_none=True, validate=validate.Range(min=0.0, max=24.0))
    notes = fields.String(allow_none=True, validate=validate.Length(max=500))

attendance_check_in_schema = AttendanceCheckInSchema()
attendance_check_out_schema = AttendanceCheckOutSchema()
attendance_correction_schema = AttendanceCorrectionSchema()

