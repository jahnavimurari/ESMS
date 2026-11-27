from marshmallow import Schema, fields, validate

class DepartmentCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    code = fields.String(required=True, validate=validate.Length(min=2, max=20))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
    is_active = fields.Boolean(load_default=True)

class DepartmentUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=2, max=100))
    code = fields.String(validate=validate.Length(min=2, max=20))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
    is_active = fields.Boolean()

class EmployeeCreateSchema(Schema):
    employee_code = fields.String(required=True, validate=validate.Length(min=2, max=30))
    first_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.String(load_default="Welcome123!", validate=validate.Length(min=6))
    role = fields.String(load_default="EMPLOYEE", validate=validate.OneOf(["ADMIN", "HR", "EMPLOYEE"]))
    phone = fields.String(allow_none=True, validate=validate.Length(max=30))
    gender = fields.String(allow_none=True, validate=validate.OneOf(["MALE", "FEMALE", "OTHER", "PREFER_NOT_TO_SAY"]))
    date_of_birth = fields.Date(allow_none=True)
    address = fields.String(allow_none=True)
    department_id = fields.Integer(required=True)
    designation = fields.String(required=True, validate=validate.Length(min=1, max=100))
    joining_date = fields.Date(allow_none=True)
    employment_type = fields.String(load_default="FULL_TIME", validate=validate.OneOf(["FULL_TIME", "PART_TIME", "CONTRACT", "INTERN"]))
    status = fields.String(load_default="ACTIVE", validate=validate.OneOf(["ACTIVE", "ON_LEAVE", "TERMINATED", "SUSPENDED"]))
    reporting_manager_id = fields.String(allow_none=True)
    profile_image_url = fields.String(allow_none=True, validate=validate.Length(max=500))

class EmployeeUpdateSchema(Schema):
    first_name = fields.String(validate=validate.Length(min=1, max=100))
    last_name = fields.String(validate=validate.Length(min=1, max=100))
    phone = fields.String(allow_none=True, validate=validate.Length(max=30))
    gender = fields.String(allow_none=True, validate=validate.OneOf(["MALE", "FEMALE", "OTHER", "PREFER_NOT_TO_SAY"]))
    date_of_birth = fields.Date(allow_none=True)
    address = fields.String(allow_none=True)
    department_id = fields.Integer()
    designation = fields.String(validate=validate.Length(min=1, max=100))
    joining_date = fields.Date(allow_none=True)
    employment_type = fields.String(validate=validate.OneOf(["FULL_TIME", "PART_TIME", "CONTRACT", "INTERN"]))
    status = fields.String(validate=validate.OneOf(["ACTIVE", "ON_LEAVE", "TERMINATED", "SUSPENDED"]))
    reporting_manager_id = fields.String(allow_none=True)
    profile_image_url = fields.String(allow_none=True, validate=validate.Length(max=500))
    role = fields.String(validate=validate.OneOf(["ADMIN", "HR", "EMPLOYEE"]))

class EmployeeStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(["ACTIVE", "ON_LEAVE", "TERMINATED", "SUSPENDED"]))
    is_active = fields.Boolean(allow_none=True)

department_create_schema = DepartmentCreateSchema()
department_update_schema = DepartmentUpdateSchema()
employee_create_schema = EmployeeCreateSchema()
employee_update_schema = EmployeeUpdateSchema()
employee_status_schema = EmployeeStatusSchema()

