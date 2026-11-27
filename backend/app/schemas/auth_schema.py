from marshmallow import Schema, fields, validate

class LoginSchema(Schema):
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.String(required=True, validate=validate.Length(min=6, max=128))

class ChangePasswordSchema(Schema):
    current_password = fields.String(required=True, validate=validate.Length(min=6, max=128))
    new_password = fields.String(required=True, validate=validate.Length(min=8, max=128))

class RefreshTokenSchema(Schema):
    refresh_token = fields.String(required=False)

login_schema = LoginSchema()
change_password_schema = ChangePasswordSchema()
refresh_token_schema = RefreshTokenSchema()

