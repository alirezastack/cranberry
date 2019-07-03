from marshmallow import fields
import datetime


# This is a workaround you can read more here:
#     - https://github.com/marshmallow-code/marshmallow/issues/656#issuecomment-318587611
class MarshmallowDateTimeField(fields.DateTime):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, datetime.datetime):
            return value
        return super()._deserialize(value, attr, data)
