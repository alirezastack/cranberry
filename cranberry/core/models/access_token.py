from olive.toolbox import MarshmallowDateTimeField
from marshmallow import Schema, fields, EXCLUDE
from olive.consts import UTC_DATE_FORMAT
import datetime


class AccessTokenSchema(Schema):
    class Meta:
        # Tuple or list of fields to include in the serialized result
        fields = ("_id", "client_id", "access_token", "refresh_token", "expires_in", "user_id", "scope", "grant_type",
                  "created_at")
        # exclude unknown fields from database on .load() call
        unknown = EXCLUDE
        datetimeformat = UTC_DATE_FORMAT

    client_id = fields.Str(required=True,
                           error_messages={'required': {'message': 'ClientID required', 'code': 400}})
    access_token = fields.Str(required=True,
                              error_messages={'required': {'message': 'access_token required', 'code': 400}})
    refresh_token = fields.Str(required=True,
                               error_messages={'required': {'message': 'refresh_token required', 'code': 400}})
    expires_in = fields.Integer(required=True,
                                error_messages={'required': {'message': 'expires_in required', 'code': 400}})
    user_id = fields.Str(required=True,
                         error_messages={'required': {'message': 'user_id required', 'code': 400}})
    scope = fields.List(cls_or_instance=fields.Str(),
                        default=['all'])
    grant_type = fields.Str(required=True,
                            error_messages={'required': {'message': 'grant_type required', 'code': 400}})
    # dump_only: Fields to skip during deserialization(i.e.: .load())
    created_at = MarshmallowDateTimeField(dump_only=True,
                                          default=lambda: datetime.datetime.utcnow(),
                                          allow_none=False
                                          )
