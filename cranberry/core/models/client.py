from olive.toolbox import MarshmallowDateTimeField
from marshmallow import Schema, fields, EXCLUDE
from olive.consts import UTC_DATE_FORMAT
import datetime


class ClientSchema(Schema):
    class Meta:
        # Tuple or list of fields to include in the serialized result
        fields = ("_id", "client_id", "client_secret", "fullname", "logo",
                  "created_at", "updated_at", "redirection_uris", "description",
                  "is_active")
        # exclude unknown fields from database on .load() call
        unknown = EXCLUDE
        datetimeformat = UTC_DATE_FORMAT

    client_id = fields.Str(required=True,
                           error_messages={'required': {'message': 'ClientID required', 'code': 400}})
    client_secret = fields.Str(required=True,
                               error_messages={'required': {'message': 'ClientSecret required', 'code': 400}})
    redirection_uris = fields.List(fields.Str(), allow_none=True)
    description = fields.Str(allow_none=True)
    fullname = fields.Str()
    logo = fields.Str(allow_none=True)
    is_active = fields.Bool(default=False)
    # dump_only: Fields to skip during deserialization(i.e.: .load())
    created_at = MarshmallowDateTimeField(dump_only=True,
                                          default=lambda: datetime.datetime.utcnow(),
                                          allow_none=False
                                          )
    updated_at = MarshmallowDateTimeField(dump_only=True,
                                          default=lambda: datetime.datetime.utcnow(),
                                          allow_none=False
                                          )
