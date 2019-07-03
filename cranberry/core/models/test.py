from marshmallow import Schema, fields
#
#
# class CartSchema(Schema):
#     name = fields.Str(required=True)
#     created_at = fields.DateTime()
#     status = fields.Str()
#
#
# out = CartSchema().load(dict(
#     name=12,
#     created_at='2018-12-12 12:22:10',
#     status='failed'
# ))
# print(out)

from marshmallow import ValidationError


class UserSchema(Schema):
    name = fields.String(required=True)
    age = fields.Integer(
        required=True,
        error_messages={'required': 'Age is required.'}
    )
    city = fields.String(
        required=True,
        error_messages={'required': {'message': 'City required', 'code': 400}}
    )
    email = fields.Email()


try:
    result = UserSchema().dump({'email': 'foo@bar.com'})
    print(result)
except ValidationError as err:
    print('exception raised:')
    print(err.messages)

# {'name': ['Missing data for required field.'],
#  'age': ['Age is required.'],
#  'city': {'message': 'City required', 'code': 400}}
